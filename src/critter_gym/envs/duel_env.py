"""DuelEnv — family C: a structurally distinct **battle system** (genre-generalization).

Family A (``CritterEnv``) and family B (``ForageEnv``) share one battle system:
turn-based, type-matchup damage, switching. Their only structural difference is the
*collection* mechanic, so an A-tuned policy transfers to B with gap≈0 — a forgiving
axis (the prior session's recorded weakness). Family C changes the **battle system
itself** to a stronger structural axis:

- **No type chart.** Battle damage is type-AGNOSTIC (stat-based), so inferring the
  hidden per-seed chart — family A's load-bearing skill — is *useless* here.
- **A stamina/commit duel** instead of move-selection + switching. Each battle turn is
  a rock-paper-scissors resource game:
    - ``ATTACK`` deals ``attack × (1 + charge)`` damage (then resets charge), but is
      **negated if the opponent GUARDs**;
    - ``CHARGE`` builds charge (a bigger next hit) but leaves you open to an ATTACK;
    - ``GUARD`` negates an incoming ATTACK but deals nothing.
  So ATTACK beats CHARGE, GUARD beats ATTACK, CHARGE beats GUARD — a prediction/timing
  skill orthogonal to type inference.

The boss plays a fixed, deterministic pattern (charge, then unleash) so the duel stays
fully deterministic (RLVR / reproducibility) and a C-appropriate policy can exploit it.

The shared obs/action contract (:func:`critter_gym.env_family.conforms`) is preserved:
``Discrete(6)`` reinterpreted in battle (0=ATTACK, 1=CHARGE, 2=GUARD), and the obs keeps
every ``REQUIRED_OBS_KEYS`` entry. The duel charge state is exposed as **extra** obs keys
(``player_charge`` / ``enemy_charge``) — ``conforms`` permits keys *beyond* the required
set, so the family is winnable from observation alone (no privileged access), while a
family-agnostic policy can ignore the extra keys.

Honest scope: this is the **third** family — a *stronger* structural axis than family B,
strengthening the genre-generalization *foundation* (DESIGN §3.1.1 (B)). Three families
is still not a genre-generalization *proof* (that needs many structurally-distinct
families); the measured env-level gap is reported as a *signal*.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from gymnasium import spaces

from critter_gym.battle import Battle, BattleState, Side
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.party import gym_boss

# Duel battle actions — the Discrete(6) reinterpretation inside a DuelEnv battle.
ATTACK, CHARGE, GUARD = 0, 1, 2
MAX_CHARGE = 2
_DUEL_TURN_CAP = 40  # a stalled duel (mutual guard/charge) ends as a loss


class DuelEnv(CritterEnv):
    """Family C: type-agnostic stamina/commit duel battle (see module docstring)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Extend the obs with the duel charge state. conforms() requires obs keys
        # ⊇ REQUIRED_OBS_KEYS, so adding keys keeps family C on the shared contract
        # while making the duel playable from observation (not privileged access).
        assert isinstance(self.observation_space, spaces.Dict)
        extended = dict(self.observation_space.spaces)
        extended["player_charge"] = spaces.Box(0, MAX_CHARGE, shape=(1,), dtype=np.int64)
        extended["enemy_charge"] = spaces.Box(0, MAX_CHARGE, shape=(1,), dtype=np.int64)
        self.observation_space = spaces.Dict(extended)
        self._pcharge = 0
        self._echarge = 0
        self._duel_turns = 0

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
        self._pcharge = 0
        self._echarge = 0
        self._duel_turns = 0
        return super().reset(seed=seed, options=options)

    def _obs(self) -> dict[str, np.ndarray]:
        obs = super()._obs()
        obs["player_charge"] = np.array([self._pcharge], dtype=np.int64)
        obs["enemy_charge"] = np.array([self._echarge], dtype=np.int64)
        return obs

    def _maybe_enter_battle(self) -> None:
        tile = (int(self._agent_pos[0]), int(self._agent_pos[1]))
        idx = self._gym_tiles.get(tile)
        if idx is None or self._gym_defeated[idx]:
            return
        for c in self._party:  # battle starts with a fully healed party.
            c.hp = c.max_hp
        boss = gym_boss(
            self._gym_types[idx], idx, hp=self.boss_hp, atk=self.boss_atk, df=self.boss_def
        )
        # A BattleState holds the active creatures (hp/attack); the duel resolves its
        # own dynamics in _step_battle and never calls Battle.step (type chart unused).
        self._battle = Battle(BattleState(party_a=self._party, party_b=boss))
        self._battle_gym_idx = idx
        self._mode = "battle"
        self._pcharge = 0
        self._echarge = 0
        self._duel_turns = 0

    def _enemy_duel_action(self) -> int:
        # Deterministic boss: build charge, then unleash it. Predictable on purpose
        # (RLVR) so a C-appropriate policy can punish the charge / guard the attack.
        return ATTACK if self._echarge >= 1 else CHARGE

    def _step_battle(self, action: int) -> float:
        battle = self._battle
        assert battle is not None
        player = battle.state.active(Side.A)
        boss = battle.state.active(Side.B)
        p_act = action if action in (ATTACK, CHARGE, GUARD) else GUARD
        e_act = self._enemy_duel_action()

        p_dmg = e_dmg = 0
        if p_act == ATTACK:
            p_dmg = 0 if e_act == GUARD else int(player.attack * (1 + self._pcharge))
            self._pcharge = 0
        elif p_act == CHARGE:
            self._pcharge = min(MAX_CHARGE, self._pcharge + 1)
        if e_act == ATTACK:
            e_dmg = 0 if p_act == GUARD else int(boss.attack * (1 + self._echarge))
            self._echarge = 0
        elif e_act == CHARGE:
            self._echarge = min(MAX_CHARGE, self._echarge + 1)
        boss.take_damage(p_dmg)
        player.take_damage(e_dmg)
        self._duel_turns += 1

        reward = 0.0
        done = boss.is_fainted or player.is_fainted or self._duel_turns >= _DUEL_TURN_CAP
        if done:
            if boss.is_fainted and not player.is_fainted:
                self._gym_defeated[self._battle_gym_idx] = True
                reward = 1.0  # RLVR subgoal: a gym boss defeated.
                winner = battle.state.active(Side.A)
                winner.gain_level()
                if winner.can_evolve:
                    winner.evolve()
                    self._evolved += 1
                    reward += 1.0  # RLVR subgoal: a creature evolved.
            self._mode = "overworld"
            self._battle = None
            self._pcharge = 0
            self._echarge = 0
        return reward
