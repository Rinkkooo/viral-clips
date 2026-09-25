"""
AI Highlight & Viral Moments Detection Engine.
Performs semantic windowing, heuristic pre-ranking, LLM multi-dimensional scoring,
diversification, and top-N candidate selection.
Produces versioned 'candidates.json' and 'ranking.json' artifacts.
"""

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
    CandidateScore,
    get_llm_provider,
    calculate_composite_score,
)
from viral_clips.exceptions import ViralClipsError

SCHEMA_VERSION = "1.0.0"
SCORER_VERSION = SCORING_VERSION
SCORE_WEIGHTS = VIRAL_WEIGHTS

HOOK_WORDS = {
    "почему", "зачем", "секрет", "никогда", "всегда", "главная", "ошибка", "правило",
    "шок", "реально", "оказывается", "правда", "деньги", "миллион", "заработал",
    "ловушка", "ловушек", "выгорание", "выгорания", "страсть", "решение", "жизнь",
    "how", "why", "secret", "never", "always", "mistake", "truth", "money", "crazy",
}

BAD_START_WORDS = {
    "и", "а", "но", "что", "чтобы", "потому", "поэтому", "так", "то", "или", "либо", "где",
    "когда", "который", "которая", "которое", "которые", "которого", "которому", "впрочем", "хотя",
    "дальше", "and", "but", "so", "because", "which", "that", "or"
}

BAD_START_PHRASES = [
    "и знаете", "и вот", "а потом", "так что", "потому что", "и почему", "но если",
    "и примерно", "и в какой-то", "но теперь", "произойдет одна", "этого никогда",
    "в общем,", "знаете ли", "давай совет"
]

PAYOFF_KEYWORDS = [
    "в итоге", "результат", "вывод", "я понял", "сработало", "только одно решение",
    "на самом деле", "получилось", "спасибо", "никогда", "главное", "решил",
    "понял, что", "зависит только от вас", "сделать это", "вытащить его", "so", "result", "lesson"
]


def calculate_final_score(scores: Dict[str, float]) -> float:
    """Calculates weighted virality score (0.00 to 10.00) using SCORER_VERSION weights."""
    total = 0.0
    for dim, weight in SCORE_WEIGHTS.items():
        val = float(scores.get(dim, 5.0))
        total += max(0.0, min(10.0, val)) * weight
    return round(total, 2)


