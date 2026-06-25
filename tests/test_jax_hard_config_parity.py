"""numpy <-> JAX parity at the HARD memory-headroom config (hard-benchmark/memory-headroom).

hard-benchmark #3 measures whether the env is hard *even for a strong memory agent*
(recurrent PPO) by going deeper: a bigger map + longer horizon under the same 5x5
egocentric view (grid 16, 5 gyms, 420 steps, patch_radius 2). The oracle ceiling is the
numpy `CritterEnv`; the learned agent runs on the JAX env — so the headroom number is only
trustworthy if the two are the **same** env at this new shape. This test is that gate:
drive the real `CritterEnv(**cfg)` and `make_jax_env(cfg)` from the same seed + actions and
assert every obs key, reward, terminated, truncated match (parity 0). Also smoke-tests that
`hard_env_spec()` trains a recurrent PPO to a finite curve. Skipped when JAX is absent.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax.numpy as jnp  # noqa: E402

from critter_gym.envs.critter_env import CritterEnv  # noqa: E402
from critter_gym.jax_env import JaxEnvConfig, make_jax_env  # noqa: E402
from critter_gym.region import generate_region, heldout_seeds  # noqa: E402

# The hard memory-headroom config (mirrors jax_train.hard_env_spec): bigger map + longer
# horizon, same 5x5 view. num_creatures matched on both sides (parity needs identical regions).
_GRID, _NGYM, _NTYPES, _NCRE, _STEPS, _PR = 16, 5, 8, 6, 420, 2
_ENV_KW = dict(grid_size=_GRID, num_creatures=_NCRE, num_gyms=_NGYM, max_steps=_STEPS,
               patch_radius=_PR, vary=True, num_types=_NTYPES, commit_battles=True,
               min_gyms=_NGYM)
_JCFG = JaxEnvConfig(grid=_GRID, patch_radius=_PR, max_steps=_STEPS, max_gyms=_NGYM)
_PATCH = 2 * _PR + 1  # 5

_OBS_KEYS = [
    "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved", "in_battle",
    "player_hp", "player_type", "player_level", "enemy_hp", "enemy_type",
    "player_charge", "enemy_charge",
]


def _region(seed: int):
    return generate_region(seed, _GRID, _NCRE, _NGYM, vary=True, num_types=_NTYPES,
                           min_gyms=_NGYM)


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


@pytest.mark.parametrize("seed", [0, 1, 2, 7, 13])
def test_hard_parity_random(seed: int) -> None:
    rng = np.random.default_rng(2000 + seed)
    assert _run_parity(seed, lambda e, o: int(rng.integers(0, 6))) > 0


@pytest.mark.parametrize("seed", [0, 1, 2, 4, 7, 11])
def test_hard_parity_gym_clearing(seed: int) -> None:
    assert _run_parity(seed, _gym_seeking_policy) > 0


@pytest.mark.parametrize("seed", [1_000_000, 1_000_001])
def test_hard_parity_heldout(seed: int) -> None:
    assert _run_parity(seed, _gym_seeking_policy) > 0


def test_hard_env_spec_shapes() -> None:
    from critter_gym import jax_train

    spec = jax_train.hard_env_spec()
    obs = spec.env.encode_obs(spec.env.reset(spec.region_fn(0)))
    assert obs["local_patch"].shape == (_PATCH, _PATCH)  # 5x5 view on the bigger map


def test_hard_recurrent_ppo_smoke() -> None:
    from critter_gym import jax_train

    spec = jax_train.hard_env_spec()
    cfg = jax_train.PPOConfig(batch=16, hidden=32, iters=4, rollout_len=8, num_minibatches=4)
    res = jax_train.train_recurrent_ppo(tuple(range(16)), cfg, seed=0, spec=spec)
    assert len(res.curve) == 4
    assert all(np.isfinite(x) for x in res.curve)
    held = jax_train.evaluate_gym_clears_recurrent(
        res.params, tuple(int(s) for s in heldout_seeds(4)), steps=30, spec=spec)
    assert np.isfinite(held)
