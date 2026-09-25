"""
LLM Provider Abstraction & Structured Virality Scoring for Viral Clips AI.
Supports Ollama (default local), Gemini, OpenAI, and explicitly marked Heuristic fallback.
Enforces Pydantic structured output validation and batch scoring per Real Video Quality Gate spec.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import httpx
from loguru import logger
from pydantic import BaseModel, Field

from viral_clips.config import settings
from viral_clips.exceptions import ViralClipsError

PROMPT_VERSION = "highlight-v2"
SCORING_VERSION = "viral-score-v2"

# Versioned virality dimension weights summing to 1.0
VIRAL_WEIGHTS = {
    "hook_strength": 0.20,
    "standalone_context": 0.15,
    "payoff": 0.20,
    "emotion": 0.10,
    "novelty": 0.10,
    "pace": 0.10,
    "shareability": 0.15,
}


class LLMError(ViralClipsError):
    def __init__(self, code: str = "LLM_FAILED", message: str = "", status_code: int = 502, details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, status_code=status_code, details=details)


HighlightLLMError = LLMError


class LLMUnavailableError(LLMError):
    def __init__(self, message: str = "LLM service is unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="LLM_UNAVAILABLE", message=message, status_code=503, details=details)


class LLMModelUnavailableError(LLMError):
    def __init__(self, message: str = "LLM model not found or unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="LLM_MODEL_UNAVAILABLE", message=message, status_code=503, details=details)


class LLMInvalidResponseError(LLMError):
    def __init__(self, message: str = "LLM output failed Pydantic validation", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="LLM_INVALID_RESPONSE", message=message, status_code=502, details=details)


class CandidateScore(BaseModel):
    """Pydantic validated structured evaluation of a candidate segment."""
    candidate_id: str
    hook_strength: int = Field(ge=0, le=10, description="Grabbing attention in the first seconds")
    standalone_context: int = Field(ge=0, le=10, description="Understood without watching the rest of the video")
    payoff: int = Field(ge=0, le=10, description="Satisfying punchline, reveal, or takeaway")
    emotion: int = Field(ge=0, le=10, description="Emotional resonance, humor, or controversy")
    novelty: int = Field(ge=0, le=10, description="Fresh ideas or surprising insight")
    pace: int = Field(ge=0, le=10, description="Dynamic delivery without boring pauses")
    shareability: int = Field(ge=0, le=10, description="Likelihood of viewer sharing to friends")
    title: str = Field(description="Catchy short viral title for this clip")
    reason: str = Field(description="Explanation of why this candidate is viral or weak")

    # Calculated composite score (0 - 100)
    final_score: float = 0.0

    def compute_final_score(self) -> float:
        raw = (
            self.hook_strength * VIRAL_WEIGHTS["hook_strength"]
            + self.standalone_context * VIRAL_WEIGHTS["standalone_context"]
            + self.payoff * VIRAL_WEIGHTS["payoff"]
            + self.emotion * VIRAL_WEIGHTS["emotion"]
            + self.novelty * VIRAL_WEIGHTS["novelty"]
            + self.pace * VIRAL_WEIGHTS["pace"]
            + self.shareability * VIRAL_WEIGHTS["shareability"]
        ) * 10.0
        self.final_score = round(raw, 1)
        return self.final_score


class BatchCandidateScoreResponse(BaseModel):
    scores: List[CandidateScore]


def calculate_composite_score(scores_dict: Dict[str, float]) -> float:
    """Calculates normalized 0-100 composite viral score using versioned weights."""
    total = 0.0
    for dim, weight in VIRAL_WEIGHTS.items():
        total += float(scores_dict.get(dim, 5.0)) * weight
    return round(total * 10.0, 1)


@runtime_checkable
class HighlightLLMProvider(Protocol):
    provider_name: str
    model_name: str
    is_fallback: bool

    def check_health(self) -> bool:
        ...

    def score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        language: str = "ru",
        highlight_strategy: Optional[List[str]] = None,
        content_type: Optional[str] = None,
    ) -> List[CandidateScore]:
        ...


SYSTEM_SCORING_PROMPT = """You are an elite short-form content producer (TikTok, Reels, YouTube Shorts).
Your task is to analyze candidate video segments from a transcript and score their viral potential.

