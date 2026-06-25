"""AC1/AC2/AC5: numpy <-> JAX full-episode parity for the NON-commit battle economy.

Drives the **real** numpy ``CritterEnv(commit_battles=False)`` (the env's *default*
battle: party + SWITCH + force-switch + party-wipe) and the unified JAX env built with
``make_jax_env(JaxEnvConfig(commit=False, ...))`` from the same seed + same action
sequence, asserting every observation key (incl. the 5x5 ``local_patch``), reward,
terminated and truncated match — over full episodes, on fixed and per-seed (``vary``)
charts, under a random policy, a gym-clearing policy (termination + evolution), and a
switch/item-heavy battle policy (force-switch + wasted-turn paths).

Skipped when JAX is absent → the default (CI) suite stays numpy-only.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from critter_gym.envs.critter_env import CritterEnv  # noqa: E402
from critter_gym.jax_env import JaxEnvConfig, make_jax_env  # noqa: E402
from critter_gym.region import generate_region  # noqa: E402

_GRID, _NC, _NG = 10, 5, 3
_NUM_TYPES = 8  # full type pool (vary mode)

_OBS_KEYS = [
    "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved", "in_battle",
    "player_hp", "player_type", "player_level", "enemy_hp", "enemy_type",
    "player_charge", "enemy_charge",
]

# the non-commit JAX env; default shape/economy constants, commit OFF.
_ENV = make_jax_env(JaxEnvConfig(commit=False))


def _assert_obs_equal(np_obs, jx_obs, where: int) -> None:
    for k in _OBS_KEYS:
        assert np.array_equal(np.asarray(np_obs[k]), np.asarray(jx_obs[k])), (
            f"obs[{k}] differs @{where}"
        )


def _make_env(seed: int, vary: bool):
    if vary:
        env = CritterEnv(commit_battles=False, vary=True, num_types=_NUM_TYPES)
        region = generate_region(seed, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    else:
        env = CritterEnv(commit_battles=False)
        region = generate_region(seed, _GRID, _NC, _NG)
    return env, region


def _run_parity(seed: int, vary: bool, policy, max_steps: int = 200) -> int:
    env, region = _make_env(seed, vary)
    np_obs, _ = env.reset(seed=seed)
    state = _ENV.reset(region)
    step = _ENV.make_step()
    jx_obs = _ENV.encode_obs(state)
    _assert_obs_equal(np_obs, jx_obs, where=0)  # reset obs parity

    compared = 0
    for _ in range(max_steps):
        action = policy(env, np_obs)
        np_obs, r_np, term_np, trunc_np, _ = env.step(action)
        state, jx_obs, r_jx, term_jx, trunc_jx = step(state, jnp.int32(action))
        compared += 1
        _assert_obs_equal(np_obs, jx_obs, where=compared)
        assert float(r_np) == float(r_jx), f"reward differs @{compared}"
        assert bool(term_np) == bool(term_jx), f"terminated differs @{compared}"
        assert bool(trunc_np) == bool(trunc_jx), f"truncated differs @{compared}"
        if term_np or trunc_np:
            break
    return compared


@pytest.mark.parametrize("seed", [0, 1, 2, 7, 13])
def test_parity_random_policy_vary(seed: int) -> None:
    """Full-episode parity under a fixed random action sequence (vary charts)."""
    rng = np.random.default_rng(2000 + seed)
    assert _run_parity(seed, vary=True, policy=lambda e, o: int(rng.integers(0, 6))) > 0


@pytest.mark.parametrize("seed", [0, 1, 3])
def test_parity_random_policy_fixed(seed: int) -> None:
    """Full-episode parity on the fixed M1 chart."""
    rng = np.random.default_rng(seed)
    assert _run_parity(seed, vary=False, policy=lambda e, o: int(rng.integers(0, 6))) > 0


def _gym_seeking_policy(env, obs):
    """Move toward the nearest undefeated gym; in battle, attack (action 0)."""
    if obs["in_battle"][0]:
        return 0  # MOVE (attack)
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


@pytest.mark.parametrize("seed", [0, 1, 2, 4, 7, 11])
def test_parity_gym_clearing_policy(seed: int) -> None:
    """Directed policy that clears gyms → exercises termination + evolution parity."""
    assert _run_parity(seed, vary=True, policy=_gym_seeking_policy) > 0


def _switchy_battle_policy_factory():
    """In battle, cycle SWITCH(4) → ITEM/wasted(5) → attack(0); else seek a gym.

    Exercises the non-commit-specific paths: mid-battle SWITCH, the wasted ``item`` turn,
    and force-switch when the active faints under the boss's attacks.
    """
    cyc = iter(())

    def policy(env, obs):
        nonlocal cyc
        if obs["in_battle"][0]:
            return next(cyc, 0)  # default attack when the cycle is exhausted
        # entering/seeking: refresh the in-battle action cycle and walk toward a gym.
        cyc = iter([4, 5, 0, 4, 0, 0, 0, 0, 0])
        return _gym_seeking_policy(env, obs)

    return policy


@pytest.mark.parametrize("seed", [0, 1, 2, 5, 8, 12])
def test_parity_switch_heavy_battle(seed: int) -> None:
    """Switch/item/force-switch battle paths stay in parity (the non-commit core)."""
    assert _run_parity(seed, vary=True, policy=_switchy_battle_policy_factory()) > 0


def test_parity_fixed_switch_heavy() -> None:
    """Switch-heavy battle on the fixed M1 chart."""
    assert _run_parity(0, vary=False, policy=_switchy_battle_policy_factory()) > 0


def _never_attack_policy(env, obs):
    """Seek a gym, then only SWITCH (never attack) → the boss grinds the party down,
    forcing fainted-active force-switches and ultimately a party-wipe loss. This is the
    non-commit path the winning policies never reach (force-switch + party-wipe + the
    loss-exit-with-no-reward branch)."""
    if obs["in_battle"][0]:
        return 4  # SWITCH only — never deal damage
    return _gym_seeking_policy(env, obs)


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4, 6, 9, 10])
def test_parity_force_switch_and_party_wipe(seed: int) -> None:
    """Force-switch + party-wipe (loss) parity — the never-win battle path."""
    assert _run_parity(seed, vary=True, policy=_never_attack_policy) > 0


def test_force_switch_actually_exercised() -> None:
    """Guard against a vacuous battery: the never-attack policy must, on some seed,
    actually faint an active and force-switch (active index jumps past a fainted member),
    and reach a party-wipe — confirming the parity test above is load-bearing."""
    saw_force_switch = saw_wipe = False
    for seed in range(8):
        env = CritterEnv(commit_battles=False, vary=True, num_types=_NUM_TYPES)
        obs, _ = env.reset(seed=seed)
        prev_active = None
        for _ in range(200):
            obs, r, term, trunc, _ = env.step(_never_attack_policy(env, obs))
            if env._battle is not None:
                cur = env._battle.state.active_a
                # a force-switch shows up as the active advancing while members are fainted.
                if prev_active is not None and cur != prev_active and any(
                    c.is_fainted for c in env._battle.state.party_a
                ):
                    saw_force_switch = True
                prev_active = cur
            else:
                prev_active = None
            if term or trunc:
                break
        # a party-wipe loss leaves the env back in overworld with at least one fainted member
        if any(c.is_fainted for c in env._party):
            saw_wipe = True
    assert saw_force_switch, "battery never exercised a force-switch"
    assert saw_wipe, "battery never exercised a party-wipe"


def test_jit_compiles() -> None:
    region = generate_region(0, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES)
    step = _ENV.make_step(jit=True)
    state = _ENV.reset(region)
    state, obs, reward, term, trunc = step(state, jnp.int32(2))
    jax.block_until_ready(state.agent_pos)
    assert obs["local_patch"].shape == (5, 5)
    assert reward.shape == ()
    assert term.dtype == jnp.bool_


def test_vmap_batches() -> None:
    """vmap a batch of full non-commit episodes (the RL-loop consumption form)."""
    batch = 16
    states = [_ENV.reset(generate_region(s, _GRID, _NC, _NG, vary=True, num_types=_NUM_TYPES))
              for s in range(batch)]
    batched = jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *states)
    vstep = jax.jit(jax.vmap(_ENV.step))
    actions = jnp.asarray(np.random.default_rng(0).integers(0, 6, size=batch), jnp.int32)
    state, obs, reward, term, trunc = vstep(batched, actions)
    jax.block_until_ready(reward)
    assert reward.shape == (batch,)
    assert obs["local_patch"].shape == (batch, 5, 5)
    assert term.shape == (batch,)
