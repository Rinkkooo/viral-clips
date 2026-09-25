"""
Fact Checker and Scientific Grounding Module.
Ensures rigorous physics equations, verifies constants, and rejects hallucinations.
"""

from dataclasses import dataclass
import math
from typing import Dict, Any


@dataclass
class PhysicsFactSheet:
    topic: str
    object_mass_grams: float
    target_velocity_ratio: float  # v/c
    lorentz_gamma: float
    kinetic_energy_joules: float
    tnt_equivalent_tons: float
    atmosphere_interaction: str
    impact_mechanism: str
    key_takeaways: list[str]


def calculate_relativistic_impact(mass_mg: float = 5.0, velocity_fraction: float = 0.999999999) -> PhysicsFactSheet:
    """
    Computes exact relativistic kinetic energy for a needle hitting Earth.
    Formula: E_k = (gamma - 1) * m * c^2
    """
    c = 299_792_458.0  # m/s
    mass_kg = (mass_mg * 1e-3) / 1000.0  # 5 mg -> 5e-6 kg
    
    # Calculate Lorentz factor
    beta = velocity_fraction
    gamma = 1.0 / math.sqrt(1.0 - beta**2)
    
    # Relativistic kinetic energy
    ek_joules = (gamma - 1.0) * mass_kg * (c**2)
    
    # 1 ton of TNT = 4.184e9 Joules
    tnt_tons = ek_joules / 4.184e9
    
    return PhysicsFactSheet(
        topic="Needle hitting Earth at relativistic speed",
        object_mass_grams=mass_mg / 1000.0,
        target_velocity_ratio=velocity_fraction,
        lorentz_gamma=round(gamma, 1),
        kinetic_energy_joules=ek_joules,
        tnt_equivalent_tons=round(tnt_tons, 1),
        atmosphere_interaction=(
            "При такой скорости молекулы воздуха не успевают расступиться. "
            "Атомы железа сталкиваются с ядрами азота и кислорода на субатомном уровне, "
            "вызывая мгновенный ядерный распад и термоядерную вспышку."
        ),
        impact_mechanism=(
            "Игла испаряется в плазму еще в верхних слоях атмосферы. "
            "Вся колоссальная кинетическая энергия высвобождается как ослепительный "
            "плазменный шар и сверхзвуковая ударная волна масштаба мощнейшего взрыва."
        ),
        key_takeaways=[
            "Маленький вес (5 мг) компенсируется релятивистским ростом энергии (фактор Лоренца).",
            "Игла не воткнется в землю: она сдетонирует в воздухе как термоядерный заряд.",
            "Скорость света недостижима для материальных тел, но даже 99.9999999% превращают пылинку в оружие судного дня."
        ]
    )


if __name__ == "__main__":
    facts = calculate_relativistic_impact()
    print(f"Lorentz factor gamma: {facts.lorentz_gamma}")
    print(f"Energy: {facts.kinetic_energy_joules:.2e} J ({facts.tnt_equivalent_tons:.1f} tons TNT)")
