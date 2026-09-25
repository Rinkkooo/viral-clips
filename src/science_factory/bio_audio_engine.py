import math
import wave
import struct
import numpy as np

def generate_heartbeat(duration_sec, start_bpm=70, end_bpm=70, flatline_at=None, sample_rate=44100):
    """
    Generates realistic physiological Lub-Dub cardiac pulse audio.
    S1 (Lub): ~50-60 Hz deep resonant thump
    S2 (Dub): ~70-85 Hz slightly shorter thump
    BPM can ramp smoothly from start_bpm to end_bpm.
    If flatline_at is provided, pulses stop at flatline_at and a medical flatline tone sounds.
    """
    n_samples = int(duration_sec * sample_rate)
    audio = np.zeros(n_samples, dtype=np.float32)
    
    # Calculate beat positions
    current_time = 0.0
    while current_time < duration_sec:
        if flatline_at is not None and current_time >= flatline_at:
            break
        
        # Calculate current instantaneous BPM
        progress = current_time / max(0.001, duration_sec)
        current_bpm = start_bpm + (end_bpm - start_bpm) * progress
        beat_interval = 60.0 / max(30.0, current_bpm)
        
        start_idx = int(current_time * sample_rate)
        
        # S1 (Lub): 52 Hz fundamental, 0.11s decay
        s1_len = int(0.12 * sample_rate)
        if start_idx + s1_len < n_samples:
            t_s1 = np.linspace(0, 0.12, s1_len, endpoint=False)
            env_s1 = np.exp(-t_s1 * 35.0) * np.sin(np.pi * t_s1 / 0.12)
            # Two low frequencies with phase offset for fleshy chest acoustic
            lub = (0.75 * np.sin(2 * np.pi * 52 * t_s1) + 0.35 * np.sin(2 * np.pi * 78 * t_s1)) * env_s1
            audio[start_idx:start_idx + s1_len] += lub
            
        # S2 (Dub): occurs ~0.18 - 0.22s after S1
        systolic_gap = max(0.14, min(0.24, 0.28 * (60.0 / current_bpm)))
        s2_idx = start_idx + int(systolic_gap * sample_rate)
        s2_len = int(0.09 * sample_rate)
        if s2_idx + s2_len < n_samples:
            t_s2 = np.linspace(0, 0.09, s2_len, endpoint=False)
            env_s2 = np.exp(-t_s2 * 45.0) * np.sin(np.pi * t_s2 / 0.09)
            dub = (0.6 * np.sin(2 * np.pi * 72 * t_s2) + 0.25 * np.sin(2 * np.pi * 105 * t_s2)) * env_s2
            audio[s2_idx:s2_idx + s2_len] += dub
            
        current_time += beat_interval
        
    # If flatline occurs, generate continuous steady medical monitor tone
    if flatline_at is not None and flatline_at < duration_sec:
        flat_start = int(flatline_at * sample_rate)
        flat_len = min(int(4.0 * sample_rate), n_samples - flat_start) # 4 seconds of flatline tone then silence
        if flat_len > 0:
            t_flat = np.linspace(0, flat_len / sample_rate, flat_len, endpoint=False)
            # Smooth fade in and fade out
            env_flat = np.ones(flat_len, dtype=np.float32)
            fade_in = int(0.05 * sample_rate)
            fade_out = int(0.8 * sample_rate)
            env_flat[:fade_in] = np.linspace(0, 1, fade_in)
            env_flat[-fade_out:] = np.linspace(1, 0, fade_out)
            flatline_tone = 0.25 * np.sin(2 * np.pi * 880 * t_flat) * env_flat
            audio[flat_start:flat_start + flat_len] += flatline_tone
            
    # Soft limiter / saturation to avoid harsh clipping
    audio = np.tanh(audio * 1.2) * 0.85
    return audio

