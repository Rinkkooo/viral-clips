"""
Subtitles Generator for Science Content Factory V2.
Features:
- Kinetic word pop scaling: {\\fscx120\\fscy120\\t(0,80,\\fscx100\\fscy100)}
- Dual color palette: Electric Gold for standard active words, Neon Red for critical/explosive terms.
- Live top-screen scientific telemetry HUD in sync with narration.
"""

from pathlib import Path
from typing import List, Dict, Any
from .audio_engine import WordTiming


def ms_to_ass_time(ms: int) -> str:
    """Converts milliseconds to ASS timestamp format: H:MM:SS.cs"""
    ms = max(0, ms)
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    centiseconds = (ms % 1000) // 10
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


CRITICAL_WORDS = {
    "ВЗРЫВ", "ВЗРЫВА", "ТРОТИЛА", "СТЕРЕТЬ", "УНИЧТОЖИТЬ", 
    "ПЛАЗМЫ", "ТЕРМОЯДЕРНУЮ", "ЧУДОВИЩНУЮ", "БЕСКОНЕЧНОСТИ", "ЗАПРЕЩАЮТ"
}


def generate_science_karaoke_subtitles(
    words: List[WordTiming],
    output_ass_path: Path,
    words_per_line: int = 3,
    play_res_x: int = 1080,
    play_res_y: int = 1920
) -> Path:
    """
    Renders kinetic ASS karaoke subtitles with word-pop scaling and top HUD telemetry.
    """
    output_ass_path.parent.mkdir(parents=True, exist_ok=True)
    
    font_name = "Arial"
    font_size = 74
    primary_color = "&H00FFFFFF&"      # Crisp White
    gold_highlight = "&H0000D7FF&"     # Hormozi Electric Gold (&HAABBGGRR)
    alert_highlight = "&H002040FF&"    # Neon Red/Orange Alert
    outline_color = "&H00000000&"      # Solid Black Outline
    back_color = "&H80000000&"
    margin_v = 420                     # Lower third safe area
    
    header = f"""[Script Info]
Title: AI Science Content Factory Kinetic Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},{gold_highlight},{outline_color},{back_color},-1,0,0,0,100,100,0,0,1,6.0,3.0,2,60,60,{margin_v},1
Style: HUDTop,{font_name},36,&H0000FFFF&,&H00000000&,&H00000000&,&HA0001020&,-1,0,0,0,100,100,1,0,3,3.0,0.0,8,60,60,170,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    dialogue_lines = []
    
    # 1. Top Screen Sci-Fi Telemetry Banner
    dialogue_lines.append(f"Dialogue: 1,0:00:00.00,0:00:10.00,HUDTop,,0,0,0,,[ TARGET: EARTH // RELATIVISTIC PROJECTILE: 5.0 mg ]")
    dialogue_lines.append(f"Dialogue: 1,0:00:10.00,0:00:23.00,HUDTop,,0,0,0,,[ VELOCITY: 299,792,458 M/S // 99.999% c // γ = 22,360 ]")
    dialogue_lines.append(f"Dialogue: 1,0:00:23.00,0:00:34.00,HUDTop,,0,0,0,,[ WARNING: THERMONUCLEAR CASCADE DETECTED ]")
    dialogue_lines.append(f"Dialogue: 1,0:00:34.00,0:00:50.00,HUDTop,,0,0,0,,[ KINETIC ENERGY: 2.4+ KILOTONS TNT // ABSOLUTE LIMIT: c ]")
    
    # 2. Group spoken words into fast 3-word visual chunks
    raw_word_dicts = []
    for w in words:
        clean_word = w.word.upper().strip()
        raw_word_dicts.append({
            "word": clean_word,
            "start_ms": int(w.start * 1000),
            "end_ms": int(w.end * 1000)
        })
        
    chunks = []
    for i in range(0, len(raw_word_dicts), words_per_line):
        chunks.append(raw_word_dicts[i:i + words_per_line])
        
    for chunk in chunks:
        if not chunk:
            continue
            
        for active_idx, active_w in enumerate(chunk):
            w_s = active_w["start_ms"]
            w_e = active_w["end_ms"]
            
            if w_e <= w_s:
                w_e = w_s + 200
                
            ass_start = ms_to_ass_time(w_s)
            ass_end = ms_to_ass_time(w_e)
            
            phrase_parts = []
            for i, w in enumerate(chunk):
                word_text = w["word"]
                if i == active_idx:
                    # Choose alert color for critical science impact words
                    hl = alert_highlight if any(cw in word_text for cw in CRITICAL_WORDS) else gold_highlight
                    # Kinetic scale pop-in animation
                    pop_tag = r"{\fscx118\fscy118\t(0,75,\fscx100\fscy100)}"
                    phrase_parts.append(r"{\c" + hl + r"\b1}" + pop_tag + word_text + r"{\r}")
                else:
                    phrase_parts.append(r"{\c" + primary_color + r"}" + word_text)
                    
            line_text = " ".join(phrase_parts)
            dialogue_lines.append(f"Dialogue: 0,{ass_start},{ass_end},Default,,0,0,0,,{line_text}")
            
    full_content = header + "\n".join(dialogue_lines) + "\n"
    output_ass_path.write_text(full_content, encoding="utf-8")
    return output_ass_path


def generate_documentary_16x9_subtitles(
    words: List[WordTiming],
    chapters: List[Dict[str, Any]],
    output_ass_path: Path,
    words_per_line: int = 5
) -> Path:
    """
    Renders 16:9 Full HD (1920x1080) documentary subtitles with chapter lower-third cards.
    """
    output_ass_path.parent.mkdir(parents=True, exist_ok=True)
    
    font_name = "Arial"
    header = f"""[Script Info]
