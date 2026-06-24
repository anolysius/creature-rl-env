"""JAX functional port of the full CritterGym episode — M4 (throughput) env integration.

Composes the overworld port (`jax_overworld`) and the commit-mode champion battle
(`jax_battle`) into a single **full-episode** env step that an RL loop can `vmap` over
thousands of environments at once. Where the prior tasks shipped step *slices*, this
exposes a usable surface: `jax_env_step(state, action) -> (state, obs, reward,
terminated, truncated)`, mirroring `CritterEnv(commit_battles=True)` (family A,
`CritterGym-commit-v0` — the reasoning-load-bearing / learnability path).

**Scope:** family A (`critter`) with `commit_battles=True`. The step dispatches by mode
(`jax.lax.cond`): the overworld branch moves / catches / enters a gym battle (heals the
party, opens the champion-select commit window); the battle branch cycles the champion
during the commit window, otherwise resolves one commit-mode turn, and on a win marks
the gym defeated, levels up and conditionally evolves the champion. Termination = all
(real) gyms defeated; truncation = `max_steps`.

**Parity contract:** for the same seed + same action sequence, this reproduces
`CritterEnv(commit_battles=True)` exactly — every observation key (incl. the 5x5
egocentric `local_patch`), reward, terminated, truncated. Procgen (`generate_region`)
stays numpy; `jax_reset` bridges a `Region` into the state. Verified in
`tests/test_jax_env_parity.py`.

Throughput comes from `vmap` (full-episode control flow diverges per env, so the
multiplier is lower than the pure slices but still large); see
`scripts/bench_throughput.py`. Requires the `[jax]` extra; core + CI stay numpy-only
(imported only by the parity test under `importorskip` and the bench script).
"""

from __future__ import annotations

from typing import Callable, NamedTuple

import jax
import jax.numpy as jnp
import numpy as np

from critter_gym.party import starter_party
from critter_gym.region import Region
from critter_gym.types import ElementType, TypeChart

# --- env constants (CritterEnv defaults for the commit-mode family-A path) ---
_GRID = 10
_PATCH_RADIUS = 2
_PATCH_SIDE = 2 * _PATCH_RADIUS + 1
_MAX_STEPS = 200
_MAX_GYMS = 3
_PARTY = 3
_CATCH = 4  # action enum: MOVE_N/S/E/W=0-3, CATCH=4, NOOP=5
_BOSS_HP, _BOSS_ATK, _BOSS_DEF, _BOSS_SPD = 120, 12, 12, 8
_BOSS_MOVE_POWER = 30.0
_PATCH_CREATURE, _PATCH_GYM = 1, 2

_MODE_OVERWORLD, _MODE_BATTLE = 0, 1

_TYPES = list(ElementType)
_NUM_TYPES = len(_TYPES)
_TYPE_TO_INT = {t: i for i, t in enumerate(_TYPES)}

_MOVE_DELTAS = jnp.array(
    [[-1, 0], [1, 0], [0, 1], [0, -1], [0, 0], [0, 0]], dtype=jnp.int32
)


def _party_stat_tables() -> tuple[jax.Array, jax.Array]:
    """(base, evolved) stat tables for the fixed starter party: (PARTY, 7) each.

    Columns: max_hp, attack, defense, speed, move_power, move_type_idx, def_type_idx.
    Evolution changes the first four (and keeps the single move / type).
    """
    base, evo = [], []
    for c in starter_party():
        mt, dt = _TYPE_TO_INT[c.moves[0].type], _TYPE_TO_INT[c.types[0]]
        base.append((c.max_hp, c.attack, c.defense, c.speed, c.moves[0].power, mt, dt))
        f = c.evolves_to
        assert f is not None
        evo.append((f.max_hp, f.attack, f.defense, f.speed, c.moves[0].power, mt, dt))
    return jnp.asarray(np.array(base, np.float32)), jnp.asarray(np.array(evo, np.float32))


_BASE_STATS, _EVO_STATS = _party_stat_tables()


class JaxEnvState(NamedTuple):
    """Full-episode env state pytree (jit/vmap-friendly). Family A, commit-mode.

    Per-episode constants (set at reset, immutable except ``gym_defeated``): ``gym_pos``,
    ``gym_type``, ``gym_active`` (real-gym mask — ``vary`` charts have 1..MAX_GYMS gyms),
    ``eff`` (the seed's type-effectiveness matrix). The rest is mutable episode state.
    """

    agent_pos: jax.Array  # (2,) int32
    creature_mask: jax.Array  # (GRID, GRID) bool
    gym_pos: jax.Array  # (MAX_GYMS, 2) int32 (unused slots = -1)
    gym_type: jax.Array  # (MAX_GYMS,) int32
    gym_active: jax.Array  # (MAX_GYMS,) bool — real gyms for this seed
    gym_defeated: jax.Array  # (MAX_GYMS,) bool
    eff: jax.Array  # (NUM_TYPES, NUM_TYPES) float32
    mode: jax.Array  # () int32 — 0 overworld / 1 battle
    commit_window: jax.Array  # () bool
    active: jax.Array  # () int32 — committed champion idx
    party_hp: jax.Array  # (PARTY,) float32
    party_level: jax.Array  # (PARTY,) int32
    party_evolved: jax.Array  # (PARTY,) bool
    boss_hp: jax.Array  # () float32
    battle_gym: jax.Array  # () int32 — gym idx currently fought
    caught: jax.Array  # () int32
    evolved: jax.Array  # () int32
    steps: jax.Array  # () int32


