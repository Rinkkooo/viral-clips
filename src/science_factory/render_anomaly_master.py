import os
import sys
import json
import math
import wave
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    from .bio_audio_engine import (
        generate_heartbeat, generate_dark_drone,
        generate_head_explosion_sfx, generate_transition_impact, save_wav
    )
    from .medical_graphics_engine import (
        render_ecg_frame, render_eeg_frame, render_fmri_slice_frame,
        render_dossier_card_frame
    )
except ImportError:
    from bio_audio_engine import (
        generate_heartbeat, generate_dark_drone,
        generate_head_explosion_sfx, generate_transition_impact, save_wav
    )
    from medical_graphics_engine import (
        render_ecg_frame, render_eeg_frame, render_fmri_slice_frame,
        render_dossier_card_frame
    )

WORKSPACE_DIR = r"C:\Users\user\Desktop\viral_clips\src\science_factory\workspace_anomalies"
MANIFEST_PATH = r"C:\Users\user\Desktop\viral_clips\src\science_factory\assets\anomaly_narration\anomaly_chapters_manifest.json"
FINAL_DOC_PATH = r"C:\Users\user\Downloads\mind_anomalies_documentary.mp4"

os.makedirs(WORKSPACE_DIR, exist_ok=True)

def load_audio_as_numpy(wav_or_mp3_path, target_sr=44100):
    """
    Decodes audio file to mono float32 numpy array using ffmpeg pipe.
    """
    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", wav_or_mp3_path,
        "-f", "s16le", "-ac", "1", "-ar", str(target_sr), "-"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw_data, _ = proc.communicate()
    samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
    return samples

def build_chapter_audio(ch, output_wav_path, sample_rate=44100):
    """
    Mixes voiceover + custom heartbeat + dark drone + SFX.
    """
    voice = load_audio_as_numpy(ch["audio_path"], target_sr=sample_rate)
    duration_s = max(len(voice) / sample_rate, ch["duration"])
    n_samples = int(duration_s * sample_rate)
    
    # Pad voice if needed
    if len(voice) < n_samples:
        voice = np.pad(voice, (0, n_samples - len(voice)))
    else:
        voice = voice[:n_samples]
        
    # 1. Dark ambient drone
    drone = generate_dark_drone(duration_s, sample_rate=sample_rate)
    if len(drone) < n_samples:
        drone = np.pad(drone, (0, n_samples - len(drone)))
    else:
        drone = drone[:n_samples]
        
    # 2. Heartbeat tailored to chapter
    ch_id = ch["id"]
    if ch_id == "intro":
        hb = generate_heartbeat(duration_s, start_bpm=70, end_bpm=75, sample_rate=sample_rate)
    elif ch_id == "ch1_paralysis":
        hb = generate_heartbeat(duration_s, start_bpm=78, end_bpm=142, sample_rate=sample_rate)
    elif ch_id == "ch2_alien_hand":
        hb = generate_heartbeat(duration_s, start_bpm=85, end_bpm=115, sample_rate=sample_rate)
    elif ch_id == "ch3_exploding_head":
        hb = generate_heartbeat(duration_s, start_bpm=80, end_bpm=130, sample_rate=sample_rate)
    elif ch_id == "ch4_fatal_insomnia":
        hb = generate_heartbeat(duration_s, start_bpm=100, end_bpm=125, sample_rate=sample_rate)
    elif ch_id == "ch5_cotard":
        flat_time = duration_s * 0.70
        hb = generate_heartbeat(duration_s, start_bpm=65, end_bpm=35, flatline_at=flat_time, sample_rate=sample_rate)
    else: # outro
        hb = generate_heartbeat(duration_s, start_bpm=72, end_bpm=68, sample_rate=sample_rate)
        
    if len(hb) < n_samples:
        hb = np.pad(hb, (0, n_samples - len(hb)))
    else:
        hb = hb[:n_samples]
        
    # 3. Transition impact at the beginning (0.0s)
    impact = generate_transition_impact(sample_rate=sample_rate)
    sfx_track = np.zeros(n_samples, dtype=np.float32)
    imp_len = min(len(impact), n_samples)
    sfx_track[:imp_len] += impact[:imp_len] * 0.75
    
    # 4. Special chapter SFX
    if ch_id == "ch3_exploding_head":
        # Sudden head explosion at t=9.5s
        expl_sfx = generate_head_explosion_sfx(sample_rate=sample_rate)
        t_expl_idx = int(9.5 * sample_rate)
        expl_len = min(len(expl_sfx), n_samples - t_expl_idx)
        if expl_len > 0:
            sfx_track[t_expl_idx:t_expl_idx + expl_len] += expl_sfx[:expl_len] * 0.95
            
    # Master mix: voice (-2 dB), heartbeat (-11 dB), drone (-16 dB), sfx (-4 dB)
    master = (voice * 0.92) + (hb * 0.32) + (drone * 0.18) + (sfx_track * 0.65)
    master = np.tanh(master) * 0.92
    
    save_wav(output_wav_path, master, sample_rate=sample_rate, channels=2)
    print(f"[OK] Master audio mixed: {output_wav_path} ({duration_s:.2f}s)")
    return duration_s

