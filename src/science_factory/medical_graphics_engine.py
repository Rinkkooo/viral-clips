import math
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_TITLE = r"C:\Windows\Fonts\arialbd.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\arial.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_medical_grid(img_draw, width=1920, height=1080):
    # Faint medical monitor grid
    grid_color_minor = (10, 24, 20)
    grid_color_major = (18, 45, 38)
    
    # 40px minor grid, 200px major grid
    for x in range(0, width, 40):
        color = grid_color_major if x % 200 == 0 else grid_color_minor
        img_draw.line([(x, 0), (x, height)], fill=color, width=1)
    for y in range(0, height, 40):
        color = grid_color_major if y % 200 == 0 else grid_color_minor
        img_draw.line([(0, y), (width, y)], fill=color, width=1)

def pqst_wave_value(phase):
    """
    Computes normalized ECG voltage for phase in [0, 1).
    P-Q-R-S-T morphology:
    P: 0.15 - 0.25 (small hump)
    Q: 0.32 - 0.35 (small dip)
    R: 0.35 - 0.40 (sharp high spike)
    S: 0.40 - 0.45 (sharp dip)
    T: 0.55 - 0.72 (medium hump)
    Isoelectric line elsewhere.
    """
    p = phase % 1.0
    if 0.15 <= p < 0.25:
        # P wave
        t = (p - 0.15) / 0.10
        return 0.18 * math.sin(math.pi * t)
    elif 0.32 <= p < 0.35:
        # Q wave
        t = (p - 0.32) / 0.03
        return -0.15 * math.sin(math.pi * t)
    elif 0.35 <= p < 0.40:
        # R wave (tall spike)
        t = (p - 0.35) / 0.05
        return 1.0 * math.sin(math.pi * t)
    elif 0.40 <= p < 0.45:
        # S wave
        t = (p - 0.40) / 0.05
        return -0.35 * math.sin(math.pi * t)
    elif 0.55 <= p < 0.72:
        # T wave
        t = (p - 0.55) / 0.17
        return 0.30 * math.sin(math.pi * t)
    return 0.0

def pleth_wave_value(phase):
    """
    Computes SpO2 photoplethysmogram pulse wave (smooth arterial expansion + dicrotic notch).
    """
    p = phase % 1.0
    if p < 0.25:
        # Rapid systolic upstroke
        t = p / 0.25
        return math.sin(0.5 * math.pi * t)
    elif p < 0.50:
        # Dicrotic notch descent
        t = (p - 0.25) / 0.25
        return 1.0 - 0.5 * t
    elif p < 0.65:
        # Small dicrotic wave
        t = (p - 0.50) / 0.15
        return 0.5 + 0.15 * math.sin(math.pi * t)
    else:
        # Diastolic runoff
        t = (p - 0.65) / 0.35
        return 0.5 * (1.0 - t)

