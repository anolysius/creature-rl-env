"""numpy <-> JAX parity for the opt-in STRICT battle rule (hard-benchmark/strict-battle).

``strict_battle=True`` zeroes resisted (< NEUTRAL effectiveness) damage in both engines.
Scripted ceilings run on numpy ``CritterEnv``; learned agents run on the JAX env — the strict
variant is only trustworthy if the two are the SAME env. This gate drives both from the same
seed + actions across the 2x2 grid {commit, non-commit} x {single-type, multi-type boss} with
strict ON and asserts every obs key, reward, terminated, truncated match (parity 0).
Skipped when JAX is absent.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax.numpy as jnp  # noqa: E402

from critter_gym.envs.critter_env import CritterEnv  # noqa: E402
from critter_gym.jax_env import JaxEnvConfig, make_jax_env  # noqa: E402
from critter_gym.region import generate_region  # noqa: E402

_GRID, _NGYM, _NTYPES, _NCRE, _STEPS, _PR = 10, 3, 8, 5, 200, 2

_OBS_KEYS = [
    "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved", "in_battle",
    "player_hp", "player_type", "player_level", "enemy_hp", "enemy_type",
    "player_charge", "enemy_charge",
]


def _envs(commit: bool, boss_secondary: bool):
    env = CritterEnv(
        grid_size=_GRID, num_creatures=_NCRE, num_gyms=_NGYM, max_steps=_STEPS,
        patch_radius=_PR, vary=True, num_types=_NTYPES, commit_battles=commit,
        min_gyms=_NGYM, boss_secondary=boss_secondary, strict_battle=True,
    )
    jenv = make_jax_env(JaxEnvConfig(
        grid=_GRID, patch_radius=_PR, max_steps=_STEPS, max_gyms=_NGYM,
        commit=commit, strict_battle=True,
    ))
    return env, jenv


def _region(seed: int, boss_secondary: bool):
    return generate_region(seed, _GRID, _NCRE, _NGYM, vary=True, num_types=_NTYPES,
                           min_gyms=_NGYM, boss_secondary=boss_secondary)


def _assert_obs_equal(np_obs, jx_obs) -> None:
    for k in _OBS_KEYS:
        assert np.array_equal(np.asarray(np_obs[k]), np.asarray(jx_obs[k])), f"obs[{k}] differs"


def _run_parity(seed: int, policy, *, commit: bool, boss_secondary: bool) -> int:
    env, jenv = _envs(commit, boss_secondary)
    np_obs, _ = env.reset(seed=seed)
    state = jenv.reset(_region(seed, boss_secondary))
    step = jenv.make_step()
    _assert_obs_equal(np_obs, jenv.encode_obs(state))  # reset parity

    compared = 0
    for _ in range(_STEPS):
        action = policy(env, np_obs)
        np_obs, r_np, term_np, trunc_np, _ = env.step(action)
        state, jx_obs, r_jx, term_jx, trunc_jx = step(state, jnp.int32(action))
        compared += 1
        _assert_obs_equal(np_obs, jx_obs)
        assert float(r_np) == float(r_jx), f"reward differs @{compared}"
        assert bool(term_np) == bool(term_jx), f"terminated differs @{compared}"
        assert bool(trunc_np) == bool(trunc_jx), f"truncated differs @{compared}"
        if term_np or trunc_np:
            break
    return compared


def _gym_seeking_policy(env, obs):
    if obs["in_battle"][0]:
        return 0
    ar, ac = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    targets = [pos for pos, i in env._gym_tiles.items() if not env._gym_defeated[i]]
    if not targets:
        return 5
    gr, gc = min(targets, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    if gr < ar:
        return 0
    if gr > ar:
        return 1
    if gc > ac:
        return 2
    if gc < ac:
        return 3
    return 5


_CONFIGS = [
    pytest.param(True, False, id="commit-single"),
    pytest.param(True, True, id="commit-multitype"),
    pytest.param(False, False, id="noncommit-single"),
    pytest.param(False, True, id="noncommit-multitype"),
]


@pytest.mark.parametrize(("commit", "boss_secondary"), _CONFIGS)
@pytest.mark.parametrize("seed", [0, 5])
def test_strict_parity_gym_clearing(seed: int, commit: bool, boss_secondary: bool) -> None:
    assert _run_parity(seed, _gym_seeking_policy, commit=commit,
                       boss_secondary=boss_secondary) > 0


@pytest.mark.parametrize(("commit", "boss_secondary"), _CONFIGS)
def test_strict_parity_random(commit: bool, boss_secondary: bool) -> None:
    rng = np.random.default_rng(4200)
    assert _run_parity(3, lambda e, o: int(rng.integers(0, 6)), commit=commit,
                       boss_secondary=boss_secondary) > 0


@pytest.mark.parametrize(("commit", "boss_secondary"), _CONFIGS)
def test_strict_parity_heldout(commit: bool, boss_secondary: bool) -> None:
    assert _run_parity(1_000_000, _gym_seeking_policy, commit=commit,
                       boss_secondary=boss_secondary) > 0
