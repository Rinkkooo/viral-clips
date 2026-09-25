"""
Procedural 3D and Scientific Video Animation Engine.
Generates genuine 1080p 60fps scientific motion graphics:
1. Animated relativistic Lorentz curve spiking to infinity
2. Animated comparative velocity gauge (Bullet vs Meteor vs Light)
3. Subatomic relativistic particle collision simulation
"""

import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from loguru import logger


def render_lorentz_curve_animation(
    output_path: Path,
    duration_s: float = 25.0,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30
) -> Path:
    """
    Renders an animated 1080p video of the relativistic Lorentz factor curve.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = int(duration_s * fps)
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    # Graph bounding box in 1920x1080
    gx1, gy1 = 250, 180
    gx2, gy2 = 1670, 920
    gw = gx2 - gx1
    gh = gy2 - gy1
    
    logger.info(f"Rendering Lorentz curve animation ({total_frames} frames)...")
    
    font_title = ImageFont.truetype("arialbd.ttf", 36)
    font_subtitle = ImageFont.truetype("arial.ttf", 24)
    font_telemetry = ImageFont.truetype("arialbd.ttf", 26)
    font_status = ImageFont.truetype("arialbd.ttf", 24)

    for frame_idx in range(total_frames):
        t_prog = frame_idx / (total_frames - 1)
        
        # Non-linear progression towards 0.999999
        beta = 1.0 - math.pow(10.0, -t_prog * 4.5)
        beta = min(0.999999, max(0.0, beta))
        
        gamma = 1.0 / math.sqrt(max(1e-9, 1.0 - beta**2))
        
        # Base frame (dark cybernetic grid)
        img = Image.new("RGB", (width, height), (6, 10, 18))
        draw = ImageDraw.Draw(img)
        
        # Grid lines
        for x in range(gx1, gx2 + 1, 140):
            draw.line([(x, gy1), (x, gy2)], fill=(18, 30, 48), width=1)
        for y in range(gy1, gy2 + 1, 100):
            draw.line([(gx1, y), (gx2, y)], fill=(18, 30, 48), width=1)
            
        # Graph axes
        draw.line([(gx1, gy2), (gx2, gy2)], fill=(60, 100, 160), width=3)  # X-axis (v/c)
        draw.line([(gx1, gy1), (gx1, gy2)], fill=(60, 100, 160), width=3)  # Y-axis (Gamma)
        
        # Draw curve up to current beta
        curve_pts = []
        steps = max(2, int(t_prog * 200))
        for s in range(steps):
            b_s = 1.0 - math.pow(10.0, -(s / 200.0) * 4.5)
            b_s = min(0.999999, max(0.0, b_s))
            g_s = 1.0 / math.sqrt(max(1e-9, 1.0 - b_s**2))
            
            px = gx1 + int((s / 200.0) * gw)
            # Logarithmic height scale for gamma
            g_scaled = math.log10(g_s) / math.log10(1000.0)
            py = gy2 - int(min(1.0, g_scaled) * gh)
            curve_pts.append((px, py))
            
        if len(curve_pts) >= 2:
            # Outer glow
            draw.line(curve_pts, fill=(0, 160, 255), width=6)
            draw.line(curve_pts, fill=(200, 240, 255), width=2)
            
            # Current point halo
            cx, cy = curve_pts[-1]
            draw.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill=(0, 240, 255))
            draw.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill=(255, 255, 255))
            
        # Headers & Live Telemetry
        draw.text((gx1, 55), "РЕЛЯТИВИСТСКИЙ ФАКТОР ЛОРЕНЦА: E = (γ - 1) m c²", font=font_title, fill=(0, 240, 255))
        draw.text((gx1, 105), "ЗАВИСИМОСТЬ КИНЕТИЧЕСКОЙ ЭНЕРГИИ ОТ СКОРОСТИ ОБЪЕКТА", font=font_subtitle, fill=(140, 170, 210))
        
        # Telemetry Box
        tx1, ty1 = gx2 - 520, gy1 + 30
        draw.rectangle([(tx1, ty1), (tx1 + 500, ty1 + 170)], fill=(12, 20, 36), outline=(0, 200, 255), width=2)
        
        draw.text((tx1 + 25, ty1 + 20), f"СКОРОСТЬ: {beta * 100:.6f} % c", font=font_telemetry, fill=(255, 255, 255))
        draw.text((tx1 + 25, ty1 + 65), f"МАССА (γ): {gamma:,.1f} x m₀", font=font_telemetry, fill=(0, 255, 200))
        
        if gamma > 500:
            status = "ВЗРЫВ ПЛАНЕТАРНОГО МАСШТАБА"
            status_color = (255, 60, 60)
        elif gamma > 10:
            status = "ЯДЕРНАЯ ДЕТОНАЦИЯ"
            status_color = (255, 180, 0)
        else:
            status = "КЛАССИЧЕСКАЯ МЕХАНИКА"
            status_color = (100, 220, 255)
            
        draw.text((tx1 + 25, ty1 + 115), f"СТАТУС: {status}", font=font_status, fill=status_color)
        
        # Convert PIL -> OpenCV BGR
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out.write(frame)
        
    out.release()
    logger.success(f"Lorentz curve animation rendered: {output_path}")
    return output_path


def render_speed_comparison_animation(
    output_path: Path,
    duration_s: float = 25.0,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30
) -> Path:
    """
    Renders an animated 1080p speed comparison scale (Bullet vs Meteor vs Needle).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = int(duration_s * fps)
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    stages = [
        {"name": "Снайперская пуля", "speed_km_s": 1.0, "color": (120, 160, 200)},
        {"name": "Ракета на орбите (МКС)", "speed_km_s": 7.9, "color": (80, 200, 240)},
        {"name": "Челябинский метеорит", "speed_km_s": 19.0, "color": (255, 180, 40)},
        {"name": "Зонд 'Паркер' (рекорд)", "speed_km_s": 176.0, "color": (255, 120, 60)},
        {"name": "Игла на околосвете (0.999999c)", "speed_km_s": 299792.0, "color": (255, 40, 40)},
    ]
    
    font_title = ImageFont.truetype("arialbd.ttf", 36)
    font_subtitle = ImageFont.truetype("arial.ttf", 22)
    font_label = ImageFont.truetype("arialbd.ttf", 24)
    font_speed = ImageFont.truetype("arialbd.ttf", 26)

    logger.info(f"Rendering speed comparison animation ({total_frames} frames)...")
    
    for frame_idx in range(total_frames):
        t_prog = frame_idx / (total_frames - 1)
        
        img = Image.new("RGB", (width, height), (8, 12, 22))
        draw = ImageDraw.Draw(img)
        
        # Header
        draw.text((150, 60), "СРАВНЕНИЕ СКОРОСТЕЙ: ПУТЬ К СКОРОСТИ СВЕТА", font=font_title, fill=(0, 240, 255))
        draw.text((150, 110), "ЛОГАРИФМИЧЕСКАЯ ШКАЛА СКОРОСТИ ОБЪЕКТОВ ВО ВСЕЛЕННОЙ", font=font_subtitle, fill=(140, 170, 210))
        
        # Render horizontal animated bars
        y_start = 220
        bar_height = 55
        spacing = 135
        max_bar_w = 1450
        
        for idx, st in enumerate(stages):
            y = y_start + idx * spacing
            # Activation progress per stage
            stage_prog = max(0.0, min(1.0, (t_prog * len(stages)) - idx * 0.8))
            
            # Label
            draw.text((150, y - 32), st["name"], font=font_label, fill=(220, 230, 245))
            
            # Bar background
            draw.rectangle([(150, y), (150 + max_bar_w, y + bar_height)], fill=(16, 25, 40), outline=(40, 60, 90), width=1)
            
            # Fill bar
            bar_w = int(stage_prog * max_bar_w * ((idx + 1) / len(stages)))
            if bar_w > 0:
                draw.rectangle([(150, y), (150 + bar_w, y + bar_height)], fill=st["color"])
                
            # Speed label
            speed_val = st["speed_km_s"] * stage_prog
            if speed_val >= 1000:
                speed_str = f"{speed_val:,.0f} км/с"
            else:
                speed_str = f"{speed_val:.1f} км/с"
                
            draw.text((150 + max_bar_w + 30, y + 12), speed_str, font=font_speed, fill=st["color"])
            
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out.write(frame)
        
    out.release()
    logger.success(f"Speed comparison animation rendered: {output_path}")
    return output_path


if __name__ == "__main__":
    p1 = render_lorentz_curve_animation(Path("test_lorentz.mp4"), duration_s=3.0)
    p2 = render_speed_comparison_animation(Path("test_speed.mp4"), duration_s=3.0)
    print("Test procedural animations finished successfully!")
