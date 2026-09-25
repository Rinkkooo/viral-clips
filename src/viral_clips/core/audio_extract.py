"""
Audio extraction module.
Converts any source video into a standardized 16kHz mono 16-bit PCM WAV
optimized for Whisper/ASR transcription engines.
"""

import subprocess
from pathlib import Path
from typing import Optional, Union
from loguru import logger

from viral_clips.core.ffmpeg_utils import get_ffmpeg_path
from viral_clips.exceptions import MediaProbeError


def _clean_ffmpeg_error(raw_stderr: str) -> str:
    """Extract clean human-readable error from ffmpeg stderr without compiler flags."""
    lines = [line.strip() for line in raw_stderr.splitlines() if line.strip()]
    filtered = [
        l for l in lines 
        if not l.startswith("ffmpeg version") 
        and not l.startswith("built with") 
        and not l.startswith("configuration:")
        and not l.startswith("libav")
        and not l.startswith("libsw")
        and not l.startswith("libpostproc")
    ]
    text = " ".join(filtered)
    if "does not contain any stream" in text or "matches no streams" in text:
        return "В исходном видеофайле отсутствует аудиодорожка. Для создания клипов с субтитрами требуется видео со звуком."
    if filtered:
        return filtered[-1]
    return raw_stderr[-300:] if len(raw_stderr) > 300 else raw_stderr


def extract_audio_for_asr(
    video_path: Union[str, Path],
    output_wav_path: Optional[Union[str, Path]] = None,
    timeout: int = 180,
) -> Path:
    """
    Extracts the primary audio stream from a video into a 16kHz mono WAV file.
    
    Args:
        video_path: Path to source video file.
        output_wav_path: Destination path for .wav. If None, created in same dir.
        timeout: Subprocess timeout in seconds.
        
    Returns:
        Path to the extracted WAV file.
    """
    src = Path(video_path).resolve()
    if not src.is_file():
        raise MediaProbeError(f"Video file not found: {src}")

    if output_wav_path:
        dst = Path(output_wav_path).resolve()
    else:
        dst = src.with_suffix(".asr.wav")

    dst.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg_bin = get_ffmpeg_path()
    cmd = [
        ffmpeg_bin,
        "-y",               # Overwrite existing
        "-i", str(src),
        "-vn",              # Disable video
        "-acodec", "pcm_s16le",
        "-ar", "16000",     # 16 kHz sample rate (optimal for Whisper)
        "-ac", "1",         # Mono channel
        "-f", "wav",
        str(dst),
    ]

    logger.info(f"Extracting audio for ASR from {src.name} -> {dst.name}...")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise MediaProbeError(f"Audio extraction timed out after {timeout} seconds.")
    except Exception as e:
        raise MediaProbeError(f"Failed to execute audio extraction: {e}")

    if proc.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
        err = _clean_ffmpeg_error(proc.stderr.strip()) or "Audio extraction produced empty or missing file."
        raise MediaProbeError(f"Audio extraction failed: {err}")

    logger.success(f"Audio extracted successfully: {dst} ({dst.stat().st_size} bytes)")
    return dst
