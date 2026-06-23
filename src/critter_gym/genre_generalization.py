"""Environment-level (genre) generalization measurement — DESIGN §3.1.1 (B).

:mod:`critter_gym.generalization` measures *instance*-level transfer (held-out seeds
of one generator). This module measures *environment*-level transfer: how a single
(family-agnostic) policy fares on a **train family** vs an **unseen family** of the
collection-RPG genre. The gap between them is the genre-generalization signal.

Honest scope (genre-generalization-foundation): with only **two** families this is a
*foundation* — the machinery to measure env-level transfer, demonstrated end-to-end —
**not** a proof of genre generalization (that needs many structurally-distinct
families; see the task report and DESIGN §3.1.1). The gap is *reported as a signal*,
never frozen as a pass threshold. numpy-only; reuses :func:`generalization.evaluate`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

import numpy as np

from critter_gym.env_family import make_family
from critter_gym.envs.critter_env import (
    CATCH,
    MOVE_E,
    MOVE_N,
    MOVE_S,
    MOVE_W,
    NOOP,
    CritterEnv,
)
from critter_gym.envs.duel_env import ATTACK, CHARGE, GUARD, MAX_CHARGE
from critter_gym.generalization import evaluate

Obs = dict[str, np.ndarray]
PolicyFn = Callable[[Obs], int]


@dataclass(frozen=True)
class GenreGapReport:
    """A policy's mean return on its train family vs an unseen family."""

    train_family: str
    test_family: str
    train_mean: float
    test_mean: float

    @property
    def gap(self) -> float:
        """Env-level generalization gap (train − unseen family). Reported, not thresholded."""
        return self.train_mean - self.test_mean

    def to_markdown(self) -> str:
        return (
            f"| family | mean | role |\n|---|---|---|\n"
            f"| {self.train_family} | {self.train_mean:.3f} | train |\n"
            f"| {self.test_family} | {self.test_mean:.3f} | unseen |\n"
            f"\nenv-level gap (train − unseen) = {self.gap:+.3f}"
        )


def _family_factory(name: str, **kwargs: object) -> Callable[[], CritterEnv]:
    # make_family returns a CollectionRPGEnv (CritterEnv or a subclass); evaluate()
    # only needs the Gymnasium step/reset contract, which every family satisfies.
    return lambda: make_family(name, **kwargs)  # type: ignore[return-value]


def measure_genre_generalization(
    policy: PolicyFn,
    train_family: str,
    test_family: str,
    seeds: Iterable[int],
) -> GenreGapReport:
    """Evaluate ``policy`` on ``train_family`` vs the unseen ``test_family``.

    Same seeds on both families so the comparison isolates the *environment* (the
    structural mechanic), not the world layout. The env-level transfer gap is the
    genre-generalization signal.
    """
    seeds_t = tuple(int(s) for s in seeds)
    train = evaluate(_family_factory(train_family), policy, seeds_t)
    test = evaluate(_family_factory(test_family), policy, seeds_t)
    return GenreGapReport(
        train_family=train_family,
        test_family=test_family,
        train_mean=train.mean,
        test_mean=test.mean,
    )


@dataclass(frozen=True)
class LeaveOneOutGap:
    """One leave-one-out fold: a policy's mean on the train families vs the held-out one.

    With N families, each fold holds one family out and trains on the other N−1. The
    gap (train − held-out) is the env-level transfer signal for that unseen family.
    """

    held_out: str
    train_families: tuple[str, ...]
    train_mean: float
    heldout_mean: float

    @property
    def gap(self) -> float:
        """Env-level generalization gap (train families − held-out). Reported, not thresholded."""
        return self.train_mean - self.heldout_mean


def measure_genre_generalization_loo(
    policy: PolicyFn,
    families: list[str],
    seeds: Iterable[int],
) -> list[LeaveOneOutGap]:
    """Leave-one-out env-level measurement over ``families`` for one policy.

    For each family it is held out as the unseen environment while the rest form the
    train set; the per-fold gap is the genre-generalization signal for that family.
    Same seeds on every family so each fold isolates the *mechanic*, not the layout.

    Honest scope: leave-one-out over a *handful* of families is still a foundation —
    the gap is a signal, never a pass threshold, and three families is not a proof.
    """
    seeds_t = tuple(int(s) for s in seeds)
    per_family = {f: evaluate(_family_factory(f), policy, seeds_t).mean for f in families}
    folds: list[LeaveOneOutGap] = []
    for held in families:
        train = tuple(f for f in families if f != held)
        train_mean = float(np.mean([per_family[f] for f in train])) if train else float("nan")
        folds.append(LeaveOneOutGap(held, train, train_mean, per_family[held]))
    return folds


# -- reference scripted policies for the env-level skill-structural contrast ----
# These are obs-only, family-agnostic instruments (not learned baselines): they let
# the measurement show that family C's env-level gap is *skill-structural* (a
# C-appropriate policy transfers, an A-tuned one does not) rather than mere difficulty.


