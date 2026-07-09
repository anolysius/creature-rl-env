"""commit-mode + SE-only closes the cycling-attrition path (hard-benchmark/attrition-closure).

#7 (super_effective_only) found SE-only only PARTIALLY dented the attrition confound, because
in non-commit mode a fainted active force-switches through the party — a no-inference policy
eventually cycles onto a super-effective member and grinds the boss down. These deterministic
Battle-level tests prove the *mechanism* of the fix: with commit-mode (no switching, a fainted
champion loses) + SE-only (only strictly super-effective hits land), a champion committed to a
non-super creature deals 0 and cannot win — whereas the same party in non-commit mode CAN win by
cycling to a super member. The statistical picture across seeds is measured by the scout; this
file pins the engine mechanism the scout's verdict rests on.
"""

from __future__ import annotations

from critter_gym.battle import ActionKind, Battle, BattleAction, BattleState, Side
from critter_gym.creatures import Creature, Move
from critter_gym.types import FIXED_CHART, ElementType

F, W, G = ElementType.FIRE, ElementType.WATER, ElementType.GRASS
# FIXED chart 3-cycle: FIRE > GRASS > WATER > FIRE (attacker super-effective vs defender).


def _creature(name: str, ctype: ElementType, move_type: ElementType, *, hp: int = 60,
              atk: int = 14, df: int = 10, spd: int = 10, power: int = 30) -> Creature:
    return Creature(name, (ctype,), hp, atk, df, spd, moves=[Move("m", move_type, power)])


def _run(battle: Battle, max_steps: int = 500):
    move = BattleAction(ActionKind.MOVE, 0)
    result = battle.step(move, move)
    for _ in range(max_steps):
        if result.terminated or result.truncated:
            break
        result = battle.step(move, move)
    return result


# -- AC2(a): a non-super committed champion deals 0 and cannot win -----------------


def test_commit_se_only_non_super_champion_cannot_win() -> None:
    # champion FIRE move vs WATER boss => resisted (eff < NEUTRAL) => 0 under SE-only.
    # boss WATER move vs FIRE champion => super => boss faints the champion => commit loss.
    champ = _creature("champ", F, F)
    boss = _creature("boss", W, W, hp=80)
    battle = Battle(BattleState(party_a=[champ], party_b=[boss]),
                    chart=FIXED_CHART, commit_mode=True, super_effective_only=True)
    result = _run(battle)
    assert result.winner is not Side.A  # the no-inference champion never wins
    assert boss.hp == boss.max_hp  # champion's resisted hits dealt exactly 0


def test_commit_se_only_neutral_champion_draws_at_zero() -> None:
    # both sides NEUTRAL to each other (FIRE move vs FIRE) => 0 both ways => draw, nobody wins.
    champ = _creature("champ", F, F)
    boss = _creature("boss", F, F)
    battle = Battle(BattleState(party_a=[champ], party_b=[boss]), chart=FIXED_CHART,
                    commit_mode=True, super_effective_only=True, max_turns=50)
    result = _run(battle, max_steps=60)
    assert result.winner is None and result.truncated
    assert champ.hp == champ.max_hp and boss.hp == boss.max_hp


# -- AC2(b): the right (super) commit still wins -----------------------------------


def test_commit_se_only_super_champion_wins() -> None:
    # champion FIRE vs GRASS boss => super => damage flows; boss GRASS vs FIRE => resisted => 0.
    champ = _creature("champ", F, F, atk=30, power=40)
    boss = _creature("boss", G, G, hp=60)
    battle = Battle(BattleState(party_a=[champ], party_b=[boss]),
                    chart=FIXED_CHART, commit_mode=True, super_effective_only=True)
    result = _run(battle)
    assert result.winner is Side.A  # oracle-style correct commit stays winnable
    assert champ.hp == champ.max_hp  # boss's resisted hits dealt 0


# -- AC2(c): commit removes the cycling that lets non-commit win -------------------


def _cycling_party() -> list[Creature]:
    # creature0 FIRE (resisted vs WATER boss, faints to it); creature1 GRASS (super vs WATER boss,
    # safe from it). Under SE-only: c0 deals 0, boss faints c0; the union needs the cycle to c1.
    c0 = _creature("c0-fire", F, F, hp=40)          # boss (WATER) is super vs FIRE => c0 faints
    c1 = _creature("c1-grass", G, G, atk=30, power=40)  # GRASS super vs WATER boss => can win
    return [c0, c1]


def _water_boss() -> list[Creature]:
    return [_creature("boss", W, W, hp=60, atk=20, power=40)]


def test_noncommit_cycles_to_super_member_and_wins() -> None:
    battle = Battle(BattleState(party_a=_cycling_party(), party_b=_water_boss()),
                    chart=FIXED_CHART, commit_mode=False, super_effective_only=True)
    result = _run(battle)
    # force-switch cycles the fainted FIRE lead to the GRASS member, which super-effects the boss.
    assert result.winner is Side.A
    assert battle.state.active_a == 1  # the cycle moved onto creature 1


def test_commit_blocks_the_cycle_and_loses() -> None:
    battle = Battle(BattleState(party_a=_cycling_party(), party_b=_water_boss()),
                    chart=FIXED_CHART, commit_mode=True, super_effective_only=True)
    result = _run(battle)
    # committed to creature 0 (FIRE): deals 0, faints to the boss, no switch => champion loses.
    assert result.winner is Side.B
    assert battle.state.active_a == 0  # never cycled off the committed lead