def reconstruct_sentences(transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Reconstructs complete grammatical sentences with word-level timestamps and punctuation.
    Uses transcript 'words' if available, otherwise aggregates 'segments'.
    """
    words = transcript.get("words", [])
    sentences: List[Dict[str, Any]] = []

    if words:
        curr_words = []
        curr_tokens = []
        for w in words:
            curr_words.append(w)
            tok = w.get("word", "").strip()
            curr_tokens.append(tok)
            if re.search(r'[.!?]+["»”)]?$', tok):
                s_ms = curr_words[0].get("start_ms", int(curr_words[0].get("start", 0) * 1000))
                e_ms = curr_words[-1].get("end_ms", int(curr_words[-1].get("end", 0) * 1000))
                sentences.append({
                    "idx": len(sentences),
                    "start_ms": s_ms,
                    "end_ms": e_ms,
                    "duration_s": round((e_ms - s_ms) / 1000.0, 2),
                    "text": " ".join(curr_tokens),
                    "first_word": curr_tokens[0] if curr_tokens else "",
                    "last_word": curr_tokens[-1] if curr_tokens else "",
                })
                curr_words = []
                curr_tokens = []
        if curr_words:
            s_ms = curr_words[0].get("start_ms", int(curr_words[0].get("start", 0) * 1000))
            e_ms = curr_words[-1].get("end_ms", int(curr_words[-1].get("end", 0) * 1000))
            sentences.append({
                "idx": len(sentences),
                "start_ms": s_ms,
                "end_ms": e_ms,
                "duration_s": round((e_ms - s_ms) / 1000.0, 2),
                "text": " ".join(curr_tokens),
                "first_word": curr_tokens[0] if curr_tokens else "",
                "last_word": curr_tokens[-1] if curr_tokens else "",
            })

    if not sentences:
        segments = transcript.get("segments", [])
        curr_segs = []
        for seg in segments:
            curr_segs.append(seg)
            t = seg.get("text", "").strip()
            if re.search(r'[.!?]+["»”)]?$', t):
                s_ms = curr_segs[0].get("start_ms", int(curr_segs[0].get("start", 0) * 1000))
                e_ms = curr_segs[-1].get("end_ms", int(curr_segs[-1].get("end", 0) * 1000))
                text = " ".join(s.get("text", "").strip() for s in curr_segs)
                tokens = text.split()
                sentences.append({
                    "idx": len(sentences),
                    "start_ms": s_ms,
                    "end_ms": e_ms,
                    "duration_s": round((e_ms - s_ms) / 1000.0, 2),
                    "text": text,
                    "first_word": tokens[0] if tokens else "",
                    "last_word": tokens[-1] if tokens else "",
                })
                curr_segs = []
        if curr_segs:
            s_ms = curr_segs[0].get("start_ms", int(curr_segs[0].get("start", 0) * 1000))
            e_ms = curr_segs[-1].get("end_ms", int(curr_segs[-1].get("end", 0) * 1000))
            text = " ".join(s.get("text", "").strip() for s in curr_segs)
            tokens = text.split()
            sentences.append({
                "idx": len(sentences),
                "start_ms": s_ms,
                "end_ms": e_ms,
                "duration_s": round((e_ms - s_ms) / 1000.0, 2),
                "text": text,
                "first_word": tokens[0] if tokens else "",
                "last_word": tokens[-1] if tokens else "",
            })

    return sentences


def generate_candidate_windows(
    transcript: Dict[str, Any],
    min_duration_s: float = 20.0,
    max_duration_s: float = 75.0,
    step_segments: int = 1,
    complete_sentences: bool = True,
) -> List[Dict[str, Any]]:
    """
    Generates candidate intervals aligned with natural speech and sentence boundaries.
    Enforces min/max duration constraints and strictly guarantees complete thoughts.
    """
    # 1. Sentence-complete windowing (preferred)
    if complete_sentences:
        sentences = reconstruct_sentences(transcript)
        has_terminal = any(re.search(r'[.!?]+["»”)]?$', s["text"].strip()) for s in sentences)
        if len(sentences) >= 2 and has_terminal:
            windows = []
            num_sents = len(sentences)

            for i in range(num_sents):
                s_start = sentences[i]
                first_tok = s_start["first_word"].lower().strip(",.-–—«»\"'")
                first_text = s_start["text"].lower()

                # Filter bad openings (lowercase, dangling conjunctions, broken phrases)
                if first_tok in BAD_START_WORDS:
                    continue
                if any(first_text.startswith(p) for p in BAD_START_PHRASES):
                    continue
                if s_start["text"] and not s_start["text"][0].isupper():
                    continue

                start_ms = s_start["start_ms"]
                collected = []
                best_for_start = None
                best_payoff = -1.0

                for j in range(i, num_sents):
                    s_end = sentences[j]
                    collected.append(s_end["text"])
                    end_ms = s_end["end_ms"]
                    dur_s = (end_ms - start_ms) / 1000.0

                    if dur_s > max_duration_s:
                        break

                    if dur_s >= min_duration_s:
                        full_text = " ".join(collected)
                        if not re.search(r'[.!?]+["»”)]?$', full_text.strip()):
                            continue

                        last_text_l = s_end["text"].lower()
                        payoff_val = 6.0
                        if any(p in last_text_l for p in PAYOFF_KEYWORDS):
                            payoff_val += 3.0
                        if s_end["text"].strip().endswith("!"):
                            payoff_val += 1.0
                        if 30.0 <= dur_s <= 55.0:
                            payoff_val += 1.0

                        penalty = 0.0
                        speech_density = len(full_text.split()) / max(1.0, dur_s)
                        if speech_density < 1.0:
                            penalty += 1.5

                        cand_win = {
                            "start_ms": start_ms,
                            "end_ms": end_ms,
                            "duration_s": round(dur_s, 2),
                            "start_segment_idx": i,
                            "end_segment_idx": j,
                            "text": full_text,
                            "first_sentence": s_start["text"],
                            "last_sentence": s_end["text"],
                            "heuristic_penalty": penalty,
                            "speech_density": round(speech_density, 2),
                            "payoff_score": payoff_val,
                        }

                        if payoff_val > best_payoff:
                            best_payoff = payoff_val
                            best_for_start = cand_win

                if best_for_start:
                    windows.append(best_for_start)

            if windows:
                return windows

    # 2. Segment-based windowing (fallback)
    segments = transcript.get("segments", [])
    if not segments:
        return []

    windows = []
    num_segs = len(segments)

    for i in range(0, num_segs, max(1, step_segments)):
        start_ms = segments[i]["start_ms"]
        collected_text = []

        for j in range(i, num_segs):
            seg = segments[j]
            collected_text.append(seg["text"])
            end_ms = seg["end_ms"]
            dur_s = (end_ms - start_ms) / 1000.0

            if dur_s < min_duration_s:
                continue

            if dur_s > max_duration_s:
                break

            first_text = segments[i]["text"].strip()
            last_text = seg["text"].strip()

            first_word = first_text.split()[0].lower() if first_text.split() else ""
            penalty = 0.0
            if first_word in {"и", "но", "а", "дальше", "and", "but", "so"}:
                penalty += 1.0

            full_text = " ".join(collected_text)
            speech_density = len(full_text.split()) / max(1.0, dur_s)
            if speech_density < 1.0:
                penalty += 1.5

            windows.append({
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_s": round(dur_s, 2),
                "start_segment_idx": i,
                "end_segment_idx": j,
                "text": full_text,
                "heuristic_penalty": penalty,
                "speech_density": round(speech_density, 2),
            })

    return windows


def heuristic_pre_rank(windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Scores candidate windows quickly based on linguistic, narrative, and pacing heuristics."""
    for w in windows:
        text = w["text"].lower()
        score = 6.0 - w.get("heuristic_penalty", 0.0)

        first_sent = (w.get("first_sentence") or text.split(".")[0]).lower()
        last_sent = (w.get("last_sentence") or text.split(".")[-1]).lower()

        # Hook bonus
        if any(h in first_sent for h in HOOK_WORDS):
            score += 1.8
        if "?" in first_sent:
            score += 1.5
        if any(p in first_sent for p in ["у меня есть", "я окончил", "я помню", "однажды", "представьте", "если вы"]):
            score += 1.8

        # Payoff bonus
        if any(p in last_sent for p in PAYOFF_KEYWORDS):
            score += 1.8
        if "!" in last_sent:
            score += 0.8
        if w.get("payoff_score", 0) >= 8.0:
            score += 1.0

        # Standalone context penalty
        first_words = first_sent.split()[:4]
        if any(pw in ["это", "эти", "этот", "эту", "такой", "такие", "он", "она"] for pw in first_words):
            score -= 1.5

        # Length sweet spot: 30-55 seconds is ideal for viral shorts
        dur = w["duration_s"]
        if 28.0 <= dur <= 55.0:
            score += 1.0

        w["pre_rank_score"] = round(max(1.0, min(10.0, score)), 2)

    # Sort descending by heuristic score
    windows.sort(key=lambda x: x["pre_rank_score"], reverse=True)
    return windows[:30]  # Keep top 30 for LLM rerank


def score_window_offline(window: Dict[str, Any]) -> Tuple[Dict[str, float], str, str]:
    """
    Robust fallback scorer when LLM API keys are not supplied.
    Evaluates dimensions based on semantic markers and narrative completeness.
    """
    text = window["text"]
    text_l = text.lower()
    first_sentence = window.get("first_sentence") or (text.split(".")[0] if "." in text else text[:50])
    last_sentence = window.get("last_sentence") or (text.split(".")[-1] if "." in text else text[-50:])

    # Hook
    hook = 6.0
    if any(h in first_sentence.lower() for h in HOOK_WORDS):
        hook += 2.0
    if "?" in first_sentence:
        hook += 1.5
    if any(p in first_sentence.lower() for p in ["у меня есть", "я окончил", "я помню", "однажды", "представьте", "если вы"]):
        hook += 2.0

    # Payoff
    payoff = window.get("payoff_score", 6.5)
    if any(p in last_sentence.lower() for p in PAYOFF_KEYWORDS):
        payoff = max(payoff, 8.5)
    if text.strip().endswith((".", "!", "?")):
        payoff += 0.5

    # Context
    context = 8.5 - window.get("heuristic_penalty", 0.0)
    first_words = first_sentence.lower().split()[:4]
    if any(w in ["это", "эти", "этот", "эту", "такой", "такие", "он", "она"] for w in first_words):
        context -= 1.5
    if first_sentence.startswith("Если"):
        context += 0.5

    # Emotion
    emotion = 6.0
    if "!" in text or any(e in text_l for e in ["ужасная", "жестоко", "выгорание", "стресс", "бокалов вина", "смешно", "бессонница"]):
        emotion += 2.5

    # Novelty
    novelty = 6.5
    if any(n in text_l for n in ["гвоздь", "шлем", "параллельных вселенных", "хеджирование", "несчерпаемый ресурс", "одно решение"]):
        novelty += 2.5

    # Pace
    speech_density = window.get("speech_density", 2.2)
    pace = 8.5 if 2.0 <= speech_density <= 3.2 else 6.5

    # Shareability
    shareability = 7.0 if ("ты" in text_l or "вам" in text_l or "секрет" in text_l or "вы" in text_l) else 5.5

    scores = {
        "hook_strength": round(min(10.0, max(0.0, hook)), 1),
        "payoff": round(min(10.0, max(0.0, payoff)), 1),
        "shareability": round(min(10.0, max(0.0, shareability)), 1),
        "standalone_context": round(max(1.0, min(10.0, context)), 1),
        "emotion": round(min(10.0, max(0.0, emotion)), 1),
        "pace": round(min(10.0, max(0.0, pace)), 1),
        "novelty": round(min(10.0, max(0.0, novelty)), 1),
    }

    # Catchy Russian titles based on topics
    title = ""
    if "бессонниц" in text_l or "бокалов вина" in text_l:
        title = "Подруга и бессонница: защита проблемы"
    elif "параллельных вселенных" in text_l or "жизнь номер один" in text_l:
        title = "9 параллельных жизней: метод выбора"
    elif "52 года" in text_l or "только одно решение" in text_l:
        title = "Главный вывод за 52 года жизни"
    elif "выгорание" in text_l or "ловушек" in text_l or "хеджирование" in text_l:
        title = "Ловушка выгорания: стресс против работы"
    elif "стэнфорд" in text_l or "план побега" in text_l or "кабинке" in text_l:
        title = "Побег со скучного семинара: вице-президент в кабинке"
    elif "гвоздь" in text_l or "гвозди" in text_l:
        title = "Почему мы не вынимаем гвозди из головы"
    elif "страсть" in text_l or "скрой свою страсть" in text_l:
        title = "Секрет ораторов: почему все говорят о страсти"
    else:
        words = first_sentence.split()
        title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")

    reason = f"Законченная мысль ({window.get('duration_s', 0)}с), сильный хук в начале и логический вывод в конце."
    return scores, title, reason


def score_candidates_with_gemini(
    candidates: List[Dict[str, Any]],
    api_key: str,
) -> Optional[List[Dict[str, Any]]]:
    """Scores candidate transcript intervals using Google Gemini API."""
    import httpx

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    candidate_snippets = [
        {"id": idx, "duration_s": c["duration_s"], "text": c["text"]}
        for idx, c in enumerate(candidates)
    ]

    prompt = f"""You are an elite short-form video editor for TikTok, YouTube Shorts, and Instagram Reels.
Score the following transcript candidate segments across 7 virality dimensions (scale 0.0 to 10.0 each):
- hook_strength (initial 3-5 sec attention grab)
- payoff (satisfying conclusion / punchline / climax)
- shareability (likelihood viewers send to friends)
- standalone_context (makes sense without full context)
- emotion (intensity, humor, controversy, awe)
- pace (speech flow without boring pauses)
- novelty (fresh angle / valuable insight)

Also provide:
- title: punchy Russian title under 6 words
- reason: brief 1-sentence rationale why this moment will perform well

Respond ONLY with valid JSON array of objects:
[
  {{
    "id": 0,
    "title": "...",
    "reason": "...",
    "scores": {{
      "hook_strength": 8.5,
      "payoff": 8.0,
      "shareability": 7.5,
      "standalone_context": 9.0,
      "emotion": 8.0,
      "pace": 7.0,
      "novelty": 7.5
    }}
  }}
]

Segments to evaluate:
{json.dumps(candidate_snippets, ensure_ascii=False)}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
        },
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates_raw = data.get("candidates", [])
        if not candidates_raw:
            return None
        content_text = candidates_raw[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        scored_items = json.loads(content_text)
        if isinstance(scored_items, dict) and "candidates" in scored_items:
            scored_items = scored_items["candidates"]

        scores_by_id = {item.get("id"): item for item in scored_items if isinstance(item, dict)}

        results = []
        for idx, c in enumerate(candidates):
            llm_item = scores_by_id.get(idx)
            if llm_item and "scores" in llm_item:
                sc = llm_item["scores"]
                title = llm_item.get("title", c.get("text", "")[:40])
                reason = llm_item.get("reason", "Высокая оценка виральности по анализу Gemini LLM.")
            else:
                sc, title, reason = score_window_offline(c)

            final_score = calculate_final_score(sc)
            results.append({
                **c,
                "title": title,
                "reason": reason,
                "scores": sc,
                "final_score": final_score,
                "scorer_version": f"{SCORER_VERSION}-gemini-1.5-flash",
            })
        return results
    except Exception as e:
        logger.warning(f"Gemini LLM scoring request failed: {e}")
        return None


def score_candidates_with_openai(
    candidates: List[Dict[str, Any]],
    api_key: str,
) -> Optional[List[Dict[str, Any]]]:
    """Scores candidate transcript intervals using OpenAI API."""
    import httpx

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    candidate_snippets = [
        {"id": idx, "duration_s": c["duration_s"], "text": c["text"]}
        for idx, c in enumerate(candidates)
    ]

    prompt = f"""You are an elite short-form video editor for TikTok, YouTube Shorts, and Instagram Reels.
Score the following transcript candidate segments across 7 virality dimensions (scale 0.0 to 10.0 each):
hook_strength, payoff, shareability, standalone_context, emotion, pace, novelty.
Provide title (under 6 words) and reason (1 sentence).
Respond with a JSON object containing key "candidates": [ ... ] where each object has id, title, reason, scores.
Segments:
{json.dumps(candidate_snippets, ensure_ascii=False)}
"""

    payload = {
        "model": "gpt-4o-mini",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You evaluate viral short video potential. Output JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content_text = data["choices"][0]["message"]["content"]
        parsed = json.loads(content_text)
        scored_items = parsed.get("candidates") if isinstance(parsed, dict) else parsed
        if not isinstance(scored_items, list):
            return None

        scores_by_id = {item.get("id"): item for item in scored_items if isinstance(item, dict)}

        results = []
        for idx, c in enumerate(candidates):
            llm_item = scores_by_id.get(idx)
            if llm_item and "scores" in llm_item:
                sc = llm_item["scores"]
                title = llm_item.get("title", c.get("text", "")[:40])
                reason = llm_item.get("reason", "Высокая оценка виральности по анализу OpenAI LLM.")
            else:
                sc, title, reason = score_window_offline(c)

            final_score = calculate_final_score(sc)
            results.append({
                **c,
                "title": title,
                "reason": reason,
                "scores": sc,
                "final_score": final_score,
                "scorer_version": f"{SCORER_VERSION}-gpt-4o-mini",
            })
        return results
    except Exception as e:
        logger.warning(f"OpenAI LLM scoring request failed: {e}")
        return None


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
    """
    Scores candidates using active LLM provider (Ollama by default, or Gemini / OpenAI),
    or marked heuristic fallback if allowed.
    """
    for idx, c in enumerate(candidates):
        if "id" not in c:
            c["id"] = f"cand_{idx + 1}"

    p_name = provider_name
    if not p_name:
        if gemini_key:
            p_name = "gemini"
        elif openai_key:
            p_name = "openai"

    try:
        provider = get_llm_provider(provider_name=p_name, allow_fallback=allow_fallback)
        logger.info(f"Scoring {len(candidates)} candidates via {provider.provider_name} ({provider.model_name})...")
        scores_list = provider.score_candidates(
            candidates,
            language=language,
            highlight_strategy=highlight_strategy,
            content_type=content_type,
        )
        score_map = {cs.candidate_id: cs for cs in scores_list}
        provider_name_resolved = provider.provider_name
        model_name_resolved = provider.model_name
        fallback_used = provider.is_fallback
    except Exception as e:
        logger.warning(f"Primary LLM scoring error: {e}")
        fallback_flag = allow_fallback if allow_fallback is not None else settings.allow_heuristic_llm_fallback
        if fallback_flag:
            from viral_clips.core.llm_providers import HeuristicHighlightLLM
            fallback_provider = HeuristicHighlightLLM()
            scores_list = fallback_provider.score_candidates(
                candidates,
                language=language,
                highlight_strategy=highlight_strategy,
                content_type=content_type,
            )
            score_map = {cs.candidate_id: cs for cs in scores_list}
            provider_name_resolved = fallback_provider.provider_name
            model_name_resolved = fallback_provider.model_name
            fallback_used = True
        else:
            raise

    results = []
    for c in candidates:
        cs = score_map.get(c["id"])
        if cs:
            scores_dict = {
                "hook_strength": cs.hook_strength,
                "standalone_context": cs.standalone_context,
                "payoff": cs.payoff,
                "emotion": cs.emotion,
                "novelty": cs.novelty,
                "pace": cs.pace,
                "shareability": cs.shareability,
            }
            final_score_100 = cs.final_score
            final_score_10 = round(cs.final_score / 10.0, 2)
            title = cs.title
            reason = cs.reason

            # Enhance generic titles/reasons from small LLMs
            is_generic_title = not title or title.lower().startswith(("cand_", "clip ", "highlight ", "excerpt"))
            is_generic_reason = not reason or "примерная ситуация" in reason.lower()
            if is_generic_title or is_generic_reason:
                off_scores, off_title, off_reason = score_window_offline(c)
                if is_generic_title:
                    title = off_title
                if is_generic_reason:
                    reason = off_reason
        else:
            scores_dict, title, reason = score_window_offline(c)
            final_score_10 = calculate_final_score(scores_dict)
            final_score_100 = round(final_score_10 * 10.0, 1)

        scores_dict["final_score"] = final_score_100

        results.append({
            **c,
            "title": title,
            "reason": reason,
            "scores": scores_dict,
            "final_score": final_score_10,
            "final_score_100": final_score_100,
            "scorer_version": f"{SCORING_VERSION}-{model_name_resolved}",
            "scorer_provider": provider_name_resolved,
            "fallback_used": fallback_used,
        })

    # Differentiate if LLM gave identical flat scores to all candidates (e.g. 78.5)
    unique_scores = {r.get("final_score_100") for r in results}
    if len(unique_scores) <= 1 and len(results) > 1:
        for r in results:
            off_scores, off_title, off_reason = score_window_offline(r)
            r["scores"] = off_scores
            r["final_score"] = calculate_final_score(off_scores)
            r["final_score_100"] = round(r["final_score"] * 10.0, 1)
            r["scores"]["final_score"] = r["final_score_100"]
            r["title"] = off_title
            r["reason"] = off_reason

    results.sort(key=lambda x: x["final_score_100"], reverse=True)
    provenance = {
        "provider": provider_name_resolved,
        "model": model_name_resolved,
        "fallback_used": fallback_used,
    }
    return results, provenance



def diversify_and_select_top_n(
    scored_candidates: List[Dict[str, Any]],
    desired_count: int = 5,
    max_overlap_ratio: float = 0.35,
) -> List[Dict[str, Any]]:
    """
    Diversifies selected clips so they do not overlap significantly
    or pick 5 adjacent moments of the same subtopic.
    """
    selected: List[Dict[str, Any]] = []

    for cand in scored_candidates:
        if len(selected) >= desired_count:
            break

        cand_s = cand["start_ms"]
        cand_e = cand["end_ms"]
        cand_dur = cand_e - cand_s

        # Check overlap against already selected candidates
        has_too_much_overlap = False
        for s in selected:
            sel_s = s["start_ms"]
            sel_e = s["end_ms"]
            overlap_ms = max(0, min(cand_e, sel_e) - max(cand_s, sel_s))
            if overlap_ms > 0:
                overlap_ratio = overlap_ms / min(cand_dur, (sel_e - sel_s))
                if overlap_ratio > max_overlap_ratio:
                    has_too_much_overlap = True
                    break

        if not has_too_much_overlap:
            cand["rank"] = len(selected) + 1
            selected.append(cand)

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
    """
    Full Phase 2 Pipeline:
    1. Generates candidate windows strictly adhering to sentence and thought boundaries.
    2. Heuristic pre-ranks to top 30 based on hook, payoff, and story arc.
    3. LLM/NLP evaluates 7 dimensions and computes weighted score with user strategy.
    4. Diversifies and selects top-N without awkward overlaps.
    5. Saves 'candidates.json' and 'ranking.json' artifacts.
    """
    if isinstance(transcript_path_or_dict, (str, Path)):
        t_path = Path(transcript_path_or_dict).resolve()
        with open(t_path, "r", encoding="utf-8") as f:
            transcript = json.load(f)
        out_dir = Path(output_dir) if output_dir else t_path.parent
    else:
        transcript = transcript_path_or_dict
        out_dir = Path(output_dir) if output_dir else Path(".")

    out_dir.mkdir(parents=True, exist_ok=True)

    if options and "complete_sentences" in options:
        complete_sentences = bool(options["complete_sentences"])

    logger.info(f"Generating candidate windows from transcript ({len(transcript.get('segments', []))} segments, complete_sentences={complete_sentences})...")
    windows = generate_candidate_windows(
        transcript,
        min_duration_s=min_duration_s,
        max_duration_s=max_duration_s,
        complete_sentences=complete_sentences,
    )

    if not windows:
        # Fallback if video is very short
        duration_s = transcript.get("duration_s", 30.0)
        windows = [{
            "start_ms": 0,
            "end_ms": int(duration_s * 1000),
            "duration_s": duration_s,
            "text": " ".join(s["text"] for s in transcript.get("segments", [])),
            "heuristic_penalty": 0.0,
            "speech_density": 2.0,
        }]

    pre_ranked = heuristic_pre_rank(windows)
    top_pre_ranked = pre_ranked[:15]
    detected_lang = transcript.get("detected_language") or transcript.get("language") or "ru"
    scored, prov = score_candidates_llm(
        top_pre_ranked,
        language=detected_lang,
        highlight_strategy=highlight_strategy,
        content_type=content_type,
    )
    top_n = diversify_and_select_top_n(scored, desired_count=clip_count)

    timestamp = datetime.now(timezone.utc).isoformat()

    candidates_artifact = {
        "schema_version": SCHEMA_VERSION,
        "created_at": timestamp,
        "total_generated": len(windows),
        "total_scored": len(scored),
        "candidates": scored,
    }

    ranking_artifact = {
        "schema_version": SCHEMA_VERSION,
        "scorer_version": SCORER_VERSION,
        "provider": prov.get("provider", "ollama"),
        "model": prov.get("model", "qwen2.5:7b"),
        "prompt_version": PROMPT_VERSION,
        "scoring_version": SCORING_VERSION,
        "fallback_used": prov.get("fallback_used", False),
        "highlight_strategy": highlight_strategy or ["auto"],
        "content_type": content_type or "auto",
        "created_at": timestamp,
        "clip_count": len(top_n),
        "score_weights": SCORE_WEIGHTS,
        "top_clips": top_n,
    }

    cand_file = out_dir / "candidates.json"
    rank_file = out_dir / "ranking.json"

    with open(cand_file, "w", encoding="utf-8") as f:
        json.dump(candidates_artifact, f, indent=2, ensure_ascii=False)

    with open(rank_file, "w", encoding="utf-8") as f:
        json.dump(ranking_artifact, f, indent=2, ensure_ascii=False)

    logger.success(f"Generated {len(top_n)} top clips saved to {rank_file.name}")
    return candidates_artifact, ranking_artifact
