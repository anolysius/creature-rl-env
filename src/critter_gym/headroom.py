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
