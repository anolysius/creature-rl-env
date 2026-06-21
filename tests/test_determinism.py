"""AC4: full-trajectory determinism under a fixed seed + policy.

Scaffolding pinned the *initial* observation; here we pin the *entire episode*
trajectory, which is what reproducible benchmarking and train/test seed splits
actually require.
"""

from __future__ import annotations

import numpy as np

from critter_gym.baselines import greedy_policy
from critter_gym.envs.critter_env import CritterEnv


def _trajectory(seed: int) -> list[tuple[np.ndarray, float]]:
    env = CritterEnv()
    obs, _ = env.reset(seed=seed)
    traj: list[tuple[np.ndarray, float]] = []
    done = False
    while not done:
        action = greedy_policy(obs, env.grid_size)
        obs, r, term, trunc, _ = env.step(action)
        traj.append((obs["agent_pos"].copy(), r))
        done = term or trunc
    return traj


def test_same_seed_same_trajectory() -> None:
    a, b = _trajectory(123), _trajectory(123)
    assert len(a) == len(b)
    for (pa, ra), (pb, rb) in zip(a, b):
        assert np.array_equal(pa, pb)
        assert ra == rb


def test_different_seed_different_world() -> None:
    ea, eb = CritterEnv(), CritterEnv()
    oa, _ = ea.reset(seed=1)
    ob, _ = eb.reset(seed=2)
    differs = not np.array_equal(oa["agent_pos"], ob["agent_pos"]) or not np.array_equal(
        oa["local_patch"], ob["local_patch"]
    )
    assert differs