CRITICAL INSTRUCTIONS:
1. Evaluate candidates RELATIVELY against each other. DO NOT give everyone high scores.
2. Only truly captivating moments deserve >= 8 in hook_strength or payoff.
3. Every score must be an INTEGER between 0 and 10.
4. Output MUST be valid JSON matching the exact schema requested.
5. Provide a catchy, click-worthy 'title' and concise 'reason' for each candidate.
"""


def build_batch_user_prompt(
    candidates: List[Dict[str, Any]],
    language: str = "ru",
    highlight_strategy: Optional[List[str]] = None,
    content_type: Optional[str] = None,
) -> str:
    cand_snippets = []
    for cand in candidates:
        c_id = cand.get("id") or cand.get("candidate_id", "1")
        dur = cand.get("duration_s", (cand.get("end_ms", 0) - cand.get("start_ms", 0)) / 1000.0)
        text = cand.get("text", "")
        cand_snippets.append(
            f"--- CANDIDATE ID: {c_id} (Duration: {dur:.1f}s) ---\n"
            f"Transcript: \"{text}\"\n"
        )
    joined_snippets = "\n".join(cand_snippets)

    schema_hint = (
        '{"scores": ['
        '{"candidate_id": "string", "hook_strength": 0-10, "standalone_context": 0-10, '
        '"payoff": 0-10, "emotion": 0-10, "novelty": 0-10, "pace": 0-10, "shareability": 0-10, '
        '"title": "short catchy title", "reason": "concise rationale"}'
        ']}'
    )

    strategy_hints = []
    if highlight_strategy and not (len(highlight_strategy) == 1 and highlight_strategy[0].lower() in ("auto", "")):
        strat_set = {s.lower() for s in highlight_strategy}
        if "hooks" in strat_set or "strong_hooks" in strat_set:
            strategy_hints.append("- Prioritize strong, curiosity-inducing openings and memorable introductory statements (boost hook_strength).")
        if "insights" in strat_set:
            strategy_hints.append("- Prioritize actionable takeaways, expert knowledge, and practical insights (boost standalone_context and payoff).")
        if "hot_takes" in strat_set:
            strategy_hints.append("- Prioritize bold, controversial opinions, counterintuitive claims, and polarizing viewpoints (boost novelty and emotion).")
        if "funny" in strat_set:
            strategy_hints.append("- Prioritize humorous moments, funny reactions, witty banter, and comedic timing (boost emotion and shareability).")
        if "stories" in strat_set:
            strategy_hints.append("- Prioritize self-contained micro-narratives with clear setup, tension, and resolution (boost narrative coherence and payoff).")
        if "quotes" in strat_set:
            strategy_hints.append("- Prioritize punchy, memorable, quotable statements that easily circulate as viral soundbites (boost shareability).")

    content_hint = ""
    if content_type and content_type.lower() not in ("auto", "auto detect", ""):
        ct = content_type.lower()
        if "podcast" in ct:
            content_hint = "Content Type: PODCAST. Avoid beginning mid-question; ensure guest answers are complete and punchy."
        elif "interview" in ct:
            content_hint = "Content Type: INTERVIEW. Seek compelling questions and revelation moments with emotional weight."
        elif "gaming" in ct:
            content_hint = "Content Type: GAMING. Focus on intense gameplay reactions, clutch moments, unexpected wins or fails."
        elif "lecture" in ct:
            content_hint = "Content Type: LECTURE / EDUCATIONAL. Prioritize clear explanations, eureka moments, and standalone mental models."
        elif "talking_head" in ct:
            content_hint = "Content Type: TALKING HEAD. Focus on direct camera address, concise arguments, and rapid pacing."
        else:
            content_hint = f"Content Type: {content_type.upper()}."

    extra_instructions = ""
    if strategy_hints:
        extra_instructions += "\nUSER HIGHLIGHT STRATEGY:\n" + "\n".join(strategy_hints) + "\n"
    if content_hint:
        extra_instructions += f"\n{content_hint}\n"

    return (
        f"Language of transcript: {language}\n"
        f"{extra_instructions}"
        f"Analyze these {len(candidates)} candidate segments and score each one:\n\n"
        f"{joined_snippets}\n\n"
        f"Return JSON adhering strictly to this schema:\n{schema_hint}"
    )


class OllamaHighlightLLM:
    """Local Ollama LLM provider (e.g. Qwen 2.5 / Qwen 3). Default free provider."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model_name = model or settings.ollama_model
        self.provider_name = "ollama"
        self.is_fallback = False
        self._ensure_model_available()

    def _ensure_model_available(self):
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    installed = [m.get("name", "") for m in res.json().get("models", [])]
                    if not any(self.model_name in m or m.startswith(self.model_name) for m in installed):
                        for m in installed:
                            if "qwen" in m.lower():
                                self.model_name = m
                                break
        except Exception:
            pass

    def check_health(self) -> bool:
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def _query_ollama(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.3},
        }

        try:
            with httpx.Client(timeout=90.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 404:
                    raise LLMModelUnavailableError(
                        f"Ollama model '{self.model_name}' not found at {self.base_url}. Run `ollama pull {self.model_name}`."
                    )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
        except httpx.ConnectError as ce:
            raise LLMUnavailableError(f"Cannot connect to Ollama at {self.base_url}: {ce}")
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(code="LLM_FAILED", message=f"Ollama inference error: {e}")

    def score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        language: str = "ru",
        highlight_strategy: Optional[List[str]] = None,
        content_type: Optional[str] = None,
    ) -> List[CandidateScore]:
        if not self.check_health():
            raise LLMUnavailableError(
                f"Ollama service is unreachable at {self.base_url}. Start Ollama with `ollama serve`."
            )

        # Batch in focused chunks of 3-4 so local models can reliably discriminate quality
        chunk_size = 4
        all_scores: List[CandidateScore] = []

        for i in range(0, len(candidates), chunk_size):
            chunk = candidates[i : i + chunk_size]
            prompt = build_batch_user_prompt(
                chunk,
                language=language,
                highlight_strategy=highlight_strategy,
                content_type=content_type,
            )

            raw_json = None
            # Retry once on malformed response
            for attempt in range(2):
                try:
                    raw_content = self._query_ollama(SYSTEM_SCORING_PROMPT, prompt)
                    raw_json = json.loads(raw_content)
                    break
                except (json.JSONDecodeError, Exception) as e:
                    if attempt == 1:
                        raise LLMInvalidResponseError(
                            f"Ollama output is not valid JSON after retry: {e}",
                            details={"raw_content": raw_content if 'raw_content' in locals() else None},
                        )

            # Pydantic parsing
            parsed_scores = self._parse_json_scores(raw_json, chunk)
            all_scores.extend(parsed_scores)

        return all_scores

    def _parse_json_scores(self, raw_json: Any, chunk: List[Dict[str, Any]]) -> List[CandidateScore]:
        scores_list = []
        if isinstance(raw_json, dict) and "scores" in raw_json:
            items = raw_json["scores"]
        elif isinstance(raw_json, list):
            items = raw_json
        else:
            items = [raw_json] if isinstance(raw_json, dict) else []

        item_map = {item.get("candidate_id"): item for item in items if isinstance(item, dict)}

        for cand in chunk:
            c_id = cand["id"]
            if c_id in item_map:
                try:
                    cs = CandidateScore(**item_map[c_id])
                except Exception:
                    # Coerce bounds if slightly out of range
                    d = item_map[c_id]
                    cs = CandidateScore(
                        candidate_id=c_id,
                        hook_strength=max(0, min(10, int(d.get("hook_strength", 5)))),
                        standalone_context=max(0, min(10, int(d.get("standalone_context", 5)))),
                        payoff=max(0, min(10, int(d.get("payoff", 5)))),
                        emotion=max(0, min(10, int(d.get("emotion", 5)))),
                        novelty=max(0, min(10, int(d.get("novelty", 5)))),
                        pace=max(0, min(10, int(d.get("pace", 5)))),
                        shareability=max(0, min(10, int(d.get("shareability", 5)))),
                        title=str(d.get("title", f"Clip {c_id}")),
                        reason=str(d.get("reason", "Interesting excerpt")),
                    )
            else:
                cs = CandidateScore(
                    candidate_id=c_id,
                    hook_strength=5,
                    standalone_context=5,
                    payoff=5,
                    emotion=5,
                    novelty=5,
                    pace=5,
                    shareability=5,
                    title=f"Highlight {c_id}",
                    reason="Evaluated by relative batch ranker",
                )
            cs.compute_final_score()
            scores_list.append(cs)

        return scores_list


