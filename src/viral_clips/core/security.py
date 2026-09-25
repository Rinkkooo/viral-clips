"""
Phase 9: Security, Observability, Cost Guard / Quotas, Audit Logging, and Disaster Recovery Backups.
Conforms to 07_SECURITY_PERFORMANCE.md.
"""

from __future__ import annotations
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class QuotaViolationError(Exception):
    pass


class CostGuard:
    """Enforces hardware limits, VRAM bounds, and budget quotas."""

    def __init__(
        self,
        max_duration_minutes: int = 180,
        max_clips_per_run: int = 10,
        max_daily_clips: int = 50,
        max_concurrent_gpu_jobs: int = 1,
        max_file_size_bytes: int = 10 * 1024 * 1024 * 1024,
    ):
        self.max_duration_minutes = max_duration_minutes
        self.max_clips_per_run = max_clips_per_run
        self.max_daily_clips = max_daily_clips
        self.max_concurrent_gpu_jobs = max_concurrent_gpu_jobs
        self.max_file_size_bytes = max_file_size_bytes
        self._active_gpu_jobs = 0
        self._today_clips_rendered = 0

    def check_video_duration(self, duration_seconds: float):
        if duration_seconds > (self.max_duration_minutes * 60):
            raise QuotaViolationError(
                f"Video duration ({duration_seconds:.1f}s) exceeds maximum allowed quota of {self.max_duration_minutes} minutes."
            )

    def check_clip_count(self, requested_clips: int):
        if requested_clips > self.max_clips_per_run:
            raise QuotaViolationError(
                f"Requested clip count ({requested_clips}) exceeds maximum run limit ({self.max_clips_per_run})."
            )
        if (self._today_clips_rendered + requested_clips) > self.max_daily_clips:
            raise QuotaViolationError(
                f"Daily quota limit reached: requested {requested_clips} clips would exceed daily allowance of {self.max_daily_clips} clips."
            )

    def record_run(self, requested_clips: int):
        self.check_clip_count(requested_clips)
        self._today_clips_rendered += requested_clips

    def acquire_gpu_slot(self) -> bool:
        """Acquires single-worker execution lock on RTX 4060 8GB."""
        if self._active_gpu_jobs >= self.max_concurrent_gpu_jobs:
            return False
        self._active_gpu_jobs += 1
        return True

    def release_gpu_slot(self):
        if self._active_gpu_jobs > 0:
            self._active_gpu_jobs -= 1


