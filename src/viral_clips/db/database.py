"""
Database layer for Viral Clips AI.
Thread-safe SQLite implementation of 04_DATABASE.md and schema.sql.
Provides complete persistence for projects, artifacts, candidates, clips, renders, and jobs.
"""

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from loguru import logger

from viral_clips.config import settings

# Thread-local storage for sqlite connections
_local = threading.local()


def get_db_path() -> Path:
    """Returns resolved database file path."""
    if settings.database_url.startswith("sqlite:///"):
        rel_or_abs = settings.database_url.replace("sqlite:///", "")
        p = Path(rel_or_abs).resolve()
    else:
        p = Path("./storage/viral_clips.db").resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_connection() -> sqlite3.Connection:
    """Gets thread-isolated SQLite connection with foreign keys and WAL mode."""
    if not hasattr(_local, "conn") or _local.conn is None:
        db_path = get_db_path()
        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        _local.conn = conn
    return _local.conn


def init_db():
    """Initializes tables and indexes based on schema.sql."""
    conn = get_connection()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            language TEXT,
            desired_clip_count INTEGER NOT NULL DEFAULT 5,
            settings_json TEXT NOT NULL DEFAULT '{}',
            pipeline_version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id, created_at DESC);

        CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            kind TEXT NOT NULL,
            provider TEXT NOT NULL,
            storage_key TEXT NOT NULL,
            sha256 TEXT,
            bytes INTEGER,
            mime_type TEXT,
            duration_ms INTEGER,
            width INTEGER,
            height INTEGER,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            UNIQUE(provider, storage_key)
        );

        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            start_ms INTEGER NOT NULL,
            end_ms INTEGER NOT NULL,
            title TEXT,
            scores TEXT NOT NULL,
            final_score REAL NOT NULL,
            reason TEXT,
            rank INTEGER,
            scorer_version TEXT NOT NULL,
            accepted INTEGER DEFAULT 0,
            CHECK (end_ms > start_ms)
        );

        CREATE TABLE IF NOT EXISTS clips (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            candidate_id TEXT REFERENCES candidates(id),
            start_ms INTEGER NOT NULL,
            end_ms INTEGER NOT NULL,
            status TEXT NOT NULL,
            current_render_id TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS renders (
            id TEXT PRIMARY KEY,
            clip_id TEXT NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
            render_version TEXT NOT NULL,
            crop_plan_artifact_id TEXT,
            subtitle_artifact_id TEXT,
            output_artifact_id TEXT,
            preset_json TEXT NOT NULL DEFAULT '{}',
            encoder TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            error_code TEXT
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            stage TEXT,
            progress INTEGER NOT NULL DEFAULT 0,
            attempt INTEGER NOT NULL DEFAULT 0,
            idempotency_key TEXT NOT NULL,
            error_code TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            UNIQUE(project_id, idempotency_key)
        );

        CREATE TABLE IF NOT EXISTS clip_reviews (
            clip_id TEXT PRIMARY KEY REFERENCES clips(id) ON DELETE CASCADE,
            publishable BOOLEAN NOT NULL DEFAULT 0,
            highlight_quality INTEGER NOT NULL DEFAULT 3,
            framing_quality INTEGER NOT NULL DEFAULT 3,
            subtitle_quality INTEGER NOT NULL DEFAULT 3,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clip_feedback (
            clip_id TEXT PRIMARY KEY REFERENCES clips(id) ON DELETE CASCADE,
            publishable BOOLEAN NOT NULL DEFAULT 0,
            issues_json TEXT NOT NULL DEFAULT '[]',
            ratings_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS product_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            entity_id TEXT,
            payload_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        );
        """)
    logger.info(f"Database initialized successfully at {get_db_path()}")


# ==========================================
# CRUD Operations
# ==========================================

def create_project(
    name: str,
    owner_id: str = "default_user",
    language: Optional[str] = "ru",
    desired_clip_count: int = 5,
    settings_dict: Optional[Dict[str, Any]] = None,
    pipeline_version: str = "1.0.0",
) -> Dict[str, Any]:
    project_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO projects (id, owner_id, name, status, language, desired_clip_count, settings_json, pipeline_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                owner_id,
                name,
                "created",
                language,
                desired_clip_count,
                json.dumps(settings_dict or {}),
                pipeline_version,
                now,
                now,
            ),
        )
    return get_project(project_id)


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM projects WHERE id = ? AND deleted_at IS NULL", (project_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["settings"] = json.loads(d["settings_json"])
    return d


def list_projects(owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    if owner_id:
        rows = conn.execute(
            "SELECT * FROM projects WHERE owner_id = ? AND deleted_at IS NULL ORDER BY created_at DESC",
            (owner_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM projects WHERE deleted_at IS NULL ORDER BY created_at DESC"
        ).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        d["settings"] = json.loads(d["settings_json"])
        results.append(d)
    return results


def update_project_status(project_id: str, status: str):
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute(
            "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, project_id),
        )


def delete_project(project_id: str) -> bool:
    """Soft-deletes project in DB and cleans up persistent project files on disk."""
    import shutil
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        res = conn.execute(
            "UPDATE projects SET deleted_at = ? WHERE id = ?",
            (now, project_id),
        )
        success = res.rowcount > 0

    if success:
        # Clean up files on disk
        for p in [
            Path("./storage/uploads") / project_id,
            Path("./storage/output") / f"proj_{project_id}",
            Path("./temp") / project_id,
        ]:
            if p.exists():
                try:
                    shutil.rmtree(p, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Could not remove project directory {p}: {e}")

    return success


# Artifacts CRUD
def register_artifact(
    project_id: str,
    kind: str,
    storage_key: str,
    provider: str = "local",
    local_path: Optional[str] = None,
    mime_type: Optional[str] = None,
    duration_ms: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> str:
    """Registers an immutable file record into the artifacts table."""
    import hashlib
    artifact_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    sha256 = None
    size_bytes = None

    if local_path and Path(local_path).exists():
        p = Path(local_path)
        size_bytes = p.stat().st_size
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        sha256 = h.hexdigest()

    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO artifacts
            (id, project_id, kind, provider, storage_key, sha256, bytes, mime_type, duration_ms, width, height, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (artifact_id, project_id, kind, provider, storage_key, sha256, size_bytes, mime_type, duration_ms, width, height, now),
        )
    return artifact_id


def get_artifact(artifact_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    return dict(row) if row else None


def create_job(
    project_id: str,
    job_type: str = "pipeline",
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates or retrieves a job with idempotency deduplication.
    Sets job["is_new"] = True if newly created, or False if existing record returned.
    """
    job_id = str(uuid.uuid4())
    key = idempotency_key or f"job_{job_id}"
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()

    # Check idempotency
    existing = conn.execute(
        "SELECT * FROM jobs WHERE project_id = ? AND idempotency_key = ?",
        (project_id, key),
    ).fetchone()
    if existing:
        d = dict(existing)
        d["is_new"] = False
        return d

    with conn:
        conn.execute(
            """
            INSERT INTO jobs (id, project_id, type, status, stage, progress, attempt, idempotency_key, created_at)
            VALUES (?, ?, ?, 'queued', 'init', 0, 1, ?, ?)
            """,
            (job_id, project_id, job_type, key, now),
        )
    job = get_job(job_id)
    if job:
        job["is_new"] = True
    return job



def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def update_job_progress(
    job_id: str,
    stage: str,
    progress: int,
    status: str = "running",
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
):
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        started_update = ", started_at = ?" if status == "running" else ""
        finished_update = ", finished_at = ?" if status in ("completed", "failed", "canceled") else ""
        sql = f"""
            UPDATE jobs
            SET status = ?, stage = ?, progress = ?, error_code = ?, error_message = ?
            {started_update} {finished_update}
            WHERE id = ?
        """
        params = [status, stage, progress, error_code, error_message]
        if started_update:
            params.append(now)
        if finished_update:
            params.append(now)
        params.append(job_id)
        conn.execute(sql, tuple(params))


# Candidates & Clips CRUD
def save_candidates(project_id: str, candidates: List[Dict[str, Any]]):
    conn = get_connection()
    with conn:
        for c in candidates:
            cand_id = c.get("id") or str(uuid.uuid4())
            conn.execute(
                """
                INSERT OR REPLACE INTO candidates
                (id, project_id, start_ms, end_ms, title, scores, final_score, reason, rank, scorer_version, accepted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cand_id,
                    project_id,
                    c["start_ms"],
                    c["end_ms"],
                    c.get("title", ""),
                    json.dumps(c.get("scores", {})),
                    c.get("final_score", 0.0),
                    c.get("reason", ""),
                    c.get("rank", 1),
                    c.get("scorer_version", "2.1.0"),
                    1 if c.get("accepted") else 0,
                ),
            )


def get_candidates(project_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM candidates WHERE project_id = ? ORDER BY rank ASC, final_score DESC",
        (project_id,),
    ).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        d["scores"] = json.loads(d["scores"])
        d["accepted"] = bool(d["accepted"])
        results.append(d)
    return results


def save_clip_and_render(
    project_id: str,
    candidate_id: Optional[str],
    start_ms: int,
    end_ms: int,
    render_manifest: Dict[str, Any],
    preset: str = "bold_karaoke",
    crop_plan_path: Optional[Union[str, Path]] = None,
    subtitle_ass_path: Optional[Union[str, Path]] = None,
) -> Tuple[str, str]:
    """Saves clip and creates corresponding artifacts and render records."""
    clip_id = str(uuid.uuid4())
    render_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Register output video artifact
    out_file = render_manifest.get("output_file")
    out_artifact_id = register_artifact(
        project_id=project_id,
        kind="video_clip",
        storage_key=str(out_file) if out_file else f"projects/{project_id}/clips/clip.mp4",
        provider="local",
        local_path=out_file,
        mime_type="video/mp4",
        duration_ms=end_ms - start_ms,
        width=1080,
        height=1920,
    )

    crop_artifact_id = None
    if crop_plan_path and Path(crop_plan_path).exists():
        crop_artifact_id = register_artifact(
            project_id=project_id,
            kind="crop_plan",
            storage_key=f"projects/{project_id}/crops/{Path(crop_plan_path).name}",
            provider="local",
            local_path=str(crop_plan_path),
            mime_type="application/json",
        )

    sub_artifact_id = None
    if subtitle_ass_path and Path(subtitle_ass_path).exists():
        sub_artifact_id = register_artifact(
            project_id=project_id,
            kind="subtitle_ass",
            storage_key=f"projects/{project_id}/subtitles/{Path(subtitle_ass_path).name}",
            provider="local",
            local_path=str(subtitle_ass_path),
            mime_type="text/x-ssa",
        )

    conn = get_connection()
    with conn:
        # Create clip
        conn.execute(
            """
            INSERT INTO clips (id, project_id, candidate_id, start_ms, end_ms, status, current_render_id, created_at)
            VALUES (?, ?, ?, ?, ?, 'ready', ?, ?)
            """,
            (clip_id, project_id, candidate_id, start_ms, end_ms, render_id, now),
        )

        # Create render record referencing real artifact ids
        conn.execute(
            """
            INSERT INTO renders (id, clip_id, render_version, crop_plan_artifact_id, subtitle_artifact_id, output_artifact_id, preset_json, encoder, started_at, completed_at)
            VALUES (?, ?, '2.0.0', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                render_id,
                clip_id,
                crop_artifact_id,
                sub_artifact_id,
                out_artifact_id,
                json.dumps({"preset": preset}),
                render_manifest.get("encoder", "h264_nvenc"),
                now,
                now,
            ),
        )

    return clip_id, render_id


def create_clip_render(
    clip_id: str,
    project_id: str,
    render_manifest: Dict[str, Any],
    preset: str = "bold_karaoke",
    crop_plan_path: Optional[Union[str, Path]] = None,
    subtitle_ass_path: Optional[Union[str, Path]] = None,
    start_ms: Optional[int] = None,
    end_ms: Optional[int] = None,
) -> str:
    """Creates a new render for an existing clip (rerender workflow) and updates current_render_id."""
    render_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    out_file = render_manifest.get("output_file", "")
    out_artifact_id = register_artifact(
        project_id=project_id,
        kind="clip_mp4",
        storage_key=str(out_file) if out_file else f"projects/{project_id}/clips/clip.mp4",
        provider="local",
        local_path=out_file,
        mime_type="video/mp4",
        width=1080,
        height=1920,
    )

    crop_artifact_id = None
    if crop_plan_path and Path(crop_plan_path).exists():
        crop_artifact_id = register_artifact(
            project_id=project_id,
            kind="crop_plan",
            storage_key=f"projects/{project_id}/crops/{Path(crop_plan_path).name}",
            provider="local",
            local_path=str(crop_plan_path),
            mime_type="application/json",
        )

    sub_artifact_id = None
    if subtitle_ass_path and Path(subtitle_ass_path).exists():
        sub_artifact_id = register_artifact(
            project_id=project_id,
            kind="subtitle_ass",
            storage_key=f"projects/{project_id}/subtitles/{Path(subtitle_ass_path).name}",
            provider="local",
            local_path=str(subtitle_ass_path),
            mime_type="text/x-ssa",
        )

    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO renders (id, clip_id, render_version, crop_plan_artifact_id, subtitle_artifact_id, output_artifact_id, preset_json, encoder, started_at, completed_at)
            VALUES (?, ?, '2.0.0', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                render_id,
                clip_id,
                crop_artifact_id,
                sub_artifact_id,
                out_artifact_id,
                json.dumps({"preset": preset}),
                render_manifest.get("encoder", "h264_nvenc"),
                now,
                now,
            ),
        )

        update_sql = "UPDATE clips SET current_render_id = ?"
        params = [render_id]
        if start_ms is not None:
            update_sql += ", start_ms = ?"
            params.append(start_ms)
        if end_ms is not None:
            update_sql += ", end_ms = ?"
            params.append(end_ms)
        update_sql += " WHERE id = ?"
        params.append(clip_id)

        conn.execute(update_sql, tuple(params))

    return render_id


def get_clip(clip_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    return dict(row) if row else None


def get_project_clips(project_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT c.*,
               COALESCE(a.storage_key, r.output_artifact_id) as video_path,
               r.encoder, r.preset_json, r.output_artifact_id,
               cand.title, cand.final_score, cand.scores as candidate_scores, cand.reason
        FROM clips c
        LEFT JOIN renders r ON c.current_render_id = r.id
        LEFT JOIN artifacts a ON r.output_artifact_id = a.id
        LEFT JOIN candidates cand ON c.candidate_id = cand.id
        WHERE c.project_id = ?
        ORDER BY c.created_at ASC
        """,
        (project_id,),
    ).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        if d.get("candidate_scores"):
            d["scores"] = json.loads(d["candidate_scores"])
        if d.get("preset_json"):
            d["preset"] = json.loads(d["preset_json"])
        results.append(d)
    return results


def save_clip_review(
    clip_id: str,
    publishable: bool = False,
    highlight_quality: int = 3,
    framing_quality: int = 3,
    subtitle_quality: int = 3,
    notes: str = "",
) -> Dict[str, Any]:
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute(
            """
            INSERT INTO clip_reviews (clip_id, publishable, highlight_quality, framing_quality, subtitle_quality, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(clip_id) DO UPDATE SET
                publishable=excluded.publishable,
                highlight_quality=excluded.highlight_quality,
                framing_quality=excluded.framing_quality,
                subtitle_quality=excluded.subtitle_quality,
                notes=excluded.notes,
                created_at=excluded.created_at
            """,
            (clip_id, int(publishable), highlight_quality, framing_quality, subtitle_quality, notes, now),
        )
    return {
        "clip_id": clip_id,
        "publishable": publishable,
        "highlight_quality": highlight_quality,
        "framing_quality": framing_quality,
        "subtitle_quality": subtitle_quality,
        "notes": notes,
        "created_at": now,
    }


def get_clip_review(clip_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM clip_reviews WHERE clip_id = ?", (clip_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["publishable"] = bool(d["publishable"])
    return d


def save_clip_feedback(
    clip_id: str,
    publishable: bool = False,
    issues: Optional[List[str]] = None,
    ratings: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Persists detailed human feedback for a clip (issues, 1-5 ratings, publishable flag)."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    issues_json = json.dumps(issues or [])
    ratings_json = json.dumps(ratings or {})
    with conn:
        conn.execute(
            """
            INSERT INTO clip_feedback (clip_id, publishable, issues_json, ratings_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(clip_id) DO UPDATE SET
                publishable=excluded.publishable,
                issues_json=excluded.issues_json,
                ratings_json=excluded.ratings_json,
                created_at=excluded.created_at
            """,
            (clip_id, int(publishable), issues_json, ratings_json, now),
        )
    return {
        "clip_id": clip_id,
        "publishable": publishable,
        "issues": issues or [],
        "ratings": ratings or {},
        "created_at": now,
    }


def get_clip_feedback(clip_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves human feedback for a clip."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM clip_feedback WHERE clip_id = ?", (clip_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    return {
        "clip_id": d["clip_id"],
        "publishable": bool(d["publishable"]),
        "issues": json.loads(d["issues_json"]) if d.get("issues_json") else [],
        "ratings": json.loads(d["ratings_json"]) if d.get("ratings_json") else {},
        "created_at": d["created_at"],
    }


def log_product_event(
    event_name: str,
    entity_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Logs internal product analytics event to SQLite."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    payload_json = json.dumps(payload or {})
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO product_events (event_name, entity_id, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (event_name, entity_id, payload_json, now),
        )
        event_id = cursor.lastrowid
    return {
        "id": event_id,
        "event_name": event_name,
        "entity_id": entity_id,
        "payload": payload or {},
        "created_at": now,
    }


def get_product_events(
    event_name: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Retrieves product analytics events from SQLite."""
    conn = get_connection()
    query = "SELECT * FROM product_events"
    conditions = []
    params: List[Any] = []
    if event_name:
        conditions.append("event_name = ?")
        params.append(event_name)
    if entity_id:
        conditions.append("entity_id = ?")
        params.append(entity_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, tuple(params)).fetchall()
    events = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload_json"]) if d.get("payload_json") else {}
        events.append(d)
    return events


def update_project_settings(project_id: str, settings_dict: Dict[str, Any]) -> bool:
    """Updates settings_json on a project."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        cur = conn.execute(
            "UPDATE projects SET settings_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(settings_dict), now, project_id),
        )
        return cur.rowcount > 0


# Initialize immediately on module import
init_db()

