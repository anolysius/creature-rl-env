"""Inference-difficulty curve (inference-difficulty-curve).

Sweeps the hidden type-chart size (``num_types``) and, for each, runs the scripted 4-arm
inference band. The ``infer`` arm (learns each matchup on first sight — an idealized in-context
inferrer) is the curve of interest: as the chart grows, does its super-effective-move rate fall?
Scripted-only, deterministic — a de-risked scout, not a learned/LLM curve.
"""

from __future__ import annotations

from critter_gym.inference_curve import CurvePoint, inference_difficulty_curve


def test_curve_length_and_num_types_match_grid() -> None:
    grid = (3, 4)
    curve = inference_difficulty_curve(grid)
    assert len(curve) == len(grid)
    assert tuple(p.num_types for p in curve) == grid
    assert all(isinstance(p, CurvePoint) for p in curve)


def test_curve_is_deterministic() -> None:
    a = inference_difficulty_curve((3, 4))
    b = inference_difficulty_curve((3, 4))
    assert a == b


def test_curve_band_sanity_oracle_at_or_above_floor() -> None:
    """At every point the chart-KNOWING oracle plays super-effective at least as often as the
    chart-BLIND floor — the band must discriminate for the curve to mean anything."""
    for p in inference_difficulty_curve((3, 4, 6)):
        assert p.oracle_se >= p.type_blind_se


def test_curve_infer_score_normalized() -> None:
    """The infer arm's inference score is normalized to [0, 1] (0 = blind floor, 1 = expert)."""
    for p in inference_difficulty_curve((3, 4, 6)):
        assert 0.0 <= p.infer_score <= 1.0


def test_curve_point_fields_present() -> None:
    (p,) = inference_difficulty_curve((3,))
    for field in ("num_types", "oracle_se", "infer_se", "type_blind_se", "probe_se",
                  "infer_score", "oracle_gyms", "winnable"):
        assert hasattr(p, field)
    assert isinstance(p.winnable, bool)
