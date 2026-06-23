"""AC3–AC8: battle engine — damage, turn order, switch/item, termination,
scripted opponent, determinism."""

from __future__ import annotations

import copy

from critter_gym.battle import (
    POTION_HEAL,
    ActionKind,
    Battle,
    BattleAction,
    BattleState,
    ItemKind,
    Side,
    play_scripted,
    scripted_opponent,
)
from critter_gym.creatures import Creature, Move
from critter_gym.types import ElementType

F, W, G = ElementType.FIRE, ElementType.WATER, ElementType.GRASS

MOVE = lambda i=0: BattleAction(ActionKind.MOVE, i)  # noqa: E731


def _c(name: str, types: tuple, hp: int = 50, atk: int = 12, df: int = 10,
       spd: int = 10, moves: list | None = None) -> Creature:
    return Creature(
        name=name, types=types, max_hp=hp, attack=atk, defense=df, speed=spd,
        moves=moves or [Move("tackle", types[0], 40)],
    )


def _state(**kw) -> BattleState:
    a = _c("A", (F,), **kw.pop("a", {}))
    b = _c("B", (G,), **kw.pop("b", {}))
    return BattleState(party_a=[a], party_b=[b], **kw)


def test_damage_is_deterministic_and_type_advantaged() -> None:
    # FIRE attacker vs GRASS defender => super effective (2.0).
    st = _state()
    battle = Battle(st)
    fire_dmg = battle.damage(st.active(Side.A), st.active(Side.B), 0)
    # vs a WATER defender the same move is not-very-effective (0.5).
    st2 = BattleState(party_a=[_c("A", (F,))], party_b=[_c("B", (W,))])
    water_dmg = Battle(st2).damage(st2.active(Side.A), st2.active(Side.B), 0)
    assert fire_dmg == max(1, int(40 * 12 / 10 * 2.0)) == 96
    assert water_dmg == max(1, int(40 * 12 / 10 * 0.5)) == 24
    assert fire_dmg > water_dmg


def test_faster_creature_strikes_first() -> None:
    # A is faster and one-shots B before B can act.
    a = _c("A", (F,), spd=20, atk=100)
    b = _c("B", (G,), spd=5, hp=10)
    battle = Battle(BattleState(party_a=[a], party_b=[b]))
    res = battle.step(MOVE(), MOVE())
    assert b.is_fainted
    assert a.hp == a.max_hp  # B never got to move
    assert res.terminated and res.winner is Side.A


def test_switch_changes_active_and_costs_turn() -> None:
    bench = _c("A2", (W,))
    # B is weak (deals 1 dmg) so the switched-in bench survives and stays active.
    weak_b = _c("B", (G,), atk=1, moves=[Move("poke", G, 1)])
    st = BattleState(party_a=[_c("A", (F,)), bench], party_b=[weak_b])
    battle = Battle(st)
    battle.step(BattleAction(ActionKind.SWITCH, 1), MOVE())
    assert st.active(Side.A) is bench       # switched in and survived
    assert bench.hp == bench.max_hp - 1     # took B's (1 dmg) hit after switching in


def test_item_heals_and_is_consumed() -> None:
    # A at 10 hp uses a potion (+20 -> capped); B deals exactly 1 dmg that turn.
    a = _c("A", (F,), hp=50)
    a.take_damage(40)  # hp -> 10
    weak_b = _c("B", (G,), atk=1, moves=[Move("poke", G, 1)])
    st = BattleState(party_a=[a], party_b=[weak_b])
    battle = Battle(st)
    before = st.items(Side.A)[ItemKind.POTION]
    battle.step(BattleAction(ActionKind.ITEM, 0), MOVE())
    assert a.hp == 10 + POTION_HEAL - 1     # healed to 30, then B's 1 dmg -> 29
    assert st.items(Side.A)[ItemKind.POTION] == before - 1


def test_forced_switch_on_faint_then_loss() -> None:
    # A's first creature faints; forced switch to the bench; when bench also faints A loses.
    a1 = _c("A1", (G,), hp=1)
    a2 = _c("A2", (G,), hp=1)
    b = _c("B", (F,), atk=100, spd=99)  # fire one-shots grass
    st = BattleState(party_a=[a1, a2], party_b=[b])
    battle = Battle(st)
    r1 = battle.step(MOVE(), MOVE())
    assert a1.is_fainted and st.active(Side.A) is a2 and not r1.terminated
    r2 = battle.step(MOVE(), MOVE())
    assert a2.is_fainted and r2.terminated and r2.winner is Side.B


def test_commit_mode_switch_is_a_noop() -> None:
    # team-commit (reasoning-load-bearing AC1): you commit one champion — a SWITCH
    # action is ignored, so a policy cannot probe by cycling creatures mid-battle.
    bench = _c("A2", (W,))
    weak_b = _c("B", (G,), atk=1, moves=[Move("poke", G, 1)])
    st = BattleState(party_a=[_c("A", (F,)), bench], party_b=[weak_b])
    battle = Battle(st, commit_mode=True)
    lead = st.active(Side.A)
    battle.step(BattleAction(ActionKind.SWITCH, 1), MOVE())
    assert st.active(Side.A) is lead          # switch ignored — still the committed lead


def test_commit_mode_active_faint_is_immediate_loss() -> None:
    # In commit mode a fainted active is NOT force-switched to an alive bench: the
    # committed champion's faint ends the battle as a loss (no free brute-force).
    a1 = _c("A1", (G,), hp=1)
    a2 = _c("A2", (G,), hp=1)            # alive bench that must NOT be cycled in
    b = _c("B", (F,), atk=100, spd=99)  # fire one-shots grass
    st = BattleState(party_a=[a1, a2], party_b=[b])
    battle = Battle(st, commit_mode=True)
    r = battle.step(MOVE(), MOVE())
    assert a1.is_fainted and not a2.is_fainted        # bench untouched
    assert r.terminated and r.winner is Side.B         # lost despite an alive bench


def test_commit_mode_defaults_off_preserves_forced_switch() -> None:
    # Regression: default (commit_mode=False) keeps M1 force-switch behavior.
    a1 = _c("A1", (G,), hp=1)
    a2 = _c("A2", (G,), hp=1)
    b = _c("B", (F,), atk=100, spd=99)
    st = BattleState(party_a=[a1, a2], party_b=[b])
    battle = Battle(st)  # default
    r1 = battle.step(MOVE(), MOVE())
    assert a1.is_fainted and st.active(Side.A) is a2 and not r1.terminated


def test_scripted_opponent_picks_most_effective_move() -> None:
    attacker = _c("A", (F,), moves=[Move("splash", W, 40), Move("flare", F, 40)])
    # defender GRASS: FIRE move (idx1) is super-effective, WATER (idx0) not-very.
    st = BattleState(party_a=[attacker], party_b=[_c("B", (G,))])
    action = scripted_opponent(st, Side.A)
    assert action.kind is ActionKind.MOVE and action.index == 1


def test_scripted_battle_terminates() -> None:
    st = BattleState(party_a=[_c("A", (F,))], party_b=[_c("B", (G,))])
    res = play_scripted(st, max_turns=200)
    assert res.terminated and res.winner in (Side.A, Side.B)
    assert res.turn <= 200


def test_stalemate_truncates() -> None:
    # Two defenders whose moves deal 1 dmg into huge HP -> never resolves in time.
    a = _c("A", (F,), hp=1000, moves=[Move("tick", F, 1)], atk=1, df=1000)
    b = _c("B", (W,), hp=1000, moves=[Move("tick", W, 1)], atk=1, df=1000)
    res = play_scripted(BattleState(party_a=[a], party_b=[b]), max_turns=5)
    assert res.truncated and not res.terminated and res.winner is None


def test_simultaneous_wipe_resolves_to_side_b() -> None:
    # Both parties fully fainted at resolution -> documented tie-break: B wins.
    # (Unreachable via normal move ordering, so this pins the defensive branch.)
    a, b = _c("A", (F,)), _c("B", (G,))
    a.take_damage(999)
    b.take_damage(999)
    res = Battle(BattleState(party_a=[a], party_b=[b])).step(MOVE(), MOVE())
    assert res.terminated and res.winner is Side.B


def test_determinism_same_actions_same_trace() -> None:
    base = BattleState(
        party_a=[_c("A", (F,), moves=[Move("m", F, 30)]), _c("A2", (W,))],
        party_b=[_c("B", (G,), moves=[Move("m", G, 30)]), _c("B2", (F,))],
    )
    actions = [MOVE(), BattleAction(ActionKind.ITEM, 0), MOVE(), MOVE()]

    def run(state: BattleState) -> list[tuple[int, int]]:
        battle = Battle(state)
        trace = []
        for act in actions:
            battle.step(act, MOVE())
            trace.append((state.active(Side.A).hp, state.active(Side.B).hp))
        return trace

    assert run(copy.deepcopy(base)) == run(copy.deepcopy(base))
