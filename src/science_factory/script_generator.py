"""
High-Retention Script Generator for Short-form Science Videos.
Generates Multi-Hook variants, body narrative, visual scene mapping, and timing markers.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .fact_checker import calculate_relativistic_impact, PhysicsFactSheet


@dataclass
class VisualScenePrompt:
    scene_id: int
    name: str
    duration_ratio: float  # Fraction of total video length
    visual_description: str
    image_prompt: str
    camera_motion: str  # zoom_in, zoom_out, pan_up, pan_down


@dataclass
class ScienceScript:
    topic: str
    hooks: List[str]
    selected_hook: str
    full_text: str
    segments: List[Dict[str, Any]]
    scenes: List[VisualScenePrompt]


def build_needle_lightspeed_script(hook_variant_idx: int = 0) -> ScienceScript:
    facts = calculate_relativistic_impact()
    
    hook_variants = [
        "Обычная швейная игла способна стереть с лица земли целый город, если разогнать ее почти до скорости света.",
        "Что произойдет, если крошечная иголка врежется в Землю на девяноста девяти процентах скорости света?",
        "Вам кажется, что маленькая иголка просто сгорит в атмосфере? Законы физики утверждают обратное."
    ]
    
    selected_hook = hook_variants[hook_variant_idx % len(hook_variants)]
    
    segments = [
        {
            "id": 1,
            "scene_id": 1,
            "title": "Хук и масштаб проблемы",
            "text": selected_hook,
            "role": "hook"
        },
        {
            "id": 2,
            "scene_id": 2,
            "title": "Релятивистская физика",
            "text": "При приближении к скорости света вступает в силу теория относительности. Маленькая игла массой всего пять миллиграммов накапливает чудовищную кинетическую энергию, равную тысячам тонн тротила.",
            "role": "exposition"
        },
        {
            "id": 3,
            "scene_id": 3,
            "title": "Столкновение с атмосферой",
            "text": "При входе в атмосферу молекулы воздуха просто не успеют расступиться. Атомы иглы столкнутся с воздухом на субатомном уровне, вызвав термоядерную вспышку и превратив иглу в ослепительный шар плазмы.",
            "role": "action"
        },
        {
            "id": 4,
            "scene_id": 4,
            "title": "Кульминация и панчлайн",
            "text": "Взрыв выжжет всё на десятки километров вокруг, породив сейсмическую волну планетарного масштаба. Вот почему законы Вселенной запрещают материальным объектам достигать абсолютной скорости света.",
            "role": "climax"
        }
    ]
    
    full_text = " ".join([seg["text"] for seg in segments])
    
    scenes = [
        VisualScenePrompt(
            scene_id=1,
            name="space_needle_closeup",
            duration_ratio=0.22,
            visual_description="Макро-план кончика стальной иглы в открытом космосе",
            image_prompt=(
                "cinematic macro shot of a sharp steel sewing needle floating in deep outer space, "
                "stars and distant nebula in background, cold harsh cosmic rim lighting, sharp metallic reflection, "
                "epic science documentary style, ultra photorealistic, 8k, vertical 9:16 aspect ratio"
            ),
            camera_motion="zoom_in"
        ),
        VisualScenePrompt(
            scene_id=2,
            name="relativistic_acceleration",
            duration_ratio=0.28,
            visual_description="Игла на околосветовой скорости с синим свечением Черенкова",
            image_prompt=(
                "relativistic high speed needle speeding through space at near speed of light, "
                "intense glowing blue Cherenkov radiation aura, warped starlight background, relativistic doppler effect, "
                "lens flares, hyper-detailed cosmic physics visual, vertical 9:16 aspect ratio"
            ),
            camera_motion="pan_up"
        ),
        VisualScenePrompt(
            scene_id=3,
            name="atmospheric_plasma_shockwave",
            duration_ratio=0.28,
            visual_description="Гиперзвуковая плазменная ударная волна в стратосфере Земли",
            image_prompt=(
                "extreme hypersonic kinetic projectile entering Earth upper atmosphere, "
                "massive blinding thermonuclear white-hot plasma shockwave, ionized air cone, curvature of Earth below, "
                "atmospheric friction detonation, ultra realistic CGI science visual, vertical 9:16 aspect ratio"
            ),
            camera_motion="zoom_in"
        ),
        VisualScenePrompt(
            scene_id=4,
            name="orbital_kinetic_explosion",
            duration_ratio=0.22,
            visual_description="Ослепительный кинетический взрыв с орбиты планеты",
            image_prompt=(
                "colossal kinetic energy explosion on Earth surface viewed from low Earth orbit, "
                "blinding spherical shockwave expanding over continents and clouds, incandescent orange and golden glow, "
                "epic planetary catastrophe scale, cinematic IMAX science visual, vertical 9:16 aspect ratio"
            ),
            camera_motion="zoom_out"
        )
    ]
    
    return ScienceScript(
        topic="Needle at Speed of Light",
        hooks=hook_variants,
        selected_hook=selected_hook,
        full_text=full_text,
        segments=segments,
        scenes=scenes
    )


if __name__ == "__main__":
    script = build_needle_lightspeed_script(0)
    print("SELECTED HOOK:", script.selected_hook)
    print("TOTAL TEXT LENGTH:", len(script.full_text), "chars")
    for s in script.scenes:
        print(f"Scene {s.scene_id}: {s.name} ({s.camera_motion})")
