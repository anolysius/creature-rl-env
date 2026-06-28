"""Tests for the pre-registered inference-score classifier (inference-score-rigor).

`classify_inference` turns a multi-run set of inference scores into a robust verdict with a
decision rule frozen before the data (infer_thresh=0.50, floor_eps=0.10, k=1.0). Pure numpy —
no LLM, no jax — so CI exercises the rigor without any probe cost. Mirrors `test_headroom`.
"""
from __future__ import annotations

import pytest

from critter_gym.inference_rigor import InferenceVerdict, classify_inference


def test_all_expert_runs_verdict_infers() -> None:
    # AC1: runs at/above the bar with no spread -> robustly infers.
    v = classify_inference([0.9, 0.95, 1.0])
    assert isinstance(v, InferenceVerdict)
    assert v.verdict == "infers"
    assert v.n_runs == 3


def test_all_floor_runs_verdict_at_floor() -> None:
    # AC1: runs at the chart-blind floor (0.0) -> robustly at-chart-blind-floor.
    v = classify_inference([0.0, 0.0, 0.0])
    assert v.verdict == "at-chart-blind-floor"
    assert v.mean == 0.0 and v.std == 0.0


def test_straddling_band_is_inconclusive() -> None:
    # AC1: a wide band around the middle clears neither bar -> inconclusive.
    v = classify_inference([0.0, 0.5, 1.0])
    assert v.verdict == "inconclusive"


def test_high_mean_but_wide_std_is_inconclusive() -> None:
    # The pessimistic bound (m - k*s) must clear infer_thresh; high variance blocks "infers".
    v = classify_inference([0.4, 1.0])  # m=0.7, s=0.3 -> m-s=0.4 < 0.5
    assert v.verdict == "inconclusive"


def test_floor_eps_boundary() -> None:
    # m + s <= floor_eps (0.1) -> at-floor; just above -> not.
    assert classify_inference([0.1, 0.1]).verdict == "at-chart-blind-floor"  # m.1 s0 -> .1<=.1
    assert classify_inference([0.0, 0.2]).verdict != "at-chart-blind-floor"  # m.1 s.1 -> .2>.1


def test_mean_std_n_reported() -> None:
    v = classify_inference([0.2, 0.4, 0.6])
    assert v.mean == pytest.approx(0.4)
    assert v.n_runs == 3
    assert v.std == pytest.approx(0.163299, abs=1e-5)


def test_empty_runs_raises() -> None:
    with pytest.raises(ValueError):
        classify_inference([])


def test_frozen_thresholds_are_defaults() -> None:
    # AC2: the pre-registered thresholds are the code defaults (0.50 / 0.10 / 1.0).
    import inspect

    sig = inspect.signature(classify_inference)
    assert sig.parameters["infer_thresh"].default == 0.50
    assert sig.parameters["floor_eps"].default == 0.10
    assert sig.parameters["k"].default == 1.0


def test_single_run_uses_zero_std() -> None:
    # A single run -> std 0; a lone expert run reads "infers", a lone floor run "at-floor".
    assert classify_inference([1.0]).verdict == "infers"
    assert classify_inference([0.0]).verdict == "at-chart-blind-floor"
    assert classify_inference([0.3]).verdict == "inconclusive"