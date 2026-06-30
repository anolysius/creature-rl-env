"""AC1/AC2/AC4: procedural region generation + train/test seed split."""

from __future__ import annotations

import pytest

from critter_gym.eval_harness import SealedEvalSet, score_inference_telemetry
from critter_gym.learnability import reference_arm
from critter_gym.region import (
    _STARTER_TYPES,
    TEST_SEED_OFFSET,
    generate_region,
    heldout_seeds,
    is_held_out,
    train_seeds,
)
from critter_gym.types import NEUTRAL


def test_generate_region_is_deterministic() -> None:
    """AC1: same seed -> identical region; positions in-bounds and disjoint."""
    a = generate_region(7, vary=True)
    b = generate_region(7, vary=True)
    assert a == b
    occupied = [*a.creatures, *(p for p, _ in a.gyms), a.agent_start]
    assert len(occupied) == len(set(occupied))  # all disjoint
    for r, c in occupied:
        assert 0 <= r < a.grid_size and 0 <= c < a.grid_size


def test_fixed_mode_matches_max_counts() -> None:
    r = generate_region(0, max_creatures=5, max_gyms=3, vary=False)
    assert len(r.creatures) == 5 and len(r.gyms) == 3


def test_vary_produces_variation_and_min_one_gym() -> None:
    """AC2: across seeds, vary regions differ; gym count is always >= 1."""
    regions = [generate_region(s, vary=True) for s in range(30)]
    gym_counts = {len(r.gyms) for r in regions}
    creature_counts = {len(r.creatures) for r in regions}
    boss_seqs = {tuple(t for _, t in r.gyms) for r in regions}
    # at least one dimension varies (disjunctive — robust to coincidences)
    assert len(gym_counts) > 1 or len(creature_counts) > 1 or len(boss_seqs) > 1
    assert min(len(r.gyms) for r in regions) >= 1  # termination contract stays valid


def test_train_heldout_seeds_are_disjoint() -> None:
    """AC4: train and test seed blocks never overlap."""
    assert set(train_seeds(1000)).isdisjoint(set(heldout_seeds(1000)))
    assert not is_held_out(0) and is_held_out(TEST_SEED_OFFSET)


def test_train_seeds_overrun_is_rejected() -> None:
    """AC4: a train block that would reach into the held-out range raises."""
    with pytest.raises(ValueError):
        train_seeds(TEST_SEED_OFFSET + 1)


def test_train_and_test_regions_do_not_leak() -> None:
    """AC4: a train-seed region is never identical to a test-seed region."""
    train_regions = {repr(generate_region(s, vary=True)) for s in train_seeds(50)}
    test_regions = {repr(generate_region(s, vary=True)) for s in heldout_seeds(50)}
    assert train_regions.isdisjoint(test_regions)


def test_region_carries_deterministic_per_seed_chart() -> None:
    """AC6: the region holds a per-seed type chart, reproducible by seed."""
    a = generate_region(11, vary=True)
    b = generate_region(11, vary=True)
    assert a.chart == b.chart


def test_train_and_heldout_charts_can_differ() -> None:
    """AC6: train and held-out seed samples each exercise multiple charts
    (no split collapse to one shared/fixed table)."""
    train_charts = {generate_region(s, vary=True).chart for s in train_seeds(40)}
    held_charts = {generate_region(s, vary=True).chart for s in heldout_seeds(40)}
    assert len(train_charts) > 1 and len(held_charts) > 1


# -- matchup validity: every placed boss must be inference-exploitable -----------
# The eval measures whether an agent infers the hidden type chart and exploits it.
# That is only well-posed if a super-effective party answer *exists* per world; a
# boss with no super-effective counter forces even the oracle to grind neutrally
# (attrition), collapsing the discrimination signal. The world generator must
# therefore guarantee one — these tests pin that guarantee.


def test_every_placed_boss_has_super_effective_party_type() -> None:
    """matchup-validity AC1: in every vary world, each placed gym boss has at least
    one starter (party move) type that is *strictly* super-effective against it.

    A NEUTRAL answer (incl. the boss's own type) is not enough — the inference
    signal needs an exploitable edge. Checked across num_types and both seed splits.
    """
    seeds = list(train_seeds(40)) + list(heldout_seeds(40))
    for num_types in (3, 4, 6):
        for seed in seeds:
            region = generate_region(seed, vary=True, num_types=num_types)
            for _pos, boss in region.gyms:
                assert any(
                    region.chart.effectiveness(s, boss) > NEUTRAL for s in _STARTER_TYPES
                ), f"seed={seed} num_types={num_types} boss={boss} has no super-effective counter"


# Skeleton frozen *before* the post-Green measurement (anti-p-hacking, plan §검증 방법):
# "oracle SE-rate never collapses across world counts AND leads the chart-blind anchor
# by a clear margin at a realistic eval scale". The non-collapse floor (the fix's actual
# claim) is checked at EVERY world count; the discrimination band is an *aggregate*
# property (type_blind fights with one fixed champion, so on a 1-3 world block it can
# coincidentally tie the oracle) and is therefore asserted only where it is well-defined
# — at the realistic eval sizes. Post-fix measurement (kept honest): oracle reads 1.000
# at every n; band is +0.93 (n=8) / +0.97 (n=16); the floor 0.5 is comfortably met.
_SE_RATE_FLOOR = 0.5          # oracle must exploit on >= half its counted moves (non-collapse)
_DISCRIMINATION_BAND = 0.3    # oracle SE-rate must lead type_blind at realistic eval scale


def _demonstrator_set(n_worlds: int) -> SealedEvalSet:
    return SealedEvalSet(
        master_seed=20260627, n_worlds=n_worlds, num_types=3,
        grid_size=5, boss_hp=140, boss_atk=6, boss_def=18,
    )


def test_oracle_se_rate_does_not_collapse_with_world_count() -> None:
    """matchup-validity AC2 (non-collapse): on the demonstrator config the oracle's
    super-effective-move rate stays robust as the world count grows — it no longer
    degenerates into attrition grind (pre-fix it fell to 0.055 / 0.227 / 0.115 at
    n_worlds 4 / 6 / 8). Checked at every world count.
    """
    for n_worlds in (1, 2, 3, 4, 6, 8):
        oracle = score_inference_telemetry(
            reference_arm("oracle"), _demonstrator_set(n_worlds)
        ).super_effective_rate
        assert oracle >= _SE_RATE_FLOOR, (
            f"n_worlds={n_worlds}: oracle SE-rate {oracle:.3f} collapsed"
        )


def test_oracle_discriminates_from_chart_blind_at_eval_scale() -> None:
    """matchup-validity AC2 (discrimination): at a realistic eval scale the oracle's
    super-effective-move rate leads the chart-blind (type_blind) anchor by a clear
    margin — so the eval still measures hidden-chart inference rather than collapsing
    into an attrition grind both arms can win.
    """
    for n_worlds in (8, 16):
        sealed = _demonstrator_set(n_worlds)
        oracle = score_inference_telemetry(reference_arm("oracle"), sealed).super_effective_rate
        blind = score_inference_telemetry(reference_arm("type_blind"), sealed).super_effective_rate
        assert oracle - blind >= _DISCRIMINATION_BAND, (
            f"n_worlds={n_worlds}: discrimination band {oracle - blind:.3f} too small "
            f"(oracle={oracle:.3f}, type_blind={blind:.3f})"
        )