def generate_dark_drone(duration_sec, sample_rate=44100):
    """
    Synthesizes deep dark cinematic drone (sub-bass 38 Hz with slow detuned beating and warmth).
    """
    n_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, n_samples, endpoint=False)
    
    # Fundamental sub-bass + detuned pairs for slow hypnotic acoustic beating
    f0 = 38.0
    f1 = 38.4
    f_sub = 19.0 # sub-octave rumble
    f_fifth = 57.0 # minor harmonic fifth
    
    # Slow LFO filter modulation
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.12 * t)
    lfo2 = 0.5 + 0.5 * np.cos(2 * np.pi * 0.07 * t)
    
    drone = (
        0.55 * np.sin(2 * np.pi * f0 * t) +
        0.45 * np.sin(2 * np.pi * f1 * t) +
        0.35 * np.sin(2 * np.pi * f_sub * t) +
        0.25 * lfo * np.sin(2 * np.pi * f_fifth * t) +
        0.15 * lfo2 * np.sin(2 * np.pi * 114.0 * t)
    )
    
    # Warm saturation
    drone = np.tanh(drone * 0.8) * 0.35
    
    # 2-second fade-in, 3-second fade-out
    fade_in = min(n_samples // 4, int(2.0 * sample_rate))
    fade_out = min(n_samples // 4, int(3.0 * sample_rate))
    if fade_in > 0:
        drone[:fade_in] *= np.linspace(0, 1, fade_in)
    if fade_out > 0:
        drone[-fade_out:] *= np.linspace(1, 0, fade_out)
        
    return drone

def generate_head_explosion_sfx(sample_rate=44100):
    """
    Violent neurological explosion: massive sub-bass shockwave (160 Hz -> 28 Hz)
    + transient white burst + high-pitched ringing tinnitus (4.2 kHz) decaying over 2.5s.
    """
    duration = 3.0
    n_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    # 1. Sub-bass boom pitch downsweep
    freq_sweep = 160.0 * np.exp(-t * 9.0) + 26.0
    phase = 2 * np.pi * np.cumsum(freq_sweep) / sample_rate
    env_boom = np.exp(-t * 2.8)
    boom = np.sin(phase) * env_boom * 0.85
    
    # 2. Transient noise burst
    noise = np.random.normal(0, 1, n_samples)
    env_noise = np.exp(-t * 22.0)
    burst = noise * env_noise * 0.4
    
    # 3. Tinnitus ringing tone (4200 Hz) slowly fading out
    env_ring = np.exp(-t * 1.3) * (1.0 - np.exp(-t * 60.0)) # quick rise, slow decay
    tinnitus = np.sin(2 * np.pi * 4200 * t) * env_ring * 0.18
    
    mix = np.tanh(boom + burst + tinnitus) * 0.9
    return mix

def generate_transition_impact(sample_rate=44100):
    """
    Subtle cinematic sub-bass transition impact for chapter cards (80 Hz -> 32 Hz).
    """
    duration = 1.6
    n_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    freq_sweep = 85.0 * np.exp(-t * 4.5) + 30.0
    phase = 2 * np.pi * np.cumsum(freq_sweep) / sample_rate
    env = np.exp(-t * 3.2)
    impact = np.sin(phase) * env * 0.65
    return np.tanh(impact)

def save_wav(filename, samples, sample_rate=44100, channels=2):
    """
    Saves float32 audio numpy array to 16-bit PCM WAV.
    """
    # Clip to -1.0 to 1.0
    samples = np.clip(samples, -0.99, 0.99)
    int_samples = (samples * 32767.0).astype(np.int16)
    
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(sample_rate)
        
        if channels == 1:
            wf.writeframes(int_samples.tobytes())
        else:
            # Duplicate mono to stereo
            stereo = np.column_stack((int_samples, int_samples)).flatten()
            wf.writeframes(stereo.tobytes())

if __name__ == "__main__":
    import os
    test_dir = r"C:\Users\user\Desktop\viral_clips\src\science_factory\assets\audio"
    os.makedirs(test_dir, exist_ok=True)
    
    print("Testing heartbeat...")
    hb = generate_heartbeat(10.0, start_bpm=65, end_bpm=130)
    save_wav(os.path.join(test_dir, "test_heartbeat.wav"), hb)
    
    print("Testing dark drone...")
    drone = generate_dark_drone(10.0)
    save_wav(os.path.join(test_dir, "test_drone.wav"), drone)
    
    print("Testing head explosion...")
    expl = generate_head_explosion_sfx()
    save_wav(os.path.join(test_dir, "test_explosion.wav"), expl)
    
    print("Audio engine verification complete!")
