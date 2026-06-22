"""AC1/AC2/AC4: procedural region generation + train/test seed split."""

from __future__ import annotations

import pytest

from critter_gym.region import (
    TEST_SEED_OFFSET,
    generate_region,
    heldout_seeds,
    is_held_out,
    train_seeds,
)


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
