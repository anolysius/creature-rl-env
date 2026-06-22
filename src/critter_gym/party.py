"""Fixed starter party and gym-boss factory for M1 (deterministic).

M1 is a fixed world (no procgen — that is M2), so parties and bosses are fixed
data, not seeded. The starter party holds one creature of each element so a
type-advantaged option always exists; each gym boss is a single creature whose
type is beaten by one party member (keeps gyms winnable with the right switch).
"""

from __future__ import annotations

from critter_gym.creatures import Creature, EvolvedForm, Move
from critter_gym.types import ElementType

F, W, G = ElementType.FIRE, ElementType.WATER, ElementType.GRASS


def starter_party() -> list[Creature]:
    """The fixed M1 player party: one creature per element, each with an
    evolved form (stronger stats) reachable by winning battles."""
    return [
        Creature(
            "Emberling", (F,), 50, 12, 10, 11, [Move("flare", F, 30)],
            evolves_to=EvolvedForm("Emberon", 80, 19, 14, 13),
        ),
        Creature(
            "Tideling", (W,), 50, 12, 10, 10, [Move("douse", W, 30)],
            evolves_to=EvolvedForm("Tidalon", 80, 19, 14, 12),
        ),
        Creature(
            "Leafling", (G,), 50, 12, 10, 9, [Move("vine", G, 30)],
            evolves_to=EvolvedForm("Leafkin", 80, 19, 14, 11),
        ),
    ]


def gym_boss(boss_type: ElementType, index: int = 0) -> list[Creature]:
    """The boss party for a gym of ``boss_type`` (single tanky creature)."""
    return [
        Creature(
            f"Warden-{index}", (boss_type,), 120, 12, 12, 8,
            [Move("strike", boss_type, 30)],
        )
    ]
