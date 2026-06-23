"""Does a policy *learn* to infer the hidden chart? — env-level measurement.

``reasoning-load-bearing`` proved, with scripted arms driving the battle engine
directly, that team-commit makes inference load-bearing (``infer`` beats ``probe``).
This module lifts that comparison to the **full env** (overworld navigation + the
champion-select action UX on ``CritterGym-commit-v0``) so a *learned* policy can be
measured on the same footing as the reference arms.

Two policy shapes:

- ``EnvPolicy = (env, obs) -> action`` — the reference arms. They need gym positions
  (for navigation; not in the obs) and, for ``oracle``/``infer``, the per-seed chart.
  These are *reference baselines*, so peeking the env internals is intentional.
- A *learned* policy sees only the obs (``obs -> action``); wrap it with
  :func:`as_env_policy` to evaluate it through the same runner. It gets no chart and
  no gym map — it must navigate and infer from experience, which is the whole point.

Everything here is numpy-only; PPO training lives in ``scripts/learnability.py``
behind the ``[rl]`` extra.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.region import is_held_out
from critter_gym.types import ElementType

Obs = dict[str, np.ndarray]
EnvPolicy = Callable[[CritterEnv, Obs], int]
ObsPolicy = Callable[[Obs], int]

_TYPES = list(ElementType)
_ATTACK, _SWITCH, _NOOP = 0, 4, 5


# -- navigation (shared by every reference arm) -------------------------------
def _nav_to_nearest_gym(env: CritterEnv) -> int:
    """A MOVE action toward the nearest undefeated gym (deterministic)."""
    ar, ac = int(env._agent_pos[0]), int(env._agent_pos[1])
    undefeated = [p for p, i in env._gym_tiles.items() if not env._gym_defeated[i]]
    if not undefeated:
        return _NOOP
    tr, tc = min(undefeated, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    if tr < ar:
        return 0  # MOVE_N
    if tr > ar:
        return 1  # MOVE_S
    if tc > ac:
        return 2  # MOVE_E
    return 3      # MOVE_W


def _favorable_type(env: CritterEnv, enemy: ElementType) -> ElementType | None:
    """A party starter type that is super-effective vs ``enemy`` under the chart."""
    best, best_eff = None, env._region_chart.super_mult - 0.001
    for c in env._party:
        eff = env._region_chart.effectiveness(c.types[0], enemy)
        if eff > best_eff:
            best, best_eff = c.types[0], eff
    return best


# -- reference arms -----------------------------------------------------------
@dataclass
class _Arm:
    """A stateful env-level reference policy (one per episode is fine — it tracks
    cross-gym memory, the substrate the ``infer`` arm exploits)."""

    arm: str
    _memory: dict[ElementType, ElementType] | None = None

    def __call__(self, env: CritterEnv, obs: Obs) -> int:
        if not obs["in_battle"][0]:
            return _nav_to_nearest_gym(env)
        cur = _TYPES[int(obs["player_type"][0])]
        enemy = _TYPES[int(obs["enemy_type"][0])]
        target = self._target_type(env, enemy)
        if target is None or cur == target:
            return _ATTACK            # commit the current champion (locks on first move)
        return _SWITCH                # free cycle while the commit window is open

    def _target_type(self, env: CritterEnv, enemy: ElementType) -> ElementType | None:
        if self.arm == "type_blind":
            return None                          # never switch — fight with creature 0
        if self.arm == "oracle":
            return _favorable_type(env, enemy)   # perfect chart knowledge (upper bound)
        if self.arm == "infer":
            if self._memory is None:
                self._memory = {}
            if enemy in self._memory:            # reuse a matchup learned this episode
                return self._memory[enemy]
            fav = _favorable_type(env, enemy)    # first sight: learn it for next recurrence
            if fav is not None:
                self._memory[enemy] = fav
            return None                          # first encounter: no commit yet (guess)
        # probe: cannot probe under commit (cycling reveals nothing) and keeps no
        # memory → a deterministic guess from the enemy's type id, unrelated to the
        # actual matchup. Approximates "pick a champion blindly each fight".
        idx = _TYPES.index(enemy) % len(env._party)
        return env._party[idx].types[0]


def reference_arm(arm: str) -> EnvPolicy:
    """A fresh stateful reference policy for ``arm`` ∈ {oracle, infer, type_blind, probe}."""
    if arm not in ("oracle", "infer", "type_blind", "probe"):
        raise ValueError(f"unknown arm: {arm}")
    return _Arm(arm)


def as_env_policy(policy: ObsPolicy) -> EnvPolicy:
    """Adapt an obs-only (learned) policy to the (env, obs) runner — it ignores env."""
    return lambda _env, obs: policy(obs)


# -- evaluation ---------------------------------------------------------------
def run_episode(env_factory: Callable[[], CritterEnv], policy: EnvPolicy, seed: int) -> float:
    """One full commit-v0 episode; return total reward (gyms defeated + evolutions)."""
    env = env_factory()
    obs, _ = env.reset(seed=int(seed))
    total, done = 0.0, False
    while not done:
        obs, reward, terminated, truncated, _ = env.step(policy(env, obs))
        total += float(reward)
        done = bool(terminated or truncated)
    return total


def arm_mean(env_factory: Callable[[], CritterEnv], arm: str, seeds: Iterable[int]) -> float:
    """Mean episode return of a reference ``arm`` over ``seeds`` (fresh state per ep)."""
    return float(np.mean([run_episode(env_factory, reference_arm(arm), s) for s in seeds]))


@dataclass(frozen=True)
class LearnabilityReport:
    """Held-in vs held-out means for each reference arm + a learned policy."""

    heldin: dict[str, float]
    heldout: dict[str, float]

    def gap(self, name: str) -> float:
        return self.heldin[name] - self.heldout[name]

    def to_markdown(self) -> str:
        names = list(self.heldin)
        rows = ["| arm | held-in | held-out | gap |", "|---|---|---|---|"]
        for n in names:
            rows.append(
                f"| {n} | {self.heldin[n]:.3f} | {self.heldout[n]:.3f} | {self.gap(n):+.3f} |"
            )
        return "\n".join(rows)


def measure_learnability(
    env_factory: Callable[[], CritterEnv],
    heldin_seeds: Iterable[int],
    heldout_seeds: Iterable[int],
    learned: ObsPolicy | None = None,
) -> LearnabilityReport:
    """Evaluate the four reference arms (+ optional learned policy) held-in vs held-out.

    Enforces the region split (held-in < TEST_SEED_OFFSET ≤ held-out) so a leaked
    seed can't flatter the gap — same guard as :mod:`critter_gym.generalization`.
    """
    hi = tuple(int(s) for s in heldin_seeds)
    ho = tuple(int(s) for s in heldout_seeds)
    leaked = [s for s in hi if is_held_out(s)]
    mislabeled = [s for s in ho if not is_held_out(s)]
    if leaked:
        raise ValueError(f"held-in seeds must be training-region; got held-out {leaked[:5]}")
    if mislabeled:
        raise ValueError(f"held-out seeds must be held-out; got training-region {mislabeled[:5]}")

    arms = ("oracle", "infer", "type_blind", "probe")
    heldin = {a: arm_mean(env_factory, a, hi) for a in arms}
    heldout = {a: arm_mean(env_factory, a, ho) for a in arms}
    if learned is not None:
        pol = as_env_policy(learned)
        heldin["learned"] = float(np.mean([run_episode(env_factory, pol, s) for s in hi]))
        heldout["learned"] = float(np.mean([run_episode(env_factory, pol, s) for s in ho]))
    return LearnabilityReport(heldin=heldin, heldout=heldout)
