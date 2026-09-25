"""
Integration tests for Phase 8 (Storage), Phase 9 (Security & Observability), and Phase 10 (Beta Evaluation).
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from viral_clips.api.app import app
from viral_clips.core.storage import (
    LocalStorageAdapter, CloudflareR2Adapter, GoogleDriveArchiveAdapter, StorageLifecycleManager
)
from viral_clips.core.security import (
    CostGuard, AuditLogger, MetricsCollector, BackupManager, QuotaViolationError
)
from viral_clips.core.evaluation import (
    ClipQualityEvaluator, GoldenBenchmarkRunner
)


def test_storage_adapters(tmp_path):
    """Test Phase 8: Storage Adapters for Local, R2, and Drive."""
    # 1. Local Storage Adapter
    local_store = LocalStorageAdapter(root_dir=str(tmp_path / "local_store"))
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("viral clips test content")

    rec = local_store.store_file(str(sample_file), "proj_1/sample.txt")
    assert rec.provider == "local"
    assert local_store.exists("proj_1/sample.txt")
    assert rec.bytes > 0

    download_target = tmp_path / "downloaded.txt"
    local_store.retrieve_file("proj_1/sample.txt", str(download_target))
    assert download_target.read_text() == "viral clips test content"

    # 2. Cloudflare R2 Adapter
    r2_store = CloudflareR2Adapter()
    r2_rec = r2_store.store_file(str(sample_file), "proj_1/video.mp4")
    assert r2_rec.provider == "r2"
    assert r2_store.exists("proj_1/video.mp4")
    r2_dl = tmp_path / "r2_downloaded.mp4"
    r2_store.retrieve_file("proj_1/video.mp4", str(r2_dl))
    assert r2_dl.read_text() == "viral clips test content"

    # 3. Google Drive Archive Adapter
    drive_store = GoogleDriveArchiveAdapter()
    d_rec = drive_store.store_file(str(sample_file), "proj_1/final.mp4")
    assert d_rec.provider == "drive"
    assert "drive.google.com" in drive_store.get_download_url("proj_1/final.mp4")


def test_lifecycle_cleanup(tmp_path):
    """Test Phase 8: Lifecycle Manager temporary artifact pruning."""
    proj_dir = tmp_path / "proj_test"
    proj_dir.mkdir()
    (proj_dir / "audio.wav").write_text("temporary audio wav")
    (proj_dir / "sub.ass").write_text("temporary subtitle")
    (proj_dir / "final.mp4").write_text("final rendered video")

    mgr = StorageLifecycleManager(root_dir=str(tmp_path))
    res = mgr.prune_temporary_artifacts(proj_dir)

    assert res["cleaned_files"] == 2
    assert not (proj_dir / "audio.wav").exists()
    assert not (proj_dir / "sub.ass").exists()
    assert (proj_dir / "final.mp4").exists()  # Keep final clips


def test_cost_guard_quotas():
    """Test Phase 9: Hardware VRAM limits and quota enforcement."""
    guard = CostGuard(max_duration_minutes=60, max_clips_per_run=5, max_concurrent_gpu_jobs=1)

    # Valid duration
    guard.check_video_duration(1800.0)  # 30 min -> OK

    # Exceeded duration
    with pytest.raises(QuotaViolationError):
        guard.check_video_duration(3700.0)  # > 60 min -> Error

    # Exceeded clips
    with pytest.raises(QuotaViolationError):
        guard.check_clip_count(10)  # > 5 clips -> Error

    # GPU Worker concurrency (RTX 4060 single slot)
    assert guard.acquire_gpu_slot() is True
    assert guard.acquire_gpu_slot() is False  # Second concurrent job rejected!
    guard.release_gpu_slot()
    assert guard.acquire_gpu_slot() is True


def test_audit_and_metrics(tmp_path):
    """Test Phase 9: Audit logging and Prometheus metrics."""
    audit_file = tmp_path / "audit.log"
    logger = AuditLogger(log_path=str(audit_file))
    logger.log("test_action", project_id="p123", details={"status": "ok"})

    assert audit_file.exists()
    lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["action"] == "test_action"
    assert data["project_id"] == "p123"

    # Metrics
    metrics = MetricsCollector()
    metrics.record_job("completed")
    metrics.record_render(35.5)
    prom_text = metrics.generate_prometheus_metrics()

    assert "viral_clips_jobs_total{status=\"completed\"} 1" in prom_text
    assert "viral_clips_renders_total 1" in prom_text
    assert "35.5" in prom_text


def test_backup_manager(tmp_path):
    """Test Phase 9: Backup creation with checksum verification."""
    source_storage = tmp_path / "source_storage"
    source_storage.mkdir()
    (source_storage / "test.db").write_text("sqlite database mock")
    (source_storage / "manifest.json").write_text('{"project": "1"}')

    dest_backup = tmp_path / "backups"
    backup_path = BackupManager.create_backup(str(source_storage), str(dest_backup))

    assert os.path.exists(backup_path)
    checksum_file = Path(backup_path) / "checksums.json"
    assert checksum_file.exists()
    chk_data = json.loads(checksum_file.read_text(encoding="utf-8"))
    assert "test.db" in chk_data["files"]


def test_beta_evaluation_framework():
    """Test Phase 10: Clip Quality Evaluator and Golden Benchmark Suite."""
    eval_res = ClipQualityEvaluator.evaluate_clip(
        clip_id="c_1",
        duration_s=45.0,
        word_count=120,
        scores={"final_score": 88.0},
        face_detected_frames=290,
        total_frames=300,
        avg_sync_error_ms=30.0,
    )

    assert eval_res.is_publishable is True
    assert eval_res.face_visible_ratio > 0.90
    assert eval_res.speech_density_wpm == 160.0

    # Benchmark Suite
    candidates = [
        {"id": "c1", "duration": 30.0, "word_count": 80, "scores": {"final_score": 85.0}},
        {"id": "c2", "duration": 50.0, "word_count": 140, "scores": {"final_score": 78.0}},
    ]
    suite_res = GoldenBenchmarkRunner.run_benchmark_suite(candidates)
    assert suite_res["total_candidates_evaluated"] == 2
    assert suite_res["publishable_candidates"] == 2
    assert suite_res["publishable_ratio"] == 1.0


def test_fastapi_new_endpoints():
    """Test Phase 8 & 9 API endpoints."""
    client = TestClient(app)

    # 1. Metrics endpoint
    res_m = client.get("/v1/metrics")
    assert res_m.status_code == 200
    assert "viral_clips_jobs_total" in res_m.text

    # 2. Storage cleanup endpoint
    res_c = client.post("/v1/storage/cleanup")
    assert res_c.status_code == 200
    assert res_c.json()["status"] == "success"