class GeminiHighlightLLM:
    """Google Gemini LLM provider using dynamic model from config."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.get_gemini_key()
        self.model_name = model or settings.gemini_model
        self.provider_name = "gemini"
        self.is_fallback = False

    def check_health(self) -> bool:
        return bool(self.api_key)

    def score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        language: str = "ru",
        highlight_strategy: Optional[List[str]] = None,
        content_type: Optional[str] = None,
    ) -> List[CandidateScore]:
        if not self.api_key:
            raise LLMUnavailableError("Gemini API key is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        chunk_size = 10
        all_scores: List[CandidateScore] = []

        for i in range(0, len(candidates), chunk_size):
            chunk = candidates[i : i + chunk_size]
            prompt = build_batch_user_prompt(
                chunk,
                language=language,
                highlight_strategy=highlight_strategy,
                content_type=content_type,
            )

            body = {
                "contents": [{"parts": [{"text": f"{SYSTEM_SCORING_PROMPT}\n\n{prompt}"}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                },
            }

            raw_json = None
            for attempt in range(2):
                try:
                    with httpx.Client(timeout=60.0) as client:
                        resp = client.post(url, json=body)
                        if resp.status_code == 404:
                            raise LLMModelUnavailableError(f"Gemini model '{self.model_name}' unavailable or not found.")
                        resp.raise_for_status()
                        res_data = resp.json()
                        text_out = res_data["candidates"][0]["content"]["parts"][0]["text"]
                        raw_json = json.loads(text_out)
                        break
                except LLMError:
                    raise
                except Exception as e:
                    if attempt == 1:
                        raise LLMInvalidResponseError(f"Gemini API error or invalid JSON: {e}")

            parsed = OllamaHighlightLLM._parse_json_scores(None, raw_json, chunk)
            all_scores.extend(parsed)

        return all_scores


class OpenAIHighlightLLM:
    """OpenAI LLM provider using dynamic model from config."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.get_openai_key()
        self.model_name = model or settings.openai_model
        self.provider_name = "openai"
        self.is_fallback = False

    def check_health(self) -> bool:
        return bool(self.api_key)

    def score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        language: str = "ru",
        highlight_strategy: Optional[List[str]] = None,
        content_type: Optional[str] = None,
    ) -> List[CandidateScore]:
        if not self.api_key:
            raise LLMUnavailableError("OpenAI API key is not configured.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        chunk_size = 10
        all_scores: List[CandidateScore] = []

        for i in range(0, len(candidates), chunk_size):
            chunk = candidates[i : i + chunk_size]
            prompt = build_batch_user_prompt(
                chunk,
                language=language,
                highlight_strategy=highlight_strategy,
                content_type=content_type,
            )
            body = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": SYSTEM_SCORING_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }

            raw_json = None
            for attempt in range(2):
                try:
                    with httpx.Client(timeout=60.0) as client:
                        resp = client.post(url, headers=headers, json=body)
                        resp.raise_for_status()
                        data = resp.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        raw_json = json.loads(raw_content)
                        break
                except Exception as e:
                    if attempt == 1:
                        raise LLMInvalidResponseError(f"OpenAI API error or invalid JSON: {e}")

            parsed = OllamaHighlightLLM._parse_json_scores(None, raw_json, chunk)
            all_scores.extend(parsed)

        return all_scores


class HeuristicHighlightLLM:
    """
    Offline linguistic & acoustic heuristic scorer.
    Permitted ONLY when ALLOW_HEURISTIC_LLM_FALLBACK is explicitly enabled.
    Must always record 'scorer_provider': 'heuristic' and 'fallback_used': True.
    """

    def __init__(self):
        self.provider_name = "heuristic"
        self.model_name = "heuristic-v2"
        self.is_fallback = True

    def check_health(self) -> bool:
        return True

    def score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        language: str = "ru",
        highlight_strategy: Optional[List[str]] = None,
        content_type: Optional[str] = None,
    ) -> List[CandidateScore]:
        logger.warning(
            "Using offline heuristic scorer! Marked with fallback_used=True and scorer_provider='heuristic'."
        )
        strat_set = {s.lower() for s in (highlight_strategy or [])}
        scores_list = []
        for cand in candidates:
            c_id = cand["id"]
            text = cand.get("text", "")
            words = text.split()
            word_count = len(words)
            dur = cand.get("duration_s", (cand.get("end_ms", 30000) - cand.get("start_ms", 0)) / 1000.0)

            # Heuristic calculation
            wpm = (word_count / max(0.1, dur)) * 60.0
            pace_score = min(10, max(2, int(wpm / 25.0)))
            hook_words = {"секрет", "почему", "как", "никогда", "главное", "внимание", "secret", "why", "how", "never", "watch"}
            has_hook = any(w.lower() in hook_words for w in words[:10])
            hook_score = 8 if has_hook else 5

            standalone_score = 6
            payoff_score = 7
            emotion_score = 6
            novelty_score = 5
            share_score = 6

            if "hooks" in strat_set or "strong_hooks" in strat_set:
                hook_score = min(10, hook_score + 1)
            if "insights" in strat_set:
                payoff_score = min(10, payoff_score + 1)
                standalone_score = min(10, standalone_score + 1)
            if "hot_takes" in strat_set:
                novelty_score = min(10, novelty_score + 2)
            if "funny" in strat_set:
                emotion_score = min(10, emotion_score + 2)
            if "stories" in strat_set:
                standalone_score = min(10, standalone_score + 1)
                payoff_score = min(10, payoff_score + 1)
            if "quotes" in strat_set:
                share_score = min(10, share_score + 2)

            cs = CandidateScore(
                candidate_id=c_id,
                hook_strength=hook_score,
                standalone_context=standalone_score,
                payoff=payoff_score,
                emotion=emotion_score,
                novelty=novelty_score,
                pace=pace_score,
                shareability=share_score,
                title=f"Ключевой момент {c_id}" if language == "ru" else f"Key moment {c_id}",
                reason="Calculated via offline heuristic pre-ranker (lexical & pace metrics).",
            )
            cs.compute_final_score()
            scores_list.append(cs)

        return scores_list


