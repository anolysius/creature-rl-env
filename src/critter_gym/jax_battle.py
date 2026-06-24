"""JAX functional port of the commit-mode champion battle — M4 (throughput).

The numpy battle engine (`critter_gym.battle.Battle`) is a stateful, branchy
turn-based sub-MDP. This module ports the **commit-mode champion fight** — the path
the env actually uses for gym bosses (`commit_battles=True`, `CritterGym-commit-v0`;
the reasoning-load-bearing / learnability work): one committed champion vs one boss,
no mid-battle switching, no force-switch, a fainted champion loses. That removes the
multi-creature switching/items/force-switch machinery, leaving a clean functional
core: each turn both sides use their move, the faster acts first (speed tie → side A),
damage applies, and a faint ends the battle.

**Scope (this task):** commit-mode champion only. The full non-commit battle
(3-creature party + SWITCH + ITEM + force-switch + party-wipe terminal) is the
follow-up `jax-battle-full`. Together with `jax_overworld`, the commit-mode battle
covers the env's load-bearing gym-boss path.

**Parity contract:** for the same initial champion/boss + same action sequence, this
port reproduces `Battle(commit_mode=True)` exactly — champion hp, boss hp, winner,
turn, done — including the integer damage formula and the `max(0, ·)` hp clamp
(`Creature.take_damage`). Verified in `tests/test_jax_battle_parity.py`.

The throughput win is from `vmap` (thousands of battles in lock-step); see
`scripts/bench_throughput.py`. Requires the `[jax]` extra; the core package and CI
stay numpy-only (this module is imported only by the parity test under `importorskip`
and the bench script).
"""

from __future__ import annotations

from typing import Callable, NamedTuple

import jax
import jax.numpy as jnp

from critter_gym.battle import Side
from critter_gym.types import ElementType, TypeChart

# Winner encoding for the JAX state (Side is not jittable).
WINNER_NONE = 0
WINNER_A = 1  # champion (Side.A)
WINNER_B = 2  # boss (Side.B)

_TYPES = list(ElementType)
_NUM_TYPES = len(_TYPES)
_TYPE_TO_INT = {t: i for i, t in enumerate(_TYPES)}


class ChampionBattleState(NamedTuple):
    """Flat array pytree for a commit-mode champion battle (jit/vmap-friendly).

    Floats for hp (the numpy engine clamps to 0 via ``max(0, ·)``; we mirror that).
    ``winner`` uses the WINNER_* encoding. All fields are scalars (or a leading batch
    dim under ``vmap``).
    """

    champ_hp: jax.Array  # () float32
    boss_hp: jax.Array  # () float32
    turn: jax.Array  # () int32
    done: jax.Array  # () bool
    winner: jax.Array  # () int32 — WINNER_NONE / WINNER_A / WINNER_B


class ChampionBattleParams(NamedTuple):
    """Static per-battle stats (champion + boss) and the type-effectiveness matrix.

    These do not change within a battle. Kept as arrays so a batched (``vmap``) run can
    vary them per battle; ``params_from_creatures`` builds one instance.
    """

    c_atk: jax.Array
    c_def: jax.Array
    c_spd: jax.Array
    c_pow: jax.Array
    c_move_type: jax.Array  # int32 index into the type axis
    c_def_type: jax.Array  # champion's (single) defending type index
    b_atk: jax.Array
    b_def: jax.Array
    b_spd: jax.Array
    b_pow: jax.Array
    b_move_type: jax.Array
    b_def_type: jax.Array
    eff: jax.Array  # (num_types, num_types) float32 — eff[move_type, def_type]
    max_turns: jax.Array  # () int32


def eff_matrix(chart: TypeChart) -> jax.Array:
    """Type-effectiveness as a ``(num_types, num_types)`` matrix: ``eff[atk, def]``.

    Single-type lookup (champion + bosses are single-type); the matrix collapses the
    chart so the JAX step is a plain gather, no Python loop.
    """
    rows = [
        [chart.effectiveness(a, d) for d in _TYPES] for a in _TYPES
    ]
    return jnp.asarray(rows, dtype=jnp.float32)


def _creature_arrays(creature: object) -> tuple[float, float, float, float, int, int]:
    """(atk, def, speed, move_power, move_type_idx, def_type_idx) from a Creature."""
    c = creature  # typed loosely to avoid importing the dataclass for a pure read
    return (
        float(c.attack),  # type: ignore[attr-defined]
        float(c.defense),  # type: ignore[attr-defined]
        float(c.speed),  # type: ignore[attr-defined]
        float(c.moves[0].power),  # type: ignore[attr-defined]
        _TYPE_TO_INT[c.moves[0].type],  # type: ignore[attr-defined]
        _TYPE_TO_INT[c.types[0]],  # type: ignore[attr-defined]
    )


