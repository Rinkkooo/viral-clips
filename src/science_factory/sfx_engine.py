"""
Procedural SFX Engine for Science Content Factory.
Synthesizes professional cinematic sound effects in pure Python:
- Whoosh (aerodynamic high-speed transition)
- Sub-bass impact (deep cinematic punch)
- Telemetry chimes & radar beeps
- Tension risers
Builds a synchronized master SFX track aligned with scene cuts and key words.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import random
import struct
from typing import List, Tuple
import wave


def generate_whoosh_samples(sample_rate: int = 44100, duration_s: float = 0.35) -> List[float]:
    """Synthesizes a cinematic whoosh / swish using frequency-swept filtered noise."""
    num_samples = int(duration_s * sample_rate)
    samples = []
    
    # Random noise with sinusoidal envelope and pitch sweep
    for i in range(num_samples):
        t = i / sample_rate
        # Bell curve volume envelope
        env = math.sin(math.pi * (t / duration_s)) ** 2
        # Center frequency sweeps up then down
        freq = 300.0 + 1200.0 * math.sin(math.pi * (t / duration_s))
        noise = (random.random() * 2.0 - 1.0)
        # Sine modulation for aerodynamic whistling body
        tone = math.sin(2 * math.pi * freq * t)
        val = (noise * 0.6 + tone * 0.4) * env * 0.65
        samples.append(val)
        
    return samples


def generate_sub_impact_samples(sample_rate: int = 44100, duration_s: float = 1.6) -> List[float]:
    """Synthesizes a deep cinematic sub-bass impact / explosion boom."""
    num_samples = int(duration_s * sample_rate)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        # Exponential pitch drop from 140 Hz to 28 Hz
        freq = 28.0 + 112.0 * math.exp(-t * 4.5)
        # Fast attack, long exponential sub-bass decay
        if t < 0.015:
            env = t / 0.015
        else:
            env = math.exp(-(t - 0.015) * 2.2)
            
        # Heavy sub-bass body + harmonic overtone
        sub = math.sin(2 * math.pi * freq * t)
        harm = 0.35 * math.sin(4 * math.pi * freq * t)
        # Soft saturation / distortion
        raw = (sub + harm) * env * 0.95
        saturated = math.tanh(raw * 1.5)
        samples.append(saturated)
        
    return samples


def generate_telemetry_beep_samples(sample_rate: int = 44100, duration_s: float = 0.08) -> List[float]:
    """Synthesizes a high-tech sci-fi telemetry ping."""
    num_samples = int(duration_s * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        env = math.exp(-t * 35.0)
        freq = 1800.0 if t < 0.04 else 2400.0
        val = math.sin(2 * math.pi * freq * t) * env * 0.35
        samples.append(val)
    return samples


def generate_tension_riser_samples(sample_rate: int = 44100, duration_s: float = 2.5) -> List[float]:
    """Synthesizes an ascending tension riser sweep before impact."""
    num_samples = int(duration_s * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Exponential rise from 110 Hz to 880 Hz
        progress = t / duration_s
        freq = 110.0 * (8.0 ** progress)
        env = progress ** 1.8  # Exponential volume swell
        # Pulse modulation (tremolo getting faster)
        tremolo = 0.7 + 0.3 * math.sin(2 * math.pi * (4.0 + 16.0 * progress) * t)
        val = math.sin(2 * math.pi * freq * t) * env * tremolo * 0.55
        samples.append(val)
    return samples


@dataclass
class SFXEvent:
    name: str
    time_s: float
    volume: float = 1.0


def build_master_sfx_track(
    events: List[SFXEvent],
    total_duration_s: float,
    output_path: Path,
    sample_rate: int = 44100
) -> Path:
    """
    Renders a synchronized stereo SFX track placing effects at exact timestamps.
    """
    total_samples = int((total_duration_s + 1.0) * sample_rate)
    left = [0.0] * total_samples
    right = [0.0] * total_samples
    
    # Pre-render sample buffers
    whoosh_buf = generate_whoosh_samples(sample_rate)
    impact_buf = generate_sub_impact_samples(sample_rate)
    beep_buf = generate_telemetry_beep_samples(sample_rate)
    riser_buf = generate_tension_riser_samples(sample_rate)
    
    buffer_map = {
        "whoosh": whoosh_buf,
        "impact": impact_buf,
        "beep": beep_buf,
        "riser": riser_buf
    }
    
    for ev in events:
        buf = buffer_map.get(ev.name)
        if not buf:
            continue
            
        start_idx = int(ev.time_s * sample_rate)
        for i, s_val in enumerate(buf):
            idx = start_idx + i
            if idx < total_samples:
                v = s_val * ev.volume
                left[idx] += v
                right[idx] += v
                
    # Soft limiter & 16-bit packing
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        
        frames = bytearray()
        for l_v, r_v in zip(left, right):
            clamped_l = max(-0.95, min(0.95, l_v))
            clamped_r = max(-0.95, min(0.95, r_v))
            frames.extend(struct.pack('<hh', int(clamped_l * 32767.0), int(clamped_r * 32767.0)))
        wav.writeframes(frames)
        
    return output_path


if __name__ == "__main__":
    test_events = [
        SFXEvent("whoosh", 0.0),
        SFXEvent("beep", 1.5),
        SFXEvent("whoosh", 2.2),
        SFXEvent("riser", 4.0),
        SFXEvent("impact", 6.5),
    ]
    p = build_master_sfx_track(test_events, 8.0, Path("test_sfx.wav"))
    print("Test SFX track written to:", p)
