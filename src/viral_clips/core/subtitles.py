"""
Karaoke & Viral Subtitle Generator.
Generates Advanced SubStation Alpha (.ass) subtitle files with exact word-level timing,
Alex Hormozi style punchy animations, and safe-area margins for Shorts/Reels/TikTok.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from loguru import logger

SCHEMA_VERSION = "1.0.0"

# ASS Color format is &HAABBGGRR (Alpha, Blue, Green, Red in Hex)
# White: &H00FFFFFF&, Yellow: &H0000FFFF&, Gold: &H0000D7FF&, Cyan: &H00FFFF00&, Black: &H00000000&
PRESET_STYLES = {
    "bold_karaoke": {
        "font_name": "Arial",
        "font_size": 24,
        "primary_color": "&H00FFFFFF&",     # Inactive word: White
        "highlight_color": "&H0000FFFF&",   # Active word: Electric Yellow
        "outline_color": "&H00000000&",     # Black outline
        "back_color": "&H80000000&",
        "bold": -1,
        "italic": 0,
        "border_style": 1,
        "outline": 4.0,
        "shadow": 2.0,
        "alignment": 2,                      # Centered bottom
        "margin_l": 60,
        "margin_r": 60,
        "margin_v": 280,                     # Above TikTok bottom UI elements
    },
    "minimalist": {
        "font_name": "Arial",
        "font_size": 20,
        "primary_color": "&H00FFFFFF&",
        "highlight_color": "&H0000D7FF&",   # Gold
        "outline_color": "&H00000000&",
        "back_color": "&HA0000000&",
        "bold": 0,
        "italic": 0,
        "border_style": 3,                   # Opaque bounding box
        "outline": 2.0,
        "shadow": 0.0,
        "alignment": 2,
        "margin_l": 50,
        "margin_r": 50,
        "margin_v": 240,
    },
    "hormozi_pop": {
        "font_name": "Impact",
        "font_size": 28,
        "primary_color": "&H00FFFFFF&",
        "highlight_color": "&H0000FF00&",   # Vibrant Green
        "outline_color": "&H00000000&",
        "back_color": "&H00000000&",
        "bold": -1,
        "italic": 0,
        "border_style": 1,
        "outline": 5.0,
        "shadow": 3.0,
        "alignment": 2,
        "margin_l": 60,
        "margin_r": 60,
        "margin_v": 320,
    },
}


def ms_to_ass_time(ms: int) -> str:
    """Converts milliseconds to ASS timestamp format: H:MM:SS.cs (centiseconds)."""
    ms = max(0, ms)
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    centiseconds = (ms % 1000) // 10
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def build_ass_header(style_name: str, style_cfg: Dict[str, Any], play_res_x: int = 1080, play_res_y: int = 1920) -> str:
    """Constructs the ASS script header and styles table."""
    return f"""[Script Info]
