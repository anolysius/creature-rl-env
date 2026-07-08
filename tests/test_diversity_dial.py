"""Per-episode type-diversity dial (diversity-dial).

The prior scout falsified num_types as the inference-difficulty dial: the recurrence pool caps
distinct boss-types at ~2 per world. This tests the real candidate — an opt-in ``boss_pool_size``
knob that controls how many distinct boss types recur per world — and the diversity curve built
on it. Default (``None``) is byte-identical to the current world.
"""

from __future__ import annotations

from critter_gym.region import generate_region

_KW = dict(vary=True, num_types=12, min_gyms=8)


def _distinct_boss_types(region) -> int:
    return len({t for (_, t) in region.gyms})


# -- AC1: opt-in knob, default byte-identical ----------------------------------


def test_default_pool_is_byte_identical() -> None:
    """boss_pool_size=None reproduces the current region exactly (no RNG-stream drift)."""
    for seed in (0, 7, 100_000, 100_001):
        a = generate_region(seed, 10, 5, 8, **_KW)
        b = generate_region(seed, 10, 5, 8, boss_pool_size=None, **_KW)
        assert a.gyms == b.gyms
        assert a.boss_secondary_types == b.boss_secondary_types
        # the chart + creatures + agent start are untouched too
        assert a.creatures == b.creatures and a.agent_start == b.agent_start


def test_pool_size_one_gives_single_boss_type() -> None:
    """boss_pool_size=1 => every gym in a world is the same type (max recurrence)."""
    for seed in range(100_000, 100_006):
        r = generate_region(seed, 10, 5, 8, boss_pool_size=1, **_KW)
        assert _distinct_boss_types(r) == 1


def test_larger_pool_raises_distinct_types() -> None:
    """A bigger pool exposes strictly more distinct boss types per world (on average)."""
    def mean_distinct(pool: int) -> float:
        rs = [generate_region(s, 10, 5, 8, boss_pool_size=pool, **_KW)
              for s in range(100_000, 100_008)]
        return sum(_distinct_boss_types(r) for r in rs) / len(rs)

    assert mean_distinct(1) < mean_distinct(4) < mean_distinct(8)


def test_pool_clamped_to_available_types() -> None:
    """A pool larger than the exploitable-type count does not crash; it clamps."""
    r = generate_region(100_000, 10, 5, 8, boss_pool_size=999, **_KW)
    assert _distinct_boss_types(r) >= 1  # clamped, still a valid world


# -- AC3: the diversity curve API ----------------------------------------------


def test_diversity_curve_structure_and_determinism() -> None:
    from critter_gym.inference_curve import DiversityPoint, diversity_curve

    grid = (1, 2)
    a = diversity_curve(grid)
    b = diversity_curve(grid)
    assert a == b                                   # deterministic
    assert len(a) == len(grid)
    assert tuple(p.pool_size for p in a) == grid
    for p in a:
        assert isinstance(p, DiversityPoint)
        assert p.oracle_se >= p.type_blind_se       # band discriminates
        assert 0.0 <= p.infer_score <= 1.0
        assert p.mean_distinct_types >= 1.0         # measured diversity x-axis
