#!/usr/bin/env python3
"""Does generalization (gap≈0) survive as difficulty rises? — PPO gap-at-difficulty ([rl]).

DESIGN §3.1.1 roadmap: a near-zero held-in/held-out gap on a *toy* env predicts little →
we want "hard-and-gap≈0". A pilot (task difficulty-generalization) FALSIFIED a clean
monotonic *scripted* difficulty ladder — difficulty is multi-dimensional (a bigger hidden
chart raises *inference* difficulty but makes *blind grinding easier*; boss stats are a
cliff, not a gradient) and a scripted oracle caps at ~0.6 (3 starters vs 12 types). So:

- The configs below are honest **difficulty points** of increasing knob intensity, NOT a
  calibrated monotonic ladder. We do not claim d0<d1<d2 by any single scalar.
- The measurement uses a **learned** policy, because a *scripted* policy cannot memorize,
  so its held-in/held-out gap is ≈0 trivially. Only a learned policy stresses whether the
  gap stays ≈0 under memorization pressure — i.e. whether generalization is real, not an
  artifact of the policy being incapable of overfitting.

For each config we train PPO on **held-in** (training-region) seeds and report the held-in
vs held-out generalization gap (reusing :mod:`critter_gym.generalization`, which enforces
the region split + leak guard; held-in eval is carved disjoint from the learning seeds via
``split_train_pool``). Nothing here is a pass/fail threshold — we *report* the gap (with its
per-seed std) at each difficulty point. Single run, modest N → a **signal**, not a tuned number.

Usage:
    pip install -e ".[rl]"
    python scripts/difficulty_generalization.py --timesteps 60000
"""

from __future__ import annotations

import argparse
import statistics
import sys
import warnings
from dataclasses import dataclass

import gymnasium as gym

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import GapReport, measure_generalization, split_train_pool
from critter_gym.region import heldout_seeds

# Pre-registered decision rule (frozen BEFORE seeing multi-run data — p-hacking guard,
# difficulty-gap-rigor task). The uncertainty that matters for "is the gap real" is the
# run-to-run variability of the gap point estimate (std-ACROSS-runs), NOT the per-seed std
# within a single run that task difficulty-generalization (#24) reported.
GAP_FLOOR = 0.3  # held-in below this → policy basically can't clear → can't test generalization
GAP_K = 1.0  # std-across-runs multiplier for the "robust" boundary

# Difficulty POINTS (increasing knob intensity) — NOT a calibrated monotonic ladder
# (the pilot falsified that). A small, fully-observed world so a short PPO run can learn,
# with the commit economy on so champion choice / inference matters.
_BASE = dict(grid_size=5, num_gyms=3, max_steps=80, patch_radius=4, vary=True,
             commit_battles=True)
CONFIGS: dict[str, dict] = {
    "d0_mild":   dict(**_BASE, num_types=3,  super_mult=2.0, boss_hp=90,  boss_atk=10),
    "d1_medium": dict(**_BASE, num_types=8,  super_mult=3.0, boss_hp=120, boss_atk=14),
    "d2_hard":   dict(**_BASE, num_types=12, super_mult=3.0, boss_hp=150, boss_atk=16),
}
N_TRAIN = 64
N_HELDIN = 16
N_HELDOUT = 16


class _SeededReset(gym.Wrapper):
    """Reset cycles through a fixed learning-seed pool (held-in eval stays unseen)."""

    def __init__(self, env: gym.Env, seeds: tuple[int, ...]) -> None:
        super().__init__(env)
        self._seeds = tuple(int(s) for s in seeds)
        self._i = 0

    def reset(self, *, seed=None, options=None):  # type: ignore[no-untyped-def]
        s = self._seeds[self._i % len(self._seeds)]
        self._i += 1
        return self.env.reset(seed=s, options=options)


def train_and_gap(config: dict, timesteps: int, *, n_heldin: int = N_HELDIN,
                  n_heldout: int = N_HELDOUT, seed: int = 0) -> GapReport:
    """Train PPO ``timesteps`` on held-in seeds at ``config``; return the held-in vs
    held-out :class:`GapReport`. Importable so a CI smoke test can use a tiny budget.
    Raises ImportError if the ``[rl]`` extra is missing (callers gate with importorskip)."""
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    warnings.filterwarnings("ignore")
    # held-in eval seeds carved DISJOINT from the learning seeds (no flattered gap).
    learn_seeds, heldin = split_train_pool(range(N_TRAIN), n_eval=n_heldin)
    heldout = heldout_seeds(n_heldout)

    def make_train_env() -> gym.Env:
        return _SeededReset(CritterEnv(**config), learn_seeds)

    model = PPO("MultiInputPolicy", DummyVecEnv([make_train_env]),
                verbose=0, n_steps=512, seed=seed)
    model.learn(timesteps, progress_bar=False)

    def ppo_policy(obs: dict) -> int:
        return int(model.predict(obs, deterministic=True)[0])

    return measure_generalization(
        lambda: CritterEnv(**config), ppo_policy, heldin, heldout
    )


