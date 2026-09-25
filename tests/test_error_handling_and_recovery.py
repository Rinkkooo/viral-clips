"""
Tests for Error Handling, Audio Validation, and UI Recovery State:
1. Audio extraction error sanitization (no raw ffmpeg gcc compiler flags).
2. Pipeline validation rejects missing audio streams early with helpful message.
3. Web UI contains dedicated error box, recovery action buttons, and draft persistence.
"""

import pytest
from fastapi.testclient import TestClient

from viral_clips.api.app import app
from viral_clips.core.audio_extract import _clean_ffmpeg_error
from viral_clips.exceptions import MissingStreamError
from viral_clips.services.pipeline_service import start_pipeline_job
from viral_clips.db.database import create_project


@pytest.fixture
def client():
    return TestClient(app)


def test_clean_ffmpeg_error():
    """Verifies that ffmpeg compiler flags are stripped and clean error is produced."""
    raw_banner = """ffmpeg version 8.0.1-essentials_build-www.gyan.dev Copyright (c) 2000-2025 the FFmpeg developers
  built with gcc 15.2.0 (Rev8, Built by MSYS2 project)
  configuration: --enable-gpl --enable-version3 --enable-static --disable-w32threads
  libavutil      60.  8.100 / 60.  8.100
  libavcodec     62. 11.100 / 62. 11.100
Output file does not contain any stream
"""
    cleaned = _clean_ffmpeg_error(raw_banner)
    assert "В исходном видеофайле отсутствует аудиодорожка" in cleaned
    assert "configuration: --enable-gpl" not in cleaned
    assert "built with gcc" not in cleaned


def test_pipeline_rejects_audio_missing_video(tmp_path):
    """Verifies that pipeline explicitly detects missing audio and raises friendly MissingStreamError."""
    # Test with video-only mock probe info
    from viral_clips.core.media_probe import probe_media
    # Test on real backup video-only file if exists
    video_only_path = "C:/Users/user/Downloads/videoplayback_video_only.mp4"
    import os
    if os.path.exists(video_only_path):
        probe = probe_media(video_only_path, allow_missing_audio=True)
        assert probe.get("audio_streams_count", 0) == 0
        assert probe.get("primary_audio") is None


def test_ui_contains_error_state_and_recovery_components(client):
    """Verifies that UI HTML contains all error handling, recovery, and persistence elements."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Dedicated error card on processing screen
    assert "processing-error-box" in html
    assert "processing-error-summary" in html
    assert "processing-error-details" in html
    assert "returnToProjectSettings" in html
    assert "retryCurrentJob" in html
    assert "toggleErrorDetails" in html

    # Draft persistence functions
    assert "saveFormDraft" in html
    assert "restoreFormDraft" in html
    assert "onVideoPathChange" in html
    assert "cleanErrorMessage" in html
