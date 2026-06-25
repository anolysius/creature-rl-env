"""JAX functional port of the NON-commit full battle — M4 (throughput), the battle
hot path's remaining half.

`jax_battle.py` ported the *commit-mode champion* fight (one champion vs one boss, no
switching) — the gym-boss load-bearing path. This module ports the **non-commit full
battle** (`Battle(commit_mode=False)`): a multi-creature party with **SWITCH**, **ITEM**
(potion), faint **force-switch**, and **party-wipe** termination — the env's default
(non-commit) battle economy. Like the commit port it is a standalone, parity-gated
`(state, action) -> state` turn step that `vmap` runs in lock-step.

**Scope:** the env-usage shape — `party_a` = the starter party (P creatures) vs a single
boss creature (`party_b = [boss]`, so the boss only ever MOVEs). One turn = one player
action: MOVE / SWITCH(i) / ITEM(i). This is a *standalone* battle step (not wired into
`jax_env`, which stays commit-only); the non-commit full-env integration is a follow-up.
Marginal-utility note: gym bosses use commit-mode (already ported), so this completes M4
battle coverage rather than replacing the load-bearing path.

**Parity contract:** for the same initial parties + same action sequence, this reproduces
`Battle(commit_mode=False)` exactly — every party hp, the active index, boss hp, winner,
turn, done — including the integer damage formula, the `max(0, ·)` damage clamp and the
`min(max_hp, ·)` heal clamp, speed-ordered moves (faster first, tie → side A) with a
fainted attacker's move skipped, and the both-wiped → side-A-wiped-loses tiebreak.
Verified in `tests/test_jax_battle_full_parity.py`.

Requires the `[jax]` extra; the core package and CI stay numpy-only (imported only by the
parity test under `importorskip` and the bench script; not imported by `__init__`).
"""

from __future__ import annotations

from typing import Callable, NamedTuple

import jax
import jax.numpy as jnp

from critter_gym.types import ElementType, TypeChart

# Winner encoding (Side is not jittable). A = player party, B = boss.
WINNER_NONE = 0
WINNER_A = 1
WINNER_B = 2

# Action-kind encoding (mirrors battle.ActionKind for the player side).
ACT_MOVE = 0
ACT_SWITCH = 1
ACT_ITEM = 2

POTION_HEAL = 20.0  # battle.POTION_HEAL

_TYPES = list(ElementType)
_NUM_TYPES = len(_TYPES)
_TYPE_TO_INT = {t: i for i, t in enumerate(_TYPES)}


class FullBattleState(NamedTuple):
    """Flat array pytree for a non-commit battle (jit/vmap-friendly).

    ``party_a_hp`` is the player party's hp (P,); the boss is a single creature
    (``boss_hp`` scalar). Floats for hp (clamped to ``[0, max_hp]`` like the numpy
    engine). All non-party fields are scalars (or a leading batch dim under ``vmap``).
    """

    party_a_hp: jax.Array  # (P,) float32
    active_a: jax.Array  # () int32
    items_a: jax.Array  # () int32 — potion count
    boss_hp: jax.Array  # () float32
    turn: jax.Array  # () int32
    done: jax.Array  # () bool
    winner: jax.Array  # () int32 — WINNER_NONE / WINNER_A / WINNER_B


class FullBattleParams(NamedTuple):
    """Static per-battle stats: the player party arrays (P,) + the single boss + chart."""

    a_max_hp: jax.Array  # (P,)
    a_atk: jax.Array  # (P,)
    a_def: jax.Array  # (P,)
    a_spd: jax.Array  # (P,)
    a_pow: jax.Array  # (P,)
    a_move_type: jax.Array  # (P,) int32
    a_def_type: jax.Array  # (P,) int32
    b_atk: jax.Array  # ()
    b_def: jax.Array  # ()
    b_spd: jax.Array  # ()
    b_pow: jax.Array  # ()
    b_move_type: jax.Array  # () int32
    b_def_type: jax.Array  # () int32
    eff: jax.Array  # (num_types, num_types) float32 — eff[move_type, def_type]
    max_turns: jax.Array  # () int32
    potion_heal: jax.Array  # () float32


