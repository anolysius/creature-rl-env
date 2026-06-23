"""Smoke test for the difficulty gap-at-difficulty experiment (difficulty-generalization).

The real measurement — does a *learned* policy's held-in/held-out generalization gap stay
≈0 as difficulty intensity rises? — is heavy ([rl], PPO) and machine-dependent, so it lives
in ``scripts/difficulty_generalization.py`` and is exercised here only at a tiny budget,
gated by ``importorskip``. The script reuses ``critter_gym.generalization`` (so the held-in/
held-out region split + leak guard are inherited). numpy-only CI stays green without [rl].
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from critter_gym.generalization import GapReport


def test_difficulty_configs_are_points_not_a_claimed_ladder() -> None:
    # The configs are honest "difficulty points" (the pilot falsified a clean monotonic
    # ladder). We only assert there are >=3 of them and each is a dict of env kwargs.
    pytest.importorskip("stable_baselines3")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import difficulty_generalization as script  # scripts/difficulty_generalization.py

    assert len(script.CONFIGS) >= 3
    for cfg in script.CONFIGS.values():
        assert isinstance(cfg, dict) and "num_types" in cfg


def test_train_and_gap_smoke_produces_finite_gapreport() -> None:
    # AC2: the [rl] script runs end-to-end at a tiny budget and yields a GapReport whose
    # held-in/held-out means are finite — and inherits the region-split leak guard.
    pytest.importorskip("stable_baselines3")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import difficulty_generalization as script

    first = next(iter(script.CONFIGS.values()))
    report = script.train_and_gap(first, timesteps=256, n_heldin=2, n_heldout=2)
    assert isinstance(report, GapReport)
    d = report.to_dict()
    import math

    assert math.isfinite(d["heldin_mean"]) and math.isfinite(d["heldout_mean"])
    assert math.isfinite(d["gap"])