def render_ecg_frame(time_sec, duration_sec, start_bpm=72, end_bpm=140, flatline_at=None, anomaly_label="CASE #01: SLEEP PARALYSIS"):
    width, height = 1920, 1080
    im = Image.new("RGB", (width, height), (4, 10, 8))
    draw = ImageDraw.Draw(im)
    draw_medical_grid(draw, width, height)
    
    # Calculate current BPM
    progress = time_sec / max(0.001, duration_sec)
    current_bpm = start_bpm + (end_bpm - start_bpm) * progress
    is_flatline = (flatline_at is not None and time_sec >= flatline_at)
    if is_flatline:
        current_bpm = 0
        
    font_hud_sm = get_font(FONT_MONO, 22)
    font_hud_md = get_font(FONT_TITLE, 28)
    font_val = get_font(FONT_MONO, 72)
    font_val_lg = get_font(FONT_TITLE, 96)
    
    # Header HUD bar
    draw.rectangle([(0, 0), (width, 80)], fill=(8, 20, 16))
    draw.line([(0, 80), (width, 80)], fill=(0, 255, 128), width=2)
    
    # Patient / Case info
    draw.text((40, 25), "PATIENT MONITOR // ICU TELEMETRY", fill=(0, 255, 128), font=font_hud_sm)
    draw.text((580, 22), anomaly_label, fill=(255, 255, 255), font=font_hud_md)
    time_str = f"T+{time_sec:05.2f}s"
    draw.text((1720, 25), time_str, fill=(0, 220, 255), font=font_hud_sm)
    
    # Channel 1: ECG (Lead II) in green
    ecg_y_center = 340
    ecg_box = [(40, 110), (1450, 560)]
    draw.rectangle(ecg_box, outline=(20, 50, 40), width=1)
    draw.text((60, 125), "LEAD II - ECG [mV]", fill=(0, 255, 100), font=font_hud_sm)
    draw.text((320, 125), "25 mm/s  10 mm/mV", fill=(0, 180, 80), font=get_font(FONT_MONO, 18))
    
    # Sweep calculation
    sweep_speed_px = 320 # px per second
    trace_width = 1370
    sweep_x = int((time_sec * sweep_speed_px) % trace_width)
    
    # Draw ECG trace
    pts_ecg = []
    for x in range(trace_width):
        t_sample = time_sec - (trace_width - x) / sweep_speed_px
        if t_sample < 0:
            continue
        
        # Check if flatlined at t_sample
        sample_flat = (flatline_at is not None and t_sample >= flatline_at)
        if sample_flat:
            y_val = 0.0
        else:
            # phase based on accumulated beats
            beat_freq = current_bpm / 60.0
            phase = (t_sample * beat_freq) % 1.0
            y_val = pqst_wave_value(phase)
            
        y_px = ecg_y_center - int(y_val * 160.0)
        pts_ecg.append((40 + x, y_px))
        
    if len(pts_ecg) > 1:
        # Dim green line
        draw.line(pts_ecg, fill=(0, 255, 100), width=3)
        # Leading bright dot
        lead_pt = pts_ecg[-1]
        draw.ellipse([(lead_pt[0] - 5, lead_pt[1] - 5), (lead_pt[0] + 5, lead_pt[1] + 5)], fill=(180, 255, 200))
        
    # Channel 2: Pleth (SpO2) in Cyan
    pleth_y_center = 780
    pleth_box = [(40, 590), (1450, 1020)]
    draw.rectangle(pleth_box, outline=(20, 45, 55), width=1)
    draw.text((60, 605), "PLETH // PULSE OXIMETRY", fill=(0, 230, 255), font=font_hud_sm)
    
    pts_pleth = []
    for x in range(trace_width):
        t_sample = time_sec - (trace_width - x) / sweep_speed_px
        if t_sample < 0:
            continue
        sample_flat = (flatline_at is not None and t_sample >= flatline_at)
        if sample_flat:
            y_val = 0.0
        else:
            beat_freq = current_bpm / 60.0
            phase = (t_sample * beat_freq) % 1.0
            y_val = pleth_wave_value(phase)
        y_px = pleth_y_center - int(y_val * 130.0)
        pts_pleth.append((40 + x, y_px))
        
    if len(pts_pleth) > 1:
        draw.line(pts_pleth, fill=(0, 230, 255), width=3)
        lead_pt2 = pts_pleth[-1]
        draw.ellipse([(lead_pt2[0] - 5, lead_pt2[1] - 5), (lead_pt2[0] + 5, lead_pt2[1] + 5)], fill=(200, 255, 255))

    # Right Telemetry Side Panel
    side_x = 1490
    draw.rectangle([(side_x, 110), (1880, 1020)], fill=(8, 18, 16), outline=(0, 255, 128), width=2)
    
    # 1. Heart Rate
    draw.text((side_x + 30, 130), "HEART RATE", fill=(0, 255, 100), font=font_hud_sm)
    hr_color = (255, 50, 50) if (is_flatline or current_bpm > 130) else (0, 255, 100)
    bpm_text = f"{int(current_bpm):03d}" if not is_flatline else "000"
    draw.text((side_x + 30, 170), bpm_text, fill=hr_color, font=font_val_lg)
    draw.text((side_x + 240, 230), "BPM", fill=hr_color, font=font_hud_sm)
    
    if is_flatline:
        # Flashing red alert
        if int(time_sec * 3) % 2 == 0:
            draw.rectangle([(side_x + 20, 290), (1860, 340)], fill=(180, 20, 20))
            draw.text((side_x + 35, 300), "! ASYSTOLE ALARM !", fill=(255, 255, 255), font=font_hud_md)
    elif current_bpm > 120:
        if int(time_sec * 3) % 2 == 0:
            draw.rectangle([(side_x + 20, 290), (1860, 340)], fill=(140, 80, 10))
            draw.text((side_x + 35, 300), "! TACHYCARDIA !", fill=(255, 240, 100), font=font_hud_md)
            
    # 2. SpO2
    draw.line([(side_x + 20, 370), (1860, 370)], fill=(30, 60, 50), width=1)
    draw.text((side_x + 30, 390), "SpO2 ARTERIAL", fill=(0, 230, 255), font=font_hud_sm)
    spo2_val = 98 if not is_flatline else 72
    if current_bpm > 130 and not is_flatline:
        spo2_val = max(82, int(98 - (current_bpm - 120) * 0.6))
    draw.text((side_x + 30, 430), f"{spo2_val}%", fill=(0, 230, 255), font=font_val)
    
    # 3. Blood Pressure
    draw.line([(side_x + 20, 540), (1860, 540)], fill=(30, 60, 50), width=1)
    draw.text((side_x + 30, 560), "NIBP (mmHg)", fill=(255, 180, 0), font=font_hud_sm)
    bp_sys = 120 if not is_flatline else 50
    bp_dia = 80 if not is_flatline else 20
    if current_bpm > 120 and not is_flatline:
        bp_sys = min(185, 120 + int((current_bpm - 120) * 1.5))
        bp_dia = min(115, 80 + int((current_bpm - 120) * 0.9))
    draw.text((side_x + 30, 600), f"{bp_sys}/{bp_dia}", fill=(255, 180, 0), font=font_val)
    
    # 4. Respiration Rate
    draw.line([(side_x + 20, 710), (1860, 710)], fill=(30, 60, 50), width=1)
    draw.text((side_x + 30, 730), "RESP RATE", fill=(200, 200, 200), font=font_hud_sm)
    resp_rate = 16 if not is_flatline else 0
    if current_bpm > 120 and not is_flatline:
        resp_rate = 32
    draw.text((side_x + 30, 770), f"{resp_rate} rpm", fill=(200, 200, 200), font=font_val)
    
    # 5. Status footer
    draw.line([(side_x + 20, 880), (1860, 880)], fill=(30, 60, 50), width=1)
    status_text = "NORMAL SINUS RHYTHM"
    if is_flatline:
        status_text = "CARDIAC ARREST // ASYSTOLE"
    elif current_bpm > 120:
        status_text = "ACUTE AUTONOMIC AROUSAL"
    draw.text((side_x + 30, 920), status_text, fill=(255, 255, 255), font=get_font(FONT_TITLE, 20))
    
    return np.array(im)

