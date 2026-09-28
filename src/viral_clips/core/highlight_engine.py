"""Highlight detection and ranking for Viral Clips AI.

Quality Core v2 deliberately avoids dataset-specific topics/titles. Candidate generation is
based on sentence boundaries and generic narrative signals; final ranking is delegated to the
configured LLM provider with an explicitly-marked heuristic fallback.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger

from viral_clips.config import settings
from viral_clips.core.llm_providers import (
    PROMPT_VERSION,
    SCORING_VERSION,
    VIRAL_WEIGHTS,
    get_llm_provider,
)

SCHEMA_VERSION = "1.1.0"
SCORER_VERSION = SCORING_VERSION
SCORE_WEIGHTS = VIRAL_WEIGHTS

# Generic linguistic signals only. Never add phrases from a particular benchmark/video here.
HOOK_TERMS = {
    "почему", "как", "зачем", "ошибка", "секрет", "правда", "главное", "представьте",
    "никогда", "всегда", "что если", "how", "why", "mistake", "secret", "truth", "imagine",
}
BAD_START_WORDS = {
    "и", "а", "но", "что", "чтобы", "потому", "поэтому", "то", "или", "либо", "который",
    "которая", "которые", "and", "but", "so", "because", "which", "that", "or",
}
DANGLING_PRONOUNS = {
    "это", "этот", "эта", "эти", "такой", "такая", "такие", "он", "она", "они",
    "this", "that", "these", "he", "she", "they",
}
PAYOFF_TERMS = {
    "в итоге", "поэтому", "вывод", "результат", "я понял", "оказалось", "на самом деле",
    "итого", "следовательно", "the result", "in the end", "that's why", "turns out", "lesson",
}
TERMINAL_RE = re.compile(r'[.!?]+[\"»”)]?$')


def calculate_final_score(scores: Dict[str, float]) -> float:
    """Return the configured weighted score on a stable 0..10 scale."""
    total = 0.0
    for dim, weight in SCORE_WEIGHTS.items():
        value = max(0.0, min(10.0, float(scores.get(dim, 5.0))))
        total += value * weight
    return round(total, 2)


def _ms(item: Dict[str, Any], field: str) -> int:
    ms_key = f"{field}_ms"
    if ms_key in item:
        return int(item[ms_key])
    return int(float(item.get(field, 0.0)) * 1000)


def reconstruct_sentences(transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build timestamped sentences from words first, then transcript segments as fallback."""
    sentences: List[Dict[str, Any]] = []
    words = transcript.get("words") or []

    if words:
        current: List[Dict[str, Any]] = []
        tokens: List[str] = []
        for word in words:
            token = str(word.get("word", "")).strip()
            if not token:
                continue
            current.append(word)
            tokens.append(token)
            if TERMINAL_RE.search(token):
                sentences.append(_sentence_from_words(current, tokens, len(sentences)))
                current, tokens = [], []
        if current:
            sentences.append(_sentence_from_words(current, tokens, len(sentences)))
        return sentences

    current_segments: List[Dict[str, Any]] = []
    for segment in transcript.get("segments") or []:
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        current_segments.append(segment)
        if TERMINAL_RE.search(text):
            sentences.append(_sentence_from_segments(current_segments, len(sentences)))
            current_segments = []
    if current_segments:
        sentences.append(_sentence_from_segments(current_segments, len(sentences)))
    return sentences


def _sentence_from_words(words: List[Dict[str, Any]], tokens: List[str], idx: int) -> Dict[str, Any]:
    start_ms, end_ms = _ms(words[0], "start"), _ms(words[-1], "end")
    text = " ".join(tokens).strip()
    return {
        "idx": idx,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_s": round((end_ms - start_ms) / 1000.0, 2),
        "text": text,
        "first_word": tokens[0] if tokens else "",
        "last_word": tokens[-1] if tokens else "",
    }


def _sentence_from_segments(segments: List[Dict[str, Any]], idx: int) -> Dict[str, Any]:
    start_ms, end_ms = _ms(segments[0], "start"), _ms(segments[-1], "end")
    text = " ".join(str(s.get("text", "")).strip() for s in segments).strip()
    tokens = text.split()
    return {
        "idx": idx,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_s": round((end_ms - start_ms) / 1000.0, 2),
        "text": text,
        "first_word": tokens[0] if tokens else "",
        "last_word": tokens[-1] if tokens else "",
    }