def nav_toward_gyms(obs: Obs) -> int:
    """Head to the nearest visible gym (else creature, else sweep) to trigger battles.

    Shared overworld navigation so the reference policies differ *only* in battle —
    isolating the battle skill, which is the genre axis under test.
    """
    patch = obs["local_patch"]
    center = patch.shape[0] // 2
    targets = np.argwhere(patch == 2)
    if targets.size == 0:
        targets = np.argwhere(patch == 1)
    if targets.size > 0:
        rel = targets - center
        nearest = rel[np.argmin(np.abs(rel).sum(axis=1))]
        dr, dc = int(nearest[0]), int(nearest[1])
        if dr == 0 and dc == 0:
            return int(CATCH)
        if abs(dr) >= abs(dc):
            return int(MOVE_S if dr > 0 else MOVE_N)
        return int(MOVE_E if dc > 0 else MOVE_W)
    r, c = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    if r % 2 == 0:
        return int(MOVE_E if c < 9 else MOVE_S)
    return int(MOVE_W if c > 0 else MOVE_S)


def type_attacker_policy(obs: Obs) -> int:
    """A-tuned reference: in battle, always attack (action 0 = best move in family A,
    = ATTACK in family C). Optimal-ish on family A; on family C it ignores the duel
    resource game and is punished — the skill does not transfer."""
    if int(obs["in_battle"][0]) == 1:
        return int(ATTACK)
    return nav_toward_gyms(obs)


_ZERO = np.zeros(1, dtype=np.int64)


def duel_aware_policy(obs: Obs) -> int:
    """C-appropriate reference: play the duel RPS from observed charge (GUARD the
    incoming attack, build charge, then punish). Reads the duel charge obs keys when
    present and falls back to 0 on families that lack them, so it is family-agnostic."""
    if int(obs["in_battle"][0]) == 1:
        echarge = int(obs.get("enemy_charge", _ZERO)[0])
        pcharge = int(obs.get("player_charge", _ZERO)[0])
        if echarge >= 1:
            return int(GUARD)  # negate the telegraphed attack
        if pcharge < MAX_CHARGE:
            return int(CHARGE)  # safe to build charge
        return int(ATTACK)  # unleash the charged hit
    return nav_toward_gyms(obs)


def _nav_gyms_only(obs: Obs) -> int:
    """Navigate to the nearest gym, else sweep — but NEVER catch (a pure 'rush' nav)."""
    patch = obs["local_patch"]
    center = patch.shape[0] // 2
    gyms = np.argwhere(patch == 2)
    if gyms.size > 0:
        rel = gyms - center
        nearest = rel[np.argmin(np.abs(rel).sum(axis=1))]
        dr, dc = int(nearest[0]), int(nearest[1])
        if dr == 0 and dc == 0:
            return int(NOOP)  # standing on the gym (battle entry handled on the move)
        if abs(dr) >= abs(dc):
            return int(MOVE_S if dr > 0 else MOVE_N)
        return int(MOVE_E if dc > 0 else MOVE_W)
    r, c = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    if r % 2 == 0:
        return int(MOVE_E if c < 9 else MOVE_S)
    return int(MOVE_W if c > 0 else MOVE_S)


def _nav_to_creature(obs: Obs) -> int:
    """Head to the nearest visible creature and CATCH it; else fall back to gyms."""
    patch = obs["local_patch"]
    center = patch.shape[0] // 2
    cre = np.argwhere(patch == 1)
    if cre.size > 0:
        rel = cre - center
        nearest = rel[np.argmin(np.abs(rel).sum(axis=1))]
        dr, dc = int(nearest[0]), int(nearest[1])
        if dr == 0 and dc == 0:
            return int(CATCH)
        if abs(dr) >= abs(dc):
            return int(MOVE_S if dr > 0 else MOVE_N)
        return int(MOVE_E if dc > 0 else MOVE_W)
    return _nav_gyms_only(obs)


def rush_policy(obs: Obs) -> int:
    """Fight-now reference: go straight to gyms and attack, NEVER collecting. On family D
    (collection-gated power + strong bosses) this floors — the party is never mustered."""
    if int(obs["in_battle"][0]) == 1:
        return int(ATTACK)
    return _nav_gyms_only(obs)


def muster_policy(obs: Obs) -> int:
    """D-appropriate reference: muster a collection first (catch until ``caught >= 4``),
    then fight. On family D the buff makes strong bosses winnable; on family A catching
    confers no buff, so this is no better than ``rush_policy`` — the contrast that shows
    family D's gap is skill-structural (a wrong/absent skill), not raw difficulty."""
    if int(obs["in_battle"][0]) == 1:
        return int(ATTACK)
    if int(obs["caught"][0]) < 4:
        return _nav_to_creature(obs)
    return _nav_gyms_only(obs)
