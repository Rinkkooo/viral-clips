"""
Pipeline Orchestration Service.
Coordinates the end-to-end transformation of long video into viral short clips.
Follows stage weighting defined in 06_PIPELINE_AND_JOBS.md:
- probing: 2%
- extracting_audio: 5% (accum: 7%)
- transcribing: 28% (accum: 35%)
- segmenting: 5% (accum: 40%)
- ranking: 10% (accum: 50%)
- visual_analysis: 15% (accum: 65%)
- rendering: 30% (accum: 95%)
- validating/finalizing: 5% (accum: 100%)
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from loguru import logger

from viral_clips.config import settings
from viral_clips.core.asr import transcribe_video
from viral_clips.core.highlight_engine import detect_highlights
from viral_clips.core.media_probe import probe_media
from viral_clips.core.renderer import render_clip
from viral_clips.core.smart_reframe import generate_crop_plan
from viral_clips.core.subtitles import generate_subtitles
from viral_clips.db.database import (
    create_job,
    get_job,
    save_candidates,
    save_clip_and_render,
    update_job_progress,
    update_project_status,
)
from viral_clips.exceptions import MissingStreamError, ViralClipsError

# Thread pool for background video processing (default 1 concurrent worker on RTX 4060)
_executor = ThreadPoolExecutor(max_workers=settings.gpu_worker_concurrency)

# Global event listeners for Server-Sent Events (SSE)
# job_id -> list of asyncio.Queue
_event_subscribers: Dict[str, List[asyncio.Queue]] = {}


class CancellationToken:
    """Thread-safe cancellation token for halting active background jobs and subprocesses."""

    def __init__(self):
        self._is_cancelled = False
        self._active_pids: List[int] = []

    def cancel(self):
        self._is_cancelled = True
        for pid in self._active_pids:
            try:
                import os, signal
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def register_pid(self, pid: int):
        self._active_pids.append(pid)

    def unregister_pid(self, pid: int):
        if pid in self._active_pids:
            self._active_pids.remove(pid)


_active_job_tokens: Dict[str, CancellationToken] = {}


def get_cancellation_token(job_id: str) -> CancellationToken:
    if job_id not in _active_job_tokens:
        _active_job_tokens[job_id] = CancellationToken()
    return _active_job_tokens[job_id]


def cancel_job(job_id: str) -> bool:
    """Cancels a running job, terminating any active worker thread or subprocess."""
    token = _active_job_tokens.get(job_id)
    if token:
        token.cancel()
    update_job_progress(job_id=job_id, stage="canceled", progress=0, status="canceled")
    broadcast_job_event(job_id, {
        "job_id": job_id,
        "status": "canceled",
        "stage": "canceled",
        "progress": 0,
        "message": "Обработка успешно прервана пользователем.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    logger.warning(f"Job {job_id} cancellation triggered and registered.")
    return True


def subscribe_job_events(job_id: str) -> asyncio.Queue:
    """Subscribes an SSE listener to job progress updates."""
    q: asyncio.Queue = asyncio.Queue()
    if job_id not in _event_subscribers:
        _event_subscribers[job_id] = []
    _event_subscribers[job_id].append(q)
    return q


def unsubscribe_job_events(job_id: str, q: asyncio.Queue):
    """Unsubscribes an SSE listener."""
    if job_id in _event_subscribers and q in _event_subscribers[job_id]:
        _event_subscribers[job_id].remove(q)
        if not _event_subscribers[job_id]:
            del _event_subscribers[job_id]


def broadcast_job_event(job_id: str, event_data: Dict[str, Any]):
    """Pushes a progress event to all active SSE subscribers."""
    subscribers = _event_subscribers.get(job_id, [])
    for q in subscribers:
        try:
            q.put_nowait(event_data)
        except Exception:
            pass


def _sync_pipeline_runner(
    job_id: str,
    project_id: str,
    video_path: Path,
    output_dir: Path,
    clip_count: int = 5,
    min_duration_s: float = 20.0,
    max_duration_s: float = 75.0,
    framing: str = "active_speaker",
    subtitle_preset: str = "bold_karaoke",
    language: Optional[str] = "ru",
    highlight_strategy: Optional[List[str]] = None,
    content_type: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
):
    """Synchronous pipeline worker executing all phases with cancellation checkpoints."""
    logger.info(f"Starting pipeline execution for Job {job_id}, Project {project_id}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    token = get_cancellation_token(job_id)

    def check_cancel() -> bool:
        if token.is_cancelled:
            logger.warning(f"Job {job_id} cancelled by token. Halting pipeline execution.")
            update_job_progress(job_id=job_id, stage="canceled", progress=0, status="canceled")
            update_project_status(project_id, "canceled")
            broadcast_job_event(job_id, {
                "job_id": job_id,
                "project_id": project_id,
                "status": "canceled",
                "stage": "canceled",
                "progress": 0,
                "message": "Обработка отменена пользователем.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return True
        return False

    def report_progress(stage: str, progress: int, message: str):
        update_job_progress(job_id=job_id, stage=stage, progress=progress, status="running")
        event = {
            "job_id": job_id,
            "project_id": project_id,
            "status": "running",
            "stage": stage,
            "progress": progress,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        broadcast_job_event(job_id, event)
        logger.info(f"[{progress}%] Stage '{stage}': {message}")

    try:
        if check_cancel():
            return

        update_project_status(project_id, "processing")

        # 1. Probing (0 -> 2%)
        report_progress("probing", 2, "Анализ медиа-контейнера и проверка кодеков...")
        probe_info = probe_media(video_path, allow_missing_audio=True)
        if check_cancel():
            return

        if probe_info.get("audio_streams_count", 0) == 0 or probe_info.get("primary_audio") is None:
            raise MissingStreamError(
                "В исходном видеофайле отсутствует аудиодорожка. Для распознавания речи (ASR) и создания клипов требуется видео со звуком.",
                stream_type="audio"
            )

        # 2. Extracting Audio & ASR Transcribing (2% -> 35%)
        report_progress("extracting_audio", 7, "Извлечение 16кГц звуковой дорожки...")
        report_progress("transcribing", 15, "Транскрибация речи и вычисление таймкодов слов...")

        transcript = transcribe_video(
            video_path=video_path,
            output_dir=output_dir,
            language=language,
        )
        report_progress("transcribing", 35, f"Транскрибировано {transcript['total_words']} слов.")
        if check_cancel():
            return

        # 3. Candidate Windows & Segmentation (35% -> 40%)
        report_progress("segmenting", 40, "Формирование смысловых окон по границам предложений...")
        if check_cancel():
            return

        # 4. Multi-dimensional Ranking & Diversification (40% -> 50%)
        report_progress("ranking", 45, "AI-оценка виральности по 7 факторам и диверсификация...")
        candidates_art, ranking_art = detect_highlights(
            transcript_path_or_dict=transcript,
            output_dir=output_dir,
            clip_count=clip_count,
            min_duration_s=min_duration_s,
            max_duration_s=max_duration_s,
            highlight_strategy=highlight_strategy,
            content_type=content_type,
            complete_sentences=options.get("complete_sentences", True) if options else True,
            options=options,
        )

        top_clips = ranking_art.get("top_clips", [])
        save_candidates(project_id, candidates_art.get("candidates", []))
        report_progress("ranking", 50, f"Отобрано {len(top_clips)} лучших вирусных клипов.")
        if check_cancel():
            return

        # 5. Visual Analysis, Crop Plan & Subtitles (50% -> 65%)
        report_progress("visual_analysis", 55, "Анализ лиц через компьютерное зрение и кадрирование 9:16...")
        words = transcript.get("words", [])

        # Process each clip
        rendered_clips = []
        num_clips = max(1, len(top_clips))
        render_step_weight = 30.0 / num_clips

        for idx, clip in enumerate(top_clips):
            if check_cancel():
                return

            clip_idx = idx + 1
            s_ms = clip["start_ms"]
            e_ms = clip["end_ms"]
            cand_id = clip.get("id")

            # Crop Plan
            crop_plan_path = output_dir / f"crop_plan_clip_{clip_idx}.json"
            crop_plan = generate_crop_plan(
                video_path=video_path,
                clip_start_ms=s_ms,
                clip_end_ms=e_ms,
                preset=framing,
                output_plan_path=crop_plan_path,
            )

            # Subtitles ASS
            sub_path = output_dir / f"subtitles_clip_{clip_idx}.ass"
            generate_subtitles(
                words=words,
                clip_start_ms=s_ms,
                clip_end_ms=e_ms,
                output_ass_path=sub_path,
                preset=subtitle_preset,
            )

            if check_cancel():
                return

            # 6. Render One-Pass (65% -> 95%)
            cur_prog = int(65 + idx * render_step_weight)
            report_progress(
                "rendering",
                cur_prog,
                f"Рендеринг клипа {clip_idx}/{num_clips} (NVENC 9:16 + субтитры)...",
            )

            out_video_path = output_dir / f"clip_{clip_idx}_{s_ms}_{e_ms}.mp4"
            render_manifest = render_clip(
                source_video=video_path,
                output_video_path=out_video_path,
                clip_start_ms=s_ms,
                clip_end_ms=e_ms,
                crop_plan=crop_plan,
                subtitle_ass_path=sub_path,
                clip_id=f"clip_{clip_idx}",
                subtitle_preset=subtitle_preset,
                transcript_provider=transcript.get("provider", settings.asr_provider),
                llm_provider=ranking_art.get("provider", settings.llm_provider),
                llm_model=ranking_art.get("model", getattr(settings, "ollama_model", "qwen2.5:7b")),
            )

            # Save to Database with real artifact registrations
            clip_id, render_id = save_clip_and_render(
                project_id=project_id,
                candidate_id=cand_id,
                start_ms=s_ms,
                end_ms=e_ms,
                render_manifest=render_manifest,
                preset=subtitle_preset,
                crop_plan_path=crop_plan_path,
                subtitle_ass_path=sub_path,
            )
            rendered_clips.append({"clip_id": clip_id, "render_id": render_id, "file": str(out_video_path)})

        # 7. Finalizing & Validation (95% -> 100%)
        if check_cancel():
            return

        model_meta = {
            "asr_provider": transcript.get("provider", settings.asr_provider),
            "asr_model": transcript.get("model", settings.whisper_model),
            "asr_device": transcript.get("device", settings.whisper_device),
            "detected_language": transcript.get("detected_language", "ru"),
            "language_probability": transcript.get("language_probability", 1.0),
            "llm_provider": ranking_art.get("provider", settings.llm_provider),
            "llm_model": ranking_art.get("model", getattr(settings, "ollama_model", "qwen2.5:7b")),
            "fallback_used": ranking_art.get("fallback_used", False),
            "framing_mode": framing,
            "encoder": "h264_nvenc" if settings.use_nvenc else "libx264",
        }

        report_progress("validating", 100, f"Готово! Сгенерировано {len(rendered_clips)} вертикальных клипов.")
        update_job_progress(job_id=job_id, stage="completed", progress=100, status="completed")
        update_project_status(project_id, "completed")

        final_event = {
            "job_id": job_id,
            "project_id": project_id,
            "status": "completed",
            "stage": "completed",
            "progress": 100,
            "message": "Пайплайн успешно завершен.",
            "clips_count": len(rendered_clips),
            "model_meta": model_meta,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        broadcast_job_event(job_id, final_event)
        logger.success(f"Pipeline job {job_id} successfully finished.")

    except Exception as e:
        if token.is_cancelled:
            logger.info(f"Pipeline job {job_id} aborted during cancellation: {e}")
            return

        logger.error(f"Pipeline job {job_id} failed: {e}")
        err_msg = str(e)
        update_job_progress(
            job_id=job_id,
            stage="failed",
            progress=0,
            status="failed",
            error_code="PIPELINE_ERROR",
            error_message=err_msg,
        )
        update_project_status(project_id, "failed")
        fail_event = {
            "job_id": job_id,
            "project_id": project_id,
            "status": "failed",
            "stage": "failed",
            "progress": 0,
            "error_message": err_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        broadcast_job_event(job_id, fail_event)


def start_pipeline_job(
    project_id: str,
    video_path: Union[str, Path],
    clip_count: int = 5,
    min_duration_s: float = 20.0,
    max_duration_s: float = 75.0,
    framing: str = "active_speaker",
    subtitle_preset: str = "bold_karaoke",
    language: Optional[str] = "ru",
    idempotency_key: Optional[str] = None,
    highlight_strategy: Optional[List[str]] = None,
    content_type: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Creates a job record and submits pipeline to background worker thread.
    Prevents duplicate executions for existing active jobs.
    """
    job = create_job(project_id=project_id, idempotency_key=idempotency_key)
    job_id = job["id"]
    is_new = job.get("is_new", True)

    # Idempotency check: if job exists and is already active or done, do NOT resubmit
    if not is_new and job.get("status") in ("queued", "running", "completed"):

        logger.info(f"Idempotent duplicate request for job {job_id} (status: {job.get('status')}). Skipping resubmission.")
        return {"job_id": job_id, "status": job.get("status"), "deduplicated": True}

    v_path = Path(video_path).resolve()
    out_dir = v_path.parent / "output" / f"proj_{project_id}"

    # Initialize cancellation token
    get_cancellation_token(job_id)

    _executor.submit(
        _sync_pipeline_runner,
        job_id=job_id,
        project_id=project_id,
        video_path=v_path,
        output_dir=out_dir,
        clip_count=clip_count,
        min_duration_s=min_duration_s,
        max_duration_s=max_duration_s,
        framing=framing,
        subtitle_preset=subtitle_preset,
        language=language,
        highlight_strategy=highlight_strategy,
        content_type=content_type,
        options=options,
    )

    return {"job_id": job_id, "status": "queued"}


