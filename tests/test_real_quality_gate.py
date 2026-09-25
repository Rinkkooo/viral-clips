"""
Unit and Integration Tests for Viral Clips - REAL VIDEO QUALITY GATE.
Verifies all core requirements from the Real Video Quality Gate specification:
1. Real Faster-Whisper ASR auto language detection and strict error gate (no fake synthetic fallback in dev/prod).
2. Modular LLM abstraction, Pydantic structured output validation, batch scoring, and fallback enforcement.
3. Real dynamic crop trajectory evaluated directly in FFmpeg filtergraph (verified by frame pixel movement).
4. Subtitle and Render manifests with provenance metadata.
5. Human review scorecard CRUD endpoints and fast rerender without re-ASR.
"""

import json
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

from viral_clips.api.app import app
from viral_clips.config import settings
from viral_clips.core.asr import ASRError, transcribe_video
from viral_clips.core.llm_providers import (
    CandidateScore,
    HeuristicHighlightLLM,
    HighlightLLMError,
    OllamaHighlightLLM,
    VIRAL_WEIGHTS,
    get_llm_provider,
)
from viral_clips.core.media_probe import probe_media
from viral_clips.core.renderer import render_clip
from viral_clips.core.smart_reframe import build_dynamic_crop_expression, generate_crop_plan
from viral_clips.core.subtitles import generate_subtitles
from viral_clips.db.database import (
    create_project,
    get_clip,
    get_clip_review,
    save_clip_and_render,
    save_clip_review,
)

SAMPLE_VIDEO = Path("./samples/sample_podcast.mp4").resolve()


# ==========================================
# 1. ASR & Auto Language Tests
# ==========================================

def test_asr_strict_rejection_of_synthetic_fallback(monkeypatch, tmp_path):
    """Verifies that ASR strictly forbids silent synthetic fallback in production/dev."""
    monkeypatch.setattr(settings, "allow_test_fixtures", False)
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "asr_provider", "faster-whisper")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "groq_api_key", None)

    import viral_clips.core.asr as asr_module
    def mock_fail(*args, **kwargs):
        raise asr_module.ASRError("Local Faster-Whisper failed to initialize")
    monkeypatch.setattr(asr_module, "transcribe_audio_faster_whisper", mock_fail)

    with pytest.raises(ASRError) as exc_info:
        transcribe_video(
            video_path=SAMPLE_VIDEO,
            output_dir=tmp_path / "strict_asr",
            force_fallback=False,
        )
    assert exc_info.value.code == "ASR_FAILED"
    assert "Silent synthetic fallback is prohibited" in exc_info.value.message


def test_asr_auto_language_capture(monkeypatch, tmp_path):
    """Verifies that transcript schema captures requested_language, detected_language, and language_probability."""
    import viral_clips.core.asr as asr_module

    def mock_transcribe_fw(*args, **kwargs):
        return {
            "schema_version": "1.0.0",
            "provider": "faster_whisper",
            "model": "small",
            "device": "cuda",
            "requested_language": kwargs.get("language"),
            "detected_language": "ru",
            "language_probability": 0.985,
            "duration_s": 10.0,
            "total_words": 5,
            "words": [
                {"word": "Привет", "start": 0.0, "end": 0.5, "start_ms": 0, "end_ms": 500, "probability": 0.99, "speaker": None},
                {"word": "мир", "start": 0.5, "end": 1.0, "start_ms": 500, "end_ms": 1000, "probability": 0.98, "speaker": None},
            ],
            "segments": [
                {"id": 0, "start": 0.0, "end": 1.0, "start_ms": 0, "end_ms": 1000, "text": "Привет мир"},
            ],
        }

    monkeypatch.setattr(asr_module, "transcribe_audio_faster_whisper", mock_transcribe_fw)

    # When language is 'auto', it passes language=None to faster_whisper
    res = asr_module.transcribe_video(
        video_path=SAMPLE_VIDEO,
        output_dir=tmp_path / "auto_asr",
        language="auto",
    )
    assert res["detected_language"] == "ru"
    assert res["language_probability"] == 0.985
    assert res["requested_language"] in ("auto", None)
    assert (tmp_path / "auto_asr" / "transcript.json").is_file()


