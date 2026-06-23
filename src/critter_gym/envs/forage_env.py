"""ForageEnv — a structurally distinct collection-RPG family (genre-generalization).

``CritterEnv`` (family A) collects creatures by an explicit **action**: stand on a
creature tile and issue ``CATCH``. ``ForageEnv`` (family B) changes the *collection
mechanic* — creatures are collected by **contact**: stepping onto a creature tile
auto-collects it, and the ``CATCH`` action is inert. Everything else (gym battles,
evolution, the per-seed hidden chart, obs/action spaces) is inherited unchanged.

This is a **minimal but real** structural difference on the *collection* axis: the
transition function takes a different code path (move-onto-creature → collect vs
move-onto-creature → nothing-until-CATCH), so the **same seed + same action sequence
yields a different trajectory** than family A — i.e. it is not a seed variant
(genre-generalization-foundation AC2). Richer, more-distinct families (different
battle systems, progression) are the documented follow-up; one structural axis is
enough to stand up the env-family + env-level measurement machinery.
"""

from __future__ import annotations

import numpy as np

from critter_gym.envs.critter_env import _MOVE_DELTAS, CritterEnv


class ForageEnv(CritterEnv):
    """Family B: contact-collect collection mechanic (see module docstring)."""

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
            tile = (int(self._agent_pos[0]), int(self._agent_pos[1]))
            if tile in self._creatures:  # contact-collect: stepping on it catches it
                self._creatures.discard(tile)
                self._caught += 1
                return 1.0  # RLVR subgoal: a creature collected (by contact).
            self._maybe_enter_battle()
            return 0.0
        # CATCH is inert in family B — collection is by contact, not by action.
        return 0.0