def eff_matrix(chart: TypeChart) -> jax.Array:
    rows = [[chart.effectiveness(a, d) for d in _TYPES] for a in _TYPES]
    return jnp.asarray(rows, dtype=jnp.float32)


def params_from_parties(
    party_a: list, boss: object, chart: TypeChart, max_turns: int = 200,
) -> FullBattleParams:
    """Build params from a numpy player party (list of Creature) + a single boss Creature."""
    f = lambda xs: jnp.asarray(xs, dtype=jnp.float32)  # noqa: E731
    i = lambda xs: jnp.asarray(xs, dtype=jnp.int32)  # noqa: E731
    return FullBattleParams(
        a_max_hp=f([c.max_hp for c in party_a]),
        a_atk=f([c.attack for c in party_a]),
        a_def=f([c.defense for c in party_a]),
        a_spd=f([c.speed for c in party_a]),
        a_pow=f([c.moves[0].power for c in party_a]),
        a_move_type=i([_TYPE_TO_INT[c.moves[0].type] for c in party_a]),
        a_def_type=i([_TYPE_TO_INT[c.types[0]] for c in party_a]),
        b_atk=f(boss.attack), b_def=f(boss.defense), b_spd=f(boss.speed),  # type: ignore[attr-defined]
        b_pow=f(boss.moves[0].power),  # type: ignore[attr-defined]
        b_move_type=i(_TYPE_TO_INT[boss.moves[0].type]),  # type: ignore[attr-defined]
        b_def_type=i(_TYPE_TO_INT[boss.types[0]]),  # type: ignore[attr-defined]
        eff=eff_matrix(chart), max_turns=i(max_turns), potion_heal=f(POTION_HEAL),
    )


def initial_state(party_a: list, boss: object, *, potions: int = 2) -> FullBattleState:
    """Fresh state: full hp, active 0, ``potions`` potions, turn 0, not done."""
    return FullBattleState(
        party_a_hp=jnp.asarray([c.hp for c in party_a], dtype=jnp.float32),
        active_a=jnp.asarray(0, dtype=jnp.int32),
        items_a=jnp.asarray(potions, dtype=jnp.int32),
        boss_hp=jnp.asarray(boss.hp, dtype=jnp.float32),  # type: ignore[attr-defined]
        turn=jnp.asarray(0, dtype=jnp.int32),
        done=jnp.asarray(False),
        winner=jnp.asarray(WINNER_NONE, dtype=jnp.int32),
    )


def _damage(power: jax.Array, atk: jax.Array, df: jax.Array, eff: jax.Array) -> jax.Array:
    """Deterministic damage = max(1, floor(power * atk / def * eff)) — numpy's int()."""
    return jnp.maximum(1.0, jnp.floor(power * atk / df * eff))