Title: Viral Clips AI Karaoke Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style_cfg['font_name']},{style_cfg['font_size']},{style_cfg['primary_color']},{style_cfg['highlight_color']},{style_cfg['outline_color']},{style_cfg['back_color']},{style_cfg['bold']},{style_cfg['italic']},0,0,100,100,0,0,{style_cfg['border_style']},{style_cfg['outline']},{style_cfg['shadow']},{style_cfg['alignment']},{style_cfg['margin_l']},{style_cfg['margin_r']},{style_cfg['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def chunk_words_into_lines(
    words: List[Dict[str, Any]],
    clip_start_ms: int,
    clip_end_ms: int,
    words_per_line: int = 4,
) -> List[List[Dict[str, Any]]]:
    """Filters words within the clip window and groups them into 2-5 word visual phrases."""
    relevant_words = []
    for w in words:
        w_start = w["start_ms"]
        w_end = w["end_ms"]
        if w_end > clip_start_ms and w_start < clip_end_ms:
            # Normalize timestamps strictly relative to clip start and clamp within interval
            rel_start = max(0, w_start - clip_start_ms)
            max_duration_ms = clip_end_ms - clip_start_ms
            rel_end = min(max_duration_ms, max(rel_start + 100, w_end - clip_start_ms))
            relevant_words.append({
                "word": w.get("word", w.get("text", "")).strip(),
                "start_ms": rel_start,
                "end_ms": rel_end,
            })

    # Group into chunks
    chunks = []
    for i in range(0, len(relevant_words), words_per_line):
        chunks.append(relevant_words[i:i + words_per_line])
    return chunks


def generate_karaoke_dialogue_lines(
    chunks: List[List[Dict[str, Any]]],
    style_cfg: Dict[str, Any],
) -> List[str]:
    """
    Generates word-highlighted ASS dialogue events.
    For each word in a chunk, renders the entire phrase with the active word highlighted.
    """
    dialogue_lines = []
    hl_color = style_cfg["highlight_color"]
    base_color = style_cfg["primary_color"]

    for chunk in chunks:
        if not chunk:
            continue

        chunk_start_ms = chunk[0]["start_ms"]
        chunk_end_ms = chunk[-1]["end_ms"]

        for active_idx, active_w in enumerate(chunk):
            w_s = active_w["start_ms"]
            w_e = active_w["end_ms"]

            # Guard against invalid durations
            if w_e <= w_s:
                w_e = w_s + 150

            ass_start = ms_to_ass_time(w_s)
            ass_end = ms_to_ass_time(w_e)

            # Build phrase with active word highlighted
            phrase_parts = []
            for i, w in enumerate(chunk):
                word_text = w["word"]
                if i == active_idx:
                    phrase_parts.append(r"{\c" + hl_color + r"\b1}" + word_text + r"{\r}")
                else:
                    phrase_parts.append(r"{\c" + base_color + r"}" + word_text)

            line_text = " ".join(phrase_parts)
            dialogue_lines.append(
                f"Dialogue: 0,{ass_start},{ass_end},Default,,0,0,0,,{line_text}"
            )

    return dialogue_lines


def generate_subtitles(
    words: List[Dict[str, Any]],
    clip_start_ms: int,
    clip_end_ms: int,
    output_ass_path: Union[str, Path],
    preset: str = "bold_karaoke",
    words_per_line: int = 3,
    transcript_id: Optional[str] = None,
    source: str = "faster_whisper",
    font_size: Optional[int] = None,
    font_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates an ASS subtitle file for a specific clip window.
    
    Args:
        words: Full list of word timestamps from transcript.json.
        clip_start_ms: Clip start offset in ms.
        clip_end_ms: Clip end offset in ms.
        output_ass_path: Target path for the generated .ass file.
        preset: Visual style preset ('bold_karaoke', 'minimalist', 'hormozi_pop').
        words_per_line: Number of words displayed per subtitle phrase.
        transcript_id: ID of source transcript for provenance.
        source: Provider name of the ASR system.
        font_size: Optional font size override.
        font_name: Optional font name override.
        
    Returns:
        Metadata artifact dictionary.
    """
    dst = Path(output_ass_path).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)

    base_style = PRESET_STYLES.get(preset, PRESET_STYLES["bold_karaoke"]).copy()
    if font_size:
        base_style["font_size"] = font_size
    if font_name:
        base_style["font_name"] = font_name

    header = build_ass_header(preset, base_style)

    chunks = chunk_words_into_lines(words, clip_start_ms, clip_end_ms, words_per_line=words_per_line)
    lines = generate_karaoke_dialogue_lines(chunks, base_style)

    ass_content = header + "\n".join(lines) + "\n"

    with open(dst, "w", encoding="utf-8") as f:
        f.write(ass_content)

    total_words_in_clip = sum(len(c) for c in chunks)

    # Save subtitle_manifest.json per Section 25
    manifest_path = dst.with_name(f"{dst.stem}_subtitle_manifest.json")
    generic_manifest = dst.parent / "subtitle_manifest.json"
    manifest = {
        "transcript_id": transcript_id or "transcript_primary",
        "source": source,
        "preset": preset,
        "word_count": total_words_in_clip,
        "start": round(clip_start_ms / 1000.0, 2),
        "end": round(clip_end_ms / 1000.0, 2),
        "total_dialogue_events": len(lines),
        "file_path": str(dst),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    with open(generic_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    artifact = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preset": preset,
        "clip_start_ms": clip_start_ms,
        "clip_end_ms": clip_end_ms,
        "duration_ms": clip_end_ms - clip_start_ms,
        "total_dialogue_events": len(lines),
        "word_count": total_words_in_clip,
        "file_path": str(dst),
        "manifest_path": str(manifest_path),
    }

    logger.success(f"Generated ASS subtitles ({preset}): {dst.name} ({len(lines)} events, {total_words_in_clip} words)")
    return artifact