def params_from_creatures(
    champion: object, boss: object, chart: TypeChart, max_turns: int = 200
) -> ChampionBattleParams:
    """Build battle params from a numpy champion + boss ``Creature`` (single-type, 1 move)."""
    c_atk, c_def, c_spd, c_pow, c_mt, c_dt = _creature_arrays(champion)
    b_atk, b_def, b_spd, b_pow, b_mt, b_dt = _creature_arrays(boss)
    f = lambda x: jnp.asarray(x, dtype=jnp.float32)  # noqa: E731
    i = lambda x: jnp.asarray(x, dtype=jnp.int32)  # noqa: E731
    return ChampionBattleParams(
        c_atk=f(c_atk), c_def=f(c_def), c_spd=f(c_spd), c_pow=f(c_pow),
        c_move_type=i(c_mt), c_def_type=i(c_dt),
        b_atk=f(b_atk), b_def=f(b_def), b_spd=f(b_spd), b_pow=f(b_pow),
        b_move_type=i(b_mt), b_def_type=i(b_dt),
        eff=eff_matrix(chart), max_turns=i(max_turns),
    )


def initial_state(champion: object, boss: object) -> ChampionBattleState:
    """Fresh state at a battle's start (full hp, turn 0, not done)."""
    return ChampionBattleState(
        champ_hp=jnp.asarray(champion.hp, dtype=jnp.float32),  # type: ignore[attr-defined]
        boss_hp=jnp.asarray(boss.hp, dtype=jnp.float32),  # type: ignore[attr-defined]
        turn=jnp.asarray(0, dtype=jnp.int32),
        done=jnp.asarray(False),
        winner=jnp.asarray(WINNER_NONE, dtype=jnp.int32),
    )


def _damage(power: jax.Array, atk: jax.Array, df: jax.Array, eff: jax.Array) -> jax.Array:
    """Deterministic damage = max(1, floor(power * atk / def * eff)) — numpy's int()."""
    return jnp.maximum(1.0, jnp.floor(power * atk / df * eff))


def champion_battle_step(
    state: ChampionBattleState, params: ChampionBattleParams
) -> ChampionBattleState:
    """One commit-mode turn: both sides MOVE, faster first (tie → champion/A).

    Mirrors ``Battle.step`` under ``commit_mode=True`` with both sides issuing their
    only move: damage with the type chart, ``max(0, ·)`` hp clamp, a fainted attacker's
    move is skipped, and a faint ends the battle (champion faint → boss wins; if both
    faint the same turn, A is wiped first → boss wins). ``max_turns`` truncates.
    Already-done states pass through unchanged.
    """

    def live(s: ChampionBattleState) -> ChampionBattleState:
        champ_dmg = _damage(
            params.c_pow, params.c_atk, params.b_def,
            params.eff[params.c_move_type, params.b_def_type],
        )
        boss_dmg = _damage(
            params.b_pow, params.b_atk, params.c_def,
            params.eff[params.b_move_type, params.c_def_type],
        )
        champ_first = params.c_spd >= params.b_spd  # tie → A first (Side.A.value < B)

        def champ_first_fn(_: None) -> tuple[jax.Array, jax.Array]:
            nb = jnp.maximum(0.0, s.boss_hp - champ_dmg)
            boss_alive = nb > 0
            nc = jnp.where(boss_alive, jnp.maximum(0.0, s.champ_hp - boss_dmg), s.champ_hp)
            return nc, nb

        def boss_first_fn(_: None) -> tuple[jax.Array, jax.Array]:
            nc = jnp.maximum(0.0, s.champ_hp - boss_dmg)
            champ_alive = nc > 0
            nb = jnp.where(champ_alive, jnp.maximum(0.0, s.boss_hp - champ_dmg), s.boss_hp)
            return nc, nb

        nc, nb = jax.lax.cond(champ_first, champ_first_fn, boss_first_fn, operand=None)
        turn = s.turn + jnp.int32(1)
        champ_fainted = nc <= 0
        boss_fainted = nb <= 0
        faint_done = champ_fainted | boss_fainted
        # commit-mode: champion faint = loss; both fainted same turn → A wiped first → B wins.
        winner = jnp.where(
            champ_fainted, WINNER_B, jnp.where(boss_fainted, WINNER_A, WINNER_NONE)
        ).astype(jnp.int32)
        truncated = (~faint_done) & (turn >= params.max_turns)
        return ChampionBattleState(
            champ_hp=nc, boss_hp=nb, turn=turn,
            done=faint_done | truncated, winner=winner,
        )

    return jax.lax.cond(state.done, lambda s: s, live, state)


def make_battle_step(jit: bool = True) -> Callable[
    [ChampionBattleState, ChampionBattleParams], ChampionBattleState
]:
    """A ready ``(state, params) -> state`` champion-battle step, ``jit`` by default.

    ``vmap`` over this for batched battles (the throughput win); a single jit battle is
    slower than numpy (dispatch overhead), like the overworld port.
    """
    return jax.jit(champion_battle_step) if jit else champion_battle_step


def scripted_move_index(params: ChampionBattleParams, *, side: Side) -> int:
    """Greedy type-aware move choice for one side — index of the max-damage move.

    Mirrors ``battle.scripted_opponent``. With a single move per creature this is
    always 0; provided for parity completeness and future multi-move ports.
    """
    return 0
