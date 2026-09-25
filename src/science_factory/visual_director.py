"""
Visual Director for Science Content Factory.
Renders high-resolution 9:16 vertical animated clips with cinematic Ken Burns motion
(zoom-in, zoom-out, pan-up) using hardware-accelerated NVIDIA NVENC.
"""

from pathlib import Path
import subprocess
from typing import List, Dict, Any


def render_scene_clip(
    image_path: Path,
    output_clip_path: Path,
    duration_s: float,
    motion_type: str = "zoom_in",
    fps: int = 30
) -> Path:
    """
    Renders an animated 9:16 vertical clip from an image using FFmpeg zoompan.
    """
    total_frames = int(duration_s * fps)
    
    # Configure zoompan expressions for 1080x1920 (9:16)
    if motion_type == "zoom_in":
        # Start at 1.0 zoom, slowly push to 1.15
        zoom_expr = "min(pzoom+0.0008,1.18)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion_type == "zoom_out":
        # Start at 1.18 zoom, slowly pull out to 1.0
        zoom_expr = "if(eq(on,0),1.18,max(pzoom-0.0008,1.0))"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion_type == "pan_up":
        # Slow pan upward along the frame
        zoom_expr = "1.12"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = f"ih/zoom*(1.0-0.4*(on/{total_frames}))"
    else:  # Static with subtle breathing
        zoom_expr = "min(pzoom+0.0004,1.08)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
        
    vf_filter = (
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
        f"d={total_frames}:s=1080x1920:fps={fps},"
        f"format=yuv420p"
    )
    
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", vf_filter,
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-b:v", "6M",
        "-t", f"{duration_s:.3f}",
        "-pix_fmt", "yuv420p",
        str(output_clip_path)
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg render_scene_clip failed:\n{res.stderr}")
        
    return output_clip_path


def render_full_visual_timeline(
    scenes: List[Dict[str, Any]],
    output_dir: Path,
    fps: int = 30
) -> Path:
    """
    Renders all individual scene clips and concatenates them into master visual stream.
    scenes format: [{'image_path': Path, 'duration_s': float, 'motion': str}, ...]
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    clips: List[Path] = []
    
    for idx, sc in enumerate(scenes):
        clip_path = output_dir / f"scene_{idx + 1}.mp4"
        render_scene_clip(
            image_path=sc["image_path"],
            output_clip_path=clip_path,
            duration_s=sc["duration_s"],
            motion_type=sc.get("motion", "zoom_in"),
            fps=fps
        )
        clips.append(clip_path)
        
    # Create concat list
    concat_file = output_dir / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for c in clips:
            # Escape path for ffmpeg concat
            f.write(f"file '{c.resolve().as_posix()}'\n")
            
    master_video = output_dir / "master_visual.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(master_video)
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed:\n{res.stderr}")
        
    return master_video
