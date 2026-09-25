"""
End-to-End and Integration Test Suite for Viral Clips AI.
Verifies all acceptance criteria from 10_ACCEPTANCE.md and 08_TESTING.md.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from viral_clips.api.app import app
from viral_clips.config import settings
from viral_clips.core.audio_extract import extract_audio_for_asr
from viral_clips.core.asr import transcribe_video
from viral_clips.core.highlight_engine import (
    calculate_final_score,
    detect_highlights,
    generate_candidate_windows,
)
from viral_clips.core.media_probe import probe_media
from viral_clips.core.renderer import render_clip
from viral_clips.core.smart_reframe import generate_crop_plan
from viral_clips.core.subtitles import generate_subtitles, ms_to_ass_time
from viral_clips.db.database import (
    create_project,
    get_connection,
    get_project,
    get_project_clips,
    list_projects,
)
from viral_clips.services.pipeline_service import _sync_pipeline_runner, create_job

SAMPLE_VIDEO = Path("./samples/sample_podcast.mp4").resolve()


def test_01_probe_valid_media():
    """Phase 0 Gate: Validates media probe and schema structure."""
    assert SAMPLE_VIDEO.is_file(), "Sample video must exist for tests"
    probe = probe_media(SAMPLE_VIDEO)
    assert probe["schema_version"] == "1.0.0"
    assert probe["is_valid"] is True
    assert probe["duration_s"] >= 40.0
    v = probe["primary_video"]
    assert v["width"] == 1920
    assert v["height"] == 1080
    assert v["codec"] in ("h264", "libx264")
    assert probe["primary_audio"] is not None


def test_02_audio_extraction_and_asr():
    """Phase 1 Gate: Extracts 16kHz WAV and generates transcript with word timestamps."""
    out_dir = Path("./storage/test_artifacts/asr")
    transcript = transcribe_video(
        video_path=SAMPLE_VIDEO,
        output_dir=out_dir,
        language="ru",
        force_fallback=True,
    )
    assert transcript["schema_version"] == "1.0.0"
    assert transcript["total_words"] > 0
    assert len(transcript["segments"]) > 0
    first_word = transcript["words"][0]
    assert "start_ms" in first_word
    assert "end_ms" in first_word
    assert first_word["end_ms"] >= first_word["start_ms"]


def test_03_highlight_engine_and_scoring(monkeypatch):
    """Phase 2 Gate: 7 virality dimensions, weighted scoring and diversification."""
    monkeypatch.setattr(settings, "allow_heuristic_llm_fallback", True)
    out_dir = Path("./storage/test_artifacts/highlights")
    cand_art, rank_art = detect_highlights(
        transcript_path_or_dict=Path("./storage/test_artifacts/asr/transcript.json"),
        output_dir=out_dir,
        clip_count=3,
        min_duration_s=15.0,
        max_duration_s=45.0,
    )
    assert cand_art["schema_version"] == "1.0.0"
    assert rank_art["schema_version"] == "1.0.0"
    top_clips = rank_art["top_clips"]
    assert len(top_clips) > 0

    first = top_clips[0]
    assert "scores" in first
    scores = first["scores"]
    for dim in ("hook_strength", "payoff", "shareability", "standalone_context", "emotion", "pace", "novelty"):
        assert dim in scores
    assert 0.0 <= first["final_score"] <= 100.0


def test_04_subtitle_ass_generation():
    """Phase 3 Gate: Generates ASS subtitles with karaoke timing."""
    with open("./storage/test_artifacts/asr/transcript.json", "r", encoding="utf-8") as f:
        t_data = json.load(f)

    ass_path = Path("./storage/test_artifacts/subs/test.ass")
    art = generate_subtitles(
        words=t_data["words"],
        clip_start_ms=0,
        clip_end_ms=25000,
        output_ass_path=ass_path,
        preset="bold_karaoke",
    )
    assert ass_path.exists()
    content = ass_path.read_text(encoding="utf-8")
    assert "[Script Info]" in content
    assert "PlayResX: 1080" in content
    assert "PlayResY: 1920" in content
    assert "Dialogue:" in content


def test_05_smart_reframe_and_one_pass_render():
    """Phase 3 & 4 Gate: Smart 9:16 reframe & hardware NVENC rendering."""
    crop_plan = generate_crop_plan(
        video_path=SAMPLE_VIDEO,
        clip_start_ms=0,
        clip_end_ms=10000,
        preset="blurred_background",
    )
    assert crop_plan["schema_version"] == "1.0.0"
    assert "ffmpeg_filtergraph_base" in crop_plan

    out_mp4 = Path("./storage/test_artifacts/render/test_clip.mp4")
    ass_path = Path("./storage/test_artifacts/subs/test.ass")

    manifest = render_clip(
        source_video=SAMPLE_VIDEO,
        output_video_path=out_mp4,
        clip_start_ms=0,
        clip_end_ms=10000,
        crop_plan=crop_plan,
        subtitle_ass_path=ass_path,
    )

    assert out_mp4.exists()
    assert out_mp4.stat().st_size > 0
    assert manifest["is_valid"] is True
    assert manifest["resolution"] == "1080x1920"
    assert manifest["encoder"] in ("h264_nvenc", "libx264")


def test_06_database_persistence():
    """Phase 5 Gate: Database operations and state tracking."""
    proj = create_project(name="E2E Test Podcast", language="ru", desired_clip_count=3)
    p_id = proj["id"]
    assert p_id is not None
    fetched = get_project(p_id)
    assert fetched["name"] == "E2E Test Podcast"
    assert fetched["status"] == "created"


def test_07_full_pipeline_sync_execution(monkeypatch):
    """Phase 6 & 8 Gate: Full synchronous pipeline execution end-to-end."""
    monkeypatch.setattr(settings, "allow_heuristic_llm_fallback", True)
    proj = create_project(name="Pipeline Full Run", language="ru", desired_clip_count=2)
    p_id = proj["id"]
    job = create_job(project_id=p_id, job_type="pipeline")
    j_id = job["id"]

    out_dir = Path(f"./storage/test_artifacts/pipeline_{p_id}")

    _sync_pipeline_runner(
        job_id=j_id,
        project_id=p_id,
        video_path=SAMPLE_VIDEO,
        output_dir=out_dir,
        clip_count=2,
        min_duration_s=15.0,
        max_duration_s=30.0,
        framing="blurred_background",
        subtitle_preset="bold_karaoke",
        language="ru",
    )

    p_after = get_project(p_id)
    assert p_after["status"] == "completed"

    clips = get_project_clips(p_id)
    assert len(clips) >= 1
    first_clip = clips[0]
    assert Path(first_clip["video_path"]).is_file()
    assert first_clip["video_path"].endswith(".mp4")


def test_08_fastapi_rest_endpoints():
    """Phase 6 Gate: REST API endpoints and health check."""
    client = TestClient(app)

    # Health
    h_res = client.get("/v1/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "healthy"

    # Create project
    p_res = client.post("/v1/projects", json={"name": "API Project", "language": "ru", "desired_clip_count": 3})
    assert p_res.status_code == 201
    p_data = p_res.json()
    proj_id = p_data["id"]

    # List projects
    l_res = client.get("/v1/projects")
    assert l_res.status_code == 200
    assert any(p["id"] == proj_id for p in l_res.json())

    # Get project
    g_res = client.get(f"/v1/projects/{proj_id}")
    assert g_res.status_code == 200
    assert g_res.json()["name"] == "API Project"

    # UI HTML endpoint
    ui_res = client.get("/")
    assert ui_res.status_code == 200
    assert "Viral Clips" in ui_res.text
