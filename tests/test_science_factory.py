"""
Tests for Science Content Factory components.
"""

import pytest
from science_factory.fact_checker import calculate_relativistic_impact
from science_factory.script_generator import build_needle_lightspeed_script
from science_factory.subtitles_generator import ms_to_ass_time, generate_science_karaoke_subtitles
from science_factory.audio_engine import WordTiming
from pathlib import Path


def test_relativistic_fact_checker():
    facts = calculate_relativistic_impact(mass_mg=5.0, velocity_fraction=0.999999999)
    assert facts.lorentz_gamma > 20000.0
    assert facts.kinetic_energy_joules > 1e12
    assert facts.tnt_equivalent_tons > 1000.0
    assert len(facts.key_takeaways) == 3


def test_script_generator_hooks():
    script = build_needle_lightspeed_script(0)
    assert len(script.hooks) == 3
    assert script.selected_hook == script.hooks[0]
    assert len(script.scenes) == 4
    assert "игла" in script.selected_hook.lower()
    
    script2 = build_needle_lightspeed_script(1)
    assert script2.selected_hook == script.hooks[1]


def test_ms_to_ass_time():
    assert ms_to_ass_time(0) == "0:00:00.00"
    assert ms_to_ass_time(1500) == "0:00:01.50"
    assert ms_to_ass_time(65430) == "0:01:05.43"


def test_generate_science_subtitles(tmp_path):
    words = [
        WordTiming(word="Обычная", start=0.1, end=0.6, duration=0.5),
        WordTiming(word="игла", start=0.7, end=1.2, duration=0.5),
        WordTiming(word="уничтожит", start=1.3, end=1.9, duration=0.6),
        WordTiming(word="город", start=2.0, end=2.5, duration=0.5),
    ]
    out_ass = tmp_path / "test.ass"
    res = generate_science_karaoke_subtitles(words, out_ass)
    assert res.exists()
    content = out_ass.read_text(encoding="utf-8")
    assert "Dialogue:" in content
    assert "ОБЫЧНАЯ" in content
    assert "&H0000D7FF&" in content
