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
from critter_gym.types import (
    NEUTRAL,
    SUPER_EFFECTIVE,
    ElementType,
    TypeChart,
    generate_typechart,
)

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


# -- difficulty knob: super-effective multiplier is configurable (not hardcoded) --


def test_super_mult_defaults_to_2_and_is_configurable() -> None:
    F, G = ElementType.FIRE, ElementType.GRASS
    beats = frozenset({(F, G)})
    default = TypeChart(beats)
    assert default.effectiveness(F, G) == SUPER_EFFECTIVE == 2.0  # M1 default unchanged
    harder = TypeChart(beats, super_mult=3.0)
    assert harder.effectiveness(F, G) == 3.0          # configurable amplitude
    assert harder.effectiveness(G, F) == 0.5          # not-very unchanged
    assert harder.effectiveness(F, F) == NEUTRAL      # neutral unchanged


def test_generate_typechart_threads_super_mult() -> None:
    active = list(ElementType)[:12]
    chart = generate_typechart(7, active, vary=True, super_mult=4.0)
    assert chart.super_mult == 4.0
    # default call keeps M1 amplitude
    assert generate_typechart(7, active, vary=True).super_mult == SUPER_EFFECTIVE


# -- env/registration expose the difficulty knobs (AC2) ----------------------


def test_env_exposes_super_mult_and_boss_strength_knobs() -> None:
    from critter_gym.envs.critter_env import CritterEnv

    env = CritterEnv(vary=True, num_types=12, super_mult=3.0,
                     boss_hp=140, boss_atk=18, commit_battles=True)
    env.reset(seed=1000)
    assert env._region_chart.super_mult == 3.0          # threaded into the hidden chart
    assert env.commit_battles is True                   # team-commit boss mode on
    assert (env.boss_hp, env.boss_atk) == (140, 18)     # boss strength configurable


def test_env_defaults_keep_m1_battle_economy() -> None:
    from critter_gym.envs.critter_env import CritterEnv
    from critter_gym.types import SUPER_EFFECTIVE as SE

    env = CritterEnv()  # M1 defaults
    env.reset(seed=0)
    assert env._region_chart.super_mult == SE           # 2.0, unchanged
    assert env.commit_battles is False                  # force-switch economy intact
    assert (env.boss_hp, env.boss_atk, env.boss_def) == (120, 12, 12)  # M1 boss stats


def test_commit_env_id_is_registered_and_compliant() -> None:
    import gymnasium as gym

    from critter_gym.registration import register_envs

    register_envs()
    env = gym.make("CritterGym-commit-v0")
    try:
        env.reset(seed=1000)
        for _ in range(30):
            obs, _r, term, trunc, _i = env.step(env.action_space.sample())
            if term or trunc:
                env.reset()
        assert env.get_wrapper_attr("commit_battles") is True
    finally:
        env.close()


# -- D9: honesty invariant — no overclaim that a *learned* policy infers ------


def test_source_does_not_overclaim_learned_inference() -> None:
    # reasoning-load-bearing changed the honest baseline: a scripted 4-arm gate now
    # PROVES inference is load-bearing under team-commit (so the SSOT may say so).
    # The remaining overclaim to guard against is *learnability* — claiming a trained
    # policy actually acquires the inference, which is not yet measured. Any
    # "load-bearing" claim in the SSOT must keep the scripted/learned caveat, and
    # explicit learnability boasts are banned.
    from critter_gym import registration as registrationmod

    banned = ("learns to infer", "proves the agent", "agent infers the chart")
    for mod in (typesmod, regionmod, registrationmod):
        low = inspect.getsource(mod).lower()
        for phrase in banned:
            assert phrase not in low, f"learnability overclaim in {mod.__name__}: {phrase}"
        if "load-bearing" in low:
            # must be qualified as scripted-arm evidence with learnability as follow-up
            assert "scripted" in low and "follow-up" in low, (
                f"{mod.__name__} claims load-bearing without the scripted/follow-up caveat"
            )
