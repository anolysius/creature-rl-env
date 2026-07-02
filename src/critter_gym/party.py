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


def gym_boss(
    boss_type: ElementType,
    index: int = 0,
    *,
    hp: int = 120,
    atk: int = 12,
    df: int = 12,
    spd: int = 8,
    secondary_type: ElementType | None = None,
) -> list[Creature]:
    """The boss party for a gym of ``boss_type`` (single tanky creature).

    Stats default to the M1 values; ``hp``/``atk``/``df``/``spd`` are difficulty
    knobs (reasoning-load-bearing AC2) — a stronger boss punishes a wrong type
    commit so the correct (inferred) matchup becomes decisive.

    ``secondary_type`` (optional) gives the boss a HIDDEN second defending type: its
    defence is then the *product* of both types' effectiveness (deeper hidden-rule
    inference). The boss's move stays single-type (``boss_type``). ``None`` = single-type
    (byte-identical to the historical boss).
    """
    types = (boss_type,) if secondary_type is None else (boss_type, secondary_type)
    return [
        Creature(
            f"Warden-{index}", types, hp, atk, df, spd,
            [Move("strike", boss_type, 30)],
        )
    ]
