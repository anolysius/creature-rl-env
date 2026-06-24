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
from critter_gym.learnability import measure_learnability
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

# -- discrimination resolution (difficulty-dynamic-range) ---------------------
# A direct pilot finding (see DESIGN §3.1.1): the prior 3-starter "oracle ceiling"
# was a misdiagnosis — oracle already clears ~all present gyms, and scripted oracle vs
# type_blind already differ by ~+1.0/gym. The real, confirmed lever for sharper
# *capability discrimination* is the score's DYNAMIC RANGE: with only ~2 gyms/episode
# the oracle-vs-blind spread is compressed. Raising (and fixing) the gym count widens
# that spread ~proportionally, so a strong policy and a weak one separate more clearly.
# (Starter diversification does NOT help — a single fixed champion super-counters ~half
# of a random tournament chart by chance; reducing type recurrence is forbidden — it
# makes in-episode inference impossible. This measures gym-count only.)
DISCRIM_BASE = dict(grid_size=6, num_creatures=5, max_steps=160, patch_radius=5,
                    vary=True, commit_battles=True, num_types=12, super_mult=3.0,
                    boss_hp=150, boss_atk=16)
DISCRIM_GYMS = (3, 5, 8)
# Pre-registered resolution rule (frozen before data — difficulty-dynamic-range task).
RESOLUTION_SPREAD_MIN = 2.0  # oracle−type_blind gym-clear spread at the max gym count
WINNABILITY_MIN = 0.70       # oracle gym-clear / num_gyms at the max gym count


@dataclass
class ResolutionRow:
    """Scripted-arm gym-clear means (held-out) at one gym count."""

    num_gyms: int
    oracle: float
    infer: float
    type_blind: float
    probe: float

    @property
    def spread(self) -> float:
        return self.oracle - self.type_blind

    @property
    def oracle_frac(self) -> float:
        return self.oracle / self.num_gyms


def discrimination_resolution(
    gym_counts: tuple[int, ...] = DISCRIM_GYMS, *, n_eval: int = N_HELDOUT,
) -> list[ResolutionRow]:
    """Oracle/infer/type_blind/probe gym-clear means (held-out) at each gym count.

    Pure numpy (scripted arms via :func:`measure_learnability`) — no ``[rl]`` needed.
    The widening of ``ResolutionRow.spread`` with the gym count is the discrimination
    resolution result.
    """
    heldin = tuple(range(n_eval))            # training-region (split guard)
    heldout = tuple(int(s) for s in heldout_seeds(n_eval))
    rows: list[ResolutionRow] = []
    for g in gym_counts:
        cfg = dict(DISCRIM_BASE, num_gyms=g, min_gyms=g)  # exact g gyms
        rep = measure_learnability(lambda c=cfg: CritterEnv(**c), heldin, heldout)
        rows.append(ResolutionRow(
            g, rep.heldout_gyms["oracle"], rep.heldout_gyms["infer"],
            rep.heldout_gyms["type_blind"], rep.heldout_gyms["probe"],
        ))
    return rows


def classify_resolution(rows: list[ResolutionRow]) -> str:
    """Pre-registered verdict: ``resolution-up`` iff the oracle−blind spread at the max
    gym count clears ``RESOLUTION_SPREAD_MIN`` AND spreads increase monotonically with
    the gym count AND winnability (oracle/num_gyms) at the max count clears
    ``WINNABILITY_MIN``; else ``insufficient`` (honest reframe)."""
    if not rows:
        return "insufficient"
    spreads = [r.spread for r in rows]
    mono = all(spreads[i] <= spreads[i + 1] + 1e-9 for i in range(len(spreads) - 1))
    top = rows[-1]
    ok = top.spread >= RESOLUTION_SPREAD_MIN and mono and top.oracle_frac >= WINNABILITY_MIN
    return "resolution-up" if ok else "insufficient"


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
    parser.add_argument("--resolution", action="store_true",
                        help="measure discrimination RESOLUTION vs gym count (scripted, "
                             "numpy-only — no [rl] needed). difficulty-dynamic-range.")
    parser.add_argument("--range-gap", action="store_true",
                        help="learned-policy gap at the high-gym (dynamic-range) config, "
                             "multi-run + classify_gap ([rl]).")
    args = parser.parse_args()

    if args.resolution:
        return _main_resolution()
    if args.range_gap:
        return _main_range_gap(args.timesteps, max(2, args.runs))

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


def _main_resolution() -> int:
    """Discrimination-resolution table (scripted, numpy-only) + pre-registered verdict."""
    rows = discrimination_resolution()
    print("discrimination resolution vs gym count | scripted arms | held-out | "
          f"gym-clear-only | N={N_HELDOUT}\n")
    print("| num_gyms | oracle | infer | type_blind | probe | spread(oracle−blind) | oracle/gyms |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r.num_gyms} | {r.oracle:.2f} | {r.infer:.2f} | {r.type_blind:.2f} | "
              f"{r.probe:.2f} | {r.spread:+.2f} | {r.oracle_frac:.2f} |")
    verdict = classify_resolution(rows)
    print(
        f"\nPRE-REGISTERED verdict (frozen before data): **{verdict}**. "
        f"'resolution-up' = spread@max ≥ {RESOLUTION_SPREAD_MIN} AND spreads monotone-increase "
        f"AND oracle/gyms@max ≥ {WINNABILITY_MIN}. The oracle−blind spread widening with the "
        "gym count = finer capability discrimination (a larger score dynamic range), NOT a "
        "harder task for a learned policy (that — making PPO unable to reach oracle — is "
        "explicitly out of scope; future work). infer≈oracle here (one sighting suffices on "
        "this config; see DESIGN §3.1.1). Single machine, scripted — a measurement, not a "
        "tuned number."
    )
    return 0


def _main_range_gap(timesteps: int, runs: int) -> int:
    """Learned-policy held-in/held-out gap at the high-gym dynamic-range config."""
    cfg = dict(DISCRIM_BASE, num_gyms=8, min_gyms=8)
    try:
        mr = train_and_gap_multirun(cfg, timesteps, runs)
    except ImportError:
        print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
        return 2
    print(f"dynamic-range learned gap | num_gyms=8 | PPO timesteps={timesteps:,} | runs={runs} "
          f"(mean ± std-across-runs) | N={N_HELDIN}/{N_HELDOUT}\n")
    print("| config | held-in | held-out | gap (±std-across-runs) | verdict |")
    print("|---|---|---|---|---|")
    print(f"| range_g8 | {mr.heldin_mean:.3f} | {mr.heldout_mean:.3f} | "
          f"{mr.gap_mean:+.3f} ±{mr.gap_std:.3f} | {mr.verdict} |")
    print(
        f"\nPRE-REGISTERED classify_gap (floor={GAP_FLOOR}, k={GAP_K}). gap≈0 at a wider "
        "dynamic range = discrimination resolution improved WHILE generalization holds (a "
        "strong result); real-gap = a train→test gap emerges (hard-benchmark signal). "
        "Single config, N modest — a signal, not a tuned number."
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
