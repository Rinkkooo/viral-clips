"""
Master End-to-End Runner for Long-Form Science Documentary (16:9 Full HD 1080p).
Theme: "Что произойдет, если швейная игла врежется в Землю на скорости света?"
Features:
- 7 narrative chapters (polished scientific storytelling)
- Real NASA 1080p video footage (ISS orbit, solar plasma, fireball entry)
- Procedural 3D/scientific animations (Lorentz curve & velocity gauge)
- Neural Russian voiceover (ru-RU-DmitryNeural) with word boundaries
- 3-track cinematic audio (Voice + Sci-Fi Drone Soundtrack + Realistic Sub-Bass Impacts/Whooshes)
- Lower-third chapter banners and kinetic 16:9 subtitles
- 100% local hardware rendering via NVIDIA NVENC (RTX 4060)
"""

import sys
import os
import json
import asyncio
import subprocess
import wave
import struct
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# Ensure package imports resolve
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.science_factory.audio_engine import synthesize_voice_with_timings, generate_scifi_ambient_track, WordTiming
from src.science_factory.sfx_engine import SFXEvent, build_master_sfx_track
from src.science_factory.procedural_graphics_engine import render_lorentz_curve_animation, render_speed_comparison_animation
from src.science_factory.subtitles_generator import generate_documentary_16x9_subtitles
from src.science_factory.longform_compositor import build_longform_visual_track, compose_longform_documentary


