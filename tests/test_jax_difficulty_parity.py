"""numpy <-> JAX parity at the HIGH-GYM dynamic-range config (jax-difficulty-report / R5).

The default-config parity lives in ``test_jax_env_parity.py``. This re-establishes the
same bit-for-bit contract for the *configured* env (`make_jax_env(cfg)`): the high-gym
difficulty config (grid 6, **8 gyms**, patch_radius 5 → an 11x11 patch larger than the
grid, num_types 12, super_mult 3.0, boss 150/16) the `difficulty-dynamic-range` task
uses. Drives the real ``CritterEnv(**cfg)`` and the JAX env from the same seed + actions
and asserts every obs key, reward, terminated, truncated match. Also smoke-tests that
``jax_train`` trains on this config (config-aware path) and the default path is unchanged.

Skipped when JAX is absent → CI stays numpy-only.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from critter_gym.envs.critter_env import CritterEnv  # noqa: E402
from critter_gym.jax_env import JaxEnvConfig, make_jax_env  # noqa: E402
from critter_gym.region import generate_region, heldout_seeds  # noqa: E402

# The high-gym dynamic-range config (mirrors difficulty_generalization.DISCRIM_BASE + 8 gyms).
_ENV_KW = dict(grid_size=6, num_creatures=5, num_gyms=8, max_steps=160, patch_radius=5,
               vary=True, num_types=12, super_mult=3.0, boss_hp=150, boss_atk=16,
               commit_battles=True, min_gyms=8)
_JCFG = JaxEnvConfig(grid=6, patch_radius=5, max_steps=160, max_gyms=8,
                     boss_hp=150, boss_atk=16, boss_def=12, boss_spd=8, boss_move_power=30.0)
_PATCH = 2 * 5 + 1  # 11 (larger than grid 6 → exercises padding)

_OBS_KEYS = [
    "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved", "in_battle",
    "player_hp", "player_type", "player_level", "enemy_hp", "enemy_type",
    "player_charge", "enemy_charge",
]


def _region(seed: int):
    return generate_region(seed, 6, 5, 8, vary=True, num_types=12, super_mult=3.0, min_gyms=8)


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
    for _ in range(_ENV_KW["max_steps"]):
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
def test_highgym_parity_random(seed: int) -> None:
    rng = np.random.default_rng(1000 + seed)
    assert _run_parity(seed, lambda e, o: int(rng.integers(0, 6))) > 0


@pytest.mark.parametrize("seed", [0, 1, 2, 4, 7, 11])
def test_highgym_parity_gym_clearing(seed: int) -> None:
    assert _run_parity(seed, _gym_seeking_policy) > 0


@pytest.mark.parametrize("seed", [1_000_000, 1_000_001])
def test_highgym_parity_heldout(seed: int) -> None:
    assert _run_parity(seed, _gym_seeking_policy) > 0


def test_highgym_jit_and_vmap() -> None:
    jenv = make_jax_env(_JCFG)
    step = jenv.make_step(jit=True)
    state = jenv.reset(_region(0))
    state, obs, reward, term, trunc = step(state, jnp.int32(2))
    jax.block_until_ready(state.agent_pos)
    assert obs["local_patch"].shape == (_PATCH, _PATCH)  # 11x11, config-sized
    assert state.gym_active.shape == (8,)
    # vmap a batch
    batch = 8
    states = [jenv.reset(_region(s)) for s in range(batch)]
    batched = jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *states)
    vstep = jax.jit(jax.vmap(jenv.step))
    acts = jnp.asarray(np.random.default_rng(0).integers(0, 6, size=batch), jnp.int32)
    _, obs, reward, term, _ = vstep(batched, acts)
    jax.block_until_ready(reward)
    assert reward.shape == (batch,)
    assert obs["local_patch"].shape == (batch, _PATCH, _PATCH)


def test_default_config_unchanged() -> None:
    # The default-config module-level env must still produce the 5x5 patch / 3-gym shapes.
    from critter_gym.jax_env import encode_obs, jax_reset
    state = jax_reset(generate_region(0, 10, 5, 3, vary=True, num_types=8))
    obs = encode_obs(state)
    assert obs["local_patch"].shape == (5, 5)
    assert state.gym_active.shape == (3,)


def test_jax_train_difficulty_smoke() -> None:
    from critter_gym import jax_train

    spec = jax_train.difficulty_env_spec()
    cfg = jax_train.TrainConfig(batch=16, rollout_len=8, iters=3)
    res = jax_train.train(tuple(range(16)), cfg, seed=0, spec=spec)
    assert len(res.curve) == 3
    assert all(np.isfinite(x) for x in res.curve)
    # held-out eval on the high-gym spec returns a finite scalar
    held = jax_train.evaluate(res.params, tuple(int(s) for s in heldout_seeds(4)),
                              steps=20, spec=spec)
    assert np.isfinite(held)
