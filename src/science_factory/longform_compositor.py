"""
Long-Form Documentary Compositor for Science Content Factory.
Assembles 16:9 Full HD (1920x1080) documentary films:
- Mixes real NASA 1080p footage and procedural 3D scientific animations
- Dynamic chapter title cards (lower-thirds)
- 3-track audio mix: Neural Voice + Ambient Soundtrack + Cinematic SFX
- Fast hardware acceleration via NVIDIA NVENC
"""

from pathlib import Path
import subprocess
from typing import List, Dict, Any
from loguru import logger


def build_longform_visual_track(
    chapter_segments: List[Dict[str, Any]],
    video_sources: Dict[str, Path],
    output_master_video: Path,
    fps: int = 30
) -> Path:
    """
    Slices and concatenates real video footage and animations across all chapters.
    """
    output_dir = output_master_video.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    clip_paths: List[Path] = []
    
    # Theme to video source mapping
    theme_map = {
        "space_needle": ["earth_orbit", "solar_plasma"],
        "speed_comparison": ["speed_anim", "earth_orbit"],
        "lorentz_curve": ["lorentz_anim", "solar_plasma"],
        "atmosphere_entry": ["solar_plasma", "earth_orbit"],
        "nuclear_plasma": ["solar_plasma", "earth_orbit"],
        "black_hole": ["black_hole", "solar_plasma"],
        "earth_orbit": ["earth_orbit", "solar_plasma"]
    }
    
    for ch_idx, ch in enumerate(chapter_segments):
        ch_num = ch["chapter_num"]
        ch_dur = ch["duration_s"]
        theme = ch.get("theme", "earth_orbit")
        sources_keys = theme_map.get(theme, ["earth_orbit", "solar_plasma"])
        
        # Split chapter into 2-3 cuts of 5-8 seconds each
        num_cuts = max(2, int(ch_dur / 6.5))
        sub_dur = ch_dur / num_cuts
        
        for cut_idx in range(num_cuts):
            source_key = sources_keys[cut_idx % len(sources_keys)]
            src_file = video_sources.get(source_key, video_sources.get("earth_orbit"))
            
            clip_out = output_dir / f"ch_{ch_num:02d}_cut_{cut_idx + 1:02d}.mp4"
            # Base start offset tailored per source to ensure 100% clean footage
            if source_key == "black_hole":
                base_start = 50.0
            elif source_key in ["speed_anim", "lorentz_anim"]:
                base_start = 0.0
            else:
                base_start = 12.0
            start_offset = base_start + (ch_idx * 14 + cut_idx * 7) % 35
            
            # Scale & crop: slight 14% zoom on b-roll to remove any corner labels/watermarks, 1:1 on animations
            if source_key in ["speed_anim", "lorentz_anim"]:
                vf = "scale=1920:1080,fps=30,format=yuv420p"
            else:
                vf = "scale=2200:1238:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,format=yuv420p"
            
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-ss", f"{start_offset:.2f}",
                "-i", str(src_file),
                "-t", f"{sub_dur:.3f}",
                "-vf", vf,
                "-c:v", "h264_nvenc",
                "-preset", "p4",
                "-b:v", "8M",
                "-pix_fmt", "yuv420p",
                "-an",
                str(clip_out)
            ]
            
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                logger.error(f"Failed cutting clip {clip_out.name}:\n{res.stderr}")
                raise RuntimeError(f"FFmpeg slice error:\n{res.stderr}")
                
            clip_paths.append(clip_out)
            
    # Concatenate all cuts
    concat_txt = output_dir / "longform_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve().as_posix()}'\n")
            
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(output_master_video)
    ]
    
    logger.info("Concatenating all chapter video cuts into master visual track...")
    res = subprocess.run(cmd_concat, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed:\n{res.stderr}")
        
    logger.success(f"Master visual track assembled: {output_master_video}")
    return output_master_video


def compose_longform_documentary(
    visual_video_path: Path,
    voice_audio_path: Path,
    ambient_music_path: Path,
    sfx_audio_path: Path,
    subtitles_ass_path: Path,
    output_path: Path,
    voice_volume: float = 1.25,
    music_volume: float = 0.22,
    sfx_volume: float = 0.85
) -> Path:
    """
    Renders the final 16:9 1080p documentary with 3-track audio mix and subtitles via NVENC.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    ass_escaped = str(subtitles_ass_path.resolve().as_posix()).replace(":", r"\:")
    vf_filter = f"ass='{ass_escaped}'"
    
    af_filter = (
        f"[1:a]volume={voice_volume}[v];"
        f"[2:a]volume={music_volume}[m];"
        f"[3:a]volume={sfx_volume}[sfx];"
        f"[v][m][sfx]amix=inputs=3:duration=first:dropout_transition=4[aout]"
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
        "-b:v", "8M",
        "-maxrate", "12M",
        "-bufsize", "16M",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "44100",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ]
    
    logger.info(f"Rendering full documentary via h264_nvenc -> {output_path.name}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error(f"Compositing failed:\n{res.stderr}")
        raise RuntimeError(f"Compositing failed:\n{res.stderr}")
        
    logger.success(f"Final documentary successfully composed: {output_path}")
    return output_path
