"""
Verification test suite for Viral Clips UI/UX v2:
- System capabilities endpoint (truthful hardware and provider state)
- Backward-compatible ProcessRequest resolution (nested v2 + legacy flat)
- Highlight strategy & content type prompt injection
- Human feedback scorecard endpoint & product events logging
- Fast highlight regeneration endpoint without re-running ASR
- UI HTML contains required creator-product components
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from viral_clips.api.app import app, ProcessRequest
from viral_clips.config import settings
from viral_clips.core.llm_providers import build_batch_user_prompt
from viral_clips.db.database import (
    create_project,
    get_connection,
    get_product_events,
    save_clip_and_render,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_system_capabilities_endpoint(client):
    """Verifies that /v1/system/capabilities reports real hardware and capabilities without fake features."""
    response = client.get("/v1/system/capabilities")
    assert response.status_code == 200
    data = response.json()

    assert "asr" in data
    assert "llm" in data
    assert "render" in data
    assert "features" in data

    # Verify real flags
    assert data["features"]["dynamic_reframe"] is True
    assert data["features"]["split_speaker"] is False  # truthful: no fake split speaker
    assert "nvenc" in data["render"]


def test_process_request_v2_resolution():
    """Verifies ProcessRequest backward compatibility for nested vs flat duration and subtitles."""
    # 1. v2 nested format
    v2_req = ProcessRequest(
        clip_count=3,
        duration={"min_seconds": 25.0, "max_seconds": 55.0},
        min_duration_s=20.0,
        max_duration_s=75.0,
        subtitles={"preset": "neon_glow"},
        subtitle_preset="bold_karaoke",
        highlight_strategy=["hooks", "hot_takes"],
        content_type="podcast",
    )
    min_d, max_d = v2_req.resolve_duration()
    assert min_d == 25.0
    assert max_d == 55.0
    assert v2_req.resolve_subtitle_preset() == "neon_glow"
    assert v2_req.highlight_strategy == ["hooks", "hot_takes"]
    assert v2_req.content_type == "podcast"

    # 2. Legacy flat format
    flat_req = ProcessRequest(
        clip_count=5,
        min_duration_s=18.0,
        max_duration_s=62.0,
        subtitle_preset="minimal",
    )
    min_flat_d, max_flat_d = flat_req.resolve_duration()
    assert min_flat_d == 18.0
    assert max_flat_d == 62.0
    assert flat_req.resolve_subtitle_preset() == "minimal"


def test_llm_prompt_incorporates_strategy_and_content_type():
    """Verifies that user highlight strategies and content types are actively injected into LLM prompt."""
    candidates = [{
        "candidate_id": 1,
        "start_ms": 1000,
        "end_ms": 30000,
        "duration_s": 29.0,
        "text": "The greatest mistake in software architecture is building without tests.",
    }]

    prompt = build_batch_user_prompt(
        candidates,
        highlight_strategy=["hooks", "insights"],
        content_type="interview",
    )

    assert "USER HIGHLIGHT STRATEGY:" in prompt
    assert "hook_strength" in prompt
    assert "INTERVIEW" in prompt


def test_clip_feedback_and_product_events(client):
    """Verifies POST /v1/clips/{clip_id}/feedback, GET /v1/clips/{clip_id}/feedback, and product_events logging."""
    # 1. Create project
    p_res = client.post("/v1/projects", json={"name": "UI/UX v2 Feedback Test", "desired_clip_count": 3})
    assert p_res.status_code == 201
    project_id = p_res.json()["id"]

    # 2. Insert dummy clip into database
    conn = get_connection()
    clip_id = f"test_clip_{project_id[:6]}"
    conn.execute(
        """
        INSERT INTO clips (id, project_id, start_ms, end_ms, status, created_at)
        VALUES (?, ?, 0, 30000, 'ready', datetime('now'))
        """,
        (clip_id, project_id),
    )
    conn.commit()

    # 3. Submit feedback
    fb_payload = {
        "publishable": True,
        "issues": ["bad_start"],
        "ratings": {"highlight": 4, "framing": 5, "subtitles": 5},
    }
    fb_res = client.post(f"/v1/clips/{clip_id}/feedback", json=fb_payload)
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data["publishable"] is True
    assert fb_data["issues"] == ["bad_start"]
    assert fb_data["ratings"]["framing"] == 5

    # 4. Retrieve feedback
    get_fb_res = client.get(f"/v1/clips/{clip_id}/feedback")
    assert get_fb_res.status_code == 200
    retrieved = get_fb_res.json()
    assert retrieved["issues"] == ["bad_start"]

    # 5. Check product analytics event
    events_res = client.get("/v1/system/events")
    assert events_res.status_code == 200
    events = events_res.json()
    event_names = [e["event_name"] for e in events]
    assert "clip_feedback_submitted" in event_names
    assert "project_created" in event_names


def test_regenerate_highlights_endpoint(client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "allow_heuristic_llm_fallback", True)
    # 1. Create project
    p_res = client.post("/v1/projects", json={"name": "Regen Test Project", "desired_clip_count": 2})
    assert p_res.status_code == 201
    project_id = p_res.json()["id"]

    # 2. Place dummy transcript in storage/output/proj_{project_id}/transcript.json
    out_dir = Path("./storage/output") / f"proj_{project_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    dummy_transcript = {
        "text": "Hello world. Here is a powerful insight about viral clips. This changed everything.",
        "duration_s": 45.0,
        "total_words": 14,
        "segments": [
            {"start_ms": 0, "end_ms": 15000, "text": "Hello world. Here is a powerful insight about viral clips."},
            {"start_ms": 15000, "end_ms": 40000, "text": "This changed everything and made our videos blow up."},
        ],
        "words": [
            {"word": "Hello", "start_s": 0.0, "end_s": 0.5},
            {"word": "world", "start_s": 0.6, "end_s": 1.0},
        ],
    }
    with open(out_dir / "transcript.json", "w", encoding="utf-8") as f:
        json.dump(dummy_transcript, f)

    # 3. Call regenerate-highlights
    regen_res = client.post(
        f"/v1/projects/{project_id}/regenerate-highlights",
        json={
            "clip_count": 2,
            "min_duration_s": 10.0,
            "max_duration_s": 40.0,
            "highlight_strategy": ["insights"],
            "content_type": "podcast",
        },
    )
    assert regen_res.status_code == 200
    regen_data = regen_res.json()
    assert regen_data["status"] == "success"
    assert "top_clips" in regen_data
    assert regen_data["candidates_count"] >= 1


def test_ui_serves_v2_creator_studio(client):
    """Verifies GET / returns HTML containing UI/UX v2 elements."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert "source-video-card" in html
    assert "btn-submit-text" in html
    assert "timeline-stage-1" in html
    assert "feedback-issues-container" in html
    assert "player-timecode-cur" in html
    assert "nudgeTrim" in html
    assert "sub-live-preview-text" in html
    assert "checkJobRecovery" in html
    assert "lang-selector" in html
    assert "theme-toggle-btn" in html
    assert "screen-projects" in html
    assert "screen-dashboard" in html
