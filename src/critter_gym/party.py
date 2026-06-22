"""Fixed starter party and gym-boss factory for M1 (deterministic).

M1 is a fixed world (no procgen — that is M2), so parties and bosses are fixed
data, not seeded. The starter party holds one creature of each element so a
type-advantaged option always exists; each gym boss is a single creature whose
type is beaten by one party member (keeps gyms winnable with the right switch).
"""

from __future__ import annotations

from critter_gym.creatures import Creature, Move
from critter_gym.types import ElementType

F, W, G = ElementType.FIRE, ElementType.WATER, ElementType.GRASS

# Gym i's boss type. FIRE>GRASS>WATER>FIRE, so the beating party member is:
#   GRASS boss -> FIRE,  FIRE boss -> WATER.
_BOSS_TYPES: list[ElementType] = [G, F]


def starter_party() -> list[Creature]:
    """The fixed M1 player party: one creature per element."""
    return [
        Creature("Emberling", (F,), 50, 12, 10, 11, [Move("flare", F, 30)]),
        Creature("Tideling", (W,), 50, 12, 10, 10, [Move("douse", W, 30)]),
        Creature("Leafling", (G,), 50, 12, 10, 9, [Move("vine", G, 30)]),
    ]


def gym_boss(index: int) -> list[Creature]:
    """The boss party for gym ``index`` (single tanky creature)."""
    t = _BOSS_TYPES[index % len(_BOSS_TYPES)]
    return [Creature(f"Warden-{index}", (t,), 120, 12, 12, 8, [Move("strike", t, 30)])]
