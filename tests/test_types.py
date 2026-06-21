"""AC1: type-effectiveness chart (fixed rock-paper-scissors cycle)."""

from __future__ import annotations

from critter_gym.types import (
    NEUTRAL,
    NOT_VERY_EFFECTIVE,
    SUPER_EFFECTIVE,
    ElementType,
    TypeChart,
)

F, W, G = ElementType.FIRE, ElementType.WATER, ElementType.GRASS


def test_rock_paper_scissors_cycle() -> None:
    chart = TypeChart()
    # FIRE > GRASS > WATER > FIRE
    assert chart.effectiveness(F, G) == SUPER_EFFECTIVE
    assert chart.effectiveness(G, W) == SUPER_EFFECTIVE
    assert chart.effectiveness(W, F) == SUPER_EFFECTIVE
    # reverse direction is not-very-effective
    assert chart.effectiveness(G, F) == NOT_VERY_EFFECTIVE
    assert chart.effectiveness(W, G) == NOT_VERY_EFFECTIVE
    assert chart.effectiveness(F, W) == NOT_VERY_EFFECTIVE


def test_same_type_is_neutral() -> None:
    chart = TypeChart()
    for t in ElementType:
        assert chart.effectiveness(t, t) == NEUTRAL


def test_multi_type_multiplies() -> None:
    chart = TypeChart()
    # FIRE vs (GRASS, GRASS): 2.0 * 2.0 = 4.0
    assert chart.multi_effectiveness(F, (G, G)) == 4.0
    # FIRE vs (GRASS, WATER): 2.0 * 0.5 = 1.0
    assert chart.multi_effectiveness(F, (G, W)) == 1.0
    # single defender
    assert chart.multi_effectiveness(F, (G,)) == SUPER_EFFECTIVE
