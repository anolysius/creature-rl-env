"""Minimal catch-only CritterGym environment (Phase 1 scaffolding).

A 10x10 grid world with seeded creature placement. The agent moves on the grid
and catches creatures. Reward is RLVR-style: a verifiable boolean subgoal
(`caught` increments) yields +1; nothing else is rewarded (no dense shaping).

This is the deliberately "dumbest-possible playable env" of DESIGN.md Phase 1 —
the stable skeleton that later tasks (subgoal chain, procgen type meta, battle)
build on. Observations are structured/symbolic (DESIGN.md §3.2), not pixels.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from gymnasium import Env, spaces

# Action indices (a minimal subset of DESIGN.md §3.3).
MOVE_N, MOVE_S, MOVE_E, MOVE_W, CATCH, NOOP = range(6)

# (row, col) deltas for the four move actions.
_MOVE_DELTAS: dict[int, tuple[int, int]] = {
    MOVE_N: (-1, 0),
    MOVE_S: (1, 0),
    MOVE_E: (0, 1),
    MOVE_W: (0, -1),
}


class CritterEnv(Env[dict[str, np.ndarray], int]):
    """Catch-only grid environment with verifiable subgoal rewards.

    Parameters
    ----------
    grid_size:
        Side length of the square grid.
    num_creatures:
        How many creatures are spawned per episode (seeded placement).
    target_catches:
        Episode terminates once this many distinct creatures are caught.
    max_steps:
        Step budget; exceeding it truncates the episode.
    patch_radius:
        Radius of the square local observation patch centered on the agent.
    """

    metadata: dict[str, Any] = {"render_modes": []}

    def __init__(
        self,
        grid_size: int = 10,
        num_creatures: int = 5,
        target_catches: int = 3,
        max_steps: int = 100,
        patch_radius: int = 2,
    ) -> None:
        super().__init__()
        if target_catches > num_creatures:
            raise ValueError("target_catches cannot exceed num_creatures")
        # Need at least one free tile for the agent's start, else reset() would
        # loop forever searching for a non-creature tile.
        if num_creatures >= grid_size * grid_size:
            raise ValueError("num_creatures must be < grid_size * grid_size")
        self.grid_size = grid_size
        self.num_creatures = num_creatures
        self.target_catches = target_catches
        self.max_steps = max_steps
        self.patch_radius = patch_radius

        patch_side = 2 * patch_radius + 1
        # gymnasium's Discrete is typed Space[np.int64]; ActType here is int, and
        # Space is invariant, so mypy flags the assignment. Both are int at runtime.
        self.action_space = spaces.Discrete(6)  # type: ignore[assignment]
        self.observation_space = spaces.Dict(
            {
                "agent_pos": spaces.Box(
                    low=0, high=grid_size - 1, shape=(2,), dtype=np.int64
                ),
                "local_patch": spaces.Box(
                    low=0, high=1, shape=(patch_side, patch_side), dtype=np.int8
                ),
                "caught": spaces.Box(
                    low=0, high=target_catches, shape=(1,), dtype=np.int64
                ),
            }
        )

        # Episode state (populated by reset).
        self._agent_pos: np.ndarray = np.zeros(2, dtype=np.int64)
        self._creatures: set[tuple[int, int]] = set()
        self._caught: int = 0
        self._steps: int = 0

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        super().reset(seed=seed)
        # Seeded, reproducible region: same seed -> identical placement.
        cells = self.grid_size * self.grid_size
        chosen = self.np_random.choice(cells, size=self.num_creatures, replace=False)
        self._creatures = {
            (int(c // self.grid_size), int(c % self.grid_size)) for c in chosen
        }
        # Agent starts on a non-creature tile, also seeded.
        while True:
            start = self.np_random.integers(0, self.grid_size, size=2)
            if (int(start[0]), int(start[1])) not in self._creatures:
                break
        self._agent_pos = start.astype(np.int64)
        self._caught = 0
        self._steps = 0
        return self._obs(), self._info()

    def step(
        self, action: int
    ) -> tuple[dict[str, np.ndarray], float, bool, bool, dict[str, Any]]:
        if not self.action_space.contains(action):
            raise ValueError(f"invalid action: {action!r}")
        self._steps += 1
        reward = 0.0

        if action in _MOVE_DELTAS:
            dr, dc = _MOVE_DELTAS[action]
            self._agent_pos = np.array(
                [
                    np.clip(self._agent_pos[0] + dr, 0, self.grid_size - 1),
                    np.clip(self._agent_pos[1] + dc, 0, self.grid_size - 1),
                ],
                dtype=np.int64,
            )
        elif action == CATCH:
            tile = (int(self._agent_pos[0]), int(self._agent_pos[1]))
            if tile in self._creatures:
                self._creatures.discard(tile)
                self._caught += 1
                reward = 1.0  # RLVR: boolean subgoal completion, not shaping.

        terminated = self._caught >= self.target_catches
        truncated = self._steps >= self.max_steps
        return self._obs(), reward, terminated, truncated, self._info()

    def _obs(self) -> dict[str, np.ndarray]:
        side = 2 * self.patch_radius + 1
        patch = np.zeros((side, side), dtype=np.int8)
        ar, ac = int(self._agent_pos[0]), int(self._agent_pos[1])
        for cr, cc in self._creatures:
            pr, pc = cr - ar + self.patch_radius, cc - ac + self.patch_radius
            if 0 <= pr < side and 0 <= pc < side:
                patch[pr, pc] = 1
        return {
            "agent_pos": self._agent_pos.copy(),
            "local_patch": patch,
            "caught": np.array([self._caught], dtype=np.int64),
        }

    def _info(self) -> dict[str, Any]:
        return {
            "subgoals": {"caught": self._caught},
            "remaining": len(self._creatures),
        }