def _generic_window_features(text: str, first_sentence: str, last_sentence: str, duration_s: float) -> Dict[str, float]:
    words = text.split()
    density = len(words) / max(duration_s, 1.0)
    first_l = first_sentence.lower().strip()
    last_l = last_sentence.lower().strip()
    first_token = re.sub(r"[^\w'-]", "", first_l.split()[0]) if first_l.split() else ""

    opening_penalty = 0.0
    if first_token in BAD_START_WORDS:
        opening_penalty += 1.5
    if any(first_l.startswith(f"{p} ") or first_l == p for p in DANGLING_PRONOUNS):
        opening_penalty += 1.25

    hook_signal = 0.0
    if "?" in first_sentence:
        hook_signal += 1.0
    if any(term in first_l for term in HOOK_TERMS):
        hook_signal += 1.0

    payoff_signal = 0.0
    if TERMINAL_RE.search(last_sentence.strip()):
        payoff_signal += 0.75
    if any(term in last_l for term in PAYOFF_TERMS):
        payoff_signal += 1.0

    length_signal = 1.0 if 28.0 <= duration_s <= 58.0 else 0.0
    density_penalty = 1.25 if density < 1.0 else 0.0
    return {
        "speech_density": round(density, 3),
        "opening_penalty": opening_penalty,
        "density_penalty": density_penalty,
        "hook_signal": hook_signal,
        "payoff_signal": payoff_signal,
        "length_signal": length_signal,
    }


def generate_candidate_windows(
    transcript: Dict[str, Any],
    min_duration_s: float = 20.0,
    max_duration_s: float = 75.0,
    step_segments: int = 1,
    complete_sentences: bool = True,
) -> List[Dict[str, Any]]:
    """Generate generic, self-contained candidate windows without topic-specific rules."""
    if complete_sentences:
        sentences = reconstruct_sentences(transcript)
        if sentences:
            windows: List[Dict[str, Any]] = []
            for start_idx, start in enumerate(sentences):
                for end_idx in range(start_idx, len(sentences)):
                    end = sentences[end_idx]
                    duration_s = (end["end_ms"] - start["start_ms"]) / 1000.0
                    if duration_s < min_duration_s:
                        continue
                    if duration_s > max_duration_s:
                        break
                    text = " ".join(s["text"] for s in sentences[start_idx : end_idx + 1]).strip()
                    features = _generic_window_features(text, start["text"], end["text"], duration_s)
                    windows.append({
                        "start_ms": start["start_ms"],
                        "end_ms": end["end_ms"],
                        "duration_s": round(duration_s, 2),
                        "start_segment_idx": start_idx,
                        "end_segment_idx": end_idx,
                        "text": text,
                        "first_sentence": start["text"],
                        "last_sentence": end["text"],
                        **features,
                    })
            if windows:
                return windows

    segments = transcript.get("segments") or []
    windows: List[Dict[str, Any]] = []
    for start_idx in range(0, len(segments), max(1, step_segments)):
        start_ms = _ms(segments[start_idx], "start")
        texts: List[str] = []
        for end_idx in range(start_idx, len(segments)):
            segment = segments[end_idx]
            texts.append(str(segment.get("text", "")).strip())
            end_ms = _ms(segment, "end")
            duration_s = (end_ms - start_ms) / 1000.0
            if duration_s < min_duration_s:
                continue
            if duration_s > max_duration_s:
                break
            text = " ".join(texts).strip()
            first_sentence = texts[0] if texts else ""
            last_sentence = texts[-1] if texts else ""
            windows.append({
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_s": round(duration_s, 2),
                "start_segment_idx": start_idx,
                "end_segment_idx": end_idx,
                "text": text,
                "first_sentence": first_sentence,
                "last_sentence": last_sentence,
                **_generic_window_features(text, first_sentence, last_sentence, duration_s),
            })
    return windows


def heuristic_pre_rank(windows: List[Dict[str, Any]], limit: int = 30) -> List[Dict[str, Any]]:
    """Cheap generic pre-ranker used only to control LLM cost/context size."""
    ranked: List[Dict[str, Any]] = []
    for window in windows:
        score = 5.0
        score += 0.9 * float(window.get("hook_signal", 0.0))
        score += 0.9 * float(window.get("payoff_signal", 0.0))
        score += 0.6 * float(window.get("length_signal", 0.0))
        score -= float(window.get("opening_penalty", 0.0))
        score -= float(window.get("density_penalty", 0.0))
        copy = dict(window)
        copy["pre_rank_score"] = round(max(0.0, min(10.0, score)), 2)
        ranked.append(copy)
    ranked.sort(key=lambda item: item["pre_rank_score"], reverse=True)
    return ranked[:limit]