def classify_gap(gap_mean: float, gap_std: float, heldin_mean: float) -> str:
    """Pre-registered verdict for one difficulty point (thresholds frozen pre-data).

    ``gap_std`` is the std **across runs** (run-to-run variability of the gap), the
    quantity that determines whether a gap is real — not the per-seed std within a run.

    - ``inconclusive`` — held-in below ``GAP_FLOOR`` (policy can't clear, so a small gap
      reflects incapacity, not generalization), OR a robustly *negative* gap (held-out
      easier = difficulty asymmetry, not transfer).
    - ``real-gap`` — gap robustly positive (``> GAP_K·gap_std``): the env exhibits a
      train→test generalization gap (a "hard benchmark" signal, Procgen-style).
    - ``gap≈0-signal`` — ``|gap_mean| ≤ GAP_K·gap_std``: run variability swamps the gap,
      robustly consistent with gap≈0 (now at multi-run rigor, not single-run noise).
    """
    if heldin_mean < GAP_FLOOR:
        return "inconclusive"
    if gap_mean > GAP_K * gap_std:
        return "real-gap"
    if gap_mean < -GAP_K * gap_std:
        return "inconclusive"
    return "gap≈0-signal"


@dataclass
class MultiRunGap:
    """Across-run aggregate of per-run :class:`GapReport`s for one difficulty point."""

    heldin_mean: float
    heldout_mean: float
    gap_mean: float
    gap_std: float  # std ACROSS runs of the per-run gap (the rigor quantity)
    runs: int

    @property
    def verdict(self) -> str:
        return classify_gap(self.gap_mean, self.gap_std, self.heldin_mean)


def train_and_gap_multirun(
    config: dict, timesteps: int, runs: int, *, n_heldin: int = N_HELDIN,
    n_heldout: int = N_HELDOUT,
) -> MultiRunGap:
    """Run :func:`train_and_gap` ``runs`` times (distinct PPO seeds) and aggregate.

    Reports the gap **mean ± std-across-runs** — the multi-run upgrade over #24's single
    run, so a small real gap can be told apart from run noise. Raises ImportError without
    the ``[rl]`` extra (callers gate with importorskip)."""
    gaps, heldins, heldouts = [], [], []
    for r in range(runs):
        rep = train_and_gap(config, timesteps, n_heldin=n_heldin, n_heldout=n_heldout, seed=r)
        d = rep.to_dict()
        heldins.append(d["heldin_mean"])
        heldouts.append(d["heldout_mean"])
        gaps.append(d["gap"])
    gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 0.0
    return MultiRunGap(
        heldin_mean=statistics.fmean(heldins),
        heldout_mean=statistics.fmean(heldouts),
        gap_mean=statistics.fmean(gaps),
        gap_std=gap_std,
        runs=runs,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=60_000)
    parser.add_argument("--runs", type=int, default=1,
                        help="PPO seeds per config; >1 reports gap mean ± std-ACROSS-runs "
                             "with the pre-registered classify_gap verdict (rigor).")
    args = parser.parse_args()

    if args.runs <= 1:
        return _main_singlerun(args.timesteps)

    try:
        rows = [(name, train_and_gap_multirun(cfg, args.timesteps, args.runs))
                for name, cfg in CONFIGS.items()]
    except ImportError:
        print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
        return 2

    print(f"gap-at-difficulty | PPO timesteps={args.timesteps:,} | runs={args.runs} "
          f"(mean ± std-across-runs) | N={N_HELDIN}/{N_HELDOUT}\n")
    print("| difficulty point | held-in | held-out | gap (±std-across-runs) | verdict |")
    print("|---|---|---|---|---|")
    for name, mr in rows:
        print(
            f"| {name} | {mr.heldin_mean:.3f} | {mr.heldout_mean:.3f} | "
            f"{mr.gap_mean:+.3f} ±{mr.gap_std:.3f} | {mr.verdict} |"
        )
    print(
        f"\nVerdict by the PRE-REGISTERED rule (frozen before data): floor={GAP_FLOOR}, "
        f"k={GAP_K}. 'gap≈0-signal' = |gap| ≤ k·std-across-runs (robustly consistent with "
        "gap≈0); 'real-gap' = gap > k·std (env shows a train→test gap = a hard-benchmark "
        "signal); 'inconclusive' = held-in < floor (policy too weak) or robustly negative "
        "(held-out easier). Multi-run corrects the single-run weak signal of #24. Configs "
        "are difficulty *points*, not a calibrated monotonic ladder. See DESIGN §3.1.1."
    )
    return 0


def _main_singlerun(timesteps: int) -> int:
    """The original single-run table (#24) — kept for the smoke path / quick look."""
    try:
        rows = [(name, train_and_gap(cfg, timesteps)) for name, cfg in CONFIGS.items()]
    except ImportError:
        print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
        return 2

    print(f"gap-at-difficulty | PPO timesteps={timesteps:,} per config | SINGLE run\n")
    print("| difficulty point | held-in (±std) | held-out (±std) | gap |")
    print("|---|---|---|---|")
    for name, rep in rows:
        d = rep.to_dict()
        print(
            f"| {name} | {d['heldin_mean']:.3f} ±{rep.train.std:.3f} | "
            f"{d['heldout_mean']:.3f} ±{rep.test.std:.3f} | {d['gap']:+.3f} |"
        )
    print(
        f"\nSINGLE run, N={N_HELDIN}/{N_HELDOUT} → a weak signal (per-seed std, not "
        "std-across-runs). Use --runs N for the pre-registered multi-run verdict. "
        "See DESIGN §3.1.1."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
