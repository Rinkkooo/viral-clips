"""LLM provider abstraction for highlight scoring.

Quality Core v2 uses a fixed absolute rubric so scores remain comparable across batches.
Cloud providers score the whole shortlist in one pass; local Ollama may chunk for context
reliability, but uses the exact same calibrated rubric for every chunk.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from viral_clips.config import settings
from viral_clips.exceptions import ViralClipsError

PROMPT_VERSION = "highlight-v3-absolute-rubric"
SCORING_VERSION = "viral-score-v3"

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
    def __init__(self, message: str = "LLM model unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="LLM_MODEL_UNAVAILABLE", message=message, status_code=503, details=details)


class LLMInvalidResponseError(LLMError):
    def __init__(self, message: str = "LLM output failed validation", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="LLM_INVALID_RESPONSE", message=message, status_code=502, details=details)


class CandidateScore(BaseModel):
    candidate_id: str
    hook_strength: int = Field(ge=0, le=10)
    standalone_context: int = Field(ge=0, le=10)
    payoff: int = Field(ge=0, le=10)
    emotion: int = Field(ge=0, le=10)
    novelty: int = Field(ge=0, le=10)
    pace: int = Field(ge=0, le=10)
    shareability: int = Field(ge=0, le=10)
    title: str
    reason: str
    final_score: float = 0.0

    def compute_final_score(self) -> float:
        self.final_score = calculate_composite_score({
            "hook_strength": self.hook_strength,
            "standalone_context": self.standalone_context,
            "payoff": self.payoff,
            "emotion": self.emotion,
            "novelty": self.novelty,
            "pace": self.pace,
            "shareability": self.shareability,
        })
        return self.final_score


class BatchCandidateScoreResponse(BaseModel):
    scores: List[CandidateScore]


def calculate_composite_score(scores_dict: Dict[str, float]) -> float:
    total = sum(float(scores_dict.get(dim, 5.0)) * weight for dim, weight in VIRAL_WEIGHTS.items())
    return round(total * 10.0, 1)


@runtime_checkable
class HighlightLLMProvider(Protocol):
    provider_name: str
    model_name: str
    is_fallback: bool

    def check_health(self) -> bool: ...

    def score_candidates(
        self,
        candidates: List[Dict[str, Any]],
        language: str = "ru",
        highlight_strategy: Optional[List[str]] = None,
        content_type: Optional[str] = None,
    ) -> List[CandidateScore]: ...


SYSTEM_SCORING_PROMPT = """You are a strict short-form video editor.
Score every candidate with the SAME ABSOLUTE rubric. Scores must remain comparable even when
candidates are evaluated in separate requests. Do NOT curve scores relative to the current batch.

ABSOLUTE SCALE:
0-2 = unusable / broken context / no payoff
3-4 = weak, unlikely to retain attention
5-6 = usable but ordinary
7 = clearly good and publishable with editing
8 = strong, memorable, above-average short-form moment
9 = exceptional; immediate hook plus strong payoff
10 = extremely rare; reserve for near-perfect standalone moments

DIMENSIONS (integer 0..10):
- hook_strength: first 3-5 seconds create curiosity or tension without requiring prior context
- standalone_context: understandable as a standalone clip
- payoff: clear conclusion, reveal, punchline, transformation, or takeaway
- emotion: humor, surprise, tension, awe, anger, empathy, excitement
- novelty: non-obvious idea, unusual story, surprising detail, or fresh framing
- pace: information/reaction density without dead air or repetitive setup
- shareability: viewers have a concrete reason to send, quote, debate, or save it

QUALITY RULES:
1. A clip that starts mid-thought cannot score standalone_context above 5.
2. A clip without a clear ending/payoff cannot score payoff above 5.
3. Generic advice or exposition should usually remain 4-6 even if grammatically complete.
4. Do not reward keywords by themselves. Judge the actual idea and narrative arc.
5. Do not invent events, emotion, or context absent from the transcript.
6. Give short titles that describe the actual moment, not clickbait unrelated to it.
7. Output valid JSON only.
"""


def build_batch_user_prompt(
    candidates: List[Dict[str, Any]],
    language: str = "ru",
    highlight_strategy: Optional[List[str]] = None,
    content_type: Optional[str] = None,
) -> str:
    strategy = ", ".join(highlight_strategy or ["auto"])
    content = content_type or "auto"
    snippets = []
    for candidate in candidates:
        cid = candidate.get("id") or candidate.get("candidate_id")
        duration = candidate.get("duration_s", 0)
        text = candidate.get("text", "")
        snippets.append(f"ID={cid} | duration={duration:.1f}s\n{text}")

    return f"""Transcript language: {language}
