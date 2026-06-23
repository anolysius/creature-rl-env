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
import sys
import warnings

import gymnasium as gym

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import GapReport, measure_generalization, split_train_pool
from critter_gym.region import heldout_seeds

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=60_000)
    args = parser.parse_args()
    try:
        rows = []
        for name, cfg in CONFIGS.items():
            rep = train_and_gap(cfg, args.timesteps)
            rows.append((name, rep))
    except ImportError:
        print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
        return 2

    print(f"gap-at-difficulty | PPO timesteps={args.timesteps:,} per config\n")
    print("| difficulty point | held-in (±std) | held-out (±std) | gap |")
    print("|---|---|---|---|")
    for name, rep in rows:
        d = rep.to_dict()
        print(
            f"| {name} | {d['heldin_mean']:.3f} ±{rep.train.std:.3f} | "
            f"{d['heldout_mean']:.3f} ±{rep.test.std:.3f} | {d['gap']:+.3f} |"
        )
    print(
        "\nReported, not pass/fail. Configs are difficulty *points* (a clean monotonic "
        "scripted ladder was falsified — difficulty is multi-dimensional). A gap within "
        "±std is consistent with gap≈0, but at this std/budget cannot distinguish a small "
        "real gap from zero (weak evidence, not 'generalization proven'); a gap growing "
        f"beyond std as intensity rises would be reported as-is. Single run, N={N_HELDIN}/"
        f"{N_HELDOUT}, low budget → a signal. See DESIGN §3.1.1."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
