"""AC5: throughput regression guard.

Measures steps/s of a random rollout and asserts a conservative floor. The floor
(5_000 steps/s/core) only catches catastrophic regressions — the DESIGN.md §4
aspiration is >=50_000 steps/s/core for the structured-obs CPU path. The actual
measured rate is recorded in the task report.
"""

from __future__ import annotations

import time

import numpy as np

from critter_gym.baselines import random_policy
from critter_gym.envs.critter_env import CritterEnv

MIN_STEPS = 20_000
FLOOR_STEPS_PER_S = 5_000


def measure_steps_per_second(min_steps: int = MIN_STEPS) -> float:
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
    elapsed = time.perf_counter() - start
    return steps / elapsed


def test_throughput_above_floor() -> None:
    rate = measure_steps_per_second()
    assert rate >= FLOOR_STEPS_PER_S, f"throughput regressed: {rate:.0f} < {FLOOR_STEPS_PER_S}"