def ms_to_ass(ms):
    ms = max(0, int(ms))
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    cs = (ms % 1000) // 10
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def generate_chapter_ass_subtitles(ch, output_ass_path):
    """
    Builds ASS karaoke subtitles with active word pop scaling.
    """
    words = ch.get("words", [])
    if not words:
        # Fallback empty subtitle
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\nScriptType: v4.00+\n[Events]\n")
        return
        
    header = f"""[Script Info]
Title: Anomaly Documentary Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,52,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2.0,2,60,60,85,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # Chunk words into groups of 3-4 words
    chunk_size = 4
    events = []
    
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        start_ms = int(chunk[0]["start"] * 1000)
        end_ms = int(chunk[-1]["end"] * 1000) + 120
        start_str = ms_to_ass(start_ms)
        end_str = ms_to_ass(end_ms)
        
        # Build kinetic karaoke line
        line_parts = []
        for w in chunk:
            w_start_rel = int((w["start"] * 1000) - start_ms)
            w_dur = int(w["duration"] * 1000)
            clean_word = w["word"].strip()
            
            # Highlight special terms in red or gold
            is_critical = any(k in clean_word.upper() for k in ["ПАРАЛИЧ", "КОШМАР", "ЧУЖОЙ", "ВЗРЫВ", "БЕССОННИЦА", "МЕРТВЕЦ", "СМЕРТЬ", "МОЗГ"])
            pop_tag = r"{\fscx112\fscy112\t(0,70,\fscx100\fscy100)}"
            if is_critical:
                color_tag = r"{\c&H002040FF&}" # Neon Red
            else:
                color_tag = r"{\c&H0000FFFF&}" # Electric Cyan/Gold
                
            line_parts.append(f"{color_tag}{pop_tag}{clean_word}" + r"{\c&H00FFFFFF&}")
            
        text_line = " ".join(line_parts)
        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_line}")
        
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")
    print(f"[OK] Generated ASS subtitles: {output_ass_path} ({len(events)} lines)")

def extract_broll_subclip(broll_path, start_time, duration, output_path, fps=30):
    """
    Extracts a dynamic subclip from broll video, scales to 1920x1080 with seamless looping.
    """
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-stream_loop", "-1",
        "-ss", f"{start_time:.2f}",
        "-t", f"{duration:.2f}",
        "-i", broll_path,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1",
        "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20",
        "-r", str(fps), "-pix_fmt", "yuv420p",
        "-an", output_path
    ]
    subprocess.run(cmd, check=True)

def render_procedural_subclip(vfx_type, duration, output_path, fps=30, **kwargs):
    """
    Renders procedural medical graphics clip (ECG, EEG, fMRI, Dossier) directly to H.264 via FFmpeg NVENC pipe.
    """
    n_frames = int(duration * fps)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", "1920x1080", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "-",
        "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20",
        "-pix_fmt", "yuv420p", "-an",
        output_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    
    for f in range(n_frames):
        t = f / fps
        if vfx_type == "dossier":
            frame_rgb = render_dossier_card_frame(
                kwargs.get("chapter_idx", 1),
                kwargs.get("total_chapters", 5),
                kwargs.get("title", ""),
                kwargs.get("icd_code", ""),
                kwargs.get("rarity", ""),
                kwargs.get("mechanism", "")
            )
        elif vfx_type == "ecg":
            frame_rgb = render_ecg_frame(
                time_sec=t, duration_sec=duration,
                start_bpm=kwargs.get("start_bpm", 75),
                end_bpm=kwargs.get("end_bpm", 140),
                flatline_at=kwargs.get("flatline_at", None),
                anomaly_label=kwargs.get("anomaly_label", "")
            )
        elif vfx_type == "eeg":
            frame_rgb = render_eeg_frame(
                time_sec=t, duration_sec=duration,
                anomaly_active=kwargs.get("anomaly_active", False),
                anomaly_title=kwargs.get("anomaly_title", "")
            )
        elif vfx_type == "fmri":
            frame_rgb = render_fmri_slice_frame(
                time_sec=t, duration_sec=duration,
                target=kwargs.get("target", "amygdala"),
                label=kwargs.get("label", "")
            )
        else:
            frame_rgb = np.zeros((1080, 1920, 3), dtype=np.uint8)
            
        proc.stdin.write(frame_rgb.tobytes())
        
    proc.stdin.close()
    proc.wait()
    print(f"[OK] Rendered VFX {vfx_type}: {output_path} ({duration:.2f}s)")

def build_chapter_video_cuts(ch, total_dur, output_video_path):
    """
    Constructs multi-shot cut sequence (2.8 - 4.5s per cut) with ZERO repetition.
    """
    ch_id = ch["id"]
    ch_num = ch["chapter_num"]
    broll_file = ch["broll_video"]
    cuts_dir = os.path.join(WORKSPACE_DIR, f"cuts_{ch_id}")
    os.makedirs(cuts_dir, exist_ok=True)
    
    shot_files = []
    
    # Shot 0: Dossier Card (3.0s) for anomaly chapters (1-5), or Intro Card (3.0s)
    shot0_path = os.path.join(cuts_dir, "shot0_dossier.mp4")
    render_procedural_subclip(
        "dossier", duration=3.0, output_path=shot0_path,
        chapter_idx=max(1, ch_num), total_chapters=5,
        title=ch["title"], icd_code=ch["icd_code"],
        rarity=ch["rarity"], mechanism=ch["mechanism"]
    )
    shot_files.append(shot0_path)
    
    remaining_dur = total_dur - 3.0
    
    # We will build 4-6 dynamic shots
    # Shot 1: B-Roll primary (4.0s)
    s1_dur = min(4.5, remaining_dur * 0.25)
    shot1_path = os.path.join(cuts_dir, "shot1_broll.mp4")
    extract_broll_subclip(broll_file, start_time=1.0, duration=s1_dur, output_path=shot1_path)
    shot_files.append(shot1_path)
    remaining_dur -= s1_dur
    
    # Shot 2: Primary Medical Telemetry VFX (5.0s)
    s2_dur = min(5.5, remaining_dur * 0.35)
    shot2_path = os.path.join(cuts_dir, f"shot2_{ch['vfx_type']}.mp4")
    if ch["vfx_type"] == "ecg":
        render_procedural_subclip(
            "ecg", duration=s2_dur, output_path=shot2_path,
            start_bpm=ch.get("vfx_start_bpm", 75),
            end_bpm=ch.get("vfx_end_bpm", 140),
            flatline_at=s2_dur * ch.get("vfx_flatline_rel", 0.99) if "vfx_flatline_rel" in ch else None,
            anomaly_label=f"CASE #0{ch_num}: {ch['title']}"
        )
    elif ch["vfx_type"] == "eeg":
        render_procedural_subclip(
            "eeg", duration=s2_dur, output_path=shot2_path,
            anomaly_active=ch.get("vfx_spike", False),
            anomaly_title=f"CASE #0{ch_num}: {ch['title']}"
        )
    else: # fmri
        render_procedural_subclip(
            "fmri", duration=s2_dur, output_path=shot2_path,
            target=ch.get("vfx_target", "amygdala"),
            label=f"CASE #0{ch_num}: {ch['title']}"
        )
    shot_files.append(shot2_path)
    remaining_dur -= s2_dur
    
    # Shot 3: B-Roll secondary perspective (4.5s)
    s3_dur = min(5.0, remaining_dur * 0.40)
    shot3_path = os.path.join(cuts_dir, "shot3_broll_alt.mp4")
    extract_broll_subclip(broll_file, start_time=6.0, duration=s3_dur, output_path=shot3_path)
    shot_files.append(shot3_path)
    remaining_dur -= s3_dur
    
    # Shot 4: Secondary Medical VFX (fMRI / EEG / Monitor) (5.0s)
    s4_dur = min(5.0, remaining_dur * 0.50)
    shot4_path = os.path.join(cuts_dir, "shot4_alt_vfx.mp4")
    # Alternate VFX: if primary was ECG -> use fMRI; if primary was fMRI -> use EEG; if EEG -> use ECG
    if ch["vfx_type"] == "ecg":
        render_procedural_subclip("fmri", duration=s4_dur, output_path=shot4_path, target="amygdala", label=f"CORRELATED CORTICAL SCAN // {ch['title']}")
    elif ch["vfx_type"] == "fmri":
        render_procedural_subclip("eeg", duration=s4_dur, output_path=shot4_path, anomaly_active=True, anomaly_title=f"ELECTRO-PHYSIOLOGY // {ch['title']}")
    else:
        render_procedural_subclip("ecg", duration=s4_dur, output_path=shot4_path, start_bpm=80, end_bpm=135, anomaly_label=f"AUTONOMIC RESPONSE // {ch['title']}")
    shot_files.append(shot4_path)
    remaining_dur -= s4_dur
    
    # Shot 5: Final B-Roll climax (remaining duration)
    s5_dur = max(2.0, remaining_dur)
    shot5_path = os.path.join(cuts_dir, "shot5_climax_broll.mp4")
    extract_broll_subclip(broll_file, start_time=11.0, duration=s5_dur, output_path=shot5_path)
    shot_files.append(shot5_path)
    
    # Concatenate shots via ffmpeg concat demuxer
    concat_txt = os.path.join(cuts_dir, "concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for s in shot_files:
            # Use forward slashes for ffmpeg concat
            f.write(f"file '{s.replace(chr(92), '/')}'\n")
            
    concat_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "19",
        "-pix_fmt", "yuv420p", "-an", output_video_path
    ]
    subprocess.run(concat_cmd, check=True)
    print(f"[OK] Chapter video assembled: {output_video_path}")

def render_master_chapter(ch):
    """
    Renders a single fully finished chapter (video + audio + kinetic subtitles).
    """
    ch_id = ch["id"]
    print(f"\n==========================================")
    print(f"PROCESSING CHAPTER: {ch_id} ({ch['title']})")
    print(f"==========================================")
    
    ch_dir = os.path.join(WORKSPACE_DIR, ch_id)
    os.makedirs(ch_dir, exist_ok=True)
    
    # 1. Master Audio mix
    audio_wav = os.path.join(ch_dir, "master_audio.wav")
    total_dur = build_chapter_audio(ch, audio_wav)
    
    # 2. Multi-cut Video stream
    raw_video = os.path.join(ch_dir, "video_raw.mp4")
    build_chapter_video_cuts(ch, total_dur, raw_video)
    
    # 3. Subtitles
    ass_subs = os.path.join(ch_dir, "subtitles.ass")
    generate_chapter_ass_subtitles(ch, ass_subs)
    
    # 4. Final Chapter Composite (NVENC + Subtitles + Audio)
    final_chapter_mp4 = os.path.join(ch_dir, f"finished_{ch_id}.mp4")
    
    # Windows path escape for ffmpeg ass filter: backslashes need escaping or colon escaping
    escaped_ass = ass_subs.replace("\\", "/").replace(":", "\\:")
    
    composite_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", raw_video,
        "-i", audio_wav,
        "-vf", f"ass='{escaped_ass}'",
        "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        final_chapter_mp4
    ]
    subprocess.run(composite_cmd, check=True)
    print(f"[SUCCESS] Chapter finished: {final_chapter_mp4}")
    return final_chapter_mp4

def render_entire_documentary():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        chapters = json.load(f)
        
    finished_chapters = []
    for ch in chapters:
        ch_mp4 = render_master_chapter(ch)
        finished_chapters.append(ch_mp4)
        
    print(f"\n==========================================")
    print("CONCATENATING ALL 7 CHAPTERS INTO MASTER DOCUMENTARY...")
    print(f"==========================================")
    
    master_concat_txt = os.path.join(WORKSPACE_DIR, "master_concat.txt")
    with open(master_concat_txt, "w", encoding="utf-8") as f:
        for ch_file in finished_chapters:
            f.write(f"file '{ch_file.replace(chr(92), '/')}'\n")
            
    final_cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", master_concat_txt,
        "-c", "copy",
        FINAL_DOC_PATH
    ]
    subprocess.run(final_cmd, check=True)
    
    final_size = os.path.getsize(FINAL_DOC_PATH)
    print(f"\n[DONE] MASTER DOCUMENTARY SUCCESSFULLY CREATED!")
    print(f"Destination: {FINAL_DOC_PATH}")
    print(f"File size: {final_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    render_entire_documentary()