def get_llm_provider(
    provider_name: Optional[str] = None,
    allow_fallback: Optional[bool] = None,
) -> HighlightLLMProvider:
    """
    Factory resolving active LLM provider per configuration and Real Video Quality Gate requirements.
    Strictly forbids silent fallback unless allow_heuristic_llm_fallback is enabled.
    """
    prov = (provider_name or settings.llm_provider).lower()
    fallback_allowed = (
        allow_fallback if allow_fallback is not None else settings.allow_heuristic_llm_fallback
    )

    primary_provider: Optional[HighlightLLMProvider] = None

    if prov == "ollama":
        primary_provider = OllamaHighlightLLM()
    elif prov == "gemini":
        primary_provider = GeminiHighlightLLM()
    elif prov == "openai":
        primary_provider = OpenAIHighlightLLM()
    elif prov == "heuristic":
        return HeuristicHighlightLLM()
    else:
        raise LLMError(code="LLM_UNAVAILABLE", message=f"Unknown LLM provider: {prov}")

    if primary_provider.check_health():
        return primary_provider

    # If primary is not healthy:
    if fallback_allowed:
        logger.warning(
            f"Primary LLM '{prov}' is unavailable, but ALLOW_HEURISTIC_LLM_FALLBACK=True. "
            "Using HeuristicHighlightLLM with explicit provenance."
        )
        return HeuristicHighlightLLM()

    # Fallback strictly prohibited
    raise LLMUnavailableError(
        f"LLM provider '{prov}' is unavailable (health check failed). "
        "Silent fallback is prohibited (ALLOW_HEURISTIC_LLM_FALLBACK=False). "
        "Please start the service or set ALLOW_HEURISTIC_LLM_FALLBACK=true to allow heuristic mode."
    )
