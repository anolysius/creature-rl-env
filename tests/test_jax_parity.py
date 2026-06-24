"""AC1/AC2: numpy <-> JAX overworld parity + jit/vmap guards (M4 foundation).

Verifies that the functional JAX overworld port (``critter_gym.jax_overworld``)
reproduces the numpy ``CritterEnv``/``ForageEnv`` overworld trajectory *exactly* for
the same seed + same action sequence, up to the battle boundary (battle is not ported
in this foundation task). Also guards that the step ``jit``-compiles and ``vmap``-
batches with the right shapes.

The whole module is skipped when JAX is not installed, so the default (CI) suite
stays numpy-only — JAX lives behind the ``[jax]`` extra.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from critter_gym.envs.critter_env import CritterEnv  # noqa: E402
from critter_gym.envs.forage_env import ForageEnv  # noqa: E402
from critter_gym.jax_overworld import (  # noqa: E402
    OverworldState,
    make_step_fn,
    overworld_step,
    state_from_region,
)
from critter_gym.region import generate_region  # noqa: E402

_GRID = 10
_NUM_CREATURES = 5
_NUM_GYMS = 3


def _numpy_env(family: str):
    return ForageEnv() if family == "forage" else CritterEnv()


def _region(seed: int):
    return generate_region(seed, _GRID, _NUM_CREATURES, _NUM_GYMS)


@pytest.mark.parametrize("family,contact", [("critter", False), ("forage", True)])
@pytest.mark.parametrize("seed", [1, 2, 7, 123])
def test_overworld_trajectory_parity(family: str, contact: bool, seed: int) -> None:
    """Same seed + same actions => identical (pos, caught, reward, battle-entry step)."""
    env = _numpy_env(family)
    env.reset(seed=seed)
    # JAX state built from the SAME region (procgen stays numpy; only step is ported).
    state = state_from_region(_region(seed))
    step = make_step_fn(contact=contact)

    rng = np.random.default_rng(1000 + seed)
    steps_compared = 0
    for _ in range(300):
        action = int(rng.integers(0, 6))
        np_obs, np_reward, np_term, np_trunc, _ = env.step(action)
        np_battle = env._mode == "battle"  # the env just entered (or is in) a battle

        state, jx_reward, jx_battle = step(state, jnp.int32(action))
        steps_compared += 1

        assert int(state.agent_pos[0]) == int(np_obs["agent_pos"][0])
        assert int(state.agent_pos[1]) == int(np_obs["agent_pos"][1])
        assert int(state.caught) == int(np_obs["caught"][0])
        assert float(jx_reward) == float(np_reward)
        assert bool(jx_battle) == np_battle

        if np_battle or np_term or np_trunc:
            break  # battle boundary (slice end) or episode end — stop comparing.

    assert steps_compared > 0


def test_jit_compiles() -> None:
    """AC1: the functional overworld step jit-compiles for both families."""
    for contact in (False, True):
        step = make_step_fn(contact=contact, jit=True)
        state = state_from_region(_region(0))
        next_state, reward, battle = step(state, jnp.int32(2))
        jax.block_until_ready(next_state.agent_pos)
        assert next_state.agent_pos.shape == (2,)
        assert reward.shape == ()
        assert battle.dtype == jnp.bool_


def test_vmap_batches() -> None:
    """vmap over a batch of envs preserves leading batch dim (vectorized rollout)."""
    batch = 32
    states = [state_from_region(_region(s)) for s in range(batch)]
    batched = OverworldState(
        agent_pos=jnp.stack([s.agent_pos for s in states]),
        creature_mask=jnp.stack([s.creature_mask for s in states]),
        gym_mask=jnp.stack([s.gym_mask for s in states]),
        caught=jnp.stack([s.caught for s in states]),
        steps=jnp.stack([s.steps for s in states]),
    )
    vstep = jax.jit(jax.vmap(lambda s, a: overworld_step(s, a, contact=True)))
    actions = jnp.asarray(np.random.default_rng(0).integers(0, 6, size=batch), jnp.int32)
    next_batched, rewards, battles = vstep(batched, actions)
    jax.block_until_ready(next_batched.agent_pos)
    assert next_batched.agent_pos.shape == (batch, 2)
    assert rewards.shape == (batch,)
    assert battles.shape == (batch,)


def test_caught_never_exceeds_creatures() -> None:
    """A sanity invariant carried by the port (int32 counters are safe)."""
    step = make_step_fn(contact=True)
    state = state_from_region(_region(3))
    rng = np.random.default_rng(0)
    for _ in range(300):
        state, _, battle = step(state, jnp.int32(int(rng.integers(0, 6))))
        if bool(battle):
            break
    assert 0 <= int(state.caught) <= _NUM_CREATURES
