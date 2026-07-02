"""Pre-registered oracle-headroom classifier (numpy-only, CI — no jax).

`jax-ppo-tuned` measured, single-run, that a tuned PPO reaches only ~15–32% of the
scripted-oracle gym-clear ceiling — the "hard-and-learnable" headline. Past (B) threads
repeatedly found single-run reads were noise, so this classifies a *multi-run* set of PPO
held-out gym-clear means against the oracle with a decision rule **frozen before the data**
(``frac=0.75``, ``k=1.0`` — see the task's qa-checklist), to report whether the headline is
robust across seeds rather than a lucky run.

Verdict (on the PPO run-mean ``m`` and run-std ``s`` vs ``oracle``):
  - ``m + k·s <= frac·oracle``  → ``hard-and-learnable`` (even the optimistic PPO bound is
    well below the oracle — the headroom is robust).
  - ``m − k·s >= frac·oracle``  → ``ppo-closes`` (even the pessimistic bound is near/above
    the oracle — PPO nearly closes the gap; the "hard" claim would need a reframe).
  - otherwise                   → ``inconclusive`` (the run band straddles the threshold —
    more runs / budget are needed).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

import numpy as np


class HeadroomVerdict(NamedTuple):
    """The classifier output (all plain floats / str — serializable, deterministic)."""

    verdict: str  # "hard-and-learnable" | "ppo-closes" | "inconclusive"
    ppo_mean: float
    ppo_std: float
    oracle: float
    ratio: float  # ppo_mean / oracle (fraction of the oracle ceiling reached)


def classify_headroom(
    ppo_runs: Sequence[float], oracle: float, *, frac: float = 0.75, k: float = 1.0,
) -> HeadroomVerdict:
    """Classify multi-run PPO held-out gym-clears vs the oracle ceiling (pre-registered).

    ``ppo_runs`` are per-run held-out gym-clear means; ``oracle`` is the scripted-oracle
    gym-clear mean (a ceiling proxy). ``frac``/``k`` are frozen before the data. Raises on
    an empty run set or a non-positive oracle (no meaningful ratio).
    """
    runs = np.asarray(list(ppo_runs), dtype=float)
    if runs.size == 0:
        raise ValueError("ppo_runs must be non-empty")
    if oracle <= 0:
        raise ValueError(f"oracle must be positive, got {oracle}")
    m = float(runs.mean())
    s = float(runs.std())
    thresh = frac * oracle
    if m + k * s <= thresh:
        verdict = "hard-and-learnable"
    elif m - k * s >= thresh:
        verdict = "ppo-closes"
    else:
        verdict = "inconclusive"
    return HeadroomVerdict(
        verdict=verdict, ppo_mean=m, ppo_std=s, oracle=float(oracle), ratio=m / oracle,
    )


class DepthVerdict(NamedTuple):
    """Output of :func:`classify_depth` (plain floats / str — serializable, deterministic)."""

    verdict: str  # "deeper-robust" | "not-deeper" | "inconclusive"
    single_mean: float
    single_std: float
    multi_mean: float
    multi_std: float
    gap: float  # single_mean - multi_mean (in oracle-fraction units)


def classify_depth(
    single_fracs: Sequence[float], multi_fracs: Sequence[float],
    *, single_winnable: bool, multi_winnable: bool,
) -> DepthVerdict:
    """Is the multi-type boss ROBUSTLY deeper than single-type? (pre-registered rule).

    Inputs are per-run **oracle fractions** (gym-clears / that config's oracle — normalized
    because the two configs have different oracle ceilings). Rule frozen before the data
    (multitype-boss-headroom plan):

    - ``deeper-robust``: ``mean(single) - mean(multi) > max(std_single, std_multi)`` AND both
      configs winnable (a non-winnable config would make the lever unfair, voiding the read).
    - ``not-deeper``: the gap is <= 0 — the scout signal is refuted; report as-is.
    - ``inconclusive``: otherwise (a positive gap within run noise, or a non-winnable config).

    Raises on an empty run set (no meaningful statistics).
    """
    s_runs = np.asarray(list(single_fracs), dtype=float)
    m_runs = np.asarray(list(multi_fracs), dtype=float)
    if s_runs.size == 0 or m_runs.size == 0:
        raise ValueError("single_fracs and multi_fracs must be non-empty")
    sm, ss = float(s_runs.mean()), float(s_runs.std())
    mm, ms = float(m_runs.mean()), float(m_runs.std())
    gap = sm - mm
    if gap <= 0:
        verdict = "not-deeper"
    elif not (single_winnable and multi_winnable):
        verdict = "inconclusive"
    elif gap > max(ss, ms):
        verdict = "deeper-robust"
    else:
        verdict = "inconclusive"
    return DepthVerdict(
        verdict=verdict, single_mean=sm, single_std=ss, multi_mean=mm, multi_std=ms, gap=gap,
    )