def render_eeg_frame(time_sec, duration_sec, anomaly_active=False, anomaly_title="EXPLODING HEAD // SENSORY STORM"):
    width, height = 1920, 1080
    im = Image.new("RGB", (width, height), (5, 8, 14))
    draw = ImageDraw.Draw(im)
    draw_medical_grid(draw, width, height)
    
    font_hud_sm = get_font(FONT_MONO, 22)
    font_hud_md = get_font(FONT_TITLE, 28)
    
    # Header HUD bar
    draw.rectangle([(0, 0), (width, 80)], fill=(10, 18, 28))
    draw.line([(0, 80), (width, 80)], fill=(0, 180, 255), width=2)
    
    draw.text((40, 25), "ELECTROENCEPHALOGRAPHY // 4-CHANNEL CORTICAL TELEMETRY", fill=(0, 180, 255), font=font_hud_sm)
    draw.text((1100, 22), anomaly_title, fill=(255, 220, 100), font=font_hud_md)
    
    channels = [
        ("FP1-F3", "DELTA (0.5-4 Hz)", 220, (100, 160, 255), 1.8),
        ("C3-P3", "THETA (4-8 Hz)", 420, (80, 230, 200), 5.5),
        ("P3-O1", "ALPHA (8-13 Hz)", 620, (150, 255, 120), 10.2),
        ("FZ-CZ", "BETA/GAMMA (15-35 Hz)", 820, (255, 180, 80), 24.0)
    ]
    
    trace_width = 1800
    sweep_speed_px = 360
    
    for ch_name, band_name, y_center, color, freq in channels:
        draw.text((60, y_center - 80), f"{ch_name} : {band_name}", fill=color, font=font_hud_sm)
        draw.line([(40, y_center), (1860, y_center)], fill=(20, 35, 50), width=1)
        
        pts = []
        for x in range(trace_width):
            t_sample = time_sec - (trace_width - x) / sweep_speed_px
            if t_sample < 0:
                continue
            
            # Normal brain rhythm + noise
            phase = 2 * math.pi * freq * t_sample
            base = 0.5 * math.sin(phase) + 0.3 * math.sin(phase * 1.61) + 0.15 * math.sin(phase * 2.7)
            
            # If anomaly active (e.g. exploding head surge)
            if anomaly_active:
                surge = math.exp(-((t_sample - 2.0) ** 2) / 0.15) if abs(t_sample - 2.0) < 1.0 else 0.0
                spike = 3.5 * math.sin(2 * math.pi * 32.0 * t_sample) * surge
                base += spike
                
            y_px = y_center - int(base * 42.0)
            pts.append((60 + x, y_px))
            
        if len(pts) > 1:
            draw.line(pts, fill=color, width=2)
            lead_pt = pts[-1]
            draw.ellipse([(lead_pt[0]-4, lead_pt[1]-4), (lead_pt[0]+4, lead_pt[1]+4)], fill=(255, 255, 255))
            
    # Bottom alert status
    draw.rectangle([(0, 1000), (width, 1080)], fill=(8, 14, 22))
    draw.line([(0, 1000), (width, 1000)], fill=(0, 180, 255), width=1)
    status = "STATUS: SYNCHRONIZED THALAMOCORTICAL ABNORMALITY DETECTED" if anomaly_active else "STATUS: REM-NREM TRANSITIONAL PATTERN"
    s_color = (255, 70, 70) if anomaly_active else (0, 220, 255)
    draw.text((60, 1025), status, fill=s_color, font=font_hud_md)
    
    return np.array(im)

