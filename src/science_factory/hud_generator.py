"""
Scientific HUD and Telemetry Generator for Science Content Factory.
Generates animated high-tech Sci-Fi telemetry, speedometers, target reticles,
and warning badges for 1080x1920 vertical Shorts.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math


def generate_target_reticle_overlay(output_path: Path, width: int = 1080, height: int = 1920) -> Path:
    """Generates a high-tech cyan targeting reticle for the needle and Earth."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cyan = (0, 240, 255, 200)
    dim_cyan = (0, 200, 220, 90)
    
    # Target brackets in upper third
    cx, cy = width // 2, int(height * 0.35)
    r = 180
    arm = 45
    
    # Corner brackets [ ]
    # Top-Left
    draw.line([(cx - r, cy - r), (cx - r + arm, cy - r)], fill=cyan, width=4)
    draw.line([(cx - r, cy - r), (cx - r, cy - r + arm)], fill=cyan, width=4)
    # Top-Right
    draw.line([(cx + r, cy - r), (cx + r - arm, cy - r)], fill=cyan, width=4)
    draw.line([(cx + r, cy - r), (cx + r, cy - r + arm)], fill=cyan, width=4)
    # Bottom-Left
    draw.line([(cx - r, cy + r), (cx - r + arm, cy + r)], fill=cyan, width=4)
    draw.line([(cx - r, cy + r), (cx - r, cy + r - arm)], fill=cyan, width=4)
    # Bottom-Right
    draw.line([(cx + r, cy + r), (cx + r - arm, cy + r)], fill=cyan, width=4)
    draw.line([(cx + r, cy + r), (cx + r, cy + r - arm)], fill=cyan, width=4)
    
    # Crosshair center tick marks
    draw.line([(cx - 25, cy), (cx + 25, cy)], fill=dim_cyan, width=2)
    draw.line([(cx, cy - 25), (cx, cy + 25)], fill=dim_cyan, width=2)
    
    # Telemetry text box near reticle
    draw.rectangle([(cx - r, cy + r + 15), (cx + r, cy + r + 55)], fill=(0, 20, 35, 160), outline=dim_cyan, width=2)
    draw.text((cx - r + 15, cy + r + 24), "[ TARGET LOCKED: EARTH // TRAJECTORY 99.9% c ]", fill=(0, 255, 255, 240))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def generate_warning_hud_overlay(output_path: Path, width: int = 1080, height: int = 1920) -> Path:
    """Generates a flashing red/orange critical warning badge for atmospheric impact."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    red = (255, 40, 40, 240)
    bg_red = (60, 0, 10, 190)
    
    bx1, by1 = 120, int(height * 0.18)
    bx2, by2 = width - 120, int(height * 0.26)
    
    # Outer glowing border
    draw.rectangle([(bx1 - 4, by1 - 4), (bx2 + 4, by2 + 4)], outline=(255, 100, 50, 180), width=3)
    draw.rectangle([(bx1, by1), (bx2, by2)], fill=bg_red, outline=red, width=4)
    
    # Warning text
    text_main = "! CRITICAL: THERMONUCLEAR CASCADE !"
    text_sub = "RELATIVISTIC KINETIC DETONATION DETECTED"
    
    # Center text approximately
    draw.text((bx1 + 70, by1 + 25), text_main, fill=(255, 240, 240, 255))
    draw.text((bx1 + 55, by1 + 75), text_sub, fill=(255, 180, 100, 230))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


if __name__ == "__main__":
    generate_target_reticle_overlay(Path("test_reticle.png"))
    generate_warning_hud_overlay(Path("test_warning.png"))
    print("HUD overlays created successfully!")