class AuditLogger:
    """
    Cryptographic tamper-evident audit logger.
    Maintains a SHA-256 hash chain across log records to detect unauthorized modifications.
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, log_path: str = "storage/audit.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._read_tail_hash()

    def _read_tail_hash(self) -> str:
        """Reads the hash of the last entry in the audit log or returns GENESIS_HASH."""
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return self.GENESIS_HASH
        last_line = ""
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last_line = line.strip()
            if last_line:
                parsed = json.loads(last_line)
                return parsed.get("hash", self.GENESIS_HASH)
        except Exception:
            pass
        return self.GENESIS_HASH

    def log(
        self,
        action: str,
        project_id: Optional[str] = None,
        user_id: str = "local_user",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        prev_hash = self._last_hash
        timestamp = datetime.now().isoformat()

        payload = {
            "timestamp": timestamp,
            "action": action,
            "project_id": project_id,
            "user_id": user_id,
            "details": details or {},
        }

        # Compute SHA-256 block hash = sha256(prev_hash + canon_json(payload))
        canon_payload = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        hasher = hashlib.sha256()
        hasher.update((prev_hash + canon_payload).encode("utf-8"))
        entry_hash = hasher.hexdigest()

        record = {
            "prev_hash": prev_hash,
            "timestamp": timestamp,
            "action": action,
            "project_id": project_id,
            "user_id": user_id,
            "details": details or {},
            "payload": payload,
            "hash": entry_hash,
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        self._last_hash = entry_hash
        return record

    # Alias for compatibility
    log_event = log

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """
        Verifies the cryptographic continuity of the audit log chain.
        Returns (True, None) if completely valid, or (False, error_reason) if tampered with.
        """
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return True, None

        expected_prev_hash = self.GENESIS_HASH
        line_idx = 0

        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                line_idx += 1
                try:
                    record = json.loads(line)
                except Exception as e:
                    return False, f"Line {line_idx}: Invalid JSON: {e}"

                if "prev_hash" not in record or "payload" not in record or "hash" not in record:
                    # Legacy record before hash chain migration
                    continue

                if record["prev_hash"] != expected_prev_hash:
                    return False, f"Line {line_idx}: Broken chain link. Expected prev_hash {expected_prev_hash}, got {record['prev_hash']}"

                canon_payload = json.dumps(record["payload"], sort_keys=True, ensure_ascii=False)
                hasher = hashlib.sha256()
                hasher.update((record["prev_hash"] + canon_payload).encode("utf-8"))
                recomputed_hash = hasher.hexdigest()

                if recomputed_hash != record["hash"]:
                    return False, f"Line {line_idx}: Corrupted entry hash. Expected {recomputed_hash}, got {record['hash']}"

                expected_prev_hash = record["hash"]

        return True, None



class MetricsCollector:
    """Prometheus-compatible in-memory metrics collector."""

    def __init__(self):
        self.counters = {
            "viral_clips_jobs_total": {"queued": 0, "completed": 0, "failed": 0},
            "viral_clips_renders_total": 0,
        }
        self.gauges = {
            "viral_clips_active_gpu_workers": 0,
            "viral_clips_total_rendered_seconds": 0.0,
        }

    def record_job(self, status: str):
        if status in self.counters["viral_clips_jobs_total"]:
            self.counters["viral_clips_jobs_total"][status] += 1

    def record_render(self, duration_s: float):
        self.counters["viral_clips_renders_total"] += 1
        self.gauges["viral_clips_total_rendered_seconds"] += duration_s

    def set_active_workers(self, count: int):
        self.gauges["viral_clips_active_gpu_workers"] = count

    def generate_prometheus_metrics(self) -> str:
        lines = [
            "# HELP viral_clips_jobs_total Total video processing jobs by status",
            "# TYPE viral_clips_jobs_total counter",
        ]
        for st, count in self.counters["viral_clips_jobs_total"].items():
            lines.append(f'viral_clips_jobs_total{{status="{st}"}} {count}')

        lines.extend([
            "# HELP viral_clips_renders_total Total completed vertical clips",
            "# TYPE viral_clips_renders_total counter",
            f"viral_clips_renders_total {self.counters['viral_clips_renders_total']}",
            "# HELP viral_clips_active_gpu_workers Current active GPU render tasks",
            "# TYPE viral_clips_active_gpu_workers gauge",
            f"viral_clips_active_gpu_workers {self.gauges['viral_clips_active_gpu_workers']}",
            "# HELP viral_clips_total_rendered_seconds Total accumulated duration of rendered clips",
            "# TYPE viral_clips_total_rendered_seconds counter",
            f"viral_clips_total_rendered_seconds {self.gauges['viral_clips_total_rendered_seconds']:.2f}",
        ])
        return "\n".join(lines) + "\n"


class BackupManager:
    """Disaster recovery and automated backup manager."""

    @classmethod
    def create_backup(cls, source_storage_dir: str = "storage", dest_backup_dir: str = "backups") -> str:
        os.makedirs(dest_backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder_name = f"viral_clips_backup_{timestamp}"
        target_path = os.path.join(dest_backup_dir, backup_folder_name)
        os.makedirs(target_path, exist_ok=True)

        copied_count = 0
        checksums = {}

        src_dir = Path(source_storage_dir)
        if src_dir.exists():
            # Backup DB files and JSON manifests
            for item in src_dir.rglob("*"):
                if item.is_file() and (item.suffix in [".db", ".json", ".log"] or item.name == "schema.sql"):
                    rel_path = item.relative_to(src_dir)
                    dest_file = Path(target_path) / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_file)

                    # Compute checksum
                    sha = hashlib.sha256(open(item, "rb").read()).hexdigest()
                    checksums[str(rel_path)] = sha
                    copied_count += 1

        # Write checksum manifest
        with open(os.path.join(target_path, "checksums.json"), "w", encoding="utf-8") as f:
            json.dump({"backup_date": datetime.now().isoformat(), "files": checksums}, f, indent=2)

        return target_path
