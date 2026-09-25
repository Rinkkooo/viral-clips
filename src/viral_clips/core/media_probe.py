"""
Sandboxed media validation and ffprobe inspector.
Enforces security boundaries, resource quotas, and codec compatibility.
Produces versioned 'probe.json' intermediate artifact.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from loguru import logger

from viral_clips.config import Settings, settings
from viral_clips.core.ffmpeg_utils import get_ffprobe_path
from viral_clips.exceptions import (
    MediaLimitExceededError,
    MediaProbeError,
    MissingStreamError,
    UnsupportedCodecError,
)

SCHEMA_VERSION = "1.0.0"

SUPPORTED_VIDEO_CODECS = {
    "h264",
    "hevc",
    "h265",
    "vp8",
    "vp9",
    "av1",
    "mpeg4",
    "mjpeg",
    "prores",
}


def parse_fraction(val: Optional[str]) -> Optional[float]:
    """Safely parse fractional frame rates like '30/1' or '60000/1001'."""
    if not val or val == "0/0":
        return None
    try:
        if "/" in val:
            num, den = val.split("/", 1)
            num_f, den_f = float(num), float(den)
            return round(num_f / den_f, 3) if den_f != 0 else None
        return round(float(val), 3)
    except (ValueError, ZeroDivisionError):
        return None


def probe_media(
    file_path: Union[str, Path],
    custom_settings: Optional[Settings] = None,
    allow_missing_audio: bool = False,
) -> Dict[str, Any]:
    """
    Sandboxed probe and validation of a media file using ffprobe.
    Validates file integrity, limits (duration, dimensions, fps, size, streams),
    and produces a standardized probe dictionary with schema_version.
    """
    cfg = custom_settings or settings
    path = Path(file_path).resolve()

    # 1. Path & Existence validation
    if not path.is_file():
        raise MediaProbeError(f"Media file not found or is not a regular file: {path}")

    # 2. File size limit
    size_bytes = path.stat().st_size
    if size_bytes <= 0:
        raise MediaProbeError("File is empty (0 bytes).")
    if size_bytes > cfg.max_file_size_bytes:
        raise MediaLimitExceededError(
            code="FILE_TOO_LARGE",
            message=f"File size {size_bytes} exceeds maximum limit of {cfg.max_file_size_bytes} bytes.",
            details={"size_bytes": size_bytes, "max_bytes": cfg.max_file_size_bytes},
        )

    # 3. Resolve ffprobe binary
    ffprobe_bin = get_ffprobe_path()

    # 4. Sandboxed execution with timeout
    cmd = [
        ffprobe_bin,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,  # 20s timeout to prevent hanging on corrupted/bomb files
        )
    except subprocess.TimeoutExpired:
        raise MediaProbeError("ffprobe timed out while analyzing the media file (corrupted or hanging stream).")
    except Exception as e:
        raise MediaProbeError(f"Failed to execute ffprobe: {e}")

    if proc.returncode != 0 or not proc.stdout.strip():
        err_msg = proc.stderr.strip() or "Corrupted or unreadable media file."
        raise MediaProbeError(f"Media probe failed: {err_msg}", details={"stderr": err_msg})

    try:
        probe_data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise MediaProbeError(f"Malformed ffprobe JSON output: {e}")

    format_info = probe_data.get("format", {})
    streams: List[Dict[str, Any]] = probe_data.get("streams", [])

    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    # 5. Stream Count Validation
    if not video_streams:
        raise MissingStreamError("File does not contain any video stream.", stream_type="video")

    if len(video_streams) > cfg.max_video_streams:
        raise MediaLimitExceededError(
            code="TOO_MANY_VIDEO_STREAMS",
            message=f"Video contains {len(video_streams)} video streams (max allowed: {cfg.max_video_streams}).",
        )

    if not audio_streams and not allow_missing_audio:
        raise MissingStreamError("File does not contain any audio stream.", stream_type="audio")

    if len(audio_streams) > cfg.max_audio_streams:
        raise MediaLimitExceededError(
            code="TOO_MANY_AUDIO_STREAMS",
            message=f"Video contains {len(audio_streams)} audio streams (max allowed: {cfg.max_audio_streams}).",
        )

    primary_v = video_streams[0]
    primary_a = audio_streams[0] if audio_streams else None

    # 6. Duration Validation
    duration_str = format_info.get("duration") or primary_v.get("duration")
    duration_s = float(duration_str) if duration_str else 0.0

    max_duration_s = cfg.max_source_duration_minutes * 60
    if duration_s > max_duration_s:
        raise MediaLimitExceededError(
            code="DURATION_EXCEEDED",
            message=f"Video duration {duration_s:.1f}s exceeds limit of {max_duration_s}s ({cfg.max_source_duration_minutes} min).",
            details={"duration_s": duration_s, "max_duration_s": max_duration_s},
        )

    # 7. Dimension & Pixel Validation
    width = int(primary_v.get("width") or 0)
    height = int(primary_v.get("height") or 0)
    max_pixels = cfg.max_video_width * cfg.max_video_height
    if width * height > max_pixels:
        raise MediaLimitExceededError(
            code="RESOLUTION_EXCEEDED",
            message=f"Video resolution {width}x{height} exceeds maximum allowable resolution {cfg.max_video_width}x{cfg.max_video_height}.",
            details={"width": width, "height": height},
        )

    # 8. FPS Validation
    fps = parse_fraction(primary_v.get("r_frame_rate")) or parse_fraction(primary_v.get("avg_frame_rate")) or 30.0
    if fps > cfg.max_video_fps:
        raise MediaLimitExceededError(
            code="FPS_EXCEEDED",
            message=f"Video frame rate {fps} fps exceeds limit of {cfg.max_video_fps} fps.",
            details={"fps": fps, "max_fps": cfg.max_video_fps},
        )

    # 9. Codec Validation
    video_codec = (primary_v.get("codec_name") or "").lower()
    if video_codec not in SUPPORTED_VIDEO_CODECS:
        raise UnsupportedCodecError(
            f"Unsupported video codec '{video_codec}'. Supported: {', '.join(sorted(SUPPORTED_VIDEO_CODECS))}",
            details={"codec": video_codec},
        )

    # 10. Assemble standard probe.json artifact
    result = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_path": str(path),
        "format_name": format_info.get("format_name", ""),
        "duration_s": round(duration_s, 3),
        "size_bytes": size_bytes,
        "bit_rate": int(format_info.get("bit_rate") or 0),
        "video_streams_count": len(video_streams),
        "audio_streams_count": len(audio_streams),
        "primary_video": {
            "index": primary_v.get("index", 0),
            "codec": video_codec,
            "profile": primary_v.get("profile"),
            "width": width,
            "height": height,
            "aspect_ratio": f"{width}:{height}",
            "fps": fps,
            "duration_s": round(float(primary_v.get("duration") or duration_s), 3),
            "pix_fmt": primary_v.get("pix_fmt"),
        },
        "primary_audio": (
            {
                "index": primary_a.get("index", 1),
                "codec": (primary_a.get("codec_name") or "").lower(),
                "sample_rate": int(primary_a.get("sample_rate") or 0),
                "channels": int(primary_a.get("channels") or 0),
                "duration_s": round(float(primary_a.get("duration") or duration_s), 3),
            }
            if primary_a
            else None
        ),
        "is_valid": True,
    }

    return result
