"""AC1: type-effectiveness chart (fixed rock-paper-scissors cycle)."""

from __future__ import annotations

from critter_gym.types import (
    FIXED_CHART,
    NEUTRAL,
    NOT_VERY_EFFECTIVE,
    SUPER_EFFECTIVE,
    ElementType,
    TypeChart,
    generate_typechart,
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


# --- data-driven + procedural charts (M2-EC2: AC1/AC2/AC3) --------------------

def test_default_chart_is_fixed_and_comparable() -> None:
    """AC1: TypeChart() is the fixed M1 chart and charts compare by value."""
    assert TypeChart() == FIXED_CHART
    assert generate_typechart(0, vary=False) == FIXED_CHART
    assert FIXED_CHART.effectiveness(F, G) == SUPER_EFFECTIVE  # M1 preserved


def _is_internally_consistent(chart: TypeChart) -> bool:
    for a in ElementType:
        if chart.effectiveness(a, a) != NEUTRAL:  # no self super/weak
            return False
        for b in ElementType:
            if a is b:
                continue
            ab, ba = chart.effectiveness(a, b), chart.effectiveness(b, a)
            if ab == SUPER_EFFECTIVE and ba != NOT_VERY_EFFECTIVE:
                return False
            if ab == NOT_VERY_EFFECTIVE and ba != SUPER_EFFECTIVE:
                return False
    return True


def test_generated_chart_is_consistent_and_deterministic() -> None:
    """AC2: per-seed charts are antisymmetric / self-neutral and reproducible."""
    for seed in range(30):
        c = generate_typechart(seed, vary=True)
        assert _is_internally_consistent(c)
        assert c == generate_typechart(seed, vary=True)  # determinism


def test_generated_charts_vary_and_can_differ_from_fixed() -> None:
    """AC3: seeds yield more than one chart, and at least one differs from fixed."""
    charts = {generate_typechart(s, vary=True) for s in range(40)}
    assert len(charts) > 1
    assert any(generate_typechart(s, vary=True) != FIXED_CHART for s in range(40))
