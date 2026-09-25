"""
Automated Speech Recognition (ASR) module.
Extracts speech with word-level timestamps and produces standardized transcript.json artifacts.
Supports Faster-Whisper (CUDA / CPU), Groq API, and deterministic fallback.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from loguru import logger

from viral_clips.config import settings
from viral_clips.core.audio_extract import extract_audio_for_asr
from viral_clips.exceptions import ViralClipsError

SCHEMA_VERSION = "1.0.0"


class ASRError(ViralClipsError):
    """Raised when speech recognition fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(code="ASR_FAILED", message=message, status_code=500, details=details)


def _register_cuda_dlls():
    """Register site-packages nvidia DLLs into Windows DLL search directory."""
    import sys, os
    if sys.platform != "win32":
        return
    for base in sys.path:
        if "site-packages" in base:
            nvidia_dir = os.path.join(base, "nvidia")
            if os.path.exists(nvidia_dir):
                for root, dirs, files in os.walk(nvidia_dir):
                    if "bin" in dirs:
                        bin_path = os.path.join(root, "bin")
                        try:
                            os.add_dll_directory(bin_path)
                            if bin_path not in os.environ.get("PATH", ""):
                                os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")
                        except Exception:
                            pass


def transcribe_audio_faster_whisper(
    wav_path: Path,
    model_size: str = "small",
    device: str = "cuda",
    compute_type: str = "float16",
    language: Optional[str] = None,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Dict[str, Any]:
    """Transcribes audio using local faster-whisper on GPU (CUDA) or CPU."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ASRError(
            "faster-whisper package is not installed. Install via pip install faster-whisper or use fallback."
        )

    _register_cuda_dlls()
    logger.info(f"Loading Faster-Whisper model '{model_size}' on {device} ({compute_type})...")
    req_lang = None if language in ("auto", "Auto detect", "", None) else language

    actual_device = device
    actual_compute_type = compute_type

    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segments_generator, info = model.transcribe(
            str(wav_path),
            language=req_lang,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        segments_list = list(segments_generator)
    except Exception as e:
        logger.warning(f"Faster-Whisper on {device} ({compute_type}) failed: {e}. Falling back to CPU (int8)...")
        actual_device = "cpu"
        actual_compute_type = "int8"
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments_generator, info = model.transcribe(
            str(wav_path),
            language=req_lang,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        segments_list = list(segments_generator)

    detected_language = info.language
    lang_prob = round(float(getattr(info, "language_probability", 1.0)), 3)
    duration_s = info.duration

    segments_out: List[Dict[str, Any]] = []
    words_out: List[Dict[str, Any]] = []

    for seg_idx, seg in enumerate(segments_list):
        seg_start_ms = int(round(seg.start * 1000))
        seg_end_ms = int(round(seg.end * 1000))
        segments_out.append({
            "id": seg_idx,
            "start": round(float(seg.start), 3),
            "end": round(float(seg.end), 3),
            "start_ms": seg_start_ms,
            "end_ms": seg_end_ms,
            "text": seg.text.strip(),
        })

        if seg.words:
            for w in seg.words:
                words_out.append({
                    "word": w.word.strip(),
                    "text": w.word.strip(),
                    "start": round(float(w.start), 3),
                    "end": round(float(w.end), 3),
                    "start_ms": int(round(w.start * 1000)),
                    "end_ms": int(round(w.end * 1000)),
                    "probability": round(float(w.probability), 3),
                })

        if progress_callback and duration_s > 0:
            pct = min(1.0, seg.end / duration_s)
            progress_callback(pct)

    return {
        "provider": "faster_whisper",
        "model": model_size,
        "device": actual_device,
        "compute_type": actual_compute_type,
        "requested_language": language if language not in (None, "") else "auto",
        "detected_language": detected_language,
        "language_probability": lang_prob,
        "duration_s": round(duration_s, 3),
        "segments": segments_out,
        "words": words_out,
    }


def generate_fallback_transcript(
    wav_path: Path,
    duration_s: float = 60.0,
    language: str = "ru",
) -> Dict[str, Any]:
    """
    Generates a realistic structured transcript fixture when offline or running tests.
    Ensures end-to-end pipeline execution without requiring multi-gigabyte model downloads.
    """
    sample_phrases = [
        ("Секрет вирусных видео заключается в первых трех секундах.", 0.5, 4.2),
        ("Если вы не зацепите зрителя сразу, он просто смахнет ролик дальше.", 4.5, 8.8),
        ("Поэтому хук — это самое главное во всем коротком контенте.", 9.0, 13.1),
        ("Второй важный фактор — это темп повествования и плотность информации.", 14.0, 19.5),
        ("Никакой воды, только факты и неожиданные инсайты.", 20.0, 24.2),
        ("И третий секрет — динамичные караоке-субтитры, которые удерживают взгляд.", 25.0, 31.0),
        ("Давайте разберем на конкретном примере, как это удвоит ваши охваты!", 32.0, 37.5),
        ("Подписывайтесь, чтобы не пропустить следующий разбор алгоритмов!", 38.0, 43.0),
    ]

    segments = []
    words = []
    for idx, (phrase, s, e) in enumerate(sample_phrases):
        if e > duration_s and duration_s > 10:
            break
        s_ms = int(s * 1000)
        e_ms = int(e * 1000)
        segments.append({
            "id": idx,
            "start_ms": s_ms,
            "end_ms": e_ms,
            "text": phrase,
        })
        tokens = phrase.split()
        word_dur = (e_ms - s_ms) / max(1, len(tokens))
        for w_idx, tok in enumerate(tokens):
            w_start = int(s_ms + w_idx * word_dur)
            w_end = int(w_start + word_dur)
            words.append({
                "word": tok,
                "text": tok,
                "start": round(w_start / 1000.0, 3),
                "end": round(w_end / 1000.0, 3),
                "start_ms": w_start,
                "end_ms": w_end,
                "probability": 0.95,
            })
    return {
        "provider": "test_fixture",
        "is_fixture": True,
        "model": "fallback-fixture-v1",
        "requested_language": language or "auto",
        "detected_language": language or "ru",
        "language": language or "ru",
        "language_probability": 1.0,
        "duration_s": round(duration_s, 3),
        "segments": segments,
        "words": words,
    }


def transcribe_audio_cloud(
    wav_path: Path,
    api_key: str,
    provider: str = "groq",
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """Transcribes audio using Groq Whisper or OpenAI Whisper API with word-level timestamps."""
    import httpx

    url = (
        "https://api.groq.com/openai/v1/audio/transcriptions"
        if provider == "groq"
        else "https://api.openai.com/v1/audio/transcriptions"
    )
    model = "whisper-large-v3" if provider == "groq" else "whisper-1"
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(wav_path, "rb") as f:
        files = {"file": (wav_path.name, f, "audio/wav")}
        data: Dict[str, Any] = {
            "model": model,
            "response_format": "verbose_json",
            "timestamp_granularities[]": ["word", "segment"],
        }
        if language:
            data["language"] = language

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, files=files, data=data)
            resp.raise_for_status()
            res = resp.json()

    detected_language = res.get("language", language or "en")
    duration_s = float(res.get("duration", 0.0))

    segments_out = []
    for s_idx, seg in enumerate(res.get("segments", [])):
        segments_out.append({
            "id": s_idx,
            "start_ms": int(round(seg["start"] * 1000)),
            "end_ms": int(round(seg["end"] * 1000)),
            "text": seg["text"].strip(),
        })

    words_out = []
    for w in res.get("words", []):
        words_out.append({
            "word": w["word"].strip(),
            "start_ms": int(round(w["start"] * 1000)),
            "end_ms": int(round(w["end"] * 1000)),
            "probability": round(float(w.get("confidence", 0.95)), 3),
        })

    return {
        "model": f"{provider}-{model}",
        "language": detected_language,
        "duration_s": round(duration_s, 3),
        "segments": segments_out,
        "words": words_out,
    }


def transcribe_video(
    video_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    language: Optional[str] = None,
    force_fallback: bool = False,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> Dict[str, Any]:
    """
    Full Phase 1 pipeline:
    Extracts audio from video and generates standardized 'transcript.json' artifact.
    Enforces strict ASR verification; silent fallback is prohibited outside test fixture mode.
    """
    v_path = Path(video_path).resolve()
    out_dir = Path(output_dir) if output_dir else v_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    transcript_artifact = out_dir / "transcript.json"

    # Audio extraction
    wav_path = out_dir / "audio_asr.wav"
    extract_audio_for_asr(v_path, wav_path)

    raw_result = None
    last_error: Optional[Exception] = None

    # 1. Local Faster-Whisper if configured and not forcing fallback
    if not force_fallback and settings.asr_provider in ("faster_whisper", "faster-whisper"):
        try:
            raw_result = transcribe_audio_faster_whisper(
                wav_path=wav_path,
                model_size=settings.whisper_model,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                language=language,
                progress_callback=progress_callback,
            )
        except Exception as e:
            last_error = e
            logger.warning(f"Local Faster-Whisper transcription failed: {e}")

    # 2. Cloud ASR providers (Groq / OpenAI) fallback if local not available or failed
    if raw_result is None and not force_fallback:
        groq_key = settings.get_groq_key()
        openai_key = settings.get_openai_key()
        if groq_key:
            try:
                logger.info("Attempting cloud ASR via Groq Whisper API...")
                raw_result = transcribe_audio_cloud(wav_path, api_key=groq_key, provider="groq", language=language)
            except Exception as e:
                last_error = e
                logger.warning(f"Groq Whisper transcription failed: {e}")
        elif openai_key:
            try:
                logger.info("Attempting cloud ASR via OpenAI Whisper API...")
                raw_result = transcribe_audio_cloud(wav_path, api_key=openai_key, provider="openai", language=language)
            except Exception as e:
                last_error = e
                logger.warning(f"OpenAI Whisper transcription failed: {e}")

    # 3. Handle failure / fixture allowance
    if raw_result is None:
        is_test_mode = force_fallback or settings.allow_test_fixtures or (settings.app_env == "test")
        if is_test_mode:
            logger.warning("Using synthetic fallback transcript strictly for testing/fixture mode.")
            raw_result = generate_fallback_transcript(
                wav_path=wav_path,
                language=language or "ru",
            )
        else:
            error_details = {"last_error": str(last_error)} if last_error else {}
            raise ASRError(
                f"ASR failed: local Faster-Whisper and cloud providers failed or were unconfigured ({last_error}). "
                "Silent synthetic fallback is prohibited in production/dev mode. "
                "Please configure faster-whisper or set GROQ_API_KEY/OPENAI_API_KEY.",
                details=error_details,
            )

    # Standardize artifact with metadata per Real Video Quality Gate spec
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_video": str(v_path),
        "provider": raw_result.get("provider", settings.asr_provider),
        "is_fixture": raw_result.get("is_fixture", False),
        "model": raw_result.get("model", settings.whisper_model),
        "device": raw_result.get("device", settings.whisper_device),
        "compute_type": raw_result.get("compute_type", settings.whisper_compute_type),
        "requested_language": raw_result.get("requested_language", language or "auto"),
        "detected_language": raw_result.get("detected_language", raw_result.get("language", language or "ru")),
        "language_probability": raw_result.get("language_probability", 1.0),
        "language": raw_result.get("detected_language", raw_result.get("language", language or "ru")),
        "duration_s": raw_result.get("duration_s", 0.0),
        "total_words": len(raw_result.get("words", [])),
        "total_segments": len(raw_result.get("segments", [])),
        "segments": raw_result.get("segments", []),
        "words": raw_result.get("words", []),
    }

    with open(transcript_artifact, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)

    logger.success(f"Saved transcript artifact: {transcript_artifact} ({artifact['total_words']} words)")
    return artifact
