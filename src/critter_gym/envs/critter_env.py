"""CritterGym environment — catch + gym-boss battle chain (M1).

A grid world (DESIGN.md §3.2, structured/symbolic obs) with two interleaved
modes:

- **OVERWORLD**: the agent moves, catches creatures, and walks onto gym tiles.
- **BATTLE**: stepping onto an undefeated gym tile starts a turn-based battle
  (the sub-MDP of `battle.py`); each env step resolves one battle turn against a
  scripted boss. Winning marks the gym defeated.

Rewards are RLVR-style boolean subgoals — catching a creature (+1) and defeating
a gym boss (+1); movement, battle turns, and losses earn nothing (no dense
shaping). The episode terminates when every gym is defeated.

The action space stays ``Discrete(6)`` and is reinterpreted by mode; the
observation's ``in_battle`` flag tells the agent which interpretation is live.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from gymnasium import Env, spaces

from critter_gym.battle import (
    ActionKind,
    Battle,
    BattleAction,
    BattleState,
    Side,
    scripted_opponent,
)
from critter_gym.creatures import Creature
from critter_gym.party import gym_boss, starter_party
from critter_gym.region import TEST_SEED_OFFSET, generate_region
from critter_gym.types import FIXED_CHART, ElementType, TypeChart

# Action indices (a minimal subset of DESIGN.md §3.3). Reinterpreted in battle:
#   0-3 -> use battle move (clamped), 4 -> switch to next alive, 5 -> pass.
MOVE_N, MOVE_S, MOVE_E, MOVE_W, CATCH, NOOP = range(6)

_MOVE_DELTAS: dict[int, tuple[int, int]] = {
    MOVE_N: (-1, 0),
    MOVE_S: (1, 0),
    MOVE_E: (0, 1),
    MOVE_W: (0, -1),
}

_PATCH_EMPTY, _PATCH_CREATURE, _PATCH_GYM = 0, 1, 2
_HP_MAX = 10_000  # generous obs upper bound for hp fields
_LEVEL_MAX = 100  # generous obs upper bound for creature level
_MAX_PARTY = 6  # generous obs upper bound for the evolved counter
_NUM_TYPES = len(ElementType)
_TYPE_TO_INT: dict[ElementType, int] = {t: i for i, t in enumerate(ElementType)}


class CritterEnv(Env[dict[str, np.ndarray], int]):
    """Grid env with catch + gym-boss battle subgoals (verifiable rewards)."""

    metadata: dict[str, Any] = {"render_modes": []}

    def __init__(
        self,
        grid_size: int = 10,
        num_creatures: int = 5,
        num_gyms: int = 3,
        max_steps: int = 200,
        patch_radius: int = 2,
        vary: bool = False,
    ) -> None:
        super().__init__()
        # num_creatures / num_gyms are the *max* counts (obs bounds); with vary=True
        # the per-episode counts are sampled in [1, max].
        occupied = num_creatures + num_gyms + 1  # +1 for the agent's start tile
        if occupied > grid_size * grid_size:
            raise ValueError("too many creatures/gyms for the grid")
        self.grid_size = grid_size
        self.num_creatures = num_creatures
        self.num_gyms = num_gyms
        self.max_steps = max_steps
        self.patch_radius = patch_radius
        self.vary = vary

        patch_side = 2 * patch_radius + 1
        # gymnasium's Discrete is typed Space[np.int64]; ActType here is int, and
        # Space is invariant, so mypy flags the assignment. Both are int at runtime.
        self.action_space = spaces.Discrete(6)  # type: ignore[assignment]
        self.observation_space = spaces.Dict(
            {
                "agent_pos": spaces.Box(0, grid_size - 1, shape=(2,), dtype=np.int64),
                "local_patch": spaces.Box(
                    0, _PATCH_GYM, shape=(patch_side, patch_side), dtype=np.int8
                ),
                "caught": spaces.Box(0, num_creatures, shape=(1,), dtype=np.int64),
                "gyms_defeated": spaces.Box(0, num_gyms, shape=(1,), dtype=np.int64),
                "evolved": spaces.Box(0, _MAX_PARTY, shape=(1,), dtype=np.int64),
                "in_battle": spaces.Box(0, 1, shape=(1,), dtype=np.int8),
                "player_hp": spaces.Box(0, _HP_MAX, shape=(1,), dtype=np.int64),
                "player_type": spaces.Box(0, _NUM_TYPES - 1, shape=(1,), dtype=np.int64),
                "player_level": spaces.Box(0, _LEVEL_MAX, shape=(1,), dtype=np.int64),
                "enemy_hp": spaces.Box(0, _HP_MAX, shape=(1,), dtype=np.int64),
                "enemy_type": spaces.Box(0, _NUM_TYPES - 1, shape=(1,), dtype=np.int64),
            }
        )

        # Episode state (populated by reset).
        self._agent_pos: np.ndarray = np.zeros(2, dtype=np.int64)
        self._creatures: set[tuple[int, int]] = set()
        self._gym_tiles: dict[tuple[int, int], int] = {}
        self._gym_types: list[ElementType] = []
        self._gym_defeated: list[bool] = []
        self._region_chart: TypeChart = FIXED_CHART
        self._caught = 0
        self._evolved = 0
        self._steps = 0
        self._party: list[Creature] = []
        self._mode = "overworld"
        self._battle: Battle | None = None
        self._battle_gym_idx = -1

    # -- gym API ------------------------------------------------------------

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        super().reset(seed=seed)
        # generate_region is a pure function of the seed; derive one when reset()
        # is called without an explicit seed. Stay strictly below TEST_SEED_OFFSET so
        # an unseeded run can never accidentally sample a held-out world (split-safe).
        region_seed = (
            seed if seed is not None else int(self.np_random.integers(0, TEST_SEED_OFFSET))
        )
        region = generate_region(
            region_seed, self.grid_size, self.num_creatures, self.num_gyms, vary=self.vary
        )

        self._creatures = set(region.creatures)
        self._gym_tiles = {pos: i for i, (pos, _) in enumerate(region.gyms)}
        self._gym_types = [t for (_, t) in region.gyms]
        self._gym_defeated = [False] * len(region.gyms)
        self._region_chart = region.chart
        self._agent_pos = np.array(region.agent_start, dtype=np.int64)

        self._caught = 0
        self._evolved = 0
        self._steps = 0
        self._party = starter_party()
        self._mode = "overworld"
        self._battle = None
        self._battle_gym_idx = -1
        return self._obs(), self._info()

    def step(
        self, action: int
    ) -> tuple[dict[str, np.ndarray], float, bool, bool, dict[str, Any]]:
        if not self.action_space.contains(action):
            raise ValueError(f"invalid action: {action!r}")
        self._steps += 1
        if self._mode == "battle":
            reward = self._step_battle(action)
        else:
            reward = self._step_overworld(action)

        terminated = len(self._gym_defeated) > 0 and all(self._gym_defeated)
        truncated = self._steps >= self.max_steps
        return self._obs(), reward, terminated, truncated, self._info()

    # -- overworld ----------------------------------------------------------

    def _step_overworld(self, action: int) -> float:
        if action in _MOVE_DELTAS:
            dr, dc = _MOVE_DELTAS[action]
            self._agent_pos = np.array(
                [
                    np.clip(self._agent_pos[0] + dr, 0, self.grid_size - 1),
                    np.clip(self._agent_pos[1] + dc, 0, self.grid_size - 1),
                ],
                dtype=np.int64,
            )
            self._maybe_enter_battle()
            return 0.0
        if action == CATCH:
            tile = (int(self._agent_pos[0]), int(self._agent_pos[1]))
            if tile in self._creatures:
                self._creatures.discard(tile)
                self._caught += 1
                return 1.0  # RLVR subgoal: a creature caught.
        return 0.0

    def _maybe_enter_battle(self) -> None:
        tile = (int(self._agent_pos[0]), int(self._agent_pos[1]))
        idx = self._gym_tiles.get(tile)
        if idx is None or self._gym_defeated[idx]:
            return
        for c in self._party:  # battle starts with a fully healed party.
            c.hp = c.max_hp
        boss = gym_boss(self._gym_types[idx], idx)
        self._battle = Battle(
            BattleState(party_a=self._party, party_b=boss), chart=self._region_chart
        )
        self._battle_gym_idx = idx  # captured at entry — robust to action-space changes
        self._mode = "battle"

    # -- battle -------------------------------------------------------------

    def _step_battle(self, action: int) -> float:
        battle = self._battle
        assert battle is not None
        result = battle.step(
            self._to_battle_action(action),
            scripted_opponent(battle.state, Side.B, self._region_chart),
        )

        reward = 0.0
        if result.terminated or result.truncated:
            if result.winner is Side.A:
                self._gym_defeated[self._battle_gym_idx] = True
                reward = 1.0  # RLVR subgoal: a gym boss defeated.
                # The creature that finished the battle gains a level; reaching
                # the threshold evolves it (a second RLVR subgoal). Investing wins
                # in one creature is the long-horizon choice (DESIGN §3.4).
                winner_creature = battle.state.active(Side.A)
                winner_creature.gain_level()
                if winner_creature.can_evolve:
                    winner_creature.evolve()
                    self._evolved += 1
                    reward += 1.0
            # win or lose, leave battle; party is re-healed on the next entry.
            self._mode = "overworld"
            self._battle = None
        return reward

    def _to_battle_action(self, action: int) -> BattleAction:
        battle = self._battle
        assert battle is not None
        if action == 4:  # switch to the next alive party member
            nxt = self._next_alive_player()
            return BattleAction(ActionKind.SWITCH, nxt)
        if action == NOOP:  # a true pass: a wasted "item" turn
            return BattleAction(ActionKind.ITEM, 99)
        moves = battle.state.active(Side.A).moves
        return BattleAction(ActionKind.MOVE, min(action, len(moves) - 1))

    def _next_alive_player(self) -> int:
        battle = self._battle
        assert battle is not None
        cur = battle.state.active_a
        n = len(self._party)
        for off in range(1, n + 1):
            i = (cur + off) % n
            if not self._party[i].is_fainted:
                return i
        return cur

    # -- observation --------------------------------------------------------

    def _obs(self) -> dict[str, np.ndarray]:
        side = 2 * self.patch_radius + 1
        patch = np.zeros((side, side), dtype=np.int8)
        ar, ac = int(self._agent_pos[0]), int(self._agent_pos[1])
        for (cr, cc), val in self._patch_entities():
            pr, pc = cr - ar + self.patch_radius, cc - ac + self.patch_radius
            if 0 <= pr < side and 0 <= pc < side:
                patch[pr, pc] = val

        in_battle = self._mode == "battle"
        p_hp = p_ty = p_lvl = e_hp = e_ty = 0
        if in_battle and self._battle is not None:
            pa = self._battle.state.active(Side.A)
            ea = self._battle.state.active(Side.B)
            p_hp, p_ty, p_lvl = pa.hp, _TYPE_TO_INT[pa.types[0]], pa.level
            e_hp, e_ty = ea.hp, _TYPE_TO_INT[ea.types[0]]

        return {
            "agent_pos": self._agent_pos.copy(),
            "local_patch": patch,
            "caught": np.array([self._caught], dtype=np.int64),
            "gyms_defeated": np.array([sum(self._gym_defeated)], dtype=np.int64),
            "evolved": np.array([self._evolved], dtype=np.int64),
            "in_battle": np.array([int(in_battle)], dtype=np.int8),
            "player_hp": np.array([p_hp], dtype=np.int64),
            "player_type": np.array([p_ty], dtype=np.int64),
            "player_level": np.array([p_lvl], dtype=np.int64),
            "enemy_hp": np.array([e_hp], dtype=np.int64),
            "enemy_type": np.array([e_ty], dtype=np.int64),
        }

    def _patch_entities(self) -> list[tuple[tuple[int, int], int]]:
        out: list[tuple[tuple[int, int], int]] = [
            (pos, _PATCH_CREATURE) for pos in self._creatures
        ]
        out += [
            (pos, _PATCH_GYM)
            for pos, i in self._gym_tiles.items()
            if not self._gym_defeated[i]
        ]
        return out

    def _info(self) -> dict[str, Any]:
        return {
            "subgoals": {
                "caught": self._caught,
                "gyms_defeated": sum(self._gym_defeated),
                "evolved": self._evolved,
            },
            "mode": self._mode,
            "remaining_gyms": len(self._gym_defeated) - sum(self._gym_defeated),
        }
