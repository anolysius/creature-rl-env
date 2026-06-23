"""Turn-based battle sub-MDP (DESIGN.md §3.4), fully deterministic.

A battle is two parties of `Creature`s. Each turn both sides choose one
`BattleAction` (move / switch / use-item); the engine resolves the turn with a
fixed, seedless rule set, so an identical initial state + action sequence always
yields an identical outcome (RLVR / reproducibility).

This is the standalone engine only. Wiring battles into `CritterEnv.step` as gated
gym/boss checkpoints is a later M1 task (`gym-boss-progression`, M1-EC3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from critter_gym.creatures import Creature
from critter_gym.types import TypeChart

POTION_HEAL = 20
DEFAULT_MAX_TURNS = 200


class Side(Enum):
    A = "a"
    B = "b"


class ActionKind(Enum):
    MOVE = "move"
    SWITCH = "switch"
    ITEM = "item"


class ItemKind(Enum):
    POTION = "potion"


@dataclass(frozen=True)
class BattleAction:
    """An agent's choice for one turn. ``index`` selects move/creature/item."""

    kind: ActionKind
    index: int = 0


def _default_items() -> dict[ItemKind, int]:
    return {ItemKind.POTION: 2}


@dataclass
class BattleState:
    party_a: list[Creature]
    party_b: list[Creature]
    active_a: int = 0
    active_b: int = 0
    items_a: dict[ItemKind, int] = field(default_factory=_default_items)
    items_b: dict[ItemKind, int] = field(default_factory=_default_items)
    turn: int = 0

    def party(self, side: Side) -> list[Creature]:
        return self.party_a if side is Side.A else self.party_b

    def active(self, side: Side) -> Creature:
        idx = self.active_a if side is Side.A else self.active_b
        return self.party(side)[idx]

    def items(self, side: Side) -> dict[ItemKind, int]:
        return self.items_a if side is Side.A else self.items_b

    def set_active(self, side: Side, idx: int) -> None:
        if side is Side.A:
            self.active_a = idx
        else:
            self.active_b = idx

    def party_wiped(self, side: Side) -> bool:
        return all(c.is_fainted for c in self.party(side))


@dataclass
class StepResult:
    terminated: bool
    truncated: bool
    winner: Side | None
    turn: int


def _other(side: Side) -> Side:
    return Side.B if side is Side.A else Side.A


