"""
FastAPI Application and REST API.
Implements the exact OpenAPI specification from 05_API.md:
Projects, Uploads, Processing, SSE Job Streaming, Candidates, Clips, and Downloads.
Includes Problem Details error formatting and Web UI static serving.
"""

import asyncio
import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, File, Header, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger

from viral_clips.config import settings
from viral_clips.core.ffmpeg_utils import check_nvenc_support, find_binary
from viral_clips.db.database import (
    create_project,
    delete_project,
    get_candidates,
    get_clip,
    get_clip_feedback,
    get_connection,
    get_job,
    get_product_events,
    get_project,
    get_project_clips,
    list_projects,
    log_product_event,
    save_candidates,
    save_clip_feedback,
    update_job_progress,
    update_project_settings,
)
from viral_clips.exceptions import ViralClipsError
from viral_clips.services.pipeline_service import (
    start_pipeline_job,
    subscribe_job_events,
    unsubscribe_job_events,
)
from viral_clips.core.highlight_engine import detect_highlights
from viral_clips.core.storage import StorageLifecycleManager, LocalStorageAdapter, GoogleDriveArchiveAdapter
from viral_clips.core.security import CostGuard, AuditLogger, MetricsCollector, BackupManager, QuotaViolationError
from viral_clips.core.evaluation import GoldenBenchmarkRunner, ClipQualityEvaluator

app = FastAPI(
    title="Viral Clips AI API",
    version="1.0.0",
    description="Automated long-to-short video generation engine with AI highlights, smart reframe, and karaoke subtitles.",
)

storage_lifecycle = StorageLifecycleManager()
gdrive_adapter = GoogleDriveArchiveAdapter()
cost_guard = CostGuard(max_clips_per_run=settings.max_clips_per_run)
audit_logger = AuditLogger()
metrics_collector = MetricsCollector()

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# Hardened CORS middleware (explicit origins, no credential wildcards)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Exception handler for Problem Details (RFC 7807)
@app.exception_handler(ViralClipsError)
async def viral_clips_error_handler(request: Request, exc: ViralClipsError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "request_id": str(uuid.uuid4()),
        },
    )


# ==========================================
# Pydantic Request Models
# ==========================================

class CreateProjectRequest(BaseModel):
    name: str = Field(..., description="Project name")
    language: Optional[str] = Field("auto", description="Audio language code (e.g., 'auto', 'ru', 'en')")
    desired_clip_count: int = Field(5, ge=1, le=10)
    settings: Optional[Dict[str, Any]] = None


class FeedbackClipRequest(BaseModel):
    publishable: bool = False
    issues: List[str] = Field(default_factory=list)
    ratings: Dict[str, int] = Field(default_factory=dict)


class ProcessRequest(BaseModel):
    video_path: Optional[str] = Field(None, description="Path to video file already on disk")
    clip_count: int = Field(5, ge=1, le=10)
    duration: Optional[Dict[str, float]] = None
    min_duration_s: float = Field(20.0, ge=10.0, le=120.0)
    max_duration_s: float = Field(75.0, ge=15.0, le=180.0)
    framing: str = Field("active_speaker", description="active_speaker | blurred_background | center_crop | split_screen")
    subtitles: Optional[Dict[str, Any]] = None
    subtitle_preset: str = Field("bold_karaoke", description="bold_karaoke | minimalist | hormozi_pop")
    language: Optional[str] = Field("auto", description="auto | ru | en")
    content_type: Optional[str] = Field("auto", description="podcast | interview | talking_head | stream | gaming | lecture | webinar | reaction | other | auto")
    highlight_strategy: Optional[List[str]] = Field(default_factory=lambda: ["auto"])
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)

    def resolve_duration(self) -> Tuple[float, float]:
        min_d = self.min_duration_s
        max_d = self.max_duration_s
        if self.duration:
            if "min_seconds" in self.duration:
                min_d = float(self.duration["min_seconds"])
            if "max_seconds" in self.duration:
                max_d = float(self.duration["max_seconds"])
        return min_d, max_d

    def resolve_subtitle_preset(self) -> str:
        if self.subtitles and "preset" in self.subtitles:
            return str(self.subtitles["preset"])
        return self.subtitle_preset