def render_fmri_slice_frame(time_sec, duration_sec, target="amygdala", label="fMRI: AMYGDALA HYPERACTIVITY"):
    """
    Renders high-contrast procedural axial brain slice with glowing thermal heatmap overlay.
    """
    width, height = 1920, 1080
    im = Image.new("RGB", (width, height), (3, 6, 10))
    draw = ImageDraw.Draw(im)
    draw_medical_grid(draw, width, height)
    
    font_hud_sm = get_font(FONT_MONO, 22)
    font_hud_md = get_font(FONT_TITLE, 28)
    font_title = get_font(FONT_TITLE, 40)
    
    # Header HUD bar
    draw.rectangle([(0, 0), (width, 80)], fill=(12, 16, 24))
    draw.line([(0, 80), (width, 80)], fill=(255, 120, 0), width=2)
    
    draw.text((40, 22), "FUNCTIONAL MRI // NEURO-IMAGING RECONSTRUCTION", fill=(255, 140, 0), font=font_hud_md)
    draw.text((1200, 25), "AXIAL SLICE Z = -18.4 mm", fill=(200, 200, 200), font=font_hud_sm)
    
    # Center brain axial contour
    cx, cy = 960, 560
    rx, ry = 420, 480
    
    # Outer skull & brain tissue layers
    draw.ellipse([(cx - rx - 20, cy - ry - 20), (cx + rx + 20, cy + ry + 20)], outline=(40, 55, 70), width=4) # Skull
    draw.ellipse([(cx - rx, cy - ry), (cx + rx, cy + ry)], fill=(15, 25, 38), outline=(60, 90, 120), width=2) # Cortex
    
    # Ventricles (CSF spaces in center)
    draw.ellipse([(cx - 70, cy - 120), (cx - 15, cy + 80)], fill=(5, 8, 12), outline=(30, 45, 60), width=2)
    draw.ellipse([(cx + 15, cy - 120), (cx + 70, cy + 80)], fill=(5, 8, 12), outline=(30, 45, 60), width=2)
    
    # Interhemispheric fissure (vertical dividing line between hemispheres)
    draw.line([(cx, cy - ry), (cx, cy + ry)], fill=(30, 45, 60), width=2)
    
    # Target coordinates
    # Amygdala: bilateral anterior temporal (~ cx +/- 140, cy - 20)
    # Thalamus: bilateral center (~ cx +/- 80, cy - 40)
    # Motor cortex / Corpus callosum: central bridge
    hotspot_pts = []
    if target == "amygdala":
        hotspot_pts = [(cx - 130, cy + 40), (cx + 130, cy + 40)]
    elif target == "thalamus":
        hotspot_pts = [(cx - 70, cy - 30), (cx + 70, cy - 30)]
    elif target == "callosum":
        hotspot_pts = [(cx, cy - 70)]
    else:
        hotspot_pts = [(cx - 120, cy - 80)]
        
    # Animate pulsing thermal hotspots
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * 1.5 * time_sec)
    max_radius = int(60 + 20 * pulse)
    
    # Draw radial heat gradient
    for pt in hotspot_pts:
        hx, hy = pt
        for r in range(max_radius, 0, -6):
            intensity = 1.0 - (r / max_radius)
            # Inferno / Plasma thermal color: Black -> Purple -> Orange -> Bright Yellow
            red = int(min(255, intensity * 350))
            green = int(min(255, max(0, (intensity - 0.4) * 400)))
            blue = int(min(255, max(0, 120 * (1.0 - intensity * 2))))
            draw.ellipse([(hx - r, hy - r), (hx + r, hy + r)], fill=(red, green, blue))
            
        # Target crosshairs
        draw.line([(hx - 40, hy), (hx + 40, hy)], fill=(255, 255, 255), width=2)
        draw.line([(hx, hy - 40), (hx, hy + 40)], fill=(255, 255, 255), width=2)
        draw.rectangle([(hx - 25, hy - 25), (hx + 25, hy + 25)], outline=(255, 255, 0), width=1)
        
    # Left Telemetry card
    card_x = 80
    draw.rectangle([(card_x, 180), (card_x + 400, 480)], fill=(8, 14, 22), outline=(255, 120, 0), width=2)
    draw.text((card_x + 20, 200), "TARGET ANOMALY", fill=(255, 140, 0), font=font_hud_sm)
    draw.text((card_x + 20, 240), label, fill=(255, 255, 255), font=get_font(FONT_TITLE, 22))
    
    bold_signal = int(240 + 80 * pulse)
    draw.text((card_x + 20, 330), "BOLD RESPONSE:", fill=(0, 220, 255), font=font_hud_sm)
    draw.text((card_x + 20, 365), f"+{bold_signal}%", fill=(255, 220, 0), font=get_font(FONT_TITLE, 52))
    draw.text((card_x + 20, 435), "PERFUSION: HYPEREMIA", fill=(255, 80, 80), font=font_hud_sm)
    
    # Right Telemetry card
    rcard_x = 1440
    draw.rectangle([(rcard_x, 180), (rcard_x + 400, 480)], fill=(8, 14, 22), outline=(0, 180, 255), width=2)
    draw.text((rcard_x + 20, 200), "NEURAL MORPHOLOGY", fill=(0, 180, 255), font=font_hud_sm)
    draw.text((rcard_x + 20, 245), "RESOLUTION: 0.8 mm³", fill=(200, 200, 200), font=font_hud_sm)
    draw.text((rcard_x + 20, 285), "TESLA: 7.0T SCANNER", fill=(200, 200, 200), font=font_hud_sm)
    draw.text((rcard_x + 20, 325), "TR / TE: 2000 / 30 ms", fill=(200, 200, 200), font=font_hud_sm)
    draw.text((rcard_x + 20, 375), "DIAGNOSTIC STATUS:", fill=(0, 220, 255), font=font_hud_sm)
    draw.text((rcard_x + 20, 415), "ACUTE ABERRATION", fill=(255, 60, 60), font=get_font(FONT_TITLE, 26))

    # Thermal Colorbar on bottom right
    cb_x, cb_y, cb_w, cb_h = 1480, 940, 340, 25
    draw.rectangle([(cb_x, cb_y), (cb_x + cb_w, cb_y + cb_h)], outline=(100, 100, 100), width=1)
    for i in range(cb_w):
        val = i / cb_w
        red = int(min(255, val * 350))
        green = int(min(255, max(0, (val - 0.4) * 400)))
        blue = int(min(255, max(0, 120 * (1.0 - val * 2))))
        draw.line([(cb_x + i, cb_y), (cb_x + i, cb_y + cb_h)], fill=(red, green, blue))
    draw.text((cb_x, cb_y - 30), "BOLD T-SCORE: 0.0 -> 8.5", fill=(200, 200, 200), font=font_hud_sm)

    return np.array(im)

