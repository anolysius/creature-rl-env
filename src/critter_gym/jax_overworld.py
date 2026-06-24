"""JAX functional port of the overworld step — M4 (throughput) de-risk foundation.

CritterGym's numpy env (``critter_gym.envs.critter_env``) is OOP/mutable: the world
state lives in Python ``set``/``dict`` containers (``self._creatures``,
``self._gym_tiles``) and the transition uses Python control flow. That cannot be
``jax.jit``-compiled directly. This module ports the **overworld transition** to a
*functional* form over a flat array pytree (:class:`OverworldState`), so it can be
``jit``-compiled and — crucially — ``vmap``-batched over thousands of envs at once
(the source of JAX's throughput win; see ``scripts/bench_throughput.py``).

**Scope (this foundation task):** only the *overworld* step is ported —
- a directional move (N/S/E/W) with grid clipping,
- creature collection (family A ``critter``: an explicit ``CATCH`` on the current
  tile; family B ``forage``: contact-collect on stepping onto a creature),
- and **battle entry as a returned flag only** — the turn-based battle sub-MDP
  (``critter_gym.battle``) is *not* ported here. When ``battle_entered`` goes True,
  the JAX slice has reached its boundary; the numpy env owns the battle. This is the
  honest boundary measured by the parity test (``tests/test_jax_parity.py``).

**Parity contract:** for the same seed + same action sequence, this port reproduces
the numpy ``CritterEnv``/``ForageEnv`` overworld trajectory exactly (agent position,
caught count, per-step reward, and the step at which a battle is entered) — up to the
battle boundary. Procedural generation (``region.generate_region``) stays in numpy
(it runs once per ``reset``, not on the hot path); only the per-step transition is
JAX. :func:`state_from_region` bridges a numpy ``Region`` into an
:class:`OverworldState`.

Requires the ``[jax]`` extra (``pip install critter_gym[jax]``); the core package and
the default (CI) test suite stay numpy-only — this module is imported only by the
parity test (under ``importorskip``) and the benchmark script.
"""

from __future__ import annotations

from typing import Callable, NamedTuple

import jax
import jax.numpy as jnp
import numpy as np

from critter_gym.region import Region

# Action enum — identical to critter_env (MOVE_N, MOVE_S, MOVE_E, MOVE_W, CATCH, NOOP).
_CATCH = 4
# Per-action (dr, dc). Rows 0-3 are the real moves; CATCH/NOOP rows are (0, 0) and are
# masked out via ``is_move`` so their delta is never applied.
_MOVE_DELTAS = jnp.array(
    [[-1, 0], [1, 0], [0, 1], [0, -1], [0, 0], [0, 0]], dtype=jnp.int32
)


class OverworldState(NamedTuple):
    """Flat array pytree for the overworld transition (jit/vmap-friendly).

    ``int32`` is used for the counters/positions so the port is correct without JAX
    x64 mode (off by default); the env's ranges (positions < grid_size, caught <=
    num_creatures, steps <= max_steps) fit int32 with room to spare.
    """

    agent_pos: jax.Array  # (2,) int32 — (row, col)
    creature_mask: jax.Array  # (grid, grid) bool — True where an UNcaught creature sits
    gym_mask: jax.Array  # (grid, grid) bool — True where an UNdefeated gym sits
    caught: jax.Array  # () int32 — creatures collected so far
    steps: jax.Array  # () int32 — overworld steps taken


def state_from_region(region: Region) -> OverworldState:
    """Bridge a numpy :class:`~critter_gym.region.Region` into an OverworldState.

    Procgen stays numpy (once-per-episode, not the hot path); this packs its output
    into the flat JAX arrays the functional step consumes.
    """
    g = region.grid_size
    creature_mask = np.zeros((g, g), dtype=bool)
    for r, c in region.creatures:
        creature_mask[r, c] = True
    gym_mask = np.zeros((g, g), dtype=bool)
    for (r, c), _boss in region.gyms:
        gym_mask[r, c] = True
    ar, ac = region.agent_start
    return OverworldState(
        agent_pos=jnp.array([ar, ac], dtype=jnp.int32),
        creature_mask=jnp.asarray(creature_mask),
        gym_mask=jnp.asarray(gym_mask),
        caught=jnp.asarray(0, dtype=jnp.int32),
        steps=jnp.asarray(0, dtype=jnp.int32),
    )