class RerenderClipRequest(BaseModel):
    subtitle_preset: str = Field("bold_karaoke", description="bold_karaoke | minimalist | hormozi_pop")
    framing: str = Field("active_speaker", description="active_speaker | blurred_background | center_crop | split_screen")
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    font_size: Optional[int] = None
    font_name: Optional[str] = None


class ReviewClipRequest(BaseModel):
    publishable: bool = False
    highlight_quality: int = Field(3, ge=1, le=5)
    framing_quality: int = Field(3, ge=1, le=5)
    subtitle_quality: int = Field(3, ge=1, le=5)
    notes: str = ""


class AcceptCandidateRequest(BaseModel):
    accepted: bool = True


class RegenerateHighlightsRequest(BaseModel):
    clip_count: Optional[int] = Field(None, ge=1, le=10)
    min_duration_s: Optional[float] = Field(None, ge=10.0, le=120.0)
    max_duration_s: Optional[float] = Field(None, ge=15.0, le=180.0)
    highlight_strategy: Optional[List[str]] = None
    content_type: Optional[str] = None


# ==========================================
# Health & Environment Endpoints
# ==========================================

@app.get("/v1/health")
def health_check():
    ffmpeg = find_binary("ffmpeg")
    ffprobe = find_binary("ffprobe")
    nvenc = check_nvenc_support() if ffmpeg else False
    return {
        "status": "healthy",
        "ffmpeg": bool(ffmpeg),
        "ffprobe": bool(ffprobe),
        "nvenc_hardware_accel": nvenc,
        "gpu_concurrency": settings.gpu_worker_concurrency,
        "asr_provider": settings.asr_provider,
    }


@app.get("/v1/system/capabilities")
def api_system_capabilities():
    """Returns real-time hardware, ASR, LLM, and feature capabilities per Section 21."""
    from viral_clips.core.llm_providers import get_llm_provider
    ffmpeg = find_binary("ffmpeg")
    nvenc = check_nvenc_support() if ffmpeg else False

    llm_available = False
    resolved_llm_model = getattr(settings, "ollama_model", "qwen2.5:1.5b")
    try:
        provider = get_llm_provider()
        llm_available = provider.check_health()
        resolved_llm_model = getattr(provider, "model_name", resolved_llm_model)
    except Exception:
        llm_available = False

    return {
        "asr": {
            "provider": settings.asr_provider,
            "model": settings.whisper_model,
            "device": settings.whisper_device,
            "available": True,
        },
        "llm": {
            "provider": settings.llm_provider,
            "model": resolved_llm_model,
            "available": llm_available,
        },
        "render": {
            "nvenc": nvenc,
        },
        "features": {
            "dynamic_reframe": True,
            "translation": False,
            "split_speaker": False,
        },
    }


@app.get("/v1/system/events")
def api_list_events(limit: int = Query(50, ge=1, le=500)):
    """Returns product analytics events logged locally in SQLite."""
    return get_product_events(limit=limit)


# ==========================================
# Projects API (05_API.md)
# ==========================================

@app.post("/v1/projects", status_code=status.HTTP_201_CREATED)
def api_create_project(body: CreateProjectRequest):
    project = create_project(
        name=body.name,
        language=body.language,
        desired_clip_count=body.desired_clip_count,
        settings_dict=body.settings,
    )
    log_product_event("project_created", entity_id=project["id"], payload={"name": project["name"]})
    return project


@app.get("/v1/projects")
def api_list_projects():
    return list_projects()


@app.get("/v1/projects/{project_id}")
def api_get_project(project_id: str):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    clips = get_project_clips(project_id)
    project["clips"] = clips
    return project


@app.delete("/v1/projects/{project_id}")
def api_delete_project(project_id: str):
    success = delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted", "id": project_id}


# ==========================================
# Upload API (Secured Against Path Traversal & Quota Abuse)
# ==========================================

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB upload limit