def render_dossier_card_frame(chapter_idx, total_chapters, title, icd_code, rarity, mechanism):
    """
    Renders a dramatic medical thriller dossier title card.
    """
    width, height = 1920, 1080
    im = Image.new("RGB", (width, height), (6, 9, 14))
    draw = ImageDraw.Draw(im)
    draw_medical_grid(draw, width, height)
    
    font_idx = get_font(FONT_TITLE, 140)
    font_title = get_font(FONT_TITLE, 64)
    font_hud = get_font(FONT_TITLE, 30)
    font_body = get_font(FONT_REGULAR, 26)
    
    # Outer neon border
    draw.rectangle([(80, 80), (width - 80, height - 80)], outline=(0, 255, 128), width=3)
    
    # Header tag
    draw.rectangle([(120, 50), (520, 110)], fill=(0, 255, 128))
    draw.text((140, 60), "CLASSIFIED MEDICAL CASE", fill=(0, 0, 0), font=get_font(FONT_TITLE, 26))
    
    # Giant index number
    idx_str = f"0{chapter_idx}"
    draw.text((140, 160), idx_str, fill=(0, 255, 128), font=font_idx)
    draw.text((360, 230), f"/ 0{total_chapters}", fill=(80, 120, 100), font=get_font(FONT_TITLE, 48))
    
    # Main Title
    draw.text((140, 360), title, fill=(255, 255, 255), font=font_title)
    
    # Dividers
    draw.line([(140, 460), (width - 140, 460)], fill=(0, 255, 128), width=2)
    
    # Three metadata pillars
    col_w = (width - 280) // 3
    
    # Col 1: ICD Classification
    x1 = 140
    draw.text((x1, 510), "КЛАССИФИКАЦИЯ:", fill=(0, 220, 255), font=font_hud)
    draw.text((x1, 560), icd_code, fill=(255, 255, 255), font=font_body)
    
    # Col 2: Rarity
    x2 = x1 + col_w
    draw.text((x2, 510), "РАСПРОСТРАНЕННОСТЬ:", fill=(0, 220, 255), font=font_hud)
    draw.text((x2, 560), rarity, fill=(255, 220, 100), font=font_body)
    
    # Col 3: Bio-Mechanism
    x3 = x2 + col_w
    draw.text((x3, 510), "НЕЙРОБИОЛОГИЧЕСКИЙ СБОЙ:", fill=(0, 220, 255), font=font_hud)
    # wrap text
    words = mechanism.split()
    line1 = " ".join(words[:4])
    line2 = " ".join(words[4:])
    draw.text((x3, 560), line1, fill=(255, 120, 120), font=font_body)
    if line2:
        draw.text((x3, 600), line2, fill=(255, 120, 120), font=font_body)
        
    # Bottom warning status
    draw.rectangle([(140, 850), (width - 140, 930)], fill=(20, 35, 30), outline=(0, 255, 128), width=1)
    draw.text((170, 875), "DIAGNOSTIC STATUS: IRREVERSIBLE / SPONTANEOUS SYNDROME", fill=(0, 255, 128), font=get_font(FONT_MONO, 24))
    
    return np.array(im)

