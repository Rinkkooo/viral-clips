"""
Kinetic Director for Science Content Factory.
Eliminates the 'slideshow' feel by generating a rapid-fire multi-angle sequence
with ~2.5s cut frequency (18 shots for a 45s video),
dynamic snap-zooms, camera shake during detonation, and flash transitions.
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageEnhance, ImageOps
from loguru import logger

from .hud_generator import generate_target_reticle_overlay, generate_warning_hud_overlay
from .sfx_engine import SFXEvent


@dataclass
class ShotConfig:
    shot_id: int
    name: str
    duration_s: float
    base_image: Path
    motion_type: str  # fast_zoom_in, snap_zoom, pan_up, pan_down, camera_shake, pull_out
    has_flash: bool = False
    hud_type: str = "none"  # "reticle", "warning", "none"
    sfx: str = "whoosh"  # "whoosh", "impact", "beep", "riser"


def prepare_multi_angle_assets(assets_dir: Path, output_cache_dir: Path) -> Dict[str, Path]:
    """
    Creates multiple distinct camera angles and crops from the primary 4 high-res scenes:
    - Extreme macro needle tip
    - Wide angle
    - Rotated dynamic angles
    - Nuclear core extreme crop
    - Dark space contrast grades
    """
    output_cache_dir.mkdir(parents=True, exist_ok=True)
    
    img1 = Image.open(assets_dir / "scene_1.jpg")  # Needle in space
    img2 = Image.open(assets_dir / "scene_2.jpg")  # Relativistic warp
    img3 = Image.open(assets_dir / "scene_3.jpg")  # Atmosphere shockwave
    img4 = Image.open(assets_dir / "scene_4.jpg")  # Fireball blast core
    
    w, h = img1.size
    
    # Angle 1A: Extreme Macro Tip
    tip_crop = img1.crop((int(w * 0.45), int(h * 0.25), int(w * 0.95), int(h * 0.55))).resize((w, h), Image.Resampling.LANCZOS)
    p_tip = output_cache_dir / "angle_needle_macro.jpg"
    tip_crop.save(p_tip, quality=95)
    
    # Angle 1B: Rotated Dynamic Needle
    rot_needle = img1.rotate(-15, expand=False).resize((w, h), Image.Resampling.LANCZOS)
    p_rot = output_cache_dir / "angle_needle_diagonal.jpg"
    rot_needle.save(p_rot, quality=95)
    
    # Angle 2A: High contrast blue warp
    enhancer = ImageEnhance.Contrast(img2)
    p_warp_high = output_cache_dir / "angle_warp_contrast.jpg"
    enhancer.enhance(1.3).save(p_warp_high, quality=95)
    
    # Angle 2B: Horizontal flip warp
    p_warp_flip = output_cache_dir / "angle_warp_inverted.jpg"
    ImageOps.mirror(img2).save(p_warp_flip, quality=95)
    
    # Angle 3A: Upper atmosphere entry point
    entry_crop = img3.crop((int(w * 0.2), 0, w, int(h * 0.7))).resize((w, h), Image.Resampling.LANCZOS)
    p_entry = output_cache_dir / "angle_entry_macro.jpg"
    entry_crop.save(p_entry, quality=95)
    
    # Angle 4A: Core detonation extreme zoom
    det_crop = img4.crop((int(w * 0.15), int(h * 0.2), int(w * 0.85), int(h * 0.8))).resize((w, h), Image.Resampling.LANCZOS)
    p_det = output_cache_dir / "angle_detonation_extreme.jpg"
    det_crop.save(p_det, quality=95)
    
    return {
        "needle_base": assets_dir / "scene_1.jpg",
        "needle_macro": p_tip,
        "needle_diag": p_rot,
        "warp_base": assets_dir / "scene_2.jpg",
        "warp_contrast": p_warp_high,
        "warp_inverted": p_warp_flip,
        "entry_base": assets_dir / "scene_3.jpg",
        "entry_macro": p_entry,
        "blast_base": assets_dir / "scene_4.jpg",
        "blast_extreme": p_det
    }


def render_kinetic_shot(
    shot: ShotConfig,
    output_clip_path: Path,
    reticle_png: Path,
    warning_png: Path,
    fps: int = 30
) -> Path:
    """
    Renders an individual kinetic shot with snap-zooms, camera shake, or flash transitions.
    """
    total_frames = int(shot.duration_s * fps)
    
    # Base motion filter
    if shot.motion_type == "camera_shake":
        # Intense explosive camera shake with noise vibration
        zoom_expr = "1.15"
        x_expr = "iw/2-(iw/zoom/2) + 20*sin(45*on) + 12*cos(35*on)"
        y_expr = "ih/2-(ih/zoom/2) + 25*cos(50*on) + 10*sin(60*on)"
    elif shot.motion_type == "snap_zoom":
        # Rapid aggressive push-in
        zoom_expr = "min(pzoom+0.0035,1.25)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif shot.motion_type == "pull_out":
        zoom_expr = "if(eq(on,0),1.22,max(pzoom-0.002,1.0))"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif shot.motion_type == "pan_up":
        zoom_expr = "1.14"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = f"ih/zoom*(1.0-0.3*(on/{total_frames}))"
    else:  # fast_zoom_in
        zoom_expr = "min(pzoom+0.0018,1.20)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
        
    vf_filters = [
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s=1080x1920:fps={fps}",
        "format=yuv420p"
    ]
    
    if shot.has_flash:
        vf_filters.append("fade=t=in:st=0:d=0.08:color=white")
        
    filter_chain = ",".join(vf_filters)
    
    # Check if HUD overlay is needed
    inputs = ["-loop", "1", "-i", str(shot.base_image)]
    if shot.hud_type == "reticle":
        inputs += ["-loop", "1", "-i", str(reticle_png)]
        filter_complex = f"[0:v]{filter_chain}[base];[base][1:v]overlay=0:0:shortest=1[vout]"
        map_args = ["-filter_complex", filter_complex, "-map", "[vout]"]
    elif shot.hud_type == "warning":
        inputs += ["-loop", "1", "-i", str(warning_png)]
        filter_complex = f"[0:v]{filter_chain}[base];[base][1:v]overlay=0:0:shortest=1[vout]"
        map_args = ["-filter_complex", filter_complex, "-map", "[vout]"]
    else:
        map_args = ["-vf", filter_chain]
        
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        *map_args,
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-b:v", "7M",
        "-t", f"{shot.duration_s:.3f}",
        "-pix_fmt", "yuv420p",
        str(output_clip_path)
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg render shot failed:\n{res.stderr}")
        
    return output_clip_path


def build_kinetic_timeline(
    total_audio_duration: float,
    assets_dir: Path,
    output_dir: Path,
    fps: int = 30
) -> Tuple[Path, List[SFXEvent]]:
    """
    Constructs the full 18-shot rapid-fire kinetic timeline and generates synchronized SFX events.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / "angles_cache"
    angles = prepare_multi_angle_assets(assets_dir, cache_dir)
    
    # Generate HUD overlays
    reticle_png = generate_target_reticle_overlay(output_dir / "reticle.png")
    warning_png = generate_warning_hud_overlay(output_dir / "warning.png")
    
    # Target 18 shots across ~46 seconds (~2.5s per shot)
    shot_templates = [
        # Act 1: Hook & Needle in Space (0.0s - 10.0s)
        ("needle_macro", 2.4, "snap_zoom", False, "reticle", "whoosh"),
        ("needle_base", 2.2, "fast_zoom_in", True, "none", "beep"),
        ("needle_diag", 2.6, "pan_up", False, "none", "whoosh"),
        ("needle_macro", 2.8, "snap_zoom", True, "none", "impact"),
        
        # Act 2: Relativistic Acceleration & Warp (10.0s - 23.0s)
        ("warp_base", 2.4, "snap_zoom", True, "none", "whoosh"),
        ("warp_contrast", 2.6, "pan_up", False, "none", "beep"),
        ("warp_inverted", 2.4, "pull_out", True, "none", "whoosh"),
        ("warp_base", 2.6, "snap_zoom", False, "none", "beep"),
        ("warp_contrast", 2.5, "fast_zoom_in", True, "none", "whoosh"),
        
        # Act 3: Atmospheric Entry & Plasma Detonation (23.0s - 34.0s)
        ("entry_base", 2.4, "fast_zoom_in", True, "reticle", "whoosh"),
        ("entry_macro", 2.5, "snap_zoom", False, "none", "beep"),
        ("entry_base", 2.4, "pull_out", True, "warning", "riser"),
        ("blast_extreme", 2.2, "snap_zoom", True, "warning", "whoosh"),
        ("blast_base", 2.8, "camera_shake", True, "none", "impact"),
        
        # Act 4: Planetary Explosion Climax & Aftermath (34.0s - End)
        ("blast_extreme", 2.8, "camera_shake", False, "none", "impact"),
        ("blast_base", 3.2, "pull_out", True, "none", "whoosh"),
        ("entry_base", 3.2, "pan_up", False, "none", "beep"),
        ("needle_base", 4.0, "pull_out", True, "none", "whoosh"),
    ]
    
    # Scale shot durations proportionally to match exact audio duration
    template_total = sum(d for _, d, _, _, _, _ in shot_templates)
    scale = total_audio_duration / template_total
    
    shots: List[ShotConfig] = []
    sfx_events: List[SFXEvent] = []
    current_time = 0.0
    
    for idx, (img_key, dur, motion, flash, hud, sfx_name) in enumerate(shot_templates):
        scaled_dur = round(dur * scale, 3)
        img_path = angles[img_key]
        
        shots.append(ShotConfig(
            shot_id=idx + 1,
            name=f"shot_{idx + 1:02d}",
            duration_s=scaled_dur,
            base_image=img_path,
            motion_type=motion,
            has_flash=flash,
            hud_type=hud,
            sfx=sfx_name
        ))
        
        sfx_events.append(SFXEvent(
            name=sfx_name,
            time_s=round(current_time, 2),
            volume=1.0 if sfx_name == "impact" else 0.75
        ))
        
        current_time += scaled_dur
        
    logger.info(f"Rendering {len(shots)} kinetic shots (avg duration: {total_audio_duration/len(shots):.2f}s per shot)...")
    
    clip_paths = []
    for s in shots:
        clip_p = output_dir / f"{s.name}.mp4"
        render_kinetic_shot(
            shot=s,
            output_clip_path=clip_p,
            reticle_png=reticle_png,
            warning_png=warning_png,
            fps=fps
        )
        clip_paths.append(clip_p)
        
    concat_file = output_dir / "kinetic_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for c in clip_paths:
            f.write(f"file '{c.resolve().as_posix()}'\n")
            
    master_video = output_dir / "master_kinetic_visual.mp4"
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
        raise RuntimeError(f"FFmpeg concat kinetic clips failed:\n{res.stderr}")
        
    logger.success(f"Master kinetic timeline assembled: {master_video.name}")
    return master_video, sfx_events