def mp3_to_wav(mp3_path: Path, wav_path: Path, sample_rate: int = 44100):
    """Converts MP3 to 16-bit 44.1kHz stereo WAV via FFmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(mp3_path),
        "-ar", str(sample_rate),
        "-ac", "2",
        str(wav_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg MP3->WAV conversion error:\n{res.stderr}")


def get_wav_duration(wav_path: Path) -> float:
    """Returns the duration of a WAV file in seconds."""
    with wave.open(str(wav_path), 'rb') as w:
        frames = w.getnframes()
        rate = w.getframerate()
        return frames / float(rate)


def create_silence_wav(output_path: Path, duration_s: float, sample_rate: int = 44100):
    """Creates a stereo silence WAV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(duration_s * sample_rate)
    with wave.open(str(output_path), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        # 4 bytes per sample (2 bytes left + 2 bytes right)
        wav.writeframes(b'\x00' * (num_samples * 4))


def concatenate_wav_files(wav_list: List[Path], output_path: Path):
    """Concatenates multiple stereo 44.1kHz 16-bit WAV files into one."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), 'wb') as outfile:
        outfile.setnchannels(2)
        outfile.setsampwidth(2)
        outfile.setframerate(44100)
        
        for w_path in wav_list:
            with wave.open(str(w_path), 'rb') as infile:
                outfile.writeframes(infile.readframes(infile.getnframes()))


async def run_full_documentary_pipeline():
    logger.info("=================================================================")
    logger.info("  STARTING AUTONOMOUS AI SCIENCE CONTENT FACTORY: LONG-FORM DOC")
    logger.info("=================================================================")
    
    workspace_dir = SRC_DIR / "workspace_longform"
    audio_dir = workspace_dir / "audio"
    visuals_dir = workspace_dir / "visuals"
    broll_dir = SRC_DIR / "video_broll"
    
    workspace_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)
    
    final_output_path = Path(r"C:\Users\user\Downloads\science_needle_documentary.mp4")
    
    # 1. Load Master Script
    script_path = workspace_dir / "script.json"
    if not script_path.exists():
        raise FileNotFoundError(f"Script file not found: {script_path}")
    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
        
    chapters = script_data.get("chapters", [])
    logger.info(f"Loaded script: '{script_data.get('title')}' with {len(chapters)} chapters.")
    
    # 2. Synthesize Chapter Audio Tracks with Word Boundaries
    logger.info("--- STEP 1: Synthesizing Neural Voiceover (ru-RU-DmitryNeural) ---")
    all_words: List[WordTiming] = []
    chapter_segments: List[Dict[str, Any]] = []
    wav_files_to_concat: List[Path] = []
    
    current_time_offset = 0.0
    silence_between_chapters_s = 1.4
    
    silence_path = audio_dir / "silence_gap.wav"
    create_silence_wav(silence_path, silence_between_chapters_s)
    
    for ch in chapters:
        ch_num = ch["chapter_num"]
        ch_title = ch["title"]
        ch_theme = ch.get("theme", "earth_orbit")
        ch_text = ch["text"]
        
        mp3_out = audio_dir / f"chapter_{ch_num:02d}.mp3"
        wav_out = audio_dir / f"chapter_{ch_num:02d}.wav"
        words_cache = audio_dir / f"chapter_{ch_num:02d}_words.json"
        
        if wav_out.exists() and words_cache.exists():
            logger.info(f"Using cached voice & timings for Chapter {ch_num}...")
            words = [WordTiming(**d) for d in json.loads(words_cache.read_text(encoding="utf-8"))]
        else:
            words, raw_dur = await synthesize_voice_with_timings(
                text=ch_text,
                output_voice_path=mp3_out,
                voice="ru-RU-DmitryNeural",
                rate="+0%"
            )
            mp3_to_wav(mp3_out, wav_out)
            words_cache.write_text(json.dumps([w.__dict__ for w in words], ensure_ascii=False), encoding="utf-8")
            
        exact_dur = get_wav_duration(wav_out)
        
        # Scale word timings to exact WAV duration to prevent cross-chapter leakage
        raw_words_end = words[-1].end if words else 1.0
        time_scale = (exact_dur / raw_words_end) if raw_words_end > 0 else 1.0
        
        # Shift and scale word timings by current chapter offset
        for w in words:
            shifted_word = WordTiming(
                word=w.word,
                start=round(w.start * time_scale + current_time_offset, 3),
                end=round(w.end * time_scale + current_time_offset, 3),
                duration=round(w.duration * time_scale, 3)
            )
            all_words.append(shifted_word)
            
        ch_info = {
            "chapter_num": ch_num,
            "title": ch_title,
            "theme": ch_theme,
            "start_s": current_time_offset,
            "start_ms": int(current_time_offset * 1000),
            "duration_s": exact_dur + silence_between_chapters_s,
            "voice_duration_s": exact_dur
        }
        chapter_segments.append(ch_info)
        wav_files_to_concat.append(wav_out)
        wav_files_to_concat.append(silence_path)
        
        current_time_offset += exact_dur + silence_between_chapters_s
        logger.success(f"  Chapter {ch_num} rendered: {exact_dur:.1f}s (Cumulative: {current_time_offset / 60.0:.2f} min)")
        
    master_voice_wav = audio_dir / "voice_master.wav"
    concatenate_wav_files(wav_files_to_concat, master_voice_wav)
    total_duration_s = current_time_offset
    logger.success(f"Master voice track assembled: {master_voice_wav} ({total_duration_s:.1f}s / {total_duration_s/60.0:.2f} min)")
    
    # 3. Generate Sci-Fi Ambient Soundtrack
    logger.info("--- STEP 2: Synthesizing Sci-Fi Ambient Drone & Pad Soundtrack ---")
    ambient_wav = audio_dir / "ambient_master.wav"
    generate_scifi_ambient_track(ambient_wav, total_duration_s + 2.0)
    logger.success(f"Ambient soundtrack generated: {ambient_wav}")
    
    # 4. Generate Cinematic Realistic SFX Track
    logger.info("--- STEP 3: Synthesizing Realistic Cinematic Sound Design (No Beeps) ---")
    sfx_events: List[SFXEvent] = []
    for ch in chapter_segments:
        # Chapter transition whoosh
        sfx_events.append(SFXEvent("whoosh", max(0.0, ch["start_s"] - 0.2), volume=0.85))
        # Dramatic sub-bass impacts at key plot points
        if ch["chapter_num"] in [1, 4, 5]:
            sfx_events.append(SFXEvent("impact", ch["start_s"] + 0.3, volume=1.0))
            
    sfx_wav = audio_dir / "sfx_master.wav"
    build_master_sfx_track(sfx_events, total_duration_s, sfx_wav)
    logger.success(f"Master SFX track rendered: {sfx_wav} with {len(sfx_events)} cinematic events")
    
    # 5. Render Procedural 3D/Scientific Video Animations
    logger.info("--- STEP 4: Rendering Procedural Scientific Animations (Cyrillic Fonts) ---")
    anim_speed = visuals_dir / "anim_speed_comparison.mp4"
    anim_lorentz = visuals_dir / "anim_lorentz_curve.mp4"
    
    if not anim_speed.exists() or anim_speed.stat().st_size == 0:
        logger.info("Rendering animated speed comparison scale (40s)...")
        render_speed_comparison_animation(anim_speed, duration_s=40.0)
    else:
        logger.info(f"Using cached speed comparison animation: {anim_speed}")
        
    if not anim_lorentz.exists() or anim_lorentz.stat().st_size == 0:
        logger.info("Rendering animated relativistic Lorentz curve (40s)...")
        render_lorentz_curve_animation(anim_lorentz, duration_s=40.0)
    else:
        logger.info(f"Using cached Lorentz curve animation: {anim_lorentz}")
        
    # 6. Assemble 16:9 Full HD Visual Track
    logger.info("--- STEP 5: Slicing and Concatenating 16:9 Video Timeline ---")
    video_sources = {
        "earth_orbit": broll_dir / "broll_earth_orbit.mp4",
        "solar_plasma": broll_dir / "broll_solar_plasma.mp4",
        "black_hole": broll_dir / "broll_black_hole.mp4",
        "speed_anim": anim_speed,
        "lorentz_anim": anim_lorentz
    }
    
    # Verify all sources exist
    for k, v in video_sources.items():
        if not v.exists():
            raise FileNotFoundError(f"Missing required video source '{k}': {v}")
            
    visual_master_video = visuals_dir / "visual_master.mp4"
    build_longform_visual_track(
        chapter_segments=chapter_segments,
        video_sources=video_sources,
        output_master_video=visual_master_video,
        fps=30
    )
    
    # 7. Generate 16:9 Subtitles with Lower-Third Chapter Cards
    logger.info("--- STEP 6: Generating 16:9 Documentary Subtitles ---")
    subtitles_ass = workspace_dir / "documentary_subtitles.ass"
    generate_documentary_16x9_subtitles(
        words=all_words,
        chapters=chapter_segments,
        output_ass_path=subtitles_ass,
        words_per_line=5
    )
    logger.success(f"16:9 Subtitles written: {subtitles_ass}")
    
    # 8. Composite Final Long-Form Documentary via NVENC
    logger.info("--- STEP 7: Compositing Master Documentary (NVENC RTX 4060) ---")
    compose_longform_documentary(
        visual_video_path=visual_master_video,
        voice_audio_path=master_voice_wav,
        ambient_music_path=ambient_wav,
        sfx_audio_path=sfx_wav,
        subtitles_ass_path=subtitles_ass,
        output_path=final_output_path,
        voice_volume=1.35,
        music_volume=0.22,
        sfx_volume=0.80
    )
    
    logger.info("=================================================================")
    logger.success(f"🎬 DOCUMENTARY COMPLETED SUCCESSFULLY!")
    logger.success(f"📁 Output: {final_output_path}")
    logger.info("=================================================================")
    return final_output_path


if __name__ == "__main__":
    asyncio.run(run_full_documentary_pipeline())
