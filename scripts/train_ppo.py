#!/usr/bin/env python3
"""Optional PPO learning + generalization demo (requires the ``[rl]`` extra).

NOT part of the default test suite — it is heavy and machine-dependent. It trains
PPO on a pool of *training* seeds of the **procgen** variant (``vary=True``: each
seed is a new map + a new type chart), then measures the Procgen-style
generalization gap on held-in (training-region) vs held-out (test-region) seeds
using :mod:`critter_gym.generalization`. The trained policy is expected to beat the
random baseline on held-out seeds (``heldout_mean >= random_heldout_mean + MARGIN``); the
gap itself is *reported*, not used as a pass/fail threshold (overfitting is the
thing we measure, not a failure condition).

Usage:
    pip install -e ".[rl]"
    python scripts/train_ppo.py --timesteps 40000
"""

from __future__ import annotations

import argparse
import sys
import warnings

import gymnasium as gym
import numpy as np

from critter_gym.baselines import random_policy
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import format_report, measure_generalization, split_train_pool
from critter_gym.region import heldout_seeds, train_seeds
from critter_gym.viz import LearningCurve

# Easy, fully-observed config so learning is visible in a short run.
CFG = dict(grid_size=5, num_creatures=8, num_gyms=2, max_steps=50, patch_radius=4)
N_TRAIN = 64  # training seed pool (split into learning + held-in eval)
N_HELDIN = 16  # held-in eval seeds carved from the pool, disjoint from learning
N_HELDOUT = 16  # held-out (test-region) eval seeds — new maps + new type charts
MARGIN = 0.5


def make_env() -> CritterEnv:
    return CritterEnv(vary=True, **CFG)  # type: ignore[arg-type]


class _SeededReset(gym.Wrapper):
    """Reset cycles deterministically through a fixed pool of seeds (the learn pool).

    Keeps training strictly on the learning seeds so the held-in eval set stays
    unseen — the disjointness that makes the measured gap honest.
    """

    def __init__(self, env: gym.Env, seeds: tuple[int, ...]) -> None:
        super().__init__(env)
        self._seeds = tuple(int(s) for s in seeds)
        self._i = 0

    def reset(self, *, seed=None, options=None):  # type: ignore[no-untyped-def]
        s = self._seeds[self._i % len(self._seeds)]
        self._i += 1
        return self.env.reset(seed=s, options=options)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=40_000)
    parser.add_argument("--plot", metavar="PATH", help="save the learning curve PNG ([viz] extra)")
    args = parser.parse_args()

    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
    except ImportError:
        print('This demo needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
        return 2

    warnings.filterwarnings("ignore")

    learn_seeds, heldin = split_train_pool(train_seeds(N_TRAIN), n_eval=N_HELDIN)
    heldout = heldout_seeds(N_HELDOUT)

    rng = np.random.default_rng(0)
    random_report = measure_generalization(
        make_env, lambda o: random_policy(o, rng), heldin, heldout
    )

    def make_train_env() -> gym.Env:
        return _SeededReset(make_env(), learn_seeds)

    model = PPO("MultiInputPolicy", DummyVecEnv([make_train_env]), verbose=0, n_steps=512, seed=0)

    def ppo_policy(obs: dict) -> int:
        return int(model.predict(obs, deterministic=True)[0])

    chunk = max(1, args.timesteps // 5)
    print(
        f"procgen (vary=True) | learn={len(learn_seeds)} held-in={len(heldin)} "
        f"held-out={len(heldout)} | random held-out mean = {random_report.test.mean:.2f}\n"
    )
    print(f"{'steps':>10} | {'held-in':>8} | {'held-out':>8} | {'gap':>7}")
    print("-" * 42)
    report = random_report
    steps_axis: list[int] = []
    heldin_curve: list[float] = []
    heldout_curve: list[float] = []
    for k in range(5):
        model.learn(chunk, reset_num_timesteps=False, progress_bar=False)
        report = measure_generalization(make_env, ppo_policy, heldin, heldout)
        d = report.to_dict()
        steps_axis.append((k + 1) * chunk)
        heldin_curve.append(d["heldin_mean"])
        heldout_curve.append(d["heldout_mean"])
        print(
            f"{(k + 1) * chunk:>10,} | {d['heldin_mean']:>8.2f} | "
            f"{d['heldout_mean']:>8.2f} | {d['gap']:>7.2f}"
        )

    print("\n" + format_report(report))

    if args.plot:
        from critter_gym.viz import plot_learning_curve  # lazy matplotlib inside

        curve = LearningCurve(
            timesteps=tuple(steps_axis),
            heldin_means=tuple(heldin_curve),
            heldout_means=tuple(heldout_curve),
        )
        try:
            fig = plot_learning_curve(curve)
        except ImportError:
            print('  (--plot skipped — install the [viz] extra: pip install -e ".[viz]")')
        else:
            fig.savefig(args.plot, dpi=100, bbox_inches="tight")
            print(f"saved learning curve -> {args.plot}")
    ok = report.test.mean >= random_report.test.mean + MARGIN
    print(
        f"\ntrained held-out {report.test.mean:.2f} vs random {random_report.test.mean:.2f} "
        f"(margin {MARGIN}) -> {'PASS' if ok else 'FAIL'}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