def full_battle_step(
    state: FullBattleState, act_kind: jax.Array, act_idx: jax.Array, params: FullBattleParams
) -> FullBattleState:
    """One non-commit turn (player action ``act_kind``/``act_idx`` vs scripted boss MOVE).

    Mirrors ``Battle.step`` with ``commit_mode=False``: Phase 1 switch/item, Phase 2
    speed-ordered moves (fainted attacker skipped), Phase 3 force-switch on faint, then
    party-wipe / max-turns termination. Branch-free (``jnp.where``); already-done states
    pass through unchanged.
    """

    def live(s: FullBattleState) -> FullBattleState:
        p = state.party_a_hp.shape[0]
        turn = s.turn + jnp.int32(1)
        kind = jnp.asarray(act_kind, dtype=jnp.int32)
        idx = jnp.asarray(act_idx, dtype=jnp.int32)
        is_move = kind == ACT_MOVE
        is_switch = kind == ACT_SWITCH
        is_item = kind == ACT_ITEM

        # -- Phase 1: switch (to an alive in-range bench member) or item (potion heal) --
        tgt = jnp.clip(idx, 0, p - 1)
        switch_ok = is_switch & (idx >= 0) & (idx < p) & (s.party_a_hp[tgt] > 0)
        active = jnp.where(switch_ok, tgt, s.active_a).astype(jnp.int32)

        cur = s.active_a  # item heals the *current* active (item turn does not switch)
        can_heal = is_item & (idx == 0) & (s.items_a > 0)
        healed = jnp.minimum(params.a_max_hp[cur], s.party_a_hp[cur] + params.potion_heal)
        hp = s.party_a_hp.at[cur].set(jnp.where(can_heal, healed, s.party_a_hp[cur]))
        items = jnp.where(can_heal, s.items_a - 1, s.items_a).astype(jnp.int32)

        # -- Phase 2: moves. Boss always MOVEs; player MOVEs only on an ACT_MOVE turn. --
        # Both actives are alive here (boss: not done; player active: switch target was
        # alive / unchanged-alive invariant), so the faster strikes first and may KO the
        # slower before it acts.
        a_hp = hp[active]
        a_atk, a_def = params.a_atk[active], params.a_def[active]
        a_spd, a_pow = params.a_spd[active], params.a_pow[active]
        a_mt, a_dt = params.a_move_type[active], params.a_def_type[active]
        player_dmg = _damage(a_pow, a_atk, params.b_def, params.eff[a_mt, params.b_def_type])
        boss_dmg = _damage(params.b_pow, params.b_atk, a_def, params.eff[params.b_move_type, a_dt])

        # player-moves resolution (speed order, faster first; tie → A first)
        player_first = a_spd >= params.b_spd
        nb_pf = jnp.maximum(0.0, s.boss_hp - player_dmg)
        na_pf = jnp.where(nb_pf > 0, jnp.maximum(0.0, a_hp - boss_dmg), a_hp)
        na_bf = jnp.maximum(0.0, a_hp - boss_dmg)
        nb_bf = jnp.where(na_bf > 0, jnp.maximum(0.0, s.boss_hp - player_dmg), s.boss_hp)
        na_move = jnp.where(player_first, na_pf, na_bf)
        nb_move = jnp.where(player_first, nb_pf, nb_bf)
        # switch/item turn: player does not attack, only the boss strikes the active.
        na = jnp.where(is_move, na_move, jnp.maximum(0.0, a_hp - boss_dmg))
        nb = jnp.where(is_move, nb_move, s.boss_hp)

        hp = hp.at[active].set(na)
        boss_hp = nb

        # -- Phase 3: force-switch a fainted active to the next alive bench member. --
        alive = hp > 0
        any_alive = jnp.any(alive)
        first_alive = jnp.argmax(alive.astype(jnp.int32)).astype(jnp.int32)
        active = jnp.where((na <= 0) & any_alive, first_alive, active).astype(jnp.int32)

        # -- terminal: party-wipe (all fainted); both wiped → A-wiped loses (B wins). --
        a_wiped = ~jnp.any(hp > 0)
        b_wiped = boss_hp <= 0
        faint_done = a_wiped | b_wiped
        winner = jnp.where(
            a_wiped, WINNER_B, jnp.where(b_wiped, WINNER_A, WINNER_NONE)
        ).astype(jnp.int32)
        truncated = (~faint_done) & (turn >= params.max_turns)
        return FullBattleState(
            party_a_hp=hp, active_a=active, items_a=items, boss_hp=boss_hp,
            turn=turn, done=faint_done | truncated, winner=winner,
        )

    return jax.lax.cond(state.done, lambda s: s, live, state)


def make_full_battle_step(jit: bool = True) -> Callable[
    [FullBattleState, jax.Array, jax.Array, FullBattleParams], FullBattleState
]:
    """A ready ``(state, act_kind, act_idx, params) -> state`` step, ``jit`` by default.
    ``vmap`` over it for batched battles (the throughput win)."""
    return jax.jit(full_battle_step) if jit else full_battle_step
