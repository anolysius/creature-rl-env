#!/usr/bin/env python3
"""Human-readable benchmark leaderboard — ranked baselines + throughput (M3-EC2).

Builds the reproducible leaderboard via :mod:`critter_gym.leaderboard` on the
**procgen** variant (``vary=True``): baselines are ranked by held-out (test-region)
mean return — performance on unseen maps + type charts — alongside their held-in
score and the generalization gap. The pinned :class:`BenchmarkSpec` is printed so a
run is self-describing and reproducible.

The core baselines (``random``, ``scripted``) need only numpy and always run. The
learned baselines (``ppo``, ``recurrent``) need the ``[rl]`` extra
(stable-baselines3 + sb3-contrib); without it they are skipped (non-fatal).

Usage:
    python scripts/benchmark.py                        # core baselines only
    pip install -e ".[rl]" && python scripts/benchmark.py --timesteps 20000
    python scripts/benchmark.py --heldin 100 --heldout 100
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable

import gymnasium as gym
import numpy as np

from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import PolicyFn
from critter_gym.leaderboard import BenchmarkSpec, run_benchmark
from critter_gym.region import train_seeds

# Easy, fully-observed env config so learning is visible in a short run.
CFG = dict(grid_size=5, num_creatures=8, num_gyms=2, max_steps=50, patch_radius=4)


class _SeededReset(gym.Wrapper):
    """Reset cycles through a fixed pool of seeds (the learn pool), kept disjoint
    from the spec's held-in eval seeds so the measured gap stays honest."""

    def __init__(self, env: gym.Env, seeds: tuple[int, ...]) -> None:
        super().__init__(env)
        self._seeds = tuple(int(s) for s in seeds)
        self._i = 0

    def reset(self, *, seed=None, options=None):  # type: ignore[no-untyped-def]
        s = self._seeds[self._i % len(self._seeds)]
        self._i += 1
        return self.env.reset(seed=s, options=options)


def steps_per_second(env_factory: Callable[[], CritterEnv], min_steps: int = 50_000) -> float:
    env = env_factory()
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


def _learned_baselines(
    env_factory: Callable[[], CritterEnv], learn_seeds: tuple[int, ...], timesteps: int
) -> dict[str, PolicyFn]:
    """Train PPO + recurrent PPO on the learn pool; return them as policies.

    Returns an empty dict (with a printed notice) if the ``[rl]`` extra is absent,
    so the leaderboard degrades to the core baselines instead of crashing.
    """
    try:
        from sb3_contrib import RecurrentPPO
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
    except ImportError:
        print('  (ppo/recurrent skipped — install the [rl] extra: pip install -e ".[rl]")\n')
        return {}

    def make_train_env() -> gym.Env:
        return _SeededReset(env_factory(), learn_seeds)

    ppo = PPO("MultiInputPolicy", DummyVecEnv([make_train_env]), n_steps=512, seed=0, verbose=0)
    rec = RecurrentPPO(
        "MultiInputLstmPolicy", DummyVecEnv([make_train_env]), n_steps=512, seed=0, verbose=0
    )
    ppo.learn(timesteps)
    rec.learn(timesteps)
    return {
        "ppo": lambda o: int(ppo.predict(o, deterministic=True)[0]),
        "recurrent": lambda o: int(rec.predict(o, deterministic=True)[0]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--heldin", type=int, default=32, help="held-in eval seed count")
    parser.add_argument("--heldout", type=int, default=32, help="held-out eval seed count")
    parser.add_argument("--learn", type=int, default=64, help="PPO learning pool size")
    parser.add_argument("--timesteps", type=int, default=20_000, help="per learned baseline")
    args = parser.parse_args()

    spec = BenchmarkSpec(**CFG, n_heldin=args.heldin, n_heldout=args.heldout)  # type: ignore[arg-type]
    env_factory = spec.env_factory()
    # Learn on a training-region pool *after* the held-in eval block [0, n_heldin),
    # so the learn seeds and the held-in eval seeds stay disjoint.
    learn_seeds = tuple(train_seeds(args.learn, start=spec.n_heldin))

    rng = np.random.default_rng(0)
    baselines: dict[str, PolicyFn] = {
        "random": lambda o: random_policy(o, rng),
        "scripted": lambda o: greedy_policy(o, grid_size=spec.grid_size),
    }
    print(f"CritterGym leaderboard — reproducible spec: {spec.to_dict()}\n")
    baselines.update(_learned_baselines(env_factory, learn_seeds, args.timesteps))

    board = run_benchmark(spec, baselines)
    print(board.to_markdown())
    print(f"throughput: {steps_per_second(env_factory):,.0f} steps/s/core")


if __name__ == "__main__":
    main()
