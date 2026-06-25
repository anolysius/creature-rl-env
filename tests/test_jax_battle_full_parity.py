"""numpy <-> JAX parity for the NON-commit full battle (jax-battle-full / M4).

Drives the real numpy ``Battle(commit_mode=False)`` (starter party of 3 vs a single
boss) and the JAX port (``critter_gym.jax_battle_full``) from the same action sequence
and asserts every party hp, the active index, boss hp, winner, turn and done match —
across an action battery (attack / switch / item-heal / force-switch / party-wipe /
truncation) and random sequences on fixed and per-seed charts, plus a jit/vmap smoke.

Skipped when JAX is absent → CI stays numpy-only.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from critter_gym import jax_battle_full as JB  # noqa: E402
from critter_gym.battle import (  # noqa: E402
    ActionKind,
    Battle,
    BattleAction,
    BattleState,
    Side,
    scripted_opponent,
)
from critter_gym.party import gym_boss, starter_party  # noqa: E402
from critter_gym.types import ElementType, TypeChart, generate_typechart  # noqa: E402

_WINNER = {None: JB.WINNER_NONE, Side.A: JB.WINNER_A, Side.B: JB.WINNER_B}
_KIND = {ActionKind.MOVE: JB.ACT_MOVE, ActionKind.SWITCH: JB.ACT_SWITCH,
         ActionKind.ITEM: JB.ACT_ITEM}


def _run(chart, boss_kw, actions, max_turns=200) -> int:
    party_a = starter_party()
    boss_party = gym_boss(ElementType.GRASS, **boss_kw)
    boss = boss_party[0]
    battle = Battle(BattleState(party_a=party_a, party_b=boss_party), chart=chart,
                    commit_mode=False, max_turns=max_turns)
    params = JB.params_from_parties(party_a, boss, chart, max_turns=max_turns)
    state = JB.initial_state(party_a, boss)
    step = JB.make_full_battle_step()

    compared = 0
    for pact in actions:
        if battle.terminated or battle.truncated:
            break
        bact = scripted_opponent(battle.state, Side.B, chart)
        battle.step(pact, bact)
        state = step(state, jnp.int32(_KIND[pact.kind]), jnp.int32(pact.index), params)
        compared += 1
        np_hp = [c.hp for c in battle.state.party_a]
        jx_hp = [float(x) for x in np.asarray(state.party_a_hp)]
        assert np_hp == jx_hp, f"party hp @{compared}: {np_hp} vs {jx_hp}"
        assert battle.state.active_a == int(state.active_a), f"active @{compared}"
        assert battle.state.party_b[0].hp == float(state.boss_hp), f"boss hp @{compared}"
        assert battle.state.turn == int(state.turn), f"turn @{compared}"
        assert (battle.terminated or battle.truncated) == bool(state.done), f"done @{compared}"
        assert _WINNER[battle.winner] == int(state.winner), f"winner @{compared}"
    return compared


_ATTACK = [BattleAction(ActionKind.MOVE, 0)] * 60
_SWITCH = ([BattleAction(ActionKind.SWITCH, 1), BattleAction(ActionKind.MOVE, 0),
            BattleAction(ActionKind.SWITCH, 2)] + [BattleAction(ActionKind.MOVE, 0)] * 40)
_ITEM = ([BattleAction(ActionKind.MOVE, 0)] + [BattleAction(ActionKind.ITEM, 0)] * 3
         + [BattleAction(ActionKind.MOVE, 0)] * 40)


def test_parity_attack_weak_boss() -> None:
    assert _run(TypeChart(), dict(hp=60, atk=10, df=10, spd=8), _ATTACK) > 0


def test_parity_force_switch_and_party_wipe() -> None:
    # strong fast boss → actives faint → force-switch → eventual party wipe (B wins).
    assert _run(TypeChart(), dict(hp=400, atk=40, df=20, spd=20), _ATTACK) > 0


def test_parity_switch_sequence() -> None:
    assert _run(TypeChart(), dict(hp=400, atk=18, df=14, spd=8), _SWITCH) > 0


def test_parity_item_heal() -> None:
    assert _run(TypeChart(), dict(hp=400, atk=18, df=14, spd=8), _ITEM) > 0


def test_parity_truncation() -> None:
    # unkillable boss, tiny budget → truncation (done via max_turns, winner NONE).
    assert _run(TypeChart(), dict(hp=100_000, atk=1, df=10_000, spd=1), _ATTACK,
                max_turns=10) > 0


@pytest.mark.parametrize("seed", list(range(12)))
def test_parity_random_sequences(seed: int) -> None:
    rng = np.random.default_rng(seed)
    chart = (generate_typechart(seed, list(ElementType)[:8], vary=True, super_mult=3.0)
             if seed % 2 else TypeChart())
    boss_kw = dict(hp=int(rng.integers(50, 300)), atk=int(rng.integers(8, 40)),
                   df=int(rng.integers(8, 24)), spd=int(rng.integers(5, 25)))
    actions = []
    for _ in range(80):
        r = int(rng.integers(0, 5))
        actions.append(
            BattleAction(ActionKind.SWITCH, int(rng.integers(0, 3))) if r == 0
            else BattleAction(ActionKind.ITEM, 0) if r == 1
            else BattleAction(ActionKind.MOVE, 0)
        )
    assert _run(chart, boss_kw, actions) > 0


def test_jit_and_vmap() -> None:
    party_a = starter_party()
    boss = gym_boss(ElementType.GRASS, hp=200, atk=15, df=12, spd=8)[0]
    params = JB.params_from_parties(party_a, boss, TypeChart())
    step = JB.make_full_battle_step(jit=True)
    state = JB.initial_state(party_a, boss)
    state = step(state, jnp.int32(JB.ACT_MOVE), jnp.int32(0), params)
    jax.block_until_ready(state.boss_hp)
    assert state.party_a_hp.shape == (3,)

    batch = 8
    states = [JB.initial_state(party_a, boss) for _ in range(batch)]
    batched = jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *states)
    bparams = jax.tree_util.tree_map(lambda x: jnp.broadcast_to(x, (batch,) + x.shape), params)
    vstep = jax.jit(jax.vmap(JB.full_battle_step))
    out = vstep(batched, jnp.zeros(batch, jnp.int32), jnp.zeros(batch, jnp.int32), bparams)
    jax.block_until_ready(out.boss_hp)
    assert out.boss_hp.shape == (batch,)
    assert out.party_a_hp.shape == (batch, 3)
