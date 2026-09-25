"""
Master Video Compositor for Science Content Factory V2.
Binds 18-shot kinetic video stream, 3-track audio (voiceover + ambient soundtrack + synchronized SFX),
and burns in animated kinetic subtitles via NVIDIA NVENC.
"""

from pathlib import Path
import subprocess
from loguru import logger


def compose_final_video_v2(
    visual_video_path: Path,
    voice_audio_path: Path,
    ambient_music_path: Path,
    sfx_audio_path: Path,
    subtitles_ass_path: Path,
    output_path: Path,
    voice_volume: float = 1.25,
    music_volume: float = 0.20,
    sfx_volume: float = 0.85
) -> Path:
    """
    Renders the final viral 9:16 short video with 3-track audio mix and NVENC acceleration.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Escape ASS path for FFmpeg filtergraph on Windows
    ass_escaped = str(subtitles_ass_path.resolve().as_posix()).replace(":", r"\:")
    
    # Video filter: Burn ASS subtitles
    vf_filter = f"ass='{ass_escaped}'"
    
    # Audio filter: 3-way mix (Voice + Music + SFX)
    af_filter = (
        f"[1:a]volume={voice_volume}[v];"
        f"[2:a]volume={music_volume}[m];"
        f"[3:a]volume={sfx_volume}[sfx];"
        f"[v][m][sfx]amix=inputs=3:duration=first:dropout_transition=3[aout]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(visual_video_path),
        "-i", str(voice_audio_path),
        "-i", str(ambient_music_path),
        "-i", str(sfx_audio_path),
        "-filter_complex", f"[0:v]{vf_filter}[vout];{af_filter}",
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-b:v", "9M",
        "-maxrate", "14M",
        "-bufsize", "18M",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "44100",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ]
    
    logger.info(f"Rendering master video V2 via h264_nvenc -> {output_path.name}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if res.returncode != 0:
        logger.error(f"FFmpeg compositing failed:\n{res.stderr}")
        raise RuntimeError(f"FFmpeg compositing error:\n{res.stderr}")
        
    logger.success(f"Final video V2 successfully composed: {output_path}")
    return output_path