@app.post("/v1/projects/{project_id}/upload")
async def api_upload_video(project_id: str, file: UploadFile = File(...)):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Sanitize filename & prevent path traversal
    raw_name = Path(file.filename or "video.mp4").name
    clean_base = re.sub(r"[^a-zA-Z0-9_.-]", "_", raw_name)
    ext = Path(clean_base).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}",
        )

    safe_filename = f"{uuid.uuid4().hex[:8]}_{clean_base}"
    upload_dir = (Path("./storage/uploads") / project_id).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    dst_path = (upload_dir / safe_filename).resolve()

    # Verify dst_path remains strictly inside upload_dir
    try:
        dst_path.relative_to(upload_dir)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal attempt detected.")

    # 2. Stream chunks and strictly enforce byte limits
    bytes_written = 0
    with open(dst_path, "wb") as buffer:
        while True:
            chunk = await file.read(65536)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > MAX_UPLOAD_BYTES:
                buffer.close()
                dst_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=f"Payload Too Large: File exceeds maximum allowed size ({MAX_UPLOAD_BYTES // (1024*1024)} MB).",
                )
            buffer.write(chunk)

    # Register raw video artifact in DB
    from viral_clips.db.database import register_artifact
    register_artifact(
        project_id=project_id,
        kind="raw_video",
        storage_key=f"projects/{project_id}/uploads/{safe_filename}",
        local_path=str(dst_path),
        mime_type=file.content_type or "video/mp4",
    )

    audit_logger.log("upload_video", project_id=project_id, details={"filename": safe_filename, "size": bytes_written})
    log_product_event("video_uploaded", entity_id=project_id, payload={"filename": safe_filename, "size_bytes": bytes_written})

    return {
        "status": "uploaded",
        "file_name": safe_filename,
        "file_path": str(dst_path),
        "size_bytes": bytes_written,
    }


# ==========================================
# Processing & Jobs API
# ==========================================

