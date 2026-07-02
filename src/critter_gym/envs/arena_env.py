"""Battle-arena probe env — K consecutive gym battles, no overworld (eval-product).

Diagnostic mode for separating two readings of a low super-effective-move rate:
"cannot infer the hidden chart" vs "never sustains battle engagement" (dies/wanders in
the overworld before accumulating battle experience). ``ArenaEnv`` removes the second
factor structurally: ``reset`` drops the agent straight into a gym battle, and when a
bout resolves (win, loss, or battle truncation) the next one starts immediately —
``k_battles`` bouts total, then the episode terminates.

Everything battle-side is the parent's code, untouched: battle entry reuses
``CritterEnv._maybe_enter_battle`` (full-heal + commit-window rules, and any future
battle knobs, automatically), and each turn is the parent's ``_step_battle`` (same
rewards: +1 win, +1 evolution). Bosses cycle the region's gyms in order (types RECUR —
cross-battle inference stays possible), so procgen, the hidden chart, the train/test
seed split, and the matchup guarantee all carry over verbatim.

Not a training path (no JAX port — same boundary as ``llm_eval``); a probe, not a
leaderboard config.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from gymnasium import spaces

from critter_gym.envs.critter_env import CritterEnv


class ArenaEnv(CritterEnv):
    """K consecutive gym battles with the overworld structurally removed."""

    def __init__(self, *args: Any, k_battles: int = 10, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if k_battles < 1:
            raise ValueError(f"k_battles must be >= 1, got {k_battles}")
        self.k_battles = int(k_battles)
        # Wins can exceed the map's gym count (bosses cycle), so the win counter's obs
        # bound is K, not num_gyms. Same key/shape/dtype — downstream obs consumers
        # (render_obs, telemetry) read it unchanged.
        obs_space = self.observation_space
        assert isinstance(obs_space, spaces.Dict)  # parent always builds a Dict space
        obs_space.spaces["gyms_defeated"] = spaces.Box(
            0, self.k_battles, shape=(1,), dtype=np.int64
        )
        self._battles_done = 0
        self._wins = 0

    # -- gym API ------------------------------------------------------------

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        super().reset(seed=seed, options=options)
        self._battles_done = 0
        self._wins = 0
        self._enter_arena_battle()
        return self._obs(), self._info()

    def step(
        self, action: int
    ) -> tuple[dict[str, np.ndarray], float, bool, bool, dict[str, Any]]:
        if not self.action_space.contains(action):
            raise ValueError(f"invalid action: {action!r}")
        self._steps += 1
        # Always a battle turn — the parent's battle logic verbatim. When the bout
        # resolves, the parent drops back to "overworld"; the arena immediately chains
        # the next bout instead (or ends the episode after the K-th).
        reward = self._step_battle(action)
        if self._mode == "overworld":
            self._wins += int(self._gym_defeated[self._battle_gym_idx])
            self._battles_done += 1
            if self._battles_done < self.k_battles:
                self._enter_arena_battle()
        terminated = self._battles_done >= self.k_battles
        truncated = self._steps >= self.max_steps
        return self._obs(), reward, terminated, truncated, self._info()

    # -- internals ----------------------------------------------------------

    def _enter_arena_battle(self) -> None:
        """Start the next bout via the parent's own gym-entry path.

        The boss is the region gym at ``battles_done % n_gyms``; its win flag is
        re-armed so the parent's win handling marks THIS bout. The agent is parked on
        that gym's tile and ``_maybe_enter_battle`` does the rest (full-heal, boss
        build with all difficulty knobs, commit window) — one battle-entry rulebook,
        inherited not copied.
        """
        idx = self._battles_done % len(self._gym_types)
        self._gym_defeated[idx] = False
        tile = next(pos for pos, i in self._gym_tiles.items() if i == idx)
        self._agent_pos = np.array(tile, dtype=np.int64)
        self._maybe_enter_battle()
        assert self._mode == "battle"  # the tile is a live gym by construction

    # -- observation / info ---------------------------------------------------

    def _obs(self) -> dict[str, np.ndarray]:
        obs = super()._obs()
        # The parent's counter is per-gym flags (re-armed each bout); the arena's
        # verifiable subgoal is cumulative bout WINS.
        obs["gyms_defeated"] = np.array([self._wins], dtype=np.int64)
        return obs

    def _info(self) -> dict[str, Any]:
        info = super()._info()
        info["subgoals"]["gyms_defeated"] = self._wins
        info["arena"] = {"battles_done": self._battles_done, "k_battles": self.k_battles}
        return info
