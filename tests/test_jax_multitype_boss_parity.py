"""numpy <-> JAX parity for the opt-in MULTI-TYPE boss (hard-benchmark/multitype-boss-scout).

A gym boss can carry a hidden secondary defending type: the player-vs-boss effectiveness is the
product over both types (numpy `multi_effectiveness` / JAX `_boss_def_eff`), while the boss's move
and the observed `enemy_type` stay the primary. The oracle ceiling runs on numpy `CritterEnv`; the
learned agent runs on the JAX env — so the multi-type difficulty is only trustworthy if the two
are the SAME env. This test is that gate: drive `CritterEnv(boss_secondary=True)` and
`make_jax_env(...)` from the same seed + actions on a multi-type-boss region and assert every obs
key, reward, terminated, truncated match (parity 0). Skipped when JAX is absent.
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
_ENV_KW = dict(grid_size=_GRID, num_creatures=_NCRE, num_gyms=_NGYM, max_steps=_STEPS,
               patch_radius=_PR, vary=True, num_types=_NTYPES, commit_battles=True,
               min_gyms=_NGYM, boss_secondary=True)
_JCFG = JaxEnvConfig(grid=_GRID, patch_radius=_PR, max_steps=_STEPS, max_gyms=_NGYM)

_OBS_KEYS = [
    "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved", "in_battle",
    "player_hp", "player_type", "player_level", "enemy_hp", "enemy_type",
    "player_charge", "enemy_charge",
]


def _region(seed: int):
    return generate_region(seed, _GRID, _NCRE, _NGYM, vary=True, num_types=_NTYPES,
                           min_gyms=_NGYM, boss_secondary=True)


def _assert_obs_equal(np_obs, jx_obs) -> None:
    for k in _OBS_KEYS:
        assert np.array_equal(np.asarray(np_obs[k]), np.asarray(jx_obs[k])), f"obs[{k}] differs"


def _run_parity(seed: int, policy) -> int:
    env = CritterEnv(**_ENV_KW)
    jenv = make_jax_env(_JCFG)
    np_obs, _ = env.reset(seed=seed)
    state = jenv.reset(_region(seed))
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


def test_region_has_multitype_bosses() -> None:
    r = _region(0)
    assert any(s is not None for s in r.boss_secondary_types)  # the config is genuinely multi-type


@pytest.mark.parametrize("seed", [0, 1, 2, 7, 13])
def test_multitype_parity_random(seed: int) -> None:
    rng = np.random.default_rng(3000 + seed)
    assert _run_parity(seed, lambda e, o: int(rng.integers(0, 6))) > 0


@pytest.mark.parametrize("seed", [0, 1, 2, 4, 7, 11])
def test_multitype_parity_gym_clearing(seed: int) -> None:
    assert _run_parity(seed, _gym_seeking_policy) > 0


@pytest.mark.parametrize("seed", [1_000_000, 1_000_001])
def test_multitype_parity_heldout(seed: int) -> None:
    assert _run_parity(seed, _gym_seeking_policy) > 0
