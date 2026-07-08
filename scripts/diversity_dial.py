"""Scout: is per-episode type diversity the calibrated inference-difficulty dial? (diversity-dial)

The prior scout falsified num_types (chart size) as the dial — the recurrence pool caps distinct
boss-types per world at ~2, so chart size never reaches a first-sight inferrer. This tests the real
candidate: at a FIXED gym budget, sweep the boss-type pool so per-episode diversity rises (and
revisits fall). The x-axis is the *measured* mean distinct-types per world, not the raw knob.

Decision rule (declared before the numbers): if the infer arm's inference score falls
monotonically as measured diversity rises, per-episode type diversity is a calibrated
inference-difficulty dial (a measuring instrument). A flat curve falsifies that.

HONEST FRAMING: scripted arms only, ONE deterministic seed set per point, no learned or LLM
agent — the infer arm is a PROXY for in-context inference. A learned/LLM anchor curve is a
separate, money-gated follow-up. Do NOT headline these numbers.

Run: `python scripts/diversity_dial.py [--quick]`. numpy only (free).
"""
from __future__ import annotations

import argparse

from critter_gym.inference_curve import diversity_curve

_GRID = (1, 2, 3, 4, 6, 8)
_GRID_QUICK = (1, 4, 8)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fewer points (1/4/8)")
    a = p.parse_args()
    grid = _GRID_QUICK if a.quick else _GRID

    print("== Type-diversity dial (scripted band) — SIGNAL, not measurement ==")
    print("  decision rule (declared before the numbers): infer-score falls monotonically as "
          "measured per-episode diversity rises => per-episode type diversity is a calibrated "
          "inference-difficulty dial; a flat curve falsifies that.")
    print(f"  {'pool':>4} {'distinct/world':>14} | {'oracle':>7} {'infer':>7} {'blind':>7} "
          f"{'probe':>7} | {'infer_score':>11} | {'oracle_gyms':>11} winnable")
    curve = diversity_curve(grid)
    for pt in curve:
        print(f"  {pt.pool_size:>4} {pt.mean_distinct_types:>14.2f} | {pt.oracle_se:>6.0%} "
              f"{pt.infer_se:>6.0%} {pt.type_blind_se:>6.0%} {pt.probe_se:>6.0%} | "
              f"{pt.infer_score:>11.2f} | {pt.oracle_gyms:>11.2f} {pt.winnable}")

    scores = [pt.infer_score for pt in curve]
    monotone = all(scores[i] >= scores[i + 1] - 1e-9 for i in range(len(scores) - 1))
    div = [pt.mean_distinct_types for pt in curve]
    print(f"  measured diversity: {div[0]:.1f} -> {div[-1]:.1f} distinct types/world  |  "
          f"infer_score: {scores[0]:.2f} -> {scores[-1]:.2f}  |  drop {scores[0] - scores[-1]:+.2f}"
          f"  |  monotone-nonincreasing={monotone}")
    print("  HONEST: scripted-arms-only, 1 seed set/point, deterministic — the infer arm is a "
          "PROXY for in-context inference, not a learned/LLM agent. A learned/LLM anchor curve is "
          "the (money-gated) follow-up. Do NOT headline these numbers.")


if __name__ == "__main__":
    main()
