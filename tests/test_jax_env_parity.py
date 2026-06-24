"""AC1/AC2/AC3: numpy <-> JAX full-episode env parity + jit/vmap (M4 env integration).

Drives the **real** numpy ``CritterEnv(commit_battles=True)`` and the unified JAX env
(``critter_gym.jax_env``) from the same seed + same action sequence and asserts every
observation key (incl. the 5x5 ``local_patch``), reward, terminated and truncated match
— over full episodes, on fixed and per-seed (``vary``) charts, with both a random
policy and a directed gym-clearing policy (to exercise the all-gyms-defeated
termination, including ``vary`` charts that have fewer than MAX_GYMS gyms).

Skipped when JAX is absent → the default (CI) suite stays numpy-only.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from critter_gym.envs.critter_env import CritterEnv  # noqa: E402
from critter_gym.jax_env import (  # noqa: E402
    encode_obs,
    jax_env_step,
    jax_reset,
    make_env_step,
)
from critter_gym.region import generate_region  # noqa: E402

_GRID, _NC, _NG = 10, 5, 3
_NUM_TYPES = 8  # full type pool (vary mode)

_OBS_KEYS = [
    "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved", "in_battle",
    "player_hp", "player_type", "player_level", "enemy_hp", "enemy_type",
    "player_charge", "enemy_charge",
]


def _assert_obs_equal(np_obs, jx_obs) -> None:
    for k in _OBS_KEYS:
        assert np.array_equal(np.asarray(np_obs[k]), np.asarray(jx_obs[k])), f"obs[{k}] differs"


def _make_env(seed: int, vary: bool):
    if vary:
        env = CritterEnv(commit_battles=True, vary=True, num_types=_NUM_TYPES)
        region = generate_region(seed, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    else:
        env = CritterEnv(commit_battles=True)
        region = generate_region(seed, _GRID, _NC, _NG)
    return env, region


def _run_parity(seed: int, vary: bool, policy, max_steps: int = 200) -> int:
    env, region = _make_env(seed, vary)
    np_obs, _ = env.reset(seed=seed)
    state = jax_reset(region)
    step = make_env_step()
    jx_obs = encode_obs(state)
    _assert_obs_equal(np_obs, jx_obs)  # reset obs parity

    compared = 0
    for _ in range(max_steps):
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


@pytest.mark.parametrize("seed", [0, 1, 2, 7, 13])
def test_parity_random_policy_vary(seed: int) -> None:
    """Full-episode parity under a fixed random action sequence (vary charts)."""
    rng = np.random.default_rng(1000 + seed)
    assert _run_parity(seed, vary=True, policy=lambda e, o: int(rng.integers(0, 6))) > 0


@pytest.mark.parametrize("seed", [0, 1, 3])
def test_parity_random_policy_fixed(seed: int) -> None:
    """Full-episode parity on the fixed M1 chart."""
    rng = np.random.default_rng(seed)
    assert _run_parity(seed, vary=False, policy=lambda e, o: int(rng.integers(0, 6))) > 0


def _gym_seeking_policy(env, obs):
    """Move toward the nearest undefeated gym; in battle, attack (action 0).

    Exercises the all-gyms-defeated termination — including vary charts with < MAX_GYMS
    gyms, the case a fixed-size mask would get wrong.
    """
    if obs["in_battle"][0]:
        return 0  # MOVE (attack) — also locks the champion out of the commit window
    ar, ac = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    targets = [pos for pos, i in env._gym_tiles.items() if not env._gym_defeated[i]]
    if not targets:
        return 5  # NOOP — all gyms cleared (episode should be terminated already)
    gr, gc = min(targets, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    if gr < ar:
        return 0  # N
    if gr > ar:
        return 1  # S
    if gc > ac:
        return 2  # E
    if gc < ac:
        return 3  # W
    return 5


@pytest.mark.parametrize("seed", [0, 1, 2, 4, 7, 11])
def test_parity_gym_clearing_policy(seed: int) -> None:
    """Directed policy that clears gyms → exercises termination + evolution parity."""
    assert _run_parity(seed, vary=True, policy=_gym_seeking_policy) > 0


def test_termination_respects_active_gym_mask() -> None:
    """All *active* gyms defeated → terminated, even on vary charts with < MAX_GYMS gyms.

    Deterministic check of the gym_active fix: a fixed-size gym mask would either never
    terminate (unused slots stay 'undefeated') or miscount gyms_defeated. We mark exactly
    the active gyms defeated and assert termination + a correct count.
    """
    # find a vary seed whose region has fewer than MAX_GYMS gyms (exercises padding).
    region = next(
        generate_region(s, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
        for s in range(200)
        if len(generate_region(s, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES).gyms) < _NG
    )
    n_real = len(region.gyms)
    assert n_real < _NG  # the padded case we want to cover
    state = jax_reset(region)
    # not terminated at start
    _, _, _, term0, _ = jax_env_step(state, jnp.int32(5))
    assert not bool(term0)
    # mark all active gyms defeated, then one NOOP step → terminated, count == n_real.
    state = state._replace(gym_defeated=state.gym_active)
    state, obs, _, term, trunc = jax_env_step(state, jnp.int32(5))
    assert bool(term)
    assert not bool(trunc)
    assert int(obs["gyms_defeated"][0]) == n_real


def test_terminated_and_truncated_independent() -> None:
    """terminated & truncated are computed independently (both True is possible).

    Mirrors CritterEnv.step, where the last gym falling exactly at max_steps yields
    terminated AND truncated. A naive `truncated = ~terminated & ...` would diverge.
    """
    region = generate_region(0, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    state = jax_reset(region)
    # one step before the budget, with every active gym already defeated.
    state = state._replace(
        gym_defeated=state.gym_active, steps=jnp.int32(199)  # _MAX_STEPS - 1
    )
    _, _, _, term, trunc = jax_env_step(state, jnp.int32(5))
    assert bool(term) and bool(trunc)  # both True on the boundary step


def test_jit_compiles() -> None:
    region = generate_region(0, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    step = make_env_step(jit=True)
    state = jax_reset(region)
    state, obs, reward, term, trunc = step(state, jnp.int32(2))
    jax.block_until_ready(state.agent_pos)
    assert obs["local_patch"].shape == (5, 5)
    assert reward.shape == ()
    assert term.dtype == jnp.bool_


def test_vmap_batches() -> None:
    """vmap a batch of full episodes (the RL-loop consumption form)."""
    batch = 16
    states = [jax_reset(generate_region(s, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES))
              for s in range(batch)]
    batched = jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *states)
    vstep = jax.jit(jax.vmap(jax_env_step))
    actions = jnp.asarray(np.random.default_rng(0).integers(0, 6, size=batch), jnp.int32)
    state, obs, reward, term, trunc = vstep(batched, actions)
    jax.block_until_ready(reward)
    assert reward.shape == (batch,)
    assert obs["local_patch"].shape == (batch, 5, 5)
    assert term.shape == (batch,)
