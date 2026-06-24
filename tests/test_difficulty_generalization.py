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


def _script():
    # importing the script needs only core deps (gymnasium + critter_gym); sb3 is imported
    # lazily inside train_and_gap, so classify_gap is testable on the numpy-only CI path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import difficulty_generalization as script

    return script


def test_classify_gap_pre_registered_rule() -> None:
    """difficulty-gap-rigor: the frozen decision rule (floor=0.3, k=1.0) on each branch.

    gap_std here is std-ACROSS-runs (the rigor quantity), not a per-seed std.
    """
    s = _script()
    assert s.GAP_FLOOR == 0.3 and s.GAP_K == 1.0  # thresholds frozen pre-data
    # held-in below floor → inconclusive regardless of the gap.
    assert s.classify_gap(gap_mean=0.0, gap_std=0.1, heldin_mean=0.2) == "inconclusive"
    # robustly positive gap (gap > k·std) with a capable policy → real-gap.
    assert s.classify_gap(gap_mean=0.8, gap_std=0.2, heldin_mean=1.5) == "real-gap"
    # |gap| within k·std → gap≈0-signal (run noise swamps the gap).
    assert s.classify_gap(gap_mean=0.3, gap_std=0.5, heldin_mean=1.5) == "gap≈0-signal"
    assert s.classify_gap(gap_mean=-0.2, gap_std=0.5, heldin_mean=1.5) == "gap≈0-signal"
    # robustly negative gap (held-out easier) → inconclusive (difficulty asymmetry).
    assert s.classify_gap(gap_mean=-0.8, gap_std=0.2, heldin_mean=1.5) == "inconclusive"
    # boundary: gap exactly == k·std is NOT > k·std → still gap≈0-signal.
    assert s.classify_gap(gap_mean=0.5, gap_std=0.5, heldin_mean=1.5) == "gap≈0-signal"


def test_train_and_gap_multirun_smoke() -> None:
    """AC1/AC3: multi-run aggregation runs end-to-end (tiny) and yields a finite verdict."""
    pytest.importorskip("stable_baselines3")
    s = _script()
    first = next(iter(s.CONFIGS.values()))
    mr = s.train_and_gap_multirun(first, timesteps=256, runs=2, n_heldin=2, n_heldout=2)
    import math

    assert mr.runs == 2
    assert math.isfinite(mr.gap_mean) and math.isfinite(mr.gap_std)
    assert mr.gap_std >= 0.0
    assert mr.verdict in {"gap≈0-signal", "real-gap", "inconclusive"}
