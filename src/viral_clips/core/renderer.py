"""
Single-Pass FFmpeg Video Rendering & Burn-in Engine.
Combines video trimming, 9:16 reframing, ASS karaoke burn-in, audio normalization,
and NVIDIA NVENC hardware acceleration into one efficient pass.
Validates output integrity and produces versioned 'render_manifest.json'.
"""

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
from loguru import logger

from viral_clips.config import settings
from viral_clips.core.ffmpeg_utils import check_nvenc_support, get_ffmpeg_path
from viral_clips.core.media_probe import probe_media
from viral_clips.exceptions import MediaProbeError, ViralClipsError

SCHEMA_VERSION = "1.0.0"


def escape_ffmpeg_path(path: Union[str, Path]) -> str:
    """Escapes file paths for FFmpeg filtergraph strings on Windows."""
    p_str = Path(path).resolve().as_posix()
    # Escape colon (e.g. C: -> C\:)
    if len(p_str) > 1 and p_str[1] == ":":
        p_str = p_str[0] + r"\:" + p_str[2:]
    # Escape single quotes and backslashes
    p_str = p_str.replace("'", r"\'").replace(" ", r"\ ")
    return p_str


def render_clip(
    source_video: Union[str, Path],
    output_video_path: Union[str, Path],
    clip_start_ms: int,
    clip_end_ms: int,
    crop_plan: Dict[str, Any],
    subtitle_ass_path: Optional[Union[str, Path]] = None,
    use_hardware_accel: Optional[bool] = None,
    progress_callback: Optional[Callable[[float], None]] = None,
    timeout: int = 300,
    clip_id: Optional[str] = None,
    subtitle_preset: str = "bold_karaoke",
    transcript_provider: Optional[str] = None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    pipeline_version: str = "quality-gate-v1",
) -> Dict[str, Any]:
    """
    Renders a single vertical clip in ONE FFmpeg pass:
    Trim -> 9:16 Scale/Crop/Blur -> Burn ASS Subtitles -> Normalize Audio -> NVENC Encode.
    """
    src = Path(source_video).resolve()
    dst = Path(output_video_path).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not src.is_file():
        raise MediaProbeError(f"Source video file not found: {src}")

    start_s = clip_start_ms / 1000.0
    duration_s = (clip_end_ms - clip_start_ms) / 1000.0

    ffmpeg_bin = get_ffmpeg_path()
    start_time_perf = time.perf_counter()

    # Determine encoder
    can_nvenc = check_nvenc_support()
    use_nvenc = (settings.use_nvenc if use_hardware_accel is None else use_hardware_accel) and can_nvenc
    encoder_name = "h264_nvenc" if use_nvenc else "libx264"

    # Base video filter from crop plan
    base_filter = crop_plan.get("ffmpeg_filtergraph_base", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920[base]")

    # Subtitle overlay
    if subtitle_ass_path and Path(subtitle_ass_path).is_file():
        ass_escaped = escape_ffmpeg_path(subtitle_ass_path)
        full_filtergraph = f"{base_filter};[base]ass='{ass_escaped}'[outv]"
    else:
        full_filtergraph = f"{base_filter};[base]null[outv]"

    # Build single-pass FFmpeg command
    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss", f"{start_s:.3f}",
        "-t", f"{duration_s:.3f}",
        "-i", str(src),
        "-filter_complex", full_filtergraph,
        "-map", "[outv]",
        "-map", "0:a?",      # Map audio if present
    ]

    if use_nvenc:
        cmd.extend([
            "-c:v", "h264_nvenc",
            "-preset", "p4",    # Fast & balanced NVENC preset
            "-cq", "23",
            "-b:v", "5000k",
            "-maxrate", "7000k",
            "-bufsize", "10000k",
        ])
    else:
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
        ])

    cmd.extend([
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-movflags", "+faststart",  # Web/mobile streaming optimization
        str(dst),
    ])

    logger.info(f"Rendering clip ({encoder_name}): {src.name} [{start_s:.1f}s - {start_s+duration_s:.1f}s] -> {dst.name}...")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise ViralClipsError(code="RENDER_TIMEOUT", message=f"Rendering timed out after {timeout} seconds.")
    except Exception as e:
        raise ViralClipsError(code="RENDER_EXECUTION_FAILED", message=f"Failed to start FFmpeg: {e}")

    render_duration_s = round(time.perf_counter() - start_time_perf, 2)

    if proc.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
        err = proc.stderr.strip()
        logger.error(f"FFmpeg render error: {err}")
        # If NVENC failed, try fallback to CPU libx264
        if use_nvenc:
            logger.warning("Retrying render with CPU libx264 fallback...")
            return render_clip(
                source_video=source_video,
                output_video_path=output_video_path,
                clip_start_ms=clip_start_ms,
                clip_end_ms=clip_end_ms,
                crop_plan=crop_plan,
                subtitle_ass_path=subtitle_ass_path,
                use_hardware_accel=False,
                progress_callback=progress_callback,
                timeout=timeout,
            )
        raise ViralClipsError(code="RENDER_FAILED", message=f"Video render failed: {err}")

    # Output Validation (10_ACCEPTANCE.md & 06_PIPELINE_AND_JOBS.md)
    logger.info("Validating rendered clip integrity...")
    probe_out = probe_media(dst, allow_missing_audio=True)
    v_out = probe_out["primary_video"]

    if v_out["width"] != 1080 or v_out["height"] != 1920:
        raise ViralClipsError(
            code="INVALID_OUTPUT_DIMENSIONS",
            message=f"Rendered video dimensions {v_out['width']}x{v_out['height']} do not match required 1080x1920.",
        )

    # Tolerant duration check (within 1.5s tolerance)
    actual_dur = probe_out["duration_s"]
    if abs(actual_dur - duration_s) > 2.0:
        logger.warning(f"Clip duration discrepancy: expected {duration_s}s, got {actual_dur}s")

    c_id = clip_id or dst.stem
    crop_mode = crop_plan.get("mode") or crop_plan.get("mode_resolved", "blurred_background")
    traj = crop_plan.get("trajectory", [])

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "clip_id": c_id,
        "source": str(src),
        "source_file": str(src),
        "output_file": str(dst),
        "start": round(start_s, 3),
        "end": round(start_s + duration_s, 3),
        "clip_start_ms": clip_start_ms,
        "clip_end_ms": clip_end_ms,
        "target_duration_s": round(duration_s, 2),
        "actual_duration_s": actual_dur,
        "resolution": f"{v_out['width']}x{v_out['height']}",
        "video_encoder": encoder_name,
        "encoder": encoder_name,
        "hardware_accelerated": use_nvenc,
        "crop_mode": crop_mode,
        "trajectory_points": len(traj),
        "has_dynamic_trajectory": len(traj) >= 2,
        "subtitle_preset": subtitle_preset,
        "transcript_provider": transcript_provider or settings.asr_provider,
        "llm_provider": llm_provider or settings.llm_provider,
        "llm_model": llm_model or getattr(settings, "ollama_model", "qwen2.5:7b"),
        "pipeline_version": pipeline_version,
        "file_size_bytes": dst.stat().st_size,
        "render_time_s": render_duration_s,
        "speed_ratio": round(duration_s / max(0.01, render_duration_s), 2),
        "is_valid": True,
    }

    manifest_path = dst.with_name(f"{dst.stem}_render_manifest.json")
    generic_manifest = dst.parent / "render_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open(generic_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.success(
        f"Clip rendered successfully in {render_duration_s}s "
        f"({manifest['speed_ratio']}x realtime) -> {dst.name}"
    )
    return manifest
