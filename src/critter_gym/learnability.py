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
from dataclasses import dataclass, field
from functools import partial

import numpy as np

from critter_gym.battle import Side
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


def _favorable_type_vs(
    env: CritterEnv, defender_types: tuple[ElementType, ...]
) -> ElementType | None:
    """A party starter type whose move is super-effective vs the defender's FULL type set.

    Uses ``multi_effectiveness`` (the product over the defender's types), so a multi-type boss
    is scored correctly. For a single-type defender this reduces to plain ``effectiveness``."""
    best, best_eff = None, env._region_chart.super_mult - 0.001
    for c in env._party:
        eff = env._region_chart.multi_effectiveness(c.types[0], defender_types)
        if eff > best_eff:
            best, best_eff = c.types[0], eff
    return best


def _favorable_type(env: CritterEnv, enemy: ElementType) -> ElementType | None:
    """A party starter type that is super-effective vs a single ``enemy`` type (observable)."""
    return _favorable_type_vs(env, (enemy,))


def _boss_types(env: CritterEnv, enemy: ElementType) -> tuple[ElementType, ...]:
    """The active boss's FULL defending types (incl. the hidden secondary) from env internals —
    the chart-knowing oracle's ground truth. Falls back to the observed primary if no battle."""
    battle = getattr(env, "_battle", None)
    if battle is not None:
        try:
            return tuple(battle.state.active(Side.B).types)
        except Exception:
            pass
    return (enemy,)


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
            # Perfect chart knowledge (upper bound): score against the boss's FULL types,
            # including a hidden secondary. infer/probe below stay on the observed primary.
            return _favorable_type_vs(env, _boss_types(env, enemy))
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
@dataclass(frozen=True)
class EpisodeOutcome:
    """One episode's outcome, with the subgoal streams **separated**.

    ``learnability-measurement`` reported a single conflated return = gym-defeats
    (+1 each) **+** evolutions (+1 each), so a policy that evolves a lot could appear
    to out-score even ``oracle`` (a noisy cross-arm comparison). Splitting the streams
    here lets the comparison use a clean **gym-clear-only** count (the actual
    inference-load-bearing subgoal), with evolution reported separately.
    """

    episode_return: float  # total reward (gym-defeats + evolutions [+ catches, if any])
    gyms_cleared: int      # bosses defeated this episode (the clean, load-bearing metric)
    evolutions: int        # creatures evolved this episode (the inflating stream)


def run_episode(
    env_factory: Callable[[], CritterEnv], policy: EnvPolicy, seed: int
) -> EpisodeOutcome:
    """One full commit-v0 episode; return the outcome with subgoal streams separated."""
    env = env_factory()
    obs, _ = env.reset(seed=int(seed))
    total, done = 0.0, False
    while not done:
        obs, reward, terminated, truncated, _ = env.step(policy(env, obs))
        total += float(reward)
        done = bool(terminated or truncated)
    # Read the separated streams from terminal env state (deterministic; no double-count).
    return EpisodeOutcome(
        episode_return=total,
        gyms_cleared=int(sum(env._gym_defeated)),
        evolutions=int(env._evolved),
    )


def _arm_means(
    env_factory: Callable[[], CritterEnv], policy_factory: Callable[[], EnvPolicy],
    seeds: Iterable[int],
) -> tuple[float, float]:
    """(combined-return mean, gym-clear-only mean) over ``seeds`` — one run per seed."""
    outs = [run_episode(env_factory, policy_factory(), s) for s in seeds]
    if not outs:
        return float("nan"), float("nan")
    return (
        float(np.mean([o.episode_return for o in outs])),
        float(np.mean([o.gyms_cleared for o in outs])),
    )


def arm_mean(env_factory: Callable[[], CritterEnv], arm: str, seeds: Iterable[int]) -> float:
    """Mean **combined** episode return of a reference ``arm`` (backward-compatible)."""
    return _arm_means(env_factory, lambda: reference_arm(arm), seeds)[0]


@dataclass(frozen=True)
class LearnabilityReport:
    """Held-in vs held-out means per arm + learned, for both the combined return and
    the clean gym-clear-only metric (``*_gyms``). The gym-clear-only means are the
    evolution-free comparison; combined is kept for backward compatibility."""

    heldin: dict[str, float]
    heldout: dict[str, float]
    heldin_gyms: dict[str, float] = field(default_factory=dict)
    heldout_gyms: dict[str, float] = field(default_factory=dict)

    def gap(self, name: str) -> float:
        return self.heldin[name] - self.heldout[name]

    def gym_gap(self, name: str) -> float:
        return self.heldin_gyms[name] - self.heldout_gyms[name]

    def to_markdown(self) -> str:
        names = list(self.heldin)
        rows = [
            "| arm | held-in (return) | held-out (return) | held-in (gym-clear) "
            "| held-out (gym-clear) | gym-clear gap |",
            "|---|---|---|---|---|---|",
        ]
        for n in names:
            gi = self.heldin_gyms.get(n, float("nan"))
            go = self.heldout_gyms.get(n, float("nan"))
            rows.append(
                f"| {n} | {self.heldin[n]:.3f} | {self.heldout[n]:.3f} | "
                f"{gi:.3f} | {go:.3f} | {go - gi:+.3f} |"
            )
        return "\n".join(rows)


def measure_learnability(
    env_factory: Callable[[], CritterEnv],
    heldin_seeds: Iterable[int],
    heldout_seeds: Iterable[int],
    learned: ObsPolicy | None = None,
) -> LearnabilityReport:
    """Evaluate the four reference arms (+ optional learned policy) held-in vs held-out,
    on both the combined return and the clean **gym-clear-only** metric.

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

    heldin: dict[str, float] = {}
    heldout: dict[str, float] = {}
    heldin_gyms: dict[str, float] = {}
    heldout_gyms: dict[str, float] = {}
    arms = ("oracle", "infer", "type_blind", "probe")
    for a in arms:
        heldin[a], heldin_gyms[a] = _arm_means(env_factory, partial(reference_arm, a), hi)
        heldout[a], heldout_gyms[a] = _arm_means(env_factory, partial(reference_arm, a), ho)
    if learned is not None:
        heldin["learned"], heldin_gyms["learned"] = _arm_means(
            env_factory, partial(as_env_policy, learned), hi
        )
        heldout["learned"], heldout_gyms["learned"] = _arm_means(
            env_factory, partial(as_env_policy, learned), ho
        )
    return LearnabilityReport(
        heldin=heldin, heldout=heldout, heldin_gyms=heldin_gyms, heldout_gyms=heldout_gyms
    )
