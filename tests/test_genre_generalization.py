"""AC3 — environment-level (genre) generalization measurement API.

Verifies the env-level measurement runs train-family → unseen-family for a
family-agnostic policy and reports a gap. numpy-only; the gap is a *signal*, never a
pass threshold (two families is a foundation, not a genre-generalization proof).
"""

from __future__ import annotations

import numpy as np

from critter_gym.baselines import random_policy
from critter_gym.genre_generalization import (
    GenreGapReport,
    measure_genre_generalization,
)
from critter_gym.region import heldout_seeds
from critter_gym.registration import register_envs

register_envs()


def _random(rng):
    return lambda obs: random_policy(obs, rng)


def test_measure_genre_generalization_runs_train_to_unseen_family() -> None:
    rng = np.random.default_rng(0)
    report = measure_genre_generalization(
        _random(rng), train_family="critter", test_family="forage",
        seeds=heldout_seeds(8),
    )
    assert isinstance(report, GenreGapReport)
    assert report.train_family == "critter" and report.test_family == "forage"
    assert np.isfinite(report.train_mean) and np.isfinite(report.test_mean)
    assert np.isfinite(report.gap)


def test_report_markdown_renders_both_families_and_gap() -> None:
    rng = np.random.default_rng(1)
    md = measure_genre_generalization(
        _random(rng), "critter", "forage", heldout_seeds(4)
    ).to_markdown()
    assert "critter" in md and "forage" in md and "env-level gap" in md


def test_gap_is_signed_difference() -> None:
    r = GenreGapReport("a", "b", train_mean=3.0, test_mean=1.0)
    assert r.gap == 2.0