def score_window_offline(window: Dict[str, Any]) -> Tuple[Dict[str, float], str, str]:
    """Generic fallback scorer. It intentionally has no benchmark/video-specific vocabulary."""
    first = str(window.get("first_sentence") or window.get("text", "")[:120]).strip()
    text = str(window.get("text", "")).strip()
    hook = 5.0 + 1.2 * float(window.get("hook_signal", 0.0)) - float(window.get("opening_penalty", 0.0))
    payoff = 5.0 + 1.3 * float(window.get("payoff_signal", 0.0))
    context = 7.0 - float(window.get("opening_penalty", 0.0))
    density = float(window.get("speech_density", 0.0))
    pace = 8.0 if 1.6 <= density <= 3.5 else 6.0 if 1.0 <= density <= 4.5 else 4.5
    emotion = 6.0 + (1.0 if "!" in text else 0.0) + (0.5 if "?" in text else 0.0)
    novelty = 5.0
    shareability = 5.5 + (0.75 if "?" in first else 0.0)

    scores = {
        "hook_strength": round(max(0.0, min(10.0, hook)), 1),
        "standalone_context": round(max(0.0, min(10.0, context)), 1),
        "payoff": round(max(0.0, min(10.0, payoff)), 1),
        "emotion": round(max(0.0, min(10.0, emotion)), 1),
        "novelty": round(novelty, 1),
        "pace": round(pace, 1),
        "shareability": round(max(0.0, min(10.0, shareability)), 1),
    }
    title_words = re.sub(r"\s+", " ", first).split()[:7]
    title = " ".join(title_words).strip(" ,.!?—-") or "Ключевой момент"
    reason = "Generic fallback score based on opening clarity, closure, duration and speech density."
    return scores, title, reason


