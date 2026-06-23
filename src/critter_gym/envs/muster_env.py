"""MusterEnv — family D: collection-gated power (a *progression* axis).

Families A/B/C vary the collection mechanic (A action-collect, B contact-collect) and
the battle system (C type-agnostic duel). Family D varies the **progression** axis: a
caught creature **buffs the whole party's attack**, and bosses are strong enough that a
starter party cannot dent them — so you must **muster a collection before you can win**.
Collection and battle become a dependency chain; the load-bearing skill is "collect
first, then fight", which is *useless* in family A (where catching confers no buff).

Like family B, this is a single-method override of ``CritterEnv`` (the CATCH path), so
family A/B/C are untouched and the same seed + actions yields a different battle
trajectory (a buffed party deals different damage) — not reducible to a seed variant.

The buff is applied to the live party creatures, so it flows into ``Battle`` damage with
no battle-engine change. The contract (``Discrete(6)`` + ``REQUIRED_OBS_KEYS``) is
unchanged; ``caught`` is already in the obs, so a policy can decide "collect vs fight"
from observation alone (no privileged access).

Honest scope: family D is the **fourth** family — a *progression* axis distinct from the
collection (B) and battle-system (C) axes. Four families still is **not** a genre proof;
the env-level gap is a *signal*. Family D uses stronger bosses (the calibration that makes
mustering load-bearing — part of its identity), so the raw cross-family mean gap is
difficulty-confounded; the honest signal is the *policy-specific* contrast (a muster
policy beats a rush policy on D, while the muster skill is useless on A).
"""

from __future__ import annotations

from critter_gym.envs.critter_env import CATCH, CritterEnv

MUSTER_ATK = 12  # attack added to every party creature per creature caught


class MusterEnv(CritterEnv):
    """Family D: catching a creature buffs party attack (collection-gated power)."""

    def _step_overworld(self, action: int) -> float:
        if action == CATCH:
            tile = (int(self._agent_pos[0]), int(self._agent_pos[1]))
            if tile in self._creatures:
                self._creatures.discard(tile)
                self._caught += 1
                for c in self._party:  # muster: each catch strengthens the party
                    c.attack += MUSTER_ATK
                return 1.0  # RLVR subgoal: a creature caught (and the party mustered).
            return 0.0
        # movement / non-catch actions behave exactly as family A.
        return super()._step_overworld(action)