def overworld_step(
    state: OverworldState, action: jax.Array, *, contact: bool
) -> tuple[OverworldState, jax.Array, jax.Array]:
    """One functional overworld step. Returns ``(next_state, reward, battle_entered)``.

    ``contact=False`` is family A (``critter``: explicit ``CATCH``); ``contact=True``
    is family B (``forage``: contact-collect). ``contact`` is a static Python bool so
    the two mechanics compile to branch-free code (no per-step ``cond``). Mirrors
    ``CritterEnv._step_overworld`` / ``ForageEnv._step_overworld`` exactly up to the
    battle boundary:

    - move (action 0-3): clip to the grid; family B collects a creature on the landed
      tile (and then does *not* check for a battle that step); a battle is entered iff
      the landed tile is an undefeated gym (family A always checks; family B only when
      no creature was collected).
    - ``CATCH`` (4): family A collects a creature on the *current* tile (no move, no
      battle check); inert in family B.
    - ``NOOP`` (5): nothing.
    """
    action = jnp.asarray(action, dtype=jnp.int32)
    grid = state.creature_mask.shape[0]
    cm = state.creature_mask
    pos = state.agent_pos
    r0, c0 = pos[0], pos[1]

    is_move = action < 4
    delta = _MOVE_DELTAS[action]
    nr = jnp.clip(r0 + delta[0], 0, grid - 1)
    nc = jnp.clip(c0 + delta[1], 0, grid - 1)
    new_pos = jnp.where(is_move, jnp.array([nr, nc], dtype=jnp.int32), pos)

    if contact:
        # family B: collect on the tile we stepped onto.
        collected = is_move & cm[nr, nc]
        cm_next = cm.at[nr, nc].set(jnp.where(collected, False, cm[nr, nc]))
        # battle only on a move that did NOT collect (numpy env's else-branch).
        battle_entered = is_move & (~collected) & state.gym_mask[nr, nc]
    else:
        # family A: collect only via CATCH on the current tile.
        collected = (action == _CATCH) & cm[r0, c0]
        cm_next = cm.at[r0, c0].set(jnp.where(collected, False, cm[r0, c0]))
        # battle on any move onto an undefeated gym (creatures irrelevant).
        battle_entered = is_move & state.gym_mask[nr, nc]

    reward = jnp.where(collected, jnp.float32(1.0), jnp.float32(0.0))
    next_state = OverworldState(
        agent_pos=new_pos,
        creature_mask=cm_next,
        gym_mask=state.gym_mask,
        caught=state.caught + collected.astype(jnp.int32),
        steps=state.steps + jnp.int32(1),
    )
    return next_state, reward, battle_entered


_StepFn = Callable[
    [OverworldState, jax.Array], "tuple[OverworldState, jax.Array, jax.Array]"
]


def make_step_fn(*, contact: bool, jit: bool = True) -> _StepFn:
    """A ready ``(state, action) -> (state, reward, battle_entered)`` for one family.

    ``contact`` is baked in as a static (Python) value; the returned callable is
    ``jax.jit``-compiled by default. Use ``jax.vmap`` over the result for batched
    (vectorized) rollouts — that is where the throughput win comes from (a single env
    under jit is *slower* than numpy due to dispatch overhead; see the bench script).
    """

    def step(
        state: OverworldState, action: jax.Array
    ) -> tuple[OverworldState, jax.Array, jax.Array]:
        return overworld_step(state, action, contact=contact)

    return jax.jit(step) if jit else step