class Battle:
    """Stateful turn-based battle engine."""

    def __init__(
        self,
        state: BattleState,
        chart: TypeChart | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
        commit_mode: bool = False,
    ) -> None:
        self.state = state
        self.chart = chart or TypeChart()
        self.max_turns = max_turns
        # team-commit (reasoning-load-bearing AC1): when True the side commits one
        # champion — SWITCH actions are ignored, a fainted active is NOT force-switched
        # to the bench, and a fainted active loses immediately. This removes the free
        # force-switch "try every creature" brute force AND in-battle probing, so that
        # cross-battle *inference* of the hidden type chart becomes load-bearing
        # (DESIGN §3.1.1). Default False keeps M1 battle behavior unchanged.
        self.commit_mode = commit_mode
        self.terminated = False
        self.truncated = False
        self.winner: Side | None = None

    # -- public API ---------------------------------------------------------

    def damage(self, attacker: Creature, defender: Creature, move_index: int) -> int:
        """Deterministic damage for a move (also used to score scripted choices)."""
        move = attacker.moves[move_index]
        eff = self.chart.multi_effectiveness(move.type, defender.types)
        return max(1, int(move.power * attacker.attack / defender.defense * eff))

    def step(self, action_a: BattleAction, action_b: BattleAction) -> StepResult:
        if self.terminated or self.truncated:
            return self._result()
        self.state.turn += 1

        # Phase 1 — non-move actions (switch / item) resolve before moves.
        for side, action in ((Side.A, action_a), (Side.B, action_b)):
            if action.kind is ActionKind.SWITCH:
                if not self.commit_mode:  # commit mode: no mid-battle switching
                    self._switch(side, action.index)
            elif action.kind is ActionKind.ITEM:
                self._use_item(side, action.index)

        # Phase 2 — moves, faster active first; ties resolve A before B.
        movers = [
            (side, action)
            for side, action in ((Side.A, action_a), (Side.B, action_b))
            if action.kind is ActionKind.MOVE
        ]
        movers.sort(key=lambda sa: (-self.state.active(sa[0]).speed, sa[0].value))
        for side, action in movers:
            attacker = self.state.active(side)
            defender = self.state.active(_other(side))
            if attacker.is_fainted or defender.is_fainted:
                continue
            defender.take_damage(self.damage(attacker, defender, action.index))

        # Phase 3 — force-switch fainted actives to the next alive creature.
        # Skipped in commit mode: a committed champion is not replaced on faint.
        if not self.commit_mode:
            for side in (Side.A, Side.B):
                if self.state.active(side).is_fainted:
                    nxt = self._next_alive(side)
                    if nxt is not None:
                        self.state.set_active(side, nxt)

        self._update_terminal()
        return self._result()

    def legal_moves(self, side: Side) -> list[int]:
        return list(range(len(self.state.active(side).moves)))

    # -- internals ----------------------------------------------------------

    def _switch(self, side: Side, idx: int) -> None:
        party = self.state.party(side)
        if 0 <= idx < len(party) and not party[idx].is_fainted:
            self.state.set_active(side, idx)
        # else: illegal switch is a wasted turn (no-op).

    def _use_item(self, side: Side, item_index: int) -> None:
        # M1: index 0 == POTION. Unknown index or empty stock == wasted turn.
        if item_index != 0:
            return
        items = self.state.items(side)
        if items.get(ItemKind.POTION, 0) > 0:
            self.state.active(side).heal(POTION_HEAL)
            items[ItemKind.POTION] -= 1

    def _next_alive(self, side: Side) -> int | None:
        for i, c in enumerate(self.state.party(side)):
            if not c.is_fainted:
                return i
        return None

    def _update_terminal(self) -> None:
        if self.commit_mode:
            # Champion's faint == loss (no bench to cycle to).
            a_wiped = self.state.active(Side.A).is_fainted
            b_wiped = self.state.active(Side.B).is_fainted
        else:
            a_wiped = self.state.party_wiped(Side.A)
            b_wiped = self.state.party_wiped(Side.B)
        if a_wiped or b_wiped:
            self.terminated = True
            # If both wiped the same turn, the side that still has a standing
            # active loses last; resolve deterministically to A-wiped => B wins.
            self.winner = Side.B if a_wiped else Side.A
        elif self.state.turn >= self.max_turns:
            self.truncated = True

    def _result(self) -> StepResult:
        return StepResult(self.terminated, self.truncated, self.winner, self.state.turn)


def scripted_opponent(
    state: BattleState, side: Side, chart: TypeChart | None = None
) -> BattleAction:
    """Greedy, type-aware policy: pick the move with the highest deterministic damage."""
    chart = chart or TypeChart()
    attacker = state.active(side)
    defender = state.active(_other(side))
    best_idx, best_dmg = 0, -1
    for i, move in enumerate(attacker.moves):
        eff = chart.multi_effectiveness(move.type, defender.types)
        dmg = max(1, int(move.power * attacker.attack / defender.defense * eff))
        if dmg > best_dmg:
            best_idx, best_dmg = i, dmg
    return BattleAction(ActionKind.MOVE, best_idx)


def play_scripted(state: BattleState, max_turns: int = DEFAULT_MAX_TURNS) -> StepResult:
    """Run a full battle with both sides driven by ``scripted_opponent``."""
    battle = Battle(state, max_turns=max_turns)
    result = StepResult(False, False, None, 0)
    while not (battle.terminated or battle.truncated):
        a = scripted_opponent(battle.state, Side.A, battle.chart)
        b = scripted_opponent(battle.state, Side.B, battle.chart)
        result = battle.step(a, b)
    return result
