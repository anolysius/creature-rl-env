"""Depth of the procgen type system (M3 reliability, DESCOPED).

These verify the *achievable* deepening: a large hidden type pool (num_types≥12),
boss-type recurrence within an episode (so inference has room), structural
winnability, and no train/test leak. They do NOT claim inference is provably
load-bearing — a pilot showed that needs a battle-economy redesign (future work,
DESIGN §3.1.1); see the task's DESCOPE NOTE.
"""

from __future__ import annotations

import inspect

import pytest

from critter_gym import region as regionmod
from critter_gym import types as typesmod
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.region import (
    TEST_SEED_OFFSET,
    generate_region,
    heldout_seeds,
    train_seeds,
)
from critter_gym.types import NEUTRAL, ElementType, generate_typechart

_STARTERS = (ElementType.FIRE, ElementType.WATER, ElementType.GRASS)
PROCGEN = dict(grid_size=10, max_creatures=5, max_gyms=8, vary=True, num_types=12)


# -- D1: pool + core ids ------------------------------------------------------


def test_type_pool_is_deep_and_core_ids_stable() -> None:
    types = list(ElementType)
    assert len(types) >= 12
    assert types[0] is ElementType.FIRE  # M1 ids 0/1/2 must not move
    assert types[1] is ElementType.WATER
    assert types[2] is ElementType.GRASS


# -- D2: active subset + guard ------------------------------------------------


def test_fixed_world_rejects_extra_types() -> None:
    with pytest.raises(ValueError):
        generate_region(0, vary=False, num_types=12)  # fixed world is 3 types only


def test_procgen_uses_only_active_subset() -> None:
    active = set(list(ElementType)[:12])
    r = generate_region(TEST_SEED_OFFSET, **PROCGEN)
    assert all(t in active for _, t in r.gyms)
    # chart only relates active types
    assert all(a in active and b in active for (a, b) in r.chart.beats)


# -- D3: boss-type recurrence (room for inference) ----------------------------


def test_boss_types_recur_within_episodes() -> None:
    # across a sample of held-out seeds, a substantial fraction of episodes repeat
    # at least one boss type (drawn from a per-seed pool) — the structure that gives
    # cross-gym inference something to exploit.
    repeated = 0
    seeds = list(heldout_seeds(40))
    for s in seeds:
        types = [t for _, t in generate_region(s, **PROCGEN).gyms]
        if len(types) != len(set(types)):
            repeated += 1
    assert repeated >= len(seeds) // 2  # was 0/40 before the per-seed boss pool


# -- D5: obs type dims fixed to the pool, independent of num_types ------------


def test_obs_type_bound_is_pool_fixed() -> None:
    pool_max = len(ElementType) - 1
    for env in (CritterEnv(), CritterEnv(vary=True, num_types=12)):
        space = env.observation_space
        assert int(space["player_type"].high[0]) == pool_max  # bound = pool, not num_types
        assert int(space["enemy_type"].high[0]) == pool_max
        assert space["player_type"].shape == (1,)  # shape unchanged


# -- D4: structural winnability -----------------------------------------------


def test_every_boss_type_is_answerable_by_a_starter() -> None:
    for s in list(heldout_seeds(30)) + list(train_seeds(30)):
        r = generate_region(s, **PROCGEN)
        for _, boss in r.gyms:
            assert any(r.chart.effectiveness(st, boss) >= NEUTRAL for st in _STARTERS)


# -- D6: deep chart, per-seed distinct, no leak -------------------------------


def test_chart_is_antisymmetric_and_per_seed_distinct() -> None:
    active = list(ElementType)[:12]
    c1 = generate_typechart(TEST_SEED_OFFSET, active, vary=True)
    c2 = generate_typechart(TEST_SEED_OFFSET + 1, active, vary=True)
    assert c1.beats != c2.beats  # different seeds → different charts
    # antisymmetric: never both (a,b) and (b,a)
    assert all((b, a) not in c1.beats for (a, b) in c1.beats)
    # a 12-type chart has C(12,2)=66 oriented pairs — far richer than the 3-cycle
    assert len(c1.beats) == 66


def test_train_and_heldout_charts_differ_no_leak() -> None:
    active = list(ElementType)[:12]
    train = {repr(generate_typechart(s, active, vary=True).beats) for s in train_seeds(40)}
    held = {repr(generate_typechart(s, active, vary=True).beats) for s in heldout_seeds(40)}
    assert train.isdisjoint(held)  # no train chart reappears in held-out


# -- D9: honesty invariant — no residual "inference is load-bearing" overclaim --


def test_source_does_not_overclaim_inference_is_load_bearing() -> None:
    # The descope (DESIGN §3.1.1) is explicit: depth makes the chart harder to
    # *memorize*, NOT proof that *inference* is load-bearing. Guard against the
    # overclaim creeping back into the in-code SSOT.
    for mod in (typesmod, regionmod):
        src = inspect.getsource(mod)
        assert "pay off" not in src  # the payoff the pilot disproved
        # "load-bearing" may appear only when paired with the open-problem caveat
        if "load-bearing" in src:
            assert "open problem" in src and "DESIGN §3.1.1" in src