def score_candidates_llm(
    candidates: List[Dict[str, Any]],
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None,
    provider_name: Optional[str] = None,
    language: str = "ru",
    allow_fallback: Optional[bool] = None,
    highlight_strategy: Optional[List[str]] = None,
    content_type: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    for idx, candidate in enumerate(candidates):
        candidate.setdefault("id", f"cand_{idx + 1}")

    resolved_provider = provider_name
    if not resolved_provider:
        resolved_provider = "gemini" if gemini_key else "openai" if openai_key else None

    try:
        provider = get_llm_provider(provider_name=resolved_provider, allow_fallback=allow_fallback)
        logger.info("Scoring {} candidates via {} ({})", len(candidates), provider.provider_name, provider.model_name)
        scores = provider.score_candidates(
            candidates,
            language=language,
            highlight_strategy=highlight_strategy,
            content_type=content_type,
        )
        score_map = {score.candidate_id: score for score in scores}
        provider_used = provider.provider_name
        model_used = provider.model_name
        fallback_used = provider.is_fallback
    except Exception as exc:
        fallback_allowed = allow_fallback if allow_fallback is not None else settings.allow_heuristic_llm_fallback
        if not fallback_allowed:
            raise
        logger.warning("LLM scoring failed; using explicit generic fallback: {}", exc)
        score_map = {}
        provider_used = "heuristic"
        model_used = "generic-heuristic-v3"
        fallback_used = True

    results: List[Dict[str, Any]] = []
    for candidate in candidates:
        score_obj = score_map.get(candidate["id"])
        if score_obj is not None:
            score_dict = {
                "hook_strength": score_obj.hook_strength,
                "standalone_context": score_obj.standalone_context,
                "payoff": score_obj.payoff,
                "emotion": score_obj.emotion,
                "novelty": score_obj.novelty,
                "pace": score_obj.pace,
                "shareability": score_obj.shareability,
            }
            final_100 = float(score_obj.final_score or calculate_final_score(score_dict) * 10.0)
            title, reason = score_obj.title, score_obj.reason
        else:
            score_dict, title, reason = score_window_offline(candidate)
            final_100 = calculate_final_score(score_dict) * 10.0

        final_100 = round(max(0.0, min(100.0, final_100)), 1)
        score_dict["final_score"] = final_100
        results.append({
            **candidate,
            "title": title,
            "reason": reason,
            "scores": score_dict,
            "final_score": round(final_100 / 10.0, 2),
            "final_score_100": final_100,
            "scorer_version": f"{SCORING_VERSION}-{model_used}",
            "scorer_provider": provider_used,
            "fallback_used": fallback_used,
        })

    results.sort(key=lambda item: item["final_score_100"], reverse=True)
    return results, {"provider": provider_used, "model": model_used, "fallback_used": fallback_used}


def diversify_and_select_top_n(
    scored_candidates: List[Dict[str, Any]],
    desired_count: int = 5,
    max_overlap_ratio: float = 0.35,
) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for candidate in scored_candidates:
        if len(selected) >= desired_count:
            break
        start, end = int(candidate["start_ms"]), int(candidate["end_ms"])
        duration = max(1, end - start)
        if any(
            max(0, min(end, int(existing["end_ms"])) - max(start, int(existing["start_ms"])))
            / min(duration, max(1, int(existing["end_ms"]) - int(existing["start_ms"])))
            > max_overlap_ratio
            for existing in selected
        ):
            continue
        selected.append({**candidate, "rank": len(selected) + 1})
    return selected


def detect_highlights(
    transcript_path_or_dict: Union[str, Path, Dict[str, Any]],
    output_dir: Optional[Union[str, Path]] = None,
    clip_count: int = 5,
    min_duration_s: float = 20.0,
    max_duration_s: float = 75.0,
    highlight_strategy: Optional[List[str]] = None,
    content_type: Optional[str] = None,
    complete_sentences: bool = True,
    options: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if isinstance(transcript_path_or_dict, (str, Path)):
        transcript_path = Path(transcript_path_or_dict).resolve()
        transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
        out_dir = Path(output_dir) if output_dir else transcript_path.parent
    else:
        transcript = transcript_path_or_dict
        out_dir = Path(output_dir) if output_dir else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)

    if options and "complete_sentences" in options:
        complete_sentences = bool(options["complete_sentences"])

    windows = generate_candidate_windows(
        transcript,
        min_duration_s=min_duration_s,
        max_duration_s=max_duration_s,
        complete_sentences=complete_sentences,
    )
    if not windows:
        segments = transcript.get("segments") or []
        duration_s = float(transcript.get("duration_s") or max_duration_s)
        windows = [{
            "start_ms": 0,
            "end_ms": int(duration_s * 1000),
            "duration_s": duration_s,
            "text": " ".join(str(s.get("text", "")) for s in segments),
            "first_sentence": str(segments[0].get("text", "")) if segments else "",
            "last_sentence": str(segments[-1].get("text", "")) if segments else "",
            "speech_density": 0.0,
            "opening_penalty": 0.0,
            "density_penalty": 0.0,
            "hook_signal": 0.0,
            "payoff_signal": 0.0,
            "length_signal": 0.0,
        }]

    # Keep enough diversity for the LLM, but bound context/cost.
    pre_ranked = heuristic_pre_rank(windows, limit=30)
    llm_candidates = pre_ranked[:20]
    language = transcript.get("detected_language") or transcript.get("language") or "ru"
    scored, provenance = score_candidates_llm(
        llm_candidates,
        language=language,
        highlight_strategy=highlight_strategy,
        content_type=content_type,
    )
    top_n = diversify_and_select_top_n(scored, desired_count=clip_count)

    created_at = datetime.now(timezone.utc).isoformat()
    candidates_artifact = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at,
        "total_generated": len(windows),
        "total_pre_ranked": len(pre_ranked),
        "total_scored": len(scored),
        "candidates": scored,
    }
    ranking_artifact = {
        "schema_version": SCHEMA_VERSION,
        "scorer_version": SCORER_VERSION,
        "provider": provenance["provider"],
        "model": provenance["model"],
        "prompt_version": PROMPT_VERSION,
        "scoring_version": SCORING_VERSION,
        "fallback_used": provenance["fallback_used"],
        "highlight_strategy": highlight_strategy or ["auto"],
        "content_type": content_type or "auto",
        "created_at": created_at,
        "clip_count": len(top_n),
        "score_weights": SCORE_WEIGHTS,
        "top_clips": top_n,
    }

    (out_dir / "candidates.json").write_text(json.dumps(candidates_artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "ranking.json").write_text(json.dumps(ranking_artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.success("Generated {} ranked clips", len(top_n))
    return candidates_artifact, ranking_artifact