def jax_reset(region: Region) -> JaxEnvState:
    """Bridge a numpy :class:`~critter_gym.region.Region` into a fresh episode state.

    Procgen stays numpy (once per episode); this packs its output into the JAX state
    arrays. Unused gym slots (``vary`` charts have fewer than ``MAX_GYMS`` gyms) are
    padded with position ``-1`` and ``gym_active=False`` so they never trigger a battle
    and do not block termination.
    """
    cm = np.zeros((_GRID, _GRID), dtype=bool)
    for r, c in region.creatures:
        cm[r, c] = True
    gym_pos = np.full((_MAX_GYMS, 2), -1, dtype=np.int32)
    gym_type = np.zeros((_MAX_GYMS,), dtype=np.int32)
    gym_active = np.zeros((_MAX_GYMS,), dtype=bool)
    for i, ((r, c), t) in enumerate(region.gyms):
        gym_pos[i] = (r, c)
        gym_type[i] = _TYPE_TO_INT[t]
        gym_active[i] = True
    return JaxEnvState(
        agent_pos=jnp.asarray(region.agent_start, dtype=jnp.int32),
        creature_mask=jnp.asarray(cm),
        gym_pos=jnp.asarray(gym_pos),
        gym_type=jnp.asarray(gym_type),
        gym_active=jnp.asarray(gym_active),
        gym_defeated=jnp.zeros((_MAX_GYMS,), dtype=bool),
        eff=_eff_matrix(region.chart),
        mode=jnp.asarray(_MODE_OVERWORLD, dtype=jnp.int32),
        commit_window=jnp.asarray(False),
        active=jnp.asarray(0, dtype=jnp.int32),
        party_hp=_BASE_STATS[:, 0],
        party_level=jnp.ones((_PARTY,), dtype=jnp.int32),
        party_evolved=jnp.zeros((_PARTY,), dtype=bool),
        boss_hp=jnp.asarray(0.0, dtype=jnp.float32),
        battle_gym=jnp.asarray(-1, dtype=jnp.int32),
        caught=jnp.asarray(0, dtype=jnp.int32),
        evolved=jnp.asarray(0, dtype=jnp.int32),
        steps=jnp.asarray(0, dtype=jnp.int32),
    )


def _eff_matrix(chart: TypeChart) -> jax.Array:
    rows = [[chart.effectiveness(a, d) for d in _TYPES] for a in _TYPES]
    return jnp.asarray(rows, dtype=jnp.float32)


def _stat(s: JaxEnvState, idx: jax.Array, col: int) -> jax.Array:
    """Current stat[col] for party member ``idx`` (evolved-aware)."""
    return jnp.where(s.party_evolved[idx], _EVO_STATS[idx, col], _BASE_STATS[idx, col])


def _damage(power: jax.Array, atk: jax.Array, df: jax.Array, eff: jax.Array) -> jax.Array:
    return jnp.maximum(1.0, jnp.floor(power * atk / df * eff))


def _overworld_branch(s: JaxEnvState, action: jax.Array) -> tuple[JaxEnvState, jax.Array]:
    is_move = action < 4
    delta = _MOVE_DELTAS[action]
    nr = jnp.clip(s.agent_pos[0] + delta[0], 0, _GRID - 1)
    nc = jnp.clip(s.agent_pos[1] + delta[1], 0, _GRID - 1)
    new_pos = jnp.where(is_move, jnp.array([nr, nc], dtype=jnp.int32), s.agent_pos)

    r0, c0 = s.agent_pos[0], s.agent_pos[1]
    catch = (action == _CATCH) & s.creature_mask[r0, c0]
    cm = s.creature_mask.at[r0, c0].set(jnp.where(catch, False, s.creature_mask[r0, c0]))
    reward = jnp.where(catch, 1.0, 0.0)

    # battle entry: a move onto an undefeated, active gym tile.
    on_gym = jnp.asarray(False)
    gym_idx = jnp.asarray(-1, dtype=jnp.int32)
    for i in range(_MAX_GYMS):
        hit = (
            is_move
            & (new_pos[0] == s.gym_pos[i, 0])
            & (new_pos[1] == s.gym_pos[i, 1])
            & s.gym_active[i]
            & (~s.gym_defeated[i])
        )
        on_gym = on_gym | hit
        gym_idx = jnp.where(hit, i, gym_idx)

    healed = jnp.where(s.party_evolved, _EVO_STATS[:, 0], _BASE_STATS[:, 0])
    s = s._replace(
        agent_pos=new_pos,
        creature_mask=cm,
        caught=s.caught + catch.astype(jnp.int32),
        mode=jnp.where(on_gym, _MODE_BATTLE, _MODE_OVERWORLD).astype(jnp.int32),
        commit_window=on_gym,
        battle_gym=jnp.where(on_gym, gym_idx, s.battle_gym).astype(jnp.int32),
        party_hp=jnp.where(on_gym, healed, s.party_hp),
        boss_hp=jnp.where(on_gym, jnp.float32(_BOSS_HP), s.boss_hp),
        active=jnp.where(on_gym, 0, s.active).astype(jnp.int32),
    )
    return s, reward


