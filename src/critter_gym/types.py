"""Elemental types and the type-effectiveness chart (data-driven).

A ``TypeChart`` is just a set of "(attacker) is super-effective against (defender)"
pairs, so charts can be *generated per seed* (``generate_typechart``) rather than
hardcoded. Per-seed charts are the project's deepest moat: the agent cannot assume
a fixed FIRE>GRASS>WATER meta and must **infer the matchup table from experience**
(DESIGN.md §3.1). The chart is never placed in the observation — only the type
*ids* are — so inference is the only route.

``TypeChart()`` defaults to the fixed M1 rock-paper-scissors chart, so fixed-world
behavior is unchanged.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

SUPER_EFFECTIVE = 2.0
NOT_VERY_EFFECTIVE = 0.5
NEUTRAL = 1.0


class ElementType(Enum):
    """Elemental types. The fixed chart is a 3-cycle (FIRE > GRASS > WATER > FIRE)."""

    FIRE = "fire"
    WATER = "water"
    GRASS = "grass"


# Fixed (M1) chart: (attacker, defender) pairs where attacker is super-effective.
_FIXED_BEATS: frozenset[tuple[ElementType, ElementType]] = frozenset(
    {
        (ElementType.FIRE, ElementType.GRASS),
        (ElementType.GRASS, ElementType.WATER),
        (ElementType.WATER, ElementType.FIRE),
    }
)


@dataclass(frozen=True)
class TypeChart:
    """Type-effectiveness lookup defined by its super-effective ``beats`` pairs.

    ``effectiveness(a, b)`` is SUPER if ``(a, b)`` is a beats pair, NOT_VERY if
    ``(b, a)`` is, else NEUTRAL. Construction is antisymmetric by convention (a
    pair and its reverse never coexist), so the chart is internally consistent.
    Defaults to the fixed M1 chart.
    """

    beats: frozenset[tuple[ElementType, ElementType]] = field(default=_FIXED_BEATS)

    def effectiveness(self, attacker: ElementType, defender: ElementType) -> float:
        if (attacker, defender) in self.beats:
            return SUPER_EFFECTIVE
        if (defender, attacker) in self.beats:
            return NOT_VERY_EFFECTIVE
        return NEUTRAL

    def multi_effectiveness(
        self, attacker: ElementType, defenders: tuple[ElementType, ...]
    ) -> float:
        mult = NEUTRAL
        for d in defenders:
            mult *= self.effectiveness(attacker, d)
        return mult


FIXED_CHART = TypeChart()


def generate_typechart(
    seed: int, types: Iterable[ElementType] | None = None, *, vary: bool = False
) -> TypeChart:
    """Deterministically build a type chart from ``seed``.

    ``vary=False`` returns the fixed M1 chart. ``vary=True`` orients each unordered
    type pair by a per-seed coin flip — antisymmetric and contradiction-free by
    construction, but un-memorizable across seeds.
    """
    if not vary:
        return FIXED_CHART
    type_list = list(ElementType) if types is None else list(types)
    rng = np.random.default_rng(seed)
    beats: set[tuple[ElementType, ElementType]] = set()
    for a, b in itertools.combinations(type_list, 2):
        if int(rng.integers(0, 2)) == 0:
            beats.add((a, b))
        else:
            beats.add((b, a))
    return TypeChart(frozenset(beats))
