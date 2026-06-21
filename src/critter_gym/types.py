"""Elemental types and the (fixed, deterministic) type-effectiveness chart.

M1 ships a minimal rock-paper-scissors cycle over 3 types. The chart is the only
source of damage multipliers, so battles are fully determined by it. A later task
(`typechart-fixed`) expands the type count / balancing — `TypeChart` is data-driven
so that expansion is a table swap, not a code change.
"""

from __future__ import annotations

from enum import Enum

SUPER_EFFECTIVE = 2.0
NOT_VERY_EFFECTIVE = 0.5
NEUTRAL = 1.0


class ElementType(Enum):
    """Elemental types. M1 = a 3-cycle (FIRE > GRASS > WATER > FIRE)."""

    FIRE = "fire"
    WATER = "water"
    GRASS = "grass"


# attacker -> set of types it is SUPER_EFFECTIVE against (rock-paper-scissors cycle).
_BEATS: dict[ElementType, ElementType] = {
    ElementType.FIRE: ElementType.GRASS,
    ElementType.GRASS: ElementType.WATER,
    ElementType.WATER: ElementType.FIRE,
}


class TypeChart:
    """Fixed type-effectiveness lookup.

    ``effectiveness`` of an attacking type against one defending type is one of
    SUPER_EFFECTIVE / NOT_VERY_EFFECTIVE / NEUTRAL. Against a multi-type defender
    the per-type multipliers are multiplied together (standard convention).
    """

    def effectiveness(self, attacker: ElementType, defender: ElementType) -> float:
        if _BEATS[attacker] is defender:
            return SUPER_EFFECTIVE
        if _BEATS[defender] is attacker:
            return NOT_VERY_EFFECTIVE
        return NEUTRAL

    def multi_effectiveness(
        self, attacker: ElementType, defenders: tuple[ElementType, ...]
    ) -> float:
        mult = NEUTRAL
        for d in defenders:
            mult *= self.effectiveness(attacker, d)
        return mult