def _battle_branch(s: JaxEnvState, action: jax.Array) -> tuple[JaxEnvState, jax.Array]:
    def cycle(s: JaxEnvState) -> tuple[JaxEnvState, jax.Array]:
        # commit window + action 4: cycle the champion to the next alive party member
        # (no battle turn) — mirrors CritterEnv._next_alive_player.
        cur = s.active
        nxt = cur
        found = jnp.asarray(False)
        for off in range(1, _PARTY + 1):
            i = (cur + off) % _PARTY
            alive = s.party_hp[i] > 0
            take = alive & (~found)
            nxt = jnp.where(take, i, nxt).astype(jnp.int32)
            found = found | alive
        return s._replace(active=nxt), jnp.float32(0.0)

    def fight(s: JaxEnvState) -> tuple[JaxEnvState, jax.Array]:
        act = s.active
        btype = s.gym_type[s.battle_gym]
        c_mt = _stat(s, act, 5).astype(jnp.int32)
        c_dt = _stat(s, act, 6).astype(jnp.int32)
        # only a MOVE (action < 4) makes the champion attack; SWITCH (4, ignored in
        # commit-mode) and NOOP (5, a wasted item turn) leave the champion idle while
        # the boss still strikes — mirrors CritterEnv._to_battle_action.
        champ_dmg = jnp.where(
            action < 4,
            _damage(_stat(s, act, 4), _stat(s, act, 1), jnp.float32(_BOSS_DEF), s.eff[c_mt, btype]),
            0.0,
        )
        boss_dmg = _damage(
            jnp.float32(_BOSS_MOVE_POWER), jnp.float32(_BOSS_ATK), _stat(s, act, 2),
            s.eff[btype, c_dt],
        )
        champ_first = _stat(s, act, 3) >= _BOSS_SPD
        ch, bh = s.party_hp[act], s.boss_hp

        def champ_first_fn(_: None) -> tuple[jax.Array, jax.Array]:
            nb = jnp.maximum(0.0, bh - champ_dmg)
            nc = jnp.where(nb > 0, jnp.maximum(0.0, ch - boss_dmg), ch)
            return nc, nb

        def boss_first_fn(_: None) -> tuple[jax.Array, jax.Array]:
            nc = jnp.maximum(0.0, ch - boss_dmg)
            nb = jnp.where(nc > 0, jnp.maximum(0.0, bh - champ_dmg), bh)
            return nc, nb

        nc, nb = jax.lax.cond(champ_first, champ_first_fn, boss_first_fn, operand=None)
        champ_fainted = nc <= 0
        boss_fainted = nb <= 0
        win = boss_fainted & (~champ_fainted)
        done_battle = champ_fainted | boss_fainted

        gym = s.battle_gym
        new_level = s.party_level[act] + jnp.where(win, 1, 0)
        can_evolve = win & (~s.party_evolved[act]) & (new_level >= 2)
        reward = jnp.where(win, 1.0, 0.0) + jnp.where(can_evolve, 1.0, 0.0)
        s = s._replace(
            commit_window=jnp.asarray(False),
            party_hp=s.party_hp.at[act].set(nc),
            boss_hp=nb,
            gym_defeated=s.gym_defeated.at[gym].set(
                jnp.where(win, True, s.gym_defeated[gym])
            ),
            party_level=s.party_level.at[act].set(new_level),
            party_evolved=s.party_evolved.at[act].set(
                jnp.where(can_evolve, True, s.party_evolved[act])
            ),
            evolved=s.evolved + can_evolve.astype(jnp.int32),
            mode=jnp.where(done_battle, _MODE_OVERWORLD, _MODE_BATTLE).astype(jnp.int32),
        )
        return s, reward

    do_cycle = s.commit_window & (action == 4)
    return jax.lax.cond(do_cycle, cycle, fight, s)