Title: AI Science Documentary Subtitles 16:9
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},48,&H00FFFFFF&,&H0000D7FF&,&H00000000&,&H80000000&,-1,0,0,0,100,100,0,0,1,4.0,2.0,2,120,120,80,1
Style: ChapterCard,{font_name},44,&H0000FFFF&,&H00000000&,&H00000000&,&HA0050810&,-1,0,0,0,100,100,2,0,3,4.0,0.0,1,100,100,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogue_lines = []
    
    # 1. Chapter Title Lower-Third Cards
    for ch in chapters:
        start_ms = ch.get("start_ms", 0)
        end_ms = start_ms + 6000  # Display for 6 seconds
        ass_start = ms_to_ass_time(start_ms)
        ass_end = ms_to_ass_time(end_ms)
        title = ch.get("title", "").upper()
        ch_num = ch.get("chapter_num", 1)
        dialogue_lines.append(
            f"Dialogue: 1,{ass_start},{ass_end},ChapterCard,,0,0,0,,[ ГЛАВА {ch_num}: {title} ]"
        )
        
    # 2. Narration Subtitles
    raw_word_dicts = []
    for w in words:
        raw_word_dicts.append({
            "word": w.word.strip(),
            "start_ms": int(w.start * 1000),
            "end_ms": int(w.end * 1000)
        })
        
    chunks = []
    for i in range(0, len(raw_word_dicts), words_per_line):
        chunks.append(raw_word_dicts[i:i + words_per_line])
        
    for c_idx, chunk in enumerate(chunks):
        if not chunk:
            continue
        chunk_start_ms = chunk[0]["start_ms"]
        chunk_end_ms = chunk[-1]["end_ms"]
        if chunk_end_ms <= chunk_start_ms:
            chunk_end_ms = chunk_start_ms + 1500
            
        if c_idx + 1 < len(chunks) and chunks[c_idx + 1]:
            next_start = chunks[c_idx + 1][0]["start_ms"]
            if chunk_end_ms > next_start:
                chunk_end_ms = max(chunk_start_ms + 100, next_start - 20)
            
        ass_start = ms_to_ass_time(chunk_start_ms)
        ass_end = ms_to_ass_time(chunk_end_ms)
        line_text = " ".join([w["word"] for w in chunk])
        dialogue_lines.append(f"Dialogue: 0,{ass_start},{ass_end},Default,,0,0,0,,{line_text}")
        
    full_content = header + "\n".join(dialogue_lines) + "\n"
    output_ass_path.write_text(full_content, encoding="utf-8")
    return output_ass_path