@app.post("/v1/projects/{project_id}/process", status_code=status.HTTP_202_ACCEPTED)
def api_process_project(
    project_id: str,
    body: ProcessRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Enforce daily quota through cost guard
    try:
        cost_guard.record_run(requested_clips=body.clip_count)
    except QuotaViolationError as qe:
        raise HTTPException(status_code=429, detail=f"Quota exceeded: {qe.message}")

    # Locate video file with strict confinement checks
    video_path = body.video_path
    if video_path:
        resolved_vpath = Path(video_path).resolve()
        storage_root = Path("./storage").resolve()
        samples_root = Path("./samples").resolve()
        is_confined = False
        try:
            resolved_vpath.relative_to(storage_root)
            is_confined = True
        except ValueError:
            pass
        try:
            resolved_vpath.relative_to(samples_root)
            is_confined = True
        except ValueError:
            pass

        if not is_confined:
            raise HTTPException(
                status_code=400,
                detail="Security violation: video_path must reside within authorized storage or samples directory.",
            )
        video_path = str(resolved_vpath)
    else:
        # Check uploaded files in storage
        upload_dir = Path("./storage/uploads") / project_id
        if upload_dir.exists():
            files = list(upload_dir.glob("*.*"))
            if files:
                video_path = str(files[0].resolve())

    if not video_path or not Path(video_path).is_file():
        raise HTTPException(status_code=400, detail="Video file not found. Upload a video first or provide video_path.")

    req_lang = body.language if body.language is not None else project.get("language")
    if req_lang in ("auto", "Auto detect", ""):
        req_lang = None

    min_d, max_d = body.resolve_duration()
    sub_preset = body.resolve_subtitle_preset()
    strat = body.highlight_strategy or ["auto"]
    c_type = body.content_type or "auto"
    opts = body.options or {}

    settings_dict = {
        "clip_count": body.clip_count,
        "duration_min": min_d,
        "duration_max": max_d,
        "language": body.language,
        "content_type": c_type,
        "highlight_strategy": strat,
        "framing": body.framing,
        "subtitle_preset": sub_preset,
        "options": opts,
    }
    update_project_settings(project_id, settings_dict)
    log_product_event("generation_started", entity_id=project_id, payload=settings_dict)

    result = start_pipeline_job(
        project_id=project_id,
        video_path=video_path,
        clip_count=body.clip_count,
        min_duration_s=min_d,
        max_duration_s=max_d,
        framing=body.framing,
        subtitle_preset=sub_preset,
        language=req_lang,
        idempotency_key=idempotency_key,
        highlight_strategy=strat,
        content_type=c_type,
        options=opts,
    )
    return result


@app.get("/v1/jobs/{job_id}")
def api_get_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/v1/jobs/{job_id}/events")
async def api_job_events(job_id: str):
    """Server-Sent Events (SSE) streaming real-time progress to frontend."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    q = subscribe_job_events(job_id)

    async def event_generator():
        try:
            # Yield initial state
            yield f"data: {json.dumps(job)}\n\n"
            while True:
                try:
                    event_data = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield f"data: {json.dumps(event_data)}\n\n"
                    if event_data.get("status") in ("completed", "failed", "canceled"):
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment
                    yield ": ping\n\n"
        finally:
            unsubscribe_job_events(job_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/v1/jobs/{job_id}/cancel")
def api_cancel_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    from viral_clips.services.pipeline_service import cancel_job
    cancel_job(job_id)
    audit_logger.log("job_cancelled", job_id=job_id)
    return {"status": "canceled", "job_id": job_id}


# ==========================================
# Results, Rerender & Downloads API
# ==========================================

@app.get("/v1/projects/{project_id}/candidates")
def api_get_candidates(project_id: str):
    candidates = get_candidates(project_id)
    return {"project_id": project_id, "candidates": candidates}


@app.post("/v1/candidates/{candidate_id}/accept")
def api_accept_candidate(candidate_id: str, body: AcceptCandidateRequest):
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE candidates SET accepted = ? WHERE id = ?",
            (1 if body.accepted else 0, candidate_id),
        )
    return {"status": "updated", "candidate_id": candidate_id, "accepted": body.accepted}


@app.get("/v1/clips/{clip_id}")
def api_get_clip(clip_id: str):
    from viral_clips.db.database import get_clip
    clip = get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    conn = get_connection()
    render_row = conn.execute("SELECT * FROM renders WHERE id = ?", (clip.get("current_render_id"),)).fetchone()
    if render_row:
        clip["render"] = dict(render_row)
    return clip


@app.post("/v1/clips/{clip_id}/render")
def api_rerender_clip(clip_id: str, body: RerenderClipRequest):
    """Fast rerender of an individual clip with modified subtitles or framing."""
    from viral_clips.db.database import get_clip
    from viral_clips.services.pipeline_service import rerender_clip_job

    clip = get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    project_id = clip["project_id"]
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    upload_dir = Path("./storage/uploads") / project_id
    video_files = list(upload_dir.glob("*.*")) if upload_dir.exists() else []
    if not video_files:
        sample = Path("samples/sample_podcast.mp4")
        if sample.exists():
            video_files = [sample]
        else:
            raise HTTPException(status_code=400, detail="Source video not found for rerender.")

    source_video = video_files[0]
    out_dir = Path("./storage/output") / f"proj_{project_id}"

    # Load transcript words if present
    words = []
    t_file = out_dir / "transcript.json"
    if t_file.exists():
        try:
            with open(t_file, "r", encoding="utf-8") as f:
                words = json.load(f).get("words", [])
        except Exception:
            pass

    start_ms = body.start_ms if body.start_ms is not None else clip["start_ms"]
    end_ms = body.end_ms if body.end_ms is not None else clip["end_ms"]

    result = rerender_clip_job(
        clip_id=clip_id,
        project_id=project_id,
        video_path=source_video,
        output_dir=out_dir,
        start_ms=start_ms,
        end_ms=end_ms,
        subtitle_preset=body.subtitle_preset,
        framing=body.framing,
        words=words,
        font_size=body.font_size,
        font_name=body.font_name,
    )
    audit_logger.log("clip_rerendered", project_id=project_id, details=result)
    log_product_event("clip_rerendered", entity_id=clip_id, payload=result)
    return result


@app.post("/v1/clips/{clip_id}/feedback")
def api_save_clip_feedback(clip_id: str, body: FeedbackClipRequest):
    """Saves human feedback scorecard (publishable, issues, ratings) for a clip."""
    clip = get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    res = save_clip_feedback(
        clip_id=clip_id,
        publishable=body.publishable,
        issues=body.issues,
        ratings=body.ratings,
    )
    log_product_event("clip_feedback_submitted", entity_id=clip_id, payload=res)
    return res


@app.get("/v1/clips/{clip_id}/feedback")
def api_get_clip_feedback(clip_id: str):
    """Retrieves human feedback scorecard for a clip."""
    fb = get_clip_feedback(clip_id)
    if not fb:
        return {
            "clip_id": clip_id,
            "publishable": True,
            "issues": [],
            "ratings": {"highlight": 5, "framing": 5, "subtitles": 5},
            "created_at": None,
        }
    return fb


@app.post("/v1/clips/{clip_id}/review")
def api_review_clip(clip_id: str, body: ReviewClipRequest):
    """Saves human review quality scorecard (publishable, 1-5 quality scales) for a clip."""
    from viral_clips.db.database import save_clip_review
    res = save_clip_review(
        clip_id=clip_id,
        publishable=body.publishable,
        highlight_quality=body.highlight_quality,
        framing_quality=body.framing_quality,
        subtitle_quality=body.subtitle_quality,
        notes=body.notes,
    )
    audit_logger.log("clip_reviewed", details=res)
    return res


@app.get("/v1/clips/{clip_id}/review")
def api_get_clip_review(clip_id: str):
    """Retrieves human review quality scorecard for a clip."""
    from viral_clips.db.database import get_clip_review
    rev = get_clip_review(clip_id)
    if not rev:
        return {
            "clip_id": clip_id,
            "publishable": False,
            "highlight_quality": 3,
            "framing_quality": 3,
            "subtitle_quality": 3,
            "notes": "",
        }
    return rev


@app.post("/v1/projects/{project_id}/regenerate-highlights")
def api_regenerate_highlights(project_id: str, body: Optional[RegenerateHighlightsRequest] = None):
    """Fast highlight regeneration from existing transcript without re-running ASR."""
    project = get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    settings_dict = project.get("settings") or {}
    clip_count = (body.clip_count if body and body.clip_count is not None else settings_dict.get("clip_count", 5))
    min_d = (body.min_duration_s if body and body.min_duration_s is not None else settings_dict.get("duration_min", 20.0))
    max_d = (body.max_duration_s if body and body.max_duration_s is not None else settings_dict.get("duration_max", 75.0))
    strat = (body.highlight_strategy if body and body.highlight_strategy is not None else settings_dict.get("highlight_strategy", ["auto"]))
    c_type = (body.content_type if body and body.content_type is not None else settings_dict.get("content_type", "auto"))

    out_dir = Path("./storage/output") / f"proj_{project_id}"
    t_file = out_dir / "transcript.json"
    if not t_file.exists():
        t_file_alt = Path("./storage/output") / project_id / "transcript.json"
        if t_file_alt.exists():
            t_file = t_file_alt
        else:
            raise HTTPException(
                status_code=400,
                detail="Transcript not found for this project. Run full processing first.",
            )

    candidates_art, ranking_art = detect_highlights(
        transcript_path_or_dict=t_file,
        output_dir=out_dir,
        clip_count=clip_count,
        min_duration_s=min_d,
        max_duration_s=max_d,
        highlight_strategy=strat,
        content_type=c_type,
    )

    save_candidates(project_id, candidates_art.get("candidates", []))
    log_product_event("highlights_regenerated", entity_id=project_id, payload={
        "clip_count": clip_count,
        "strategy": strat,
        "content_type": c_type,
        "top_clips_count": len(ranking_art.get("top_clips", [])),
    })

    return {
        "status": "success",
        "project_id": project_id,
        "top_clips": ranking_art.get("top_clips", []),
        "candidates_count": len(candidates_art.get("candidates", [])),
    }


@app.get("/v1/renders/{render_id}/download")
def api_download_render(render_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM renders WHERE id = ?", (render_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Render not found")

    from viral_clips.db.database import get_artifact
    target_id_or_path = row["output_artifact_id"]
    file_path = None

    if target_id_or_path:
        p = Path(target_id_or_path)
        if p.is_file():
            file_path = p
        else:
            art = get_artifact(target_id_or_path)
            if art and art.get("storage_key"):
                cand = Path("storage") / art["storage_key"].replace("projects/", "")
                if cand.is_file():
                    file_path = cand
                elif Path(art.get("storage_key")).is_file():
                    file_path = Path(art.get("storage_key"))

    if not file_path or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Rendered video file missing from disk")

    log_product_event("clip_downloaded", entity_id=render_id, payload={"filename": file_path.name})

    return FileResponse(
        path=str(file_path.resolve()),
        media_type="video/mp4",
        filename=file_path.name,
    )



# ==========================================
# Web UI Endpoint (Phase 7 Modern Dashboard)
# ==========================================

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def serve_ui():
    from viral_clips.ui.web_ui import get_ui_html
    return HTMLResponse(content=get_ui_html())


# ==========================================
# Phase 8, 9, 10: Storage, Metrics, Evaluation
# ==========================================

@app.get("/v1/metrics", response_class=HTMLResponse)
def api_get_metrics():
    """Prometheus-compatible plain text metrics."""
    return HTMLResponse(
        content=metrics_collector.generate_prometheus_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.post("/v1/storage/cleanup")
def api_trigger_storage_cleanup(max_age_days: int = 14):
    """Prunes expired artifacts and temp files."""
    audit_logger.log("storage_cleanup_triggered", details={"max_age_days": max_age_days})
    res = storage_lifecycle.enforce_retention_policy(max_age_days=max_age_days)
    return {"status": "success", "cleanup": res}


@app.get("/v1/projects/{project_id}/evaluate")
def api_evaluate_project_clips(project_id: str):
    """Phase 10: Beta quality benchmark and scorecard evaluation."""
    candidates = get_candidates(project_id)
    if not candidates:
        raise HTTPException(status_code=404, detail="No candidates found for project evaluation")

    benchmark = GoldenBenchmarkRunner.run_benchmark_suite(candidates)
    audit_logger.log("project_evaluated", project_id=project_id, details={"publishable_ratio": benchmark["publishable_ratio"]})
    return benchmark


@app.post("/v1/clips/{clip_id}/archive/drive")
def api_archive_clip_to_drive(clip_id: str):
    """Archives rendered clip to Google Drive 10 TB storage."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip = dict(row)
    render_id = clip.get("current_render_id")
    render_row = conn.execute("SELECT * FROM renders WHERE id = ?", (render_id,)).fetchone()
    if not render_row:
        raise HTTPException(status_code=404, detail="Render not found for clip")

    file_path = render_row["output_artifact_id"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Rendered video file not on disk")

    storage_key = f"{clip['project_id']}/clips/{clip_id}.mp4"
    artifact = gdrive_adapter.store_file(file_path, storage_key, mime_type="video/mp4")
    drive_url = gdrive_adapter.get_download_url(storage_key)

    audit_logger.log("clip_archived_to_drive", project_id=clip['project_id'], details={"clip_id": clip_id, "drive_url": drive_url})
    return {
        "status": "archived",
        "clip_id": clip_id,
        "provider": "drive",
        "drive_url": drive_url,
        "artifact_id": artifact.id,
        "message": f"Ролик успешно сохранен в Google Drive 10 TB ({drive_url})"
    }


@app.post("/v1/projects/{project_id}/archive/drive")
def api_archive_project_to_drive(project_id: str):
    """Archives all clips and manifests of project to Google Drive."""
    clips = get_project_clips(project_id)
    archived = []
    for c in clips:
        if c.get("video_path") and os.path.exists(c["video_path"]):
            s_key = f"{project_id}/clips/{c['id']}.mp4"
            art = gdrive_adapter.store_file(c["video_path"], s_key, mime_type="video/mp4")
            archived.append({
                "clip_id": c["id"],
                "drive_url": gdrive_adapter.get_download_url(s_key),
            })
    audit_logger.log("project_archived_to_drive", project_id=project_id, details={"archived_clips": len(archived)})
    return {
        "status": "success",
        "project_id": project_id,
        "provider": "drive",
        "archived_count": len(archived),
        "drive_folder": f"https://drive.google.com/drive/folders/{project_id[:12]}",
        "clips": archived,
    }

