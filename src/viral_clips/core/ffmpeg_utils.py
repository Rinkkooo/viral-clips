"""
FFmpeg and FFprobe binary locator and hardware acceleration detector.
Ensures resilient discovery across Windows PATH, WinGet, and local virtualenvs.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from loguru import logger

from viral_clips.config import settings


def find_binary(binary_name: str) -> Optional[str]:
    """Find the path of a binary across PATH, common directories, and packages."""
    # 1. Try static_ffmpeg if available
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except Exception:
        pass

    # 2. Check settings
    configured = getattr(settings, f"{binary_name}_path", None)
    if configured and shutil.which(configured):
        return shutil.which(configured)
    if configured and Path(configured).is_file():
        return str(Path(configured).resolve())

    # 3. System PATH
    found = shutil.which(binary_name)
    if found:
        return found

    # 4. Check Windows WinGet directory
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        winget_dir = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            for match in winget_dir.glob(f"**/bin/{binary_name}.exe"):
                if match.is_file():
                    return str(match.resolve())
            for match in winget_dir.glob(f"**/{binary_name}.exe"):
                if match.is_file():
                    return str(match.resolve())

    # 5. Check Program Files
    for prog_dir in ["C:\\Program Files\\ffmpeg\\bin", "C:\\ffmpeg\\bin"]:
        candidate = Path(prog_dir) / f"{binary_name}.exe"
        if candidate.is_file():
            return str(candidate.resolve())

    # 6. Imageio fallback for ffmpeg
    if binary_name == "ffmpeg":
        try:
            import imageio_ffmpeg
            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and Path(exe).is_file():
                return exe
        except Exception:
            pass

    return None


def get_ffmpeg_path() -> str:
    path = find_binary("ffmpeg")
    if not path:
        raise RuntimeError("FFmpeg executable not found. Please ensure FFmpeg is installed and accessible.")
    return path


def get_ffprobe_path() -> str:
    path = find_binary("ffprobe")
    if not path:
        # If ffmpeg was found in a directory, check if ffprobe is in the same directory
        ffmpeg_p = find_binary("ffmpeg")
        if ffmpeg_p:
            sibling = Path(ffmpeg_p).parent / "ffprobe.exe"
            if sibling.is_file():
                return str(sibling.resolve())
        raise RuntimeError("FFprobe executable not found. Please ensure FFprobe is installed.")
    return path


def check_nvenc_support() -> bool:
    """Checks if NVIDIA h264_nvenc encoder is supported by FFmpeg installation."""
    try:
        ffmpeg = get_ffmpeg_path()
        result = subprocess.run(
            [ffmpeg, "-encoders"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        return "h264_nvenc" in result.stdout
    except Exception as e:
        logger.warning(f"Failed to check NVENC support: {e}")
        return False
