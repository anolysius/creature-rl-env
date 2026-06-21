#!/usr/bin/env python3
"""Optional PPO learning demo (requires the ``[rl]`` extra: stable-baselines3 + torch).

NOT part of the default test suite — it is heavy and machine-dependent. It trains
PPO on an easy, fully-observed config and asserts the learned policy beats the
random baseline on held-out seeds (``trained_mean >= random_mean + 0.5``), exiting
non-zero otherwise. This is the reproducible form of the learning-curve demo.

Usage:
    pip install -e ".[rl]"
    python scripts/train_ppo.py --timesteps 40000
"""

from __future__ import annotations

import argparse
import sys
import warnings

import numpy as np

from critter_gym.baselines import random_policy
from critter_gym.envs.critter_env import CritterEnv

# Easy config so learning is visible in a short run: small grid, full observability.
CFG = dict(grid_size=5, num_creatures=8, target_catches=3, max_steps=50, patch_radius=4)
HELDOUT = range(50_000, 50_120)
MARGIN = 0.5


def make_env() -> CritterEnv:
    return CritterEnv(**CFG)  # type: ignore[arg-type]


def eval_mean(act, seeds: range = HELDOUT) -> float:
    totals = []
    for s in seeds:
        env = make_env()
        obs, _ = env.reset(seed=s)
        done = False
        g = 0.0
        while not done:
            obs, r, term, trunc, _ = env.step(act(obs))
            g += r
            done = term or trunc
        totals.append(g)
    return float(np.mean(totals))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=40_000)
    args = parser.parse_args()

    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
    except ImportError:
        print("This demo needs the [rl] extra:  pip install -e \".[rl]\"", file=sys.stderr)
        return 2

    warnings.filterwarnings("ignore")
    rng = np.random.default_rng(0)
    random_mean = eval_mean(lambda o: random_policy(o, rng))

    model = PPO("MultiInputPolicy", DummyVecEnv([make_env]), verbose=0, n_steps=512, seed=0)
    chunk = max(1, args.timesteps // 5)
    print(f"max score = {CFG['target_catches']} | random held-out mean = {random_mean:.2f}\n")
    print(f"{'steps':>10} | {'held-out mean':>13}")
    print("-" * 28)
    trained_mean = 0.0
    for k in range(5):
        model.learn(chunk, reset_num_timesteps=False, progress_bar=False)
        trained_mean = eval_mean(lambda o: int(model.predict(o, deterministic=True)[0]))
        print(f"{(k + 1) * chunk:>10,} | {trained_mean:>13.2f}")

    ok = trained_mean >= random_mean + MARGIN
    print(f"\ntrained {trained_mean:.2f} vs random {random_mean:.2f} "
          f"(margin {MARGIN}) -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
