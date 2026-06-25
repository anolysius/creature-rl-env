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
