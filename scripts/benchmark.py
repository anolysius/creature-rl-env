#!/usr/bin/env python3
"""Human-readable benchmark report: baseline scores on held-out seeds + throughput.

Usage:
    python scripts/benchmark.py                 # defaults: seeds 50000..50099
    python scripts/benchmark.py --episodes 200 --seed0 60000
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.envs.critter_env import CritterEnv


def rollout_mean(policy, seeds: range) -> float:
    totals = []
    for s in seeds:
        env = CritterEnv()
        obs, _ = env.reset(seed=s)
        done = False
        g = 0.0
        while not done:
            obs, r, term, trunc, _ = env.step(policy(obs))
            g += r
            done = term or trunc
        totals.append(g)
    return float(np.mean(totals))


def steps_per_second(min_steps: int = 50_000) -> float:
    env = CritterEnv()
    rng = np.random.default_rng(0)
    obs, _ = env.reset(seed=0)
    steps = 0
    start = time.perf_counter()
    while steps < min_steps:
        obs, _, term, trunc, _ = env.step(random_policy(obs, rng))
        steps += 1
        if term or trunc:
            obs, _ = env.reset(seed=steps)
    return steps / (time.perf_counter() - start)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed0", type=int, default=50_000, help="first held-out seed")
    args = parser.parse_args()

    seeds = range(args.seed0, args.seed0 + args.episodes)
    rng = np.random.default_rng(0)
    target = CritterEnv().target_catches

    print(f"CritterGym benchmark — held-out seeds {seeds.start}..{seeds.stop - 1}")
    print(f"  max score / episode : {target}")
    print(f"  random  mean        : {rollout_mean(lambda o: random_policy(o, rng), seeds):.3f}")
    print(f"  greedy  mean        : {rollout_mean(lambda o: greedy_policy(o, 10), seeds):.3f}")
    print(f"  throughput          : {steps_per_second():,.0f} steps/s/core")


if __name__ == "__main__":
    main()
