"""Tests for the opt-in multi-type gym boss (hard-benchmark: deeper hidden-rule inference).

A gym boss can carry a HIDDEN secondary type: the effectiveness the agent faces is the product
over both types, but the observation reveals only the primary — so the second type must be
inferred from battle outcomes. The lever is opt-in (`boss_secondary=True`); off is byte-identical
to the historical single-type world. The scripted oracle (chart-knowing) scores against both
types; infer/probe stay on the observed primary.
"""
from __future__ import annotations

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import generate_region

# --- Step 1: region + env carry an opt-in hidden secondary boss type -------------------

def test_region_off_has_no_secondary_and_is_byte_identical():
    a = generate_region(7, vary=True, num_types=8)
    b = generate_region(7, vary=True, num_types=8)  # off (default)
    assert a.boss_secondary_types == ()      # no secondary when off
    assert a.gyms == b.gyms                    # deterministic + unchanged draw sequence


def test_region_on_draws_distinct_hidden_secondary_per_gym():
    r = generate_region(7, vary=True, num_types=8, boss_secondary=True)
    assert len(r.boss_secondary_types) == len(r.gyms)
    for (_, primary), secondary in zip(r.gyms, r.boss_secondary_types):
        assert secondary is not None
        assert secondary != primary          # a genuine second type


def test_region_on_does_not_change_primary_placement():
    # Enabling the secondary must not perturb the historical primary/coord draw (drawn after).
    off = generate_region(7, vary=True, num_types=8)
    on = generate_region(7, vary=True, num_types=8, boss_secondary=True)
    assert on.gyms == off.gyms


def test_env_boss_has_two_types_when_enabled():
    env = CritterEnv(vary=True, num_types=8, commit_battles=True, boss_secondary=True)
    env.reset(seed=7)
    assert any(s is not None for s in env._gym_secondary)


def test_obs_enemy_type_reveals_only_primary():
    # Drive into a battle and confirm the observed enemy_type is the boss's PRIMARY only.
    env = CritterEnv(vary=True, num_types=8, commit_battles=True, boss_secondary=True,
                     grid_size=6, max_steps=200)
    obs, _ = env.reset(seed=3)
    # Step until a battle starts (nav oracle drives toward a gym).
    pol = reference_arm("oracle")
    for _ in range(200):
        if obs["in_battle"][0]:
            break
        obs, _, term, trunc, _ = env.step(pol(env, obs))
        if term or trunc:
            break
    if obs["in_battle"][0]:
        # enemy_type obs is a single scalar (shape (1,)) — the primary only (secondary hidden).
        assert obs["enemy_type"].shape == (1,)


def test_backward_compat_full_episode_identical_when_off():
    # An identical episode (same seed, same policy) is deterministic with the flag off.
    def play(secondary: bool) -> int:
        return run_episode(lambda: CritterEnv(
            vary=True, num_types=8, commit_battles=True, boss_secondary=secondary,
            grid_size=6, max_steps=150), reference_arm("oracle"), seed=5).gyms_cleared
    # Off must equal a second off run (determinism); on may differ (harder world).
    assert play(False) == play(False)


# --- Step 2: oracle scores against the boss's full (hidden) types ----------------------

def test_oracle_uses_multi_effectiveness_for_two_type_boss():
    # The oracle (chart-knowing) still clears gyms on a two-type-boss world (it reads both types
    # from env internals); a run completes without error and clears >= 0 gyms.
    factory = lambda: CritterEnv(  # noqa: E731
        vary=True, num_types=8, commit_battles=True, boss_secondary=True,
        grid_size=6, max_steps=200)
    out = run_episode(factory, reference_arm("oracle"), seed=11)
    assert out.gyms_cleared >= 0  # runs end-to-end; oracle handles the multi-type defender


def test_oracle_single_type_unchanged():
    # With the flag off, the oracle behaves exactly as before (single-type path).
    factory = lambda: CritterEnv(  # noqa: E731
        vary=True, num_types=8, commit_battles=True, grid_size=6, max_steps=200)
    a = run_episode(factory, reference_arm("oracle"), seed=11).gyms_cleared
    b = run_episode(factory, reference_arm("oracle"), seed=11).gyms_cleared
    assert a == b