def jax_env_step(
    state: JaxEnvState, action: jax.Array
) -> tuple[JaxEnvState, dict[str, jax.Array], jax.Array, jax.Array, jax.Array]:
    """One full-episode env step → (state, obs, reward, terminated, truncated).

    Dispatches by mode (`lax.cond`): overworld (move/catch/battle-entry) or battle
    (commit-window cycle or one commit-mode turn). Mirrors
    ``CritterEnv(commit_battles=True).step`` for family A.
    """
    action = jnp.asarray(action, dtype=jnp.int32)
    steps = state.steps + jnp.int32(1)

    def ow(s: JaxEnvState) -> tuple[JaxEnvState, jax.Array]:
        return _overworld_branch(s, action)

    def bt(s: JaxEnvState) -> tuple[JaxEnvState, jax.Array]:
        return _battle_branch(s, action)

    state, reward = jax.lax.cond(state.mode == _MODE_OVERWORLD, ow, bt, state)
    state = state._replace(steps=steps)

    # termination: all real (active) gyms defeated; truncation: step budget. These are
    # computed *independently* (mirroring CritterEnv.step) — both can be True on the same
    # step if the last gym falls exactly at max_steps; suppressing one would break parity.
    terminated = jnp.all(jnp.where(state.gym_active, state.gym_defeated, True))
    truncated = steps >= _MAX_STEPS
    return state, encode_obs(state), reward, terminated, truncated


def encode_obs(state: JaxEnvState) -> dict[str, jax.Array]:
    """The 13-key observation, matching ``CritterEnv._obs`` (HARMONIZED_OBS_KEYS).

    ``local_patch`` is the (2r+1)² egocentric view (creatures=1, undefeated active
    gyms=2) built by padding the grid and ``dynamic_slice``-ing a window at the agent.
    Battle fields are 0 outside battle; charge keys are 0 (family A, base mask).
    """
    grid = state.creature_mask.astype(jnp.int8) * _PATCH_CREATURE
    for i in range(_MAX_GYMS):
        show = state.gym_active[i] & (~state.gym_defeated[i])
        gr, gc = state.gym_pos[i, 0], state.gym_pos[i, 1]
        # unused slots have pos -1; jnp index -1 wraps to last cell, so guard with show
        # AND a valid-position check (pos >= 0).
        valid = show & (gr >= 0) & (gc >= 0)
        gr_s, gc_s = jnp.maximum(gr, 0), jnp.maximum(gc, 0)
        grid = grid.at[gr_s, gc_s].set(
            jnp.where(valid, jnp.int8(_PATCH_GYM), grid[gr_s, gc_s])
        )
    padded = jnp.pad(grid, _PATCH_RADIUS)
    patch = jax.lax.dynamic_slice(
        padded,
        (state.agent_pos[0], state.agent_pos[1]),
        (_PATCH_SIDE, _PATCH_SIDE),
    )

    in_battle = state.mode == _MODE_BATTLE
    act = state.active
    p_hp = jnp.where(in_battle, state.party_hp[act], 0.0).astype(jnp.int32)
    p_ty = jnp.where(in_battle, _stat(state, act, 6).astype(jnp.int32), 0)
    p_lvl = jnp.where(in_battle, state.party_level[act], 0)
    e_hp = jnp.where(in_battle, state.boss_hp, 0.0).astype(jnp.int32)
    e_ty = jnp.where(in_battle, state.gym_type[state.battle_gym], 0)
    defeated = jnp.sum((state.gym_defeated & state.gym_active).astype(jnp.int32))

    return {
        "agent_pos": state.agent_pos,
        "local_patch": patch,
        "caught": state.caught[jnp.newaxis],
        "gyms_defeated": defeated[jnp.newaxis],
        "evolved": state.evolved[jnp.newaxis],
        "in_battle": in_battle.astype(jnp.int8)[jnp.newaxis],
        "player_hp": p_hp[jnp.newaxis],
        "player_type": p_ty[jnp.newaxis],
        "player_level": p_lvl[jnp.newaxis],
        "enemy_hp": e_hp[jnp.newaxis],
        "enemy_type": e_ty[jnp.newaxis],
        "player_charge": jnp.zeros((1,), dtype=jnp.int32),
        "enemy_charge": jnp.zeros((1,), dtype=jnp.int32),
    }


def make_env_step(jit: bool = True) -> Callable[
    [JaxEnvState, jax.Array],
    tuple[JaxEnvState, dict[str, jax.Array], jax.Array, jax.Array, jax.Array],
]:
    """A ready full-episode env step, ``jit`` by default. ``vmap`` it for batched RL."""
    return jax.jit(jax_env_step) if jit else jax_env_step
