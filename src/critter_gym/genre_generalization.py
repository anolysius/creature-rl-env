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
from critter_gym.envs.critter_env import CritterEnv
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