Content type: {content}
Requested strategy: {strategy}

Evaluate every candidate using the fixed absolute rubric from the system message.
Return exactly this JSON shape:
{{
  "scores": [
    {{
      "candidate_id": "cand_1",
      "hook_strength": 0,
      "standalone_context": 0,
      "payoff": 0,
      "emotion": 0,
      "novelty": 0,
      "pace": 0,
      "shareability": 0,
      "title": "short title",
      "reason": "specific one-sentence rationale"
    }}
  ]
}}

Candidates:\n\n""" + "\n\n---\n\n".join(snippets)


def _coerce_candidate_score(item: Dict[str, Any], candidate_id: str) -> CandidateScore:
    def score(name: str) -> int:
        try:
            return max(0, min(10, int(round(float(item.get(name, 5))))))
        except Exception:
            return 5

    result = CandidateScore(
        candidate_id=candidate_id,
        hook_strength=score("hook_strength"),
        standalone_context=score("standalone_context"),
        payoff=score("payoff"),
        emotion=score("emotion"),
        novelty=score("novelty"),
        pace=score("pace"),
        shareability=score("shareability"),
        title=str(item.get("title") or f"Highlight {candidate_id}"),
        reason=str(item.get("reason") or "No rationale returned by scorer."),
    )
    result.compute_final_score()
    return result


def _parse_scores(raw_json: Any, candidates: List[Dict[str, Any]]) -> List[CandidateScore]:
    if isinstance(raw_json, dict):
        items = raw_json.get("scores", [])
    elif isinstance(raw_json, list):
        items = raw_json
    else:
        items = []
    item_map = {
        str(item.get("candidate_id")): item
        for item in items
        if isinstance(item, dict) and item.get("candidate_id") is not None
    }

    parsed: List[CandidateScore] = []
    for candidate in candidates:
        cid = str(candidate["id"])
        item = item_map.get(cid)
        if item is None:
            parsed.append(_coerce_candidate_score({}, cid))
            continue
        try:
            score = CandidateScore(**item)
            score.compute_final_score()
        except Exception:
            score = _coerce_candidate_score(item, cid)
        parsed.append(score)
    return parsed


class OllamaHighlightLLM:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model_name = model or settings.ollama_model
        self.provider_name = "ollama"
        self.is_fallback = False
        self._ensure_model_available()

    def _ensure_model_available(self) -> None:
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return
                installed = [m.get("name", "") for m in response.json().get("models", [])]
                if any(self.model_name in name or name.startswith(self.model_name) for name in installed):
                    return
                qwen = next((name for name in installed if "qwen" in name.lower()), None)
                if qwen:
                    self.model_name = qwen
        except Exception:
            return

    def check_health(self) -> bool:
        try:
            with httpx.Client(timeout=3.0) as client:
                return client.get(f"{self.base_url}/api/tags").status_code == 200
        except Exception:
            return False

    def _query(self, prompt: str) -> Any:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_SCORING_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.15},
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                if response.status_code == 404:
                    raise LLMModelUnavailableError(f"Ollama model '{self.model_name}' not found")
                response.raise_for_status()
                return json.loads(response.json().get("message", {}).get("content", "{}"))
        except httpx.ConnectError as exc:
            raise LLMUnavailableError(f"Cannot connect to Ollama at {self.base_url}: {exc}")
        except LLMError:
            raise
        except Exception as exc:
            raise LLMInvalidResponseError(f"Ollama returned invalid output: {exc}")

    def score_candidates(self, candidates, language="ru", highlight_strategy=None, content_type=None):
        if not self.check_health():
            raise LLMUnavailableError(f"Ollama is unreachable at {self.base_url}")
        # Local models may need smaller requests, but the absolute rubric keeps chunks calibrated.
        chunk_size = 6
        results: List[CandidateScore] = []
        for start in range(0, len(candidates), chunk_size):
            chunk = candidates[start:start + chunk_size]
            prompt = build_batch_user_prompt(chunk, language, highlight_strategy, content_type)
            results.extend(_parse_scores(self._query(prompt), chunk))
        return results


class GeminiHighlightLLM:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.get_gemini_key()
        self.model_name = model or settings.gemini_model
        self.provider_name = "gemini"
        self.is_fallback = False

    def check_health(self) -> bool:
        return bool(self.api_key)

    def score_candidates(self, candidates, language="ru", highlight_strategy=None, content_type=None):
        if not self.api_key:
            raise LLMUnavailableError("Gemini API key is not configured")
        prompt = build_batch_user_prompt(candidates, language, highlight_strategy, content_type)
        body = {
            "contents": [{"parts": [{"text": f"{SYSTEM_SCORING_PROMPT}\n\n{prompt}"}]}],
            "generationConfig": {"temperature": 0.15, "response_mime_type": "application/json"},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, json=body)
                if response.status_code == 404:
                    raise LLMModelUnavailableError(f"Gemini model '{self.model_name}' unavailable")
                response.raise_for_status()
                payload = response.json()
                text = payload["candidates"][0]["content"]["parts"][0]["text"]
                return _parse_scores(json.loads(text), candidates)
        except LLMError:
            raise
        except Exception as exc:
            raise LLMInvalidResponseError(f"Gemini API/JSON error: {exc}")


class OpenAIHighlightLLM:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.get_openai_key()
        self.model_name = model or settings.openai_model
        self.provider_name = "openai"
        self.is_fallback = False

    def check_health(self) -> bool:
        return bool(self.api_key)

    def score_candidates(self, candidates, language="ru", highlight_strategy=None, content_type=None):
        if not self.api_key:
            raise LLMUnavailableError("OpenAI API key is not configured")
        prompt = build_batch_user_prompt(candidates, language, highlight_strategy, content_type)
        body = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_SCORING_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.15,
        }
        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"]
                return _parse_scores(json.loads(raw), candidates)
        except Exception as exc:
            raise LLMInvalidResponseError(f"OpenAI API/JSON error: {exc}")


class HeuristicHighlightLLM:
    """Explicit fallback only; generic heuristics, never benchmark-specific phrases."""

    def __init__(self):
        self.provider_name = "heuristic"
        self.model_name = "heuristic-v3"
        self.is_fallback = True

    def check_health(self) -> bool:
        return True

    def score_candidates(self, candidates, language="ru", highlight_strategy=None, content_type=None):
        logger.warning("Using explicit heuristic highlight fallback")
        output: List[CandidateScore] = []
        for candidate in candidates:
            text = str(candidate.get("text", ""))
            duration = max(float(candidate.get("duration_s", 1.0)), 1.0)
            words = text.split()
            density = len(words) / duration
            first = " ".join(words[:12]).lower()
            last = " ".join(words[-18:]).lower()
            starts_dangling = bool(words and words[0].lower().strip(",.!?") in {"и", "а", "но", "and", "but", "so"})
            closes = text.rstrip().endswith((".", "!", "?"))
            hook = 5 + (1 if "?" in first else 0) - (2 if starts_dangling else 0)
            payoff = 6 + (1 if closes else -1)
            standalone = 7 - (2 if starts_dangling else 0)
            pace = 8 if 1.6 <= density <= 3.5 else 6 if 1.0 <= density <= 4.5 else 4
            emotion = 6 + (1 if "!" in text else 0)
            novelty = 5
            shareability = 5 + (1 if "?" in first else 0)
            title = " ".join(words[:7]).strip(" ,.!?—-") or ("Ключевой момент" if language == "ru" else "Key moment")
            score = CandidateScore(
                candidate_id=str(candidate["id"]),
                hook_strength=max(0, min(10, hook)),
                standalone_context=max(0, min(10, standalone)),
                payoff=max(0, min(10, payoff)),
                emotion=max(0, min(10, emotion)),
                novelty=novelty,
                pace=pace,
                shareability=max(0, min(10, shareability)),
                title=title,
                reason="Generic fallback based on context completeness, closure and speech density.",
            )
            score.compute_final_score()
            output.append(score)
        return output


def get_llm_provider(provider_name: Optional[str] = None, allow_fallback: Optional[bool] = None) -> HighlightLLMProvider:
    provider = (provider_name or settings.llm_provider).lower()
    fallback_allowed = allow_fallback if allow_fallback is not None else settings.allow_heuristic_llm_fallback

    if provider == "ollama":
        primary: HighlightLLMProvider = OllamaHighlightLLM()
    elif provider == "gemini":
        primary = GeminiHighlightLLM()
    elif provider == "openai":
        primary = OpenAIHighlightLLM()
    elif provider == "heuristic":
        return HeuristicHighlightLLM()
    else:
        raise LLMError(code="LLM_UNAVAILABLE", message=f"Unknown LLM provider: {provider}")

    if primary.check_health():
        return primary
    if fallback_allowed:
        logger.warning("Primary LLM '{}' unavailable; explicit heuristic fallback enabled", provider)
        return HeuristicHighlightLLM()
    raise LLMUnavailableError(
        f"LLM provider '{provider}' is unavailable and heuristic fallback is disabled"
    )
