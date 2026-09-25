"""
AI Science Content Factory - Master Autonomous Pipeline V2 (High-Density Shorts Edition).
Executes End-to-End:
1. Fact Check & Physics Grounding
2. Script & Hook Multiplier
3. Neural Voiceover & Ambient Soundtrack
4. Kinetic Pop Subtitles with Real-Time Top HUD Telemetry
5. 18-Shot Rapid-Fire Visual Timeline (Snap-Zooms, Camera Shake, Flash Cuts)
6. Synchronized Procedural SFX Track (Whooshes, Impacts, Beeps, Risers)
7. 3-Track Master Audio Mix & Hardware NVENC Compositing
"""

from pathlib import Path
import time
from loguru import logger

from .fact_checker import calculate_relativistic_impact
from .script_generator import build_needle_lightspeed_script
from .audio_engine import build_audio_package
from .subtitles_generator import generate_science_karaoke_subtitles
from .kinetic_director import build_kinetic_timeline
from .sfx_engine import build_master_sfx_track
from .compositor import compose_final_video_v2


def run_science_factory_pipeline_v2(
    hook_variant_idx: int = 0,
    output_final_path: Path = Path(r"C:\Users\user\Downloads\science_needle_lightspeed_v2.mp4"),
    work_dir: Path = Path(r"C:\Users\user\Desktop\viral_clips\src\science_factory\workspace_v2")
) -> Path:
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("STARTING AI SCIENCE CONTENT FACTORY V2 (RAPID-FIRE PACING)")
    logger.info("=" * 60)
    
    work_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = Path(r"C:\Users\user\Desktop\viral_clips\src\science_factory\assets")
    
    # 1. Fact Checking & Scientific Grounding
    logger.info("[Step 1/7] Fact Checking & Grounding Relativistic Physics...")
    facts = calculate_relativistic_impact(mass_mg=5.0, velocity_fraction=0.999999999)
    logger.info(f"Verified Physics: Lorentz Gamma = {facts.lorentz_gamma:,}, Kinetic Energy = {facts.tnt_equivalent_tons:.1f} tons TNT")
    
    # 2. Script Generation
    logger.info("[Step 2/7] Generating High-Retention Script & Storyboard...")
    script = build_needle_lightspeed_script(hook_variant_idx=hook_variant_idx)
    logger.info(f"Selected Hook #{hook_variant_idx + 1}: '{script.selected_hook}'")
    
    # 3. Audio Synthesis & Word Boundaries
    logger.info("[Step 3/7] Synthesizing Neural Voiceover & Ambient Soundtrack...")
    audio_res = build_audio_package(
        text=script.full_text,
        output_dir=work_dir / "audio",
        voice="ru-RU-DmitryNeural"
    )
    total_audio_duration = audio_res.duration_s
    logger.success(f"Audio synthesized: {len(audio_res.words)} words, total length: {total_audio_duration:.2f}s")
    
    # 4. Kinetic Subtitles & Top HUD Telemetry
    logger.info("[Step 4/7] Generating Kinetic Pop Subtitles + Top Scientific Telemetry HUD...")
    subtitles_path = work_dir / "subtitles_v2.ass"
    generate_science_karaoke_subtitles(
        words=audio_res.words,
        output_ass_path=subtitles_path,
        words_per_line=3
    )
    logger.success(f"Kinetic subtitles generated: {subtitles_path.name}")
    
    # 5. 18-Shot Rapid-Fire Visual Timeline (Camera Shake, Snap-Zooms, Flash Cuts)
    logger.info("[Step 5/7] Building 18-Shot Rapid-Fire Visual Timeline (~2.5s cuts)...")
    master_visual, sfx_events = build_kinetic_timeline(
        total_audio_duration=total_audio_duration,
        assets_dir=assets_dir,
        output_dir=work_dir / "visuals",
        fps=30
    )
    logger.success(f"Master kinetic video assembled: {master_visual.name}")
    
    # 6. Procedural SFX Track Synthesis
    logger.info(f"[Step 6/7] Synthesizing {len(sfx_events)} Synchronized Sound Effects (Whooshes, Impacts, Beeps, Risers)...")
    sfx_track_path = work_dir / "sfx_master.wav"
    build_master_sfx_track(
        events=sfx_events,
        total_duration_s=total_audio_duration,
        output_path=sfx_track_path
    )
    logger.success(f"SFX audio track synthesized: {sfx_track_path.name}")
    
    # 7. Master Compositing with 3 Audio Tracks via NVENC
    logger.info("[Step 7/7] Compositing 18-Shot Video, 3-Track Audio & Subtitles via NVENC...")
    final_video = compose_final_video_v2(
        visual_video_path=master_visual,
        voice_audio_path=audio_res.voice_path,
        ambient_music_path=audio_res.music_path,
        sfx_audio_path=sfx_track_path,
        subtitles_ass_path=subtitles_path,
        output_path=output_final_path
    )
    
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.success(f"REEL V2 SUCCESSFULLY GENERATED IN {elapsed:.2f}s!")
    logger.success(f"OUTPUT PATH: {final_video}")
    logger.info("=" * 60)
    
    return final_video


if __name__ == "__main__":
    run_science_factory_pipeline_v2(0)