def generate_video_from_renderer(renderer_func, output_path, duration_sec, fps=30, **kwargs):
    """
    Renders animation using OpenCV VideoWriter.
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (1920, 1080))
    n_frames = int(duration_sec * fps)
    
    for f in range(n_frames):
        t = f / fps
        frame_rgb = renderer_func(time_sec=t, duration_sec=duration_sec, **kwargs)
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        out.write(frame_bgr)
        
    out.release()
    print(f"[OK] Generated {output_path} ({duration_sec}s, {n_frames} frames)")

if __name__ == "__main__":
    test_dir = r"C:\Users\user\Desktop\viral_clips\src\science_factory\assets\test_medical"
    os.makedirs(test_dir, exist_ok=True)
    
    print("Testing ECG frame render...")
    f_ecg = render_ecg_frame(2.5, 5.0, start_bpm=80, end_bpm=140)
    cv2.imwrite(os.path.join(test_dir, "test_ecg.jpg"), cv2.cvtColor(f_ecg, cv2.COLOR_RGB2BGR))
    
    print("Testing EEG frame render...")
    f_eeg = render_eeg_frame(2.0, 5.0, anomaly_active=True)
    cv2.imwrite(os.path.join(test_dir, "test_eeg.jpg"), cv2.cvtColor(f_eeg, cv2.COLOR_RGB2BGR))
    
    print("Testing fMRI frame render...")
    f_fmri = render_fmri_slice_frame(2.0, 5.0, target="amygdala")
    cv2.imwrite(os.path.join(test_dir, "test_fmri.jpg"), cv2.cvtColor(f_fmri, cv2.COLOR_RGB2BGR))
    
    print("Testing Dossier frame render...")
    f_dos = render_dossier_card_frame(1, 5, "СОННЫЙ ПАРАЛИЧ", "ICD-11: 7A40", "8% населения планеты", "Рассинхронизация таламуса и мотонейронов")
    cv2.imwrite(os.path.join(test_dir, "test_dossier.jpg"), cv2.cvtColor(f_dos, cv2.COLOR_RGB2BGR))
    
    print("Medical Graphics Engine tests passed!")