def rerender_clip_job(
    clip_id: str,
    project_id: str,
    video_path: Path,
    output_dir: Path,
    start_ms: int,
    end_ms: int,
    subtitle_preset: str = "bold_karaoke",
    framing: str = "active_speaker",
    words: Optional[List[Dict[str, Any]]] = None,
    font_size: Optional[int] = None,
    font_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Performs fast rerender of an individual clip with updated subtitle preset or framing.
    Avoids re-running ASR or highlight ranking.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(datetime.now(timezone.utc).timestamp())

    # 1. New Crop Plan
    crop_plan_path = output_dir / f"crop_plan_rerender_{clip_id}_{timestamp}.json"
    crop_plan = generate_crop_plan(
        video_path=video_path,
        clip_start_ms=start_ms,
        clip_end_ms=end_ms,
        preset=framing,
        output_plan_path=crop_plan_path,
    )

    # 2. Subtitles ASS
    sub_path = None
    if words:
        sub_path = output_dir / f"subtitles_rerender_{clip_id}_{timestamp}.ass"
        generate_subtitles(
            words=words,
            clip_start_ms=start_ms,
            clip_end_ms=end_ms,
            output_ass_path=sub_path,
            preset=subtitle_preset,
            font_size=font_size,
            font_name=font_name,
        )

    # 3. Render
    out_video_path = output_dir / f"clip_rerender_{clip_id}_{timestamp}.mp4"
    manifest = render_clip(
        source_video=video_path,
        output_video_path=out_video_path,
        clip_start_ms=start_ms,
        clip_end_ms=end_ms,
        crop_plan=crop_plan,
        subtitle_ass_path=sub_path,
        clip_id=clip_id,
        subtitle_preset=subtitle_preset,
    )

    # 4. Save new render in DB
    from viral_clips.db.database import create_clip_render
    render_id = create_clip_render(
        clip_id=clip_id,
        project_id=project_id,
        render_manifest=manifest,
        preset=subtitle_preset,
        crop_plan_path=crop_plan_path,
        subtitle_ass_path=sub_path,
        start_ms=start_ms,
        end_ms=end_ms,
    )

    return {
        "clip_id": clip_id,
        "render_id": render_id,
        "output_file": str(out_video_path),
        "encoder": manifest.get("encoder"),
    }

