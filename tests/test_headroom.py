"""Unit tests for the pre-registered oracle-headroom classifier (numpy-only, CI).

`classify_headroom` decides — from a set of multi-run PPO held-out gym-clear means vs the
scripted oracle ceiling — whether the "hard-and-learnable" headline survives across seeds
(not single-run noise). The thresholds (frac=0.75, k=1.0) are frozen in the plan/qa-checklist
BEFORE the data; these tests pin the decision boundaries.
"""

from __future__ import annotations

import pytest

from critter_gym.headroom import HeadroomVerdict, classify_headroom


def test_hard_and_learnable_when_optimistic_bound_below_oracle() -> None:
    # PPO ~1.0±0.1 vs oracle 7.0: even mean + k*std = 1.1 << 0.75*7 = 5.25.
    v = classify_headroom([1.0, 1.1, 0.9, 1.05, 0.95], oracle=7.0)
    assert v.verdict == "hard-and-learnable"
    assert v.oracle == 7.0
    assert abs(v.ppo_mean - 1.0) < 0.05


def test_ppo_closes_when_pessimistic_bound_above_threshold() -> None:
    # PPO ~6.0±0.1 vs oracle 7.0: mean - k*std = 5.9 >= 0.75*7 = 5.25.
    v = classify_headroom([6.0, 6.1, 5.9, 6.05], oracle=7.0)
    assert v.verdict == "ppo-closes"


def test_inconclusive_when_band_straddles_threshold() -> None:
    # PPO ~5.25±0.6 vs oracle 7.0: band [4.65, 5.85] straddles 0.75*7 = 5.25.
    v = classify_headroom([4.7, 5.8, 5.2, 5.3], oracle=7.0)
    assert v.verdict == "inconclusive"


def test_ratio_and_fields() -> None:
    v = classify_headroom([2.0, 2.0, 2.0], oracle=8.0)
    assert v.ratio == pytest.approx(0.25)
    assert v.ppo_std == pytest.approx(0.0)
    assert isinstance(v, HeadroomVerdict)


def test_custom_frac_k() -> None:
    # With frac=0.5: 0.5*7 = 3.5. PPO 1.0±0.1 -> optimistic 1.1 <= 3.5 -> hard-and-learnable.
    v = classify_headroom([1.0, 1.1, 0.9], oracle=7.0, frac=0.5, k=2.0)
    assert v.verdict == "hard-and-learnable"


def test_empty_runs_raises() -> None:
    with pytest.raises(ValueError):
        classify_headroom([], oracle=7.0)


def test_nonpositive_oracle_raises() -> None:
    with pytest.raises(ValueError):
        classify_headroom([1.0], oracle=0.0)


# --- classify_depth (multitype-boss-headroom, pre-registered depth rule) ----------------
#
# Decides — from per-run oracle-FRACTIONS on the single-type vs multi-type configs — whether
# the hidden secondary boss type is ROBUSTLY deeper. Rule frozen in the plan BEFORE the data:
#   deeper-robust : mean(single) - mean(multi) > max(std_single, std_multi)  AND both winnable
#   not-deeper    : mean(single) - mean(multi) <= 0   (the scout Delta is refuted)
#   inconclusive  : otherwise (0 < gap <= max std), or a non-winnable config.

from critter_gym.headroom import DepthVerdict, classify_depth  # noqa: E402


def test_depth_deeper_robust_when_gap_exceeds_max_std() -> None:
    # single ~0.50±0.02, multi ~0.30±0.03: gap 0.20 > max std 0.03.
    v = classify_depth([0.50, 0.52, 0.48], [0.30, 0.33, 0.27],
                       single_winnable=True, multi_winnable=True)
    assert v.verdict == "deeper-robust"
    assert abs(v.gap - 0.20) < 0.02


def test_depth_not_deeper_when_gap_nonpositive() -> None:
    # multi >= single: the scout signal is refuted — report as-is.
    v = classify_depth([0.30, 0.31, 0.29], [0.35, 0.36, 0.34],
                       single_winnable=True, multi_winnable=True)
    assert v.verdict == "not-deeper"
    assert v.gap <= 0


def test_depth_inconclusive_when_gap_within_noise() -> None:
    # gap 0.05 but stds ~0.10: 0 < gap <= max std.
    v = classify_depth([0.40, 0.50, 0.30], [0.35, 0.45, 0.25],
                       single_winnable=True, multi_winnable=True)
    assert v.verdict == "inconclusive"


def test_depth_inconclusive_when_not_winnable() -> None:
    # A non-winnable config voids the comparison even with a big gap (unfair lever).
    v = classify_depth([0.50, 0.52, 0.48], [0.10, 0.12, 0.08],
                       single_winnable=True, multi_winnable=False)
    assert v.verdict == "inconclusive"


def test_depth_rejects_empty_runs() -> None:
    with pytest.raises(ValueError):
        classify_depth([], [0.3], single_winnable=True, multi_winnable=True)
    with pytest.raises(ValueError):
        classify_depth([0.3], [], single_winnable=True, multi_winnable=True)


def test_depth_single_run_zero_std_boundary() -> None:
    # One run each => std 0; any positive gap > 0 = max std, so deeper-robust — this is why
    # the measurement uses >=3 runs (a 1-run "robust" is vacuous; the script enforces N).
    v = classify_depth([0.28], [0.24], single_winnable=True, multi_winnable=True)
    assert isinstance(v, DepthVerdict)
    assert v.verdict == "deeper-robust"