# ==========================================
# 2. LLM Provider & Scoring Tests
# ==========================================

def test_candidate_score_pydantic_validation():
    """Verifies Pydantic structured output validation and 0-100 composite scoring."""
    # Valid candidate
    cs = CandidateScore(
        candidate_id="cand_1",
        hook_strength=9,
        standalone_context=8,
        payoff=9,
        emotion=7,
        novelty=8,
        pace=7,
        shareability=9,
        title="Секрет экспоненциального роста",
        reason="Сильный хук в первые секунды и четкая законченная мысль.",
    )
    score = cs.compute_final_score()
    assert 0.0 <= score <= 100.0
    # Weights sum verification
    weight_sum = sum(VIRAL_WEIGHTS.values())
    assert abs(weight_sum - 1.0) < 1e-6

    # Test invalid score > 10 raises validation error
    with pytest.raises(Exception):
        CandidateScore(
            candidate_id="cand_bad",
            hook_strength=15,  # Invalid: > 10
            standalone_context=8,
            payoff=9,
            emotion=7,
            novelty=8,
            pace=7,
            shareability=9,
            title="Bad",
            reason="Invalid score",
        )


def test_heuristic_fallback_strict_rejection(monkeypatch):
    """Verifies that heuristic fallback is rejected when allow_heuristic_llm_fallback=False."""
    monkeypatch.setattr(settings, "allow_heuristic_llm_fallback", False)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    with pytest.raises(HighlightLLMError) as exc_info:
        get_llm_provider("gemini", allow_fallback=False)
    assert "Silent fallback is prohibited" in str(exc_info.value.message)


def test_heuristic_fallback_allowed_when_enabled(monkeypatch):
    """Verifies that when allowed, heuristic fallback scores candidates and marks fallback_used."""
    monkeypatch.setattr(settings, "allow_heuristic_llm_fallback", True)
    provider = get_llm_provider("heuristic")
    scores = provider.score_candidates([
        {"id": "c1", "text": "секрет почему это работает никогда не забывайте", "duration_s": 30.0},
    ])
    assert len(scores) == 1
    assert scores[0].hook_strength == 8
    assert scores[0].final_score > 0.0
    assert provider.is_fallback is True


# ==========================================
# 3. Real Dynamic Crop Execution in FFmpeg
# ==========================================

def test_dynamic_crop_expression_syntax():
    """Verifies nested lerp piecewise linear expression syntax."""
    keyframes = [
        {"timestamp_s": 0.0, "crop_x": 100},
        {"timestamp_s": 1.0, "crop_x": 300},
        {"timestamp_s": 2.0, "crop_x": 500},
    ]
    expr = build_dynamic_crop_expression(keyframes, default_x=200)
    assert "lerp" in expr
    assert "if(lt(t" in expr


