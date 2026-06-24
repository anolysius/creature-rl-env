"""AC1/AC2/AC3: numpy <-> JAX commit-mode champion battle parity + jit/vmap guards (M4).

Drives the **real** numpy ``Battle(commit_mode=True)`` (champion vs gym boss) and the
functional JAX port (``critter_gym.jax_battle``) from the same initial state + same
action sequence, and asserts identical trajectories (champion hp, boss hp, winner,
turn, done) — including the integer damage formula, the ``max(0, ·)`` hp clamp, the
speed-tie order, and ``max_turns`` truncation. Covers the fixed M1 chart and several
per-seed (``vary``) charts.

Skipped when JAX is absent, so the default (CI) suite stays numpy-only.
"""

from __future__ import annotations

import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from critter_gym.battle import (  # noqa: E402
    ActionKind,
    Battle,
    BattleAction,
    BattleState,
    Side,
    scripted_opponent,
)
from critter_gym.jax_battle import (  # noqa: E402
    WINNER_A,
    WINNER_B,
    WINNER_NONE,
    ChampionBattleState,
    champion_battle_step,
    initial_state,
    make_battle_step,
    params_from_creatures,
)
from critter_gym.party import gym_boss, starter_party  # noqa: E402
from critter_gym.region import generate_region  # noqa: E402
from critter_gym.types import ElementType, TypeChart  # noqa: E402

_TYPES = list(ElementType)
_MAX_TURNS = 200


def _numpy_trajectory(champ_idx, boss_type, chart):
    """Run numpy Battle(commit_mode=True): champion vs boss, both MOVE / scripted boss."""
    party = starter_party()
    boss_party = gym_boss(boss_type)
    state = BattleState(party_a=party, party_b=boss_party)
    state.set_active(Side.A, champ_idx)
    battle = Battle(state, chart=chart, max_turns=_MAX_TURNS, commit_mode=True)
    traj = []
    for _ in range(_MAX_TURNS + 5):
        if battle.terminated or battle.truncated:
            break
        res = battle.step(
            BattleAction(ActionKind.MOVE, 0),
            scripted_opponent(battle.state, Side.B, chart),
        )
        winner = WINNER_NONE if res.winner is None else (
            WINNER_A if res.winner is Side.A else WINNER_B
        )
        traj.append((
            float(state.active(Side.A).hp), float(state.active(Side.B).hp),
            res.turn, res.terminated or res.truncated, winner,
        ))
    return traj


def _jax_trajectory(champ_idx, boss_type, chart):
    party = starter_party()
    boss = gym_boss(boss_type)[0]
    champ = party[champ_idx]
    params = params_from_creatures(champ, boss, chart, max_turns=_MAX_TURNS)
    state = initial_state(champ, boss)
    step = make_battle_step()
    traj = []
    for _ in range(_MAX_TURNS + 5):
        if bool(state.done):
            break
        state = step(state, params)
        traj.append((
            float(state.champ_hp), float(state.boss_hp),
            int(state.turn), bool(state.done), int(state.winner),
        ))
    return traj


@pytest.mark.parametrize("champ_idx", [0, 1, 2])
@pytest.mark.parametrize("boss_type", _TYPES)
def test_parity_fixed_chart(champ_idx: int, boss_type: ElementType) -> None:
    """AC2/AC3: JAX battle == numpy battle on the fixed M1 chart, all champ/boss pairs."""
    chart = TypeChart()
    assert _jax_trajectory(champ_idx, boss_type, chart) == _numpy_trajectory(
        champ_idx, boss_type, chart
    )


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 7])
def test_parity_vary_chart(seed: int) -> None:
    """AC2/AC3: parity holds on per-seed (vary) charts with different effectiveness."""
    region = generate_region(seed, vary=True, num_types=len(_TYPES))
    chart = region.chart
    boss_type = region.gyms[0][1]
    for champ_idx in range(3):
        assert _jax_trajectory(champ_idx, boss_type, chart) == _numpy_trajectory(
            champ_idx, boss_type, chart
        )


def test_jit_compiles_and_terminates() -> None:
    """AC1: the champion battle step jit-compiles and a battle reaches a winner."""
    party = starter_party()
    boss = gym_boss(ElementType.GRASS)[0]
    params = params_from_creatures(party[0], boss, TypeChart())
    state = initial_state(party[0], boss)
    step = make_battle_step(jit=True)
    for _ in range(_MAX_TURNS + 5):
        if bool(state.done):
            break
        state = step(state, params)
    jax.block_until_ready(state.champ_hp)
    assert bool(state.done)
    assert int(state.winner) in (WINNER_A, WINNER_B)


def test_done_state_is_idempotent() -> None:
    """A finished battle does not change under further steps."""
    party = starter_party()
    boss = gym_boss(ElementType.GRASS)[0]
    params = params_from_creatures(party[0], boss, TypeChart())
    state = initial_state(party[0], boss)
    step = make_battle_step()
    while not bool(state.done):
        state = step(state, params)
    frozen = step(state, params)
    assert int(frozen.turn) == int(state.turn)
    assert float(frozen.champ_hp) == float(state.champ_hp)
    assert int(frozen.winner) == int(state.winner)


def test_vmap_batches() -> None:
    """vmap runs a batch of independent battles (the throughput path)."""
    batch = 16
    party = starter_party()
    boss = gym_boss(ElementType.GRASS)[0]
    p = params_from_creatures(party[0], boss, TypeChart())
    params = jax.tree_util.tree_map(lambda x: jnp.broadcast_to(x, (batch,) + x.shape), p)
    state = ChampionBattleState(
        champ_hp=jnp.full((batch,), float(party[0].hp), jnp.float32),
        boss_hp=jnp.full((batch,), float(boss.hp), jnp.float32),
        turn=jnp.zeros((batch,), jnp.int32),
        done=jnp.zeros((batch,), jnp.bool_),
        winner=jnp.zeros((batch,), jnp.int32),
    )
    vstep = jax.jit(jax.vmap(champion_battle_step))
    state = vstep(state, params)
    jax.block_until_ready(state.champ_hp)
    assert state.champ_hp.shape == (batch,)
    assert state.winner.shape == (batch,)
