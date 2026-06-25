"""AC1/AC2/AC3/AC5: numpy <-> JAX full-episode parity for families B (forage) and D (muster).

`make_jax_env(JaxEnvConfig(family=...))` ports two more families to the vectorized JAX env:
  - **forage** (B): contact-collect overworld (stepping onto a creature collects it; CATCH
    inert), mirroring `ForageEnv`.
  - **muster** (D): CATCH-collect + each catch buffs every party member's attack (+12),
    which evolution then wipes (`attack = form.attack`) — mirroring `MusterEnv`. The buff
    flows into battle damage, so parity on `enemy_hp`/`player_hp` during battles *is* the
    buff check; a focused catch→win(evolve)→catch probe pins the reset.

Both families use the non-commit battle (the env default). Skipped when JAX is absent.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from critter_gym.envs.forage_env import ForageEnv  # noqa: E402
from critter_gym.envs.muster_env import MusterEnv  # noqa: E402
from critter_gym.jax_env import (  # noqa: E402
    _FAM_FORAGE,
    _FAM_MUSTER,
    JaxEnvConfig,
    make_jax_env,
)
from critter_gym.region import generate_region  # noqa: E402

_GRID, _NC, _NG, _NUM_TYPES = 10, 5, 3, 8

_OBS_KEYS = [
    "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved", "in_battle",
    "player_hp", "player_type", "player_level", "enemy_hp", "enemy_type",
    "player_charge", "enemy_charge",
]

_FORAGE_ENV = make_jax_env(JaxEnvConfig(commit=False, family=_FAM_FORAGE))
_MUSTER_ENV = make_jax_env(JaxEnvConfig(commit=False, family=_FAM_MUSTER))


def _assert_obs_equal(np_obs, jx_obs, where: int) -> None:
    for k in _OBS_KEYS:
        assert np.array_equal(np.asarray(np_obs[k]), np.asarray(jx_obs[k])), (
            f"obs[{k}] differs @{where}"
        )


def _run_parity(np_env, jx_env, region, seed: int, policy, max_steps: int = 200) -> int:
    np_obs, _ = np_env.reset(seed=seed)
    state = jx_env.reset(region)
    step = jx_env.make_step()
    _assert_obs_equal(np_obs, jx_env.encode_obs(state), where=0)
    compared = 0
    for _ in range(max_steps):
        action = policy(np_env, np_obs)
        np_obs, r_np, term_np, trunc_np, _ = np_env.step(action)
        state, jx_obs, r_jx, term_jx, trunc_jx = step(state, jnp.int32(action))
        compared += 1
        _assert_obs_equal(np_obs, jx_obs, where=compared)
        assert float(r_np) == float(r_jx), f"reward differs @{compared}"
        assert bool(term_np) == bool(term_jx), f"terminated differs @{compared}"
        assert bool(trunc_np) == bool(trunc_jx), f"truncated differs @{compared}"
        if term_np or trunc_np:
            break
    return compared


def _gym_seeking(env, obs):
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


def _catch_then_gym(env, obs):
    """Stand on a creature → CATCH (muster buff); else seek a gym; in battle, attack."""
    if obs["in_battle"][0]:
        return 0
    tile = (int(obs["agent_pos"][0]), int(obs["agent_pos"][1]))
    if tile in env._creatures:
        return 4  # CATCH (muster: buffs the party)
    # walk toward the nearest creature first (to muster), else toward a gym.
    ar, ac = tile
    creatures = list(env._creatures)
    if creatures:
        gr, gc = min(creatures, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    else:
        return _gym_seeking(env, obs)
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
def test_forage_parity_random(seed: int) -> None:
    rng = np.random.default_rng(3000 + seed)
    region = generate_region(seed, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    env = ForageEnv(commit_battles=False, vary=True, num_types=_NUM_TYPES)
    assert _run_parity(env, _FORAGE_ENV, region, seed,
                       lambda e, o: int(rng.integers(0, 6))) > 0


@pytest.mark.parametrize("seed", [0, 1, 2, 4, 7, 11])
def test_forage_parity_gym_clearing(seed: int) -> None:
    region = generate_region(seed, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    env = ForageEnv(commit_battles=False, vary=True, num_types=_NUM_TYPES)
    assert _run_parity(env, _FORAGE_ENV, region, seed, _gym_seeking) > 0


@pytest.mark.parametrize("seed", [0, 1, 2, 7, 13])
def test_muster_parity_random(seed: int) -> None:
    rng = np.random.default_rng(4000 + seed)
    region = generate_region(seed, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    env = MusterEnv(commit_battles=False, vary=True, num_types=_NUM_TYPES)
    assert _run_parity(env, _MUSTER_ENV, region, seed,
                       lambda e, o: int(rng.integers(0, 6))) > 0


@pytest.mark.parametrize("seed", [0, 1, 2, 4, 7, 11])
def test_muster_parity_catch_then_gym(seed: int) -> None:
    """Catch-heavy + gym-clearing → exercises the muster buff (via battle damage parity)
    and its reset on evolution. enemy_hp/player_hp parity through battles IS the buff check."""
    region = generate_region(seed, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    env = MusterEnv(commit_battles=False, vary=True, num_types=_NUM_TYPES)
    assert _run_parity(env, _MUSTER_ENV, region, seed, _catch_then_gym) > 0


def test_muster_buff_actually_exercised() -> None:
    """Guard against a vacuous parity: confirm the catch-then-gym battery actually catches
    creatures (applying the muster buff) AND evolves a creature (which wipes the buff —
    `evolve()` sets `attack = form.attack`), so the parity tests above are load-bearing on
    both the buff and its reset."""
    saw_catch = saw_evolve = False
    for seed in range(8):
        env = MusterEnv(commit_battles=False, vary=True, num_types=_NUM_TYPES)
        obs, _ = env.reset(seed=seed)
        for _ in range(200):
            a = _catch_then_gym(env, obs)
            obs, r, term, trunc, _ = env.step(a)
            if a == 4 and r >= 1.0:
                saw_catch = True
            if int(obs["evolved"][0]) > 0:
                saw_evolve = True
            if term or trunc:
                break
    assert saw_catch, "battery never caught a creature (muster buff never applied)"
    assert saw_evolve, "battery never evolved a creature (buff-reset path not exercised)"


def test_jit_and_vmap_families() -> None:
    region = generate_region(0, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    for env in (_FORAGE_ENV, _MUSTER_ENV):
        step = env.make_step(jit=True)
        state = env.reset(region)
        state, obs, reward, term, trunc = step(state, jnp.int32(2))
        jax.block_until_ready(state.agent_pos)
        assert obs["local_patch"].shape == (5, 5)
        # vmap a small batch
        states = [env.reset(generate_region(s, _GRID, _NC, _NG, vary=True,
                                            num_types=_NUM_TYPES)) for s in range(8)]
        batched = jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *states)
        vstep = jax.jit(jax.vmap(env.step))
        bstate, bobs, br, bt, btr = vstep(batched, jnp.zeros((8,), jnp.int32))
        jax.block_until_ready(br)
        assert br.shape == (8,)
