"""AC2 + AC3: baselines exist, return valid actions, and produce a spread.

The spread guard (greedy > random > 0) is the load-bearing assertion that the
environment is a *valid benchmark* — neither trivial (random already maxes out)
nor impossible (no policy beats chance). It runs on held-out seeds the policies
never "trained" on, mirroring the generalization protocol.
"""

from __future__ import annotations

import numpy as np

from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.envs.critter_env import CritterEnv

HELDOUT = range(50_000, 50_100)


def _rollout_mean(policy, seeds) -> float:
    totals = []
    for s in seeds:
        # num_gyms=0 isolates the catch baseline (the overworld navigation +
        # catch behavior these policies target); gym battles are exercised in
        # tests/test_gym_battle.py.
        env = CritterEnv(num_gyms=0)
        obs, _ = env.reset(seed=s)
        done = False
        g = 0.0
        while not done:
            obs, r, term, trunc, _ = env.step(policy(obs))
            g += r
            done = term or trunc
        totals.append(g)
    return float(np.mean(totals))


def test_policies_return_valid_actions() -> None:
    env = CritterEnv(num_gyms=0)
    obs, _ = env.reset(seed=0)
    rng = np.random.default_rng(0)
    for _ in range(50):
        for action in (random_policy(obs, rng), greedy_policy(obs, env.grid_size)):
            assert env.action_space.contains(action)
        obs, _, term, trunc, _ = env.step(greedy_policy(obs, env.grid_size))
        if term or trunc:
            obs, _ = env.reset(seed=0)


def test_baseline_spread_makes_env_a_valid_benchmark() -> None:
    rng = np.random.default_rng(0)
    random_mean = _rollout_mean(lambda o: random_policy(o, rng), HELDOUT)
    greedy_mean = _rollout_mean(lambda o: greedy_policy(o, 10), HELDOUT)
    # Max attainable catch score is the creature count (num_gyms=0 here).
    cap = CritterEnv(num_gyms=0).num_creatures

    # Margins scale with the cap so the guard survives env-param changes
    # (a fixed absolute margin would go brittle if the cap moves).
    assert random_mean > 0, "env unsolvable even by chance"
    assert greedy_mean > random_mean, "no spread — env may be trivial/broken"
    assert greedy_mean >= 0.5 * cap, "scripted policy is not meaningfully competent"
    assert greedy_mean <= cap, "scripted policy exceeds the max attainable score"
