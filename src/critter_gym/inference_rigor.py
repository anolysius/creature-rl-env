"""Pre-registered inference-score classifier (numpy-only, CI — no jax).

`inference-score-metric` (#8) added the moat KPI ``inference_score`` ∈ [0,1] (0 = plays like a
chart-BLIND baseline, 1 = a chart-KNOWING expert) and a first **single-run** probe read 0.00.
Past threads found single reads were noise, so this classifies a *multi-run* set of inference
scores with a decision rule **frozen before the data** (``infer_thresh=0.50``, ``floor_eps=0.10``,
``k=1.0`` — see the task's qa-checklist), to report whether a submission *robustly* infers the
hidden rule or *robustly* sits at the chart-blind floor — rather than a lucky/unlucky run.

Verdict (on the per-run inference-score mean ``m`` and std ``s``):
  - ``m − k·s >= infer_thresh`` → ``infers`` (even the pessimistic bound clears the bar — the
    submission robustly beats the chart-blind baseline / shows in-context inference).
  - ``m + k·s <= floor_eps``    → ``at-chart-blind-floor`` (even the optimistic bound is at the
    floor — it robustly fails to infer the hidden rule).
  - otherwise                   → ``inconclusive`` (the run band straddles — more runs needed).

This mirrors :mod:`critter_gym.headroom`'s ``classify_headroom`` rigor pattern. It is a *tool*:
whatever verdict it returns is recorded honestly (this module never asserts a result).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

import numpy as np


class InferenceVerdict(NamedTuple):
    """The classifier output (plain floats / str — serializable, deterministic)."""

    verdict: str  # "infers" | "at-chart-blind-floor" | "inconclusive"
    mean: float
    std: float
    n_runs: int


def classify_inference(
    inference_runs: Sequence[float], *,
    infer_thresh: float = 0.50, floor_eps: float = 0.10, k: float = 1.0,
) -> InferenceVerdict:
    """Classify multi-run inference scores (pre-registered decision rule).

    ``inference_runs`` are per-run ``Scorecard.inference_score`` values (each already in [0,1]).
    ``infer_thresh`` / ``floor_eps`` / ``k`` are frozen before the data. Raises on an empty run
    set. The optimistic/pessimistic band is ``m ± k·s`` (std across runs).
    """
    runs = np.asarray(list(inference_runs), dtype=float)
    if runs.size == 0:
        raise ValueError("inference_runs must be non-empty")
    m = float(runs.mean())
    s = float(runs.std())
    if m - k * s >= infer_thresh:
        verdict = "infers"
    elif m + k * s <= floor_eps:
        verdict = "at-chart-blind-floor"
    else:
        verdict = "inconclusive"
    return InferenceVerdict(verdict=verdict, mean=m, std=s, n_runs=int(runs.size))
