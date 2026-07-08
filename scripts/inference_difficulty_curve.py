"""Scout: is hidden-chart size a calibrated inference-difficulty dial? (inference-difficulty-curve)

Sweeps ``num_types`` (the size of the hidden type-chart) and prints, for each, the scripted 4-arm
band — with the ``infer`` arm (an idealized first-sight inferrer) as the curve of interest. If its
super-effective-move rate / normalized inference score falls monotonically as the chart grows, then
``num_types`` calibrates inference difficulty (a measuring dial). A flat curve falsifies that.

HONEST FRAMING (read before quoting): scripted arms only, ONE deterministic seed set per point,
no learned or LLM agent. The infer arm is a *proxy* for in-context inference, not a model. The
curve is the task's difficulty as an idealized inferrer sees it — a learned/LLM anchor curve is a
separate, money-gated follow-up. Do not headline these numbers.

Run: `python scripts/inference_difficulty_curve.py [--quick]`. numpy only (free).
"""
from __future__ import annotations

import argparse

from critter_gym.inference_curve import inference_difficulty_curve

_GRID = (3, 4, 6, 8, 10, 12)
_GRID_QUICK = (3, 6, 12)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fewer points (3/6/12)")
    a = p.parse_args()
    grid = _GRID_QUICK if a.quick else _GRID

    print("== Inference-difficulty curve (scripted band) — SIGNAL, not measurement ==")
    print("  decision rule (declared before the numbers): infer-score falls monotonically as "
          "num_types grows => num_types is a calibrated inference-difficulty dial; a flat/"
          "non-monotone curve falsifies that.")
    print(f"  {'num_types':>9} | {'oracle':>7} {'infer':>7} {'blind':>7} {'probe':>7} | "
          f"{'infer_score':>11} | {'oracle_gyms':>11} winnable")
    curve = inference_difficulty_curve(grid)
    for pt in curve:
        print(f"  {pt.num_types:>9} | {pt.oracle_se:>6.0%} {pt.infer_se:>6.0%} "
              f"{pt.type_blind_se:>6.0%} {pt.probe_se:>6.0%} | {pt.infer_score:>11.2f} | "
              f"{pt.oracle_gyms:>11.2f} {pt.winnable}")

    scores = [pt.infer_score for pt in curve]
    monotone = all(scores[i] >= scores[i + 1] - 1e-9 for i in range(len(scores) - 1))
    drop = scores[0] - scores[-1]
    print(f"  infer_score: {scores[0]:.2f} (num_types={grid[0]}) -> {scores[-1]:.2f} "
          f"(num_types={grid[-1]})  |  drop {drop:+.2f}  |  monotone-nonincreasing={monotone}")
    print("  HONEST: scripted-arms-only, 1 seed set/point, deterministic — the infer arm is a "
          "PROXY for in-context inference, not a learned/LLM agent. A learned/LLM anchor curve is "
          "the (money-gated) follow-up. Do NOT headline these numbers.")


if __name__ == "__main__":
    main()