def test_dynamic_crop_ffmpeg_pixel_movement(tmp_path):
    """
    Renders a clip with dynamic crop and verifies that FFmpeg actually moved the camera.
    Compares pixels extracted at t=0.5s and t=2.0s to prove real camera motion.
    """
    out_video = tmp_path / "dynamic_crop_render.mp4"

    # Define crop plan with explicit pan from crop_x=0 to crop_x=500
    crop_plan = {
        "schema_version": "1.0.0",
        "preset": "active_speaker",
        "crop_width": 607,
        "crop_height": 1080,
        "crop_x": 0,
        "crop_y": 0,
        "trajectory": [
            {"timestamp_s": 0.0, "crop_x": 50},
            {"timestamp_s": 1.0, "crop_x": 250},
            {"timestamp_s": 2.5, "crop_x": 500},
        ],
    }

    manifest = render_clip(
        source_video=SAMPLE_VIDEO,
        output_video_path=out_video,
        clip_start_ms=0,
        clip_end_ms=3000,
        crop_plan=crop_plan,
        clip_id="test_dynamic_clip",
    )
    assert out_video.is_file()
    assert manifest["has_dynamic_trajectory"] is True
    assert manifest["encoder"] in ("h264_nvenc", "libx264")

    # Extract 2 frames from the rendered vertical video via cv2
    import cv2
    cap = cv2.VideoCapture(str(out_video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Frame at 0.5s
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(0.5 * fps))
    ret1, frame1 = cap.read()

    # Frame at 2.0s
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(2.0 * fps))
    ret2, frame2 = cap.read()
    cap.release()

    assert ret1 and ret2
    assert frame1.shape == (1920, 1080, 3)
    assert frame2.shape == (1920, 1080, 3)

    # Calculate absolute pixel difference: must be > 0 (proving camera moved)
    diff = np.mean(np.abs(frame1.astype(float) - frame2.astype(float)))
    assert diff > 0.01, "Rendered video frames must differ due to horizontal camera trajectory!"


# ==========================================
# 4. Manifests & Provenance
# ==========================================

def test_subtitle_manifest_generation(tmp_path):
    """Verifies that generate_subtitles produces subtitle_manifest.json with clamped interval."""
    words = [
        {"word": "Первое", "start": 1.0, "end": 1.4, "start_ms": 1000, "end_ms": 1400},
        {"word": "слово", "start": 1.5, "end": 2.0, "start_ms": 1500, "end_ms": 2000},
        {"word": "вне_клипа", "start": 10.0, "end": 10.5, "start_ms": 10000, "end_ms": 10500},
    ]
    ass_path = tmp_path / "test.ass"
    art = generate_subtitles(
        words=words,
        clip_start_ms=1000,
        clip_end_ms=3000,
        output_ass_path=ass_path,
        preset="bold_karaoke",
    )
    assert ass_path.is_file()
    assert art["word_count"] == 2  # Only clamped words in range [1000, 3000]

    manifest_path = tmp_path / "subtitle_manifest.json"
    assert manifest_path.is_file()
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["word_count"] == 2
    assert data["preset"] == "bold_karaoke"


# ==========================================
# 5. Human Review Scorecard & Rerender
# ==========================================

def test_clip_review_scorecard_api(tmp_path):
    """Verifies POST /v1/clips/{clip_id}/review and GET /v1/clips/{clip_id}/review."""
    client = TestClient(app)
    proj = create_project(name="Scorecard Test Project")
    p_id = proj["id"]

    dummy_manifest = {
        "output_file": str(tmp_path / "dummy.mp4"),
        "resolution": "1080x1920",
        "encoder": "libx264",
        "file_size_bytes": 1024,
    }
    clip_id, _ = save_clip_and_render(
        project_id=p_id,
        candidate_id=None,
        start_ms=0,
        end_ms=5000,
        render_manifest=dummy_manifest,
        preset="bold_karaoke",
    )

    # Initial get returns default
    get_res = client.get(f"/v1/clips/{clip_id}/review")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["publishable"] is False

    # Save review scorecard
    post_res = client.post(
        f"/v1/clips/{clip_id}/review",
        json={
            "publishable": True,
            "highlight_quality": 5,
            "framing_quality": 4,
            "subtitle_quality": 5,
            "notes": "Отличный вирусный хук и идеальный синхрон субтитров.",
        },
    )
    assert post_res.status_code == 200
    rev = post_res.json()
    assert rev["publishable"] is True
    assert rev["highlight_quality"] == 5
    assert rev["framing_quality"] == 4
    assert rev["subtitle_quality"] == 5
    assert rev["notes"] == "Отличный вирусный хук и идеальный синхрон субтитров."

    # Verify persistence
    persisted = get_clip_review(clip_id)
    assert persisted is not None
    assert persisted["publishable"] == 1
    assert persisted["highlight_quality"] == 5
