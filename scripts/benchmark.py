#!/usr/bin/env python3
"""Human-readable benchmark report: a 4-baseline train+test score table + throughput.

Builds the M3-EC1 baseline score table via :mod:`critter_gym.scoreboard` on the
**procgen** variant (``vary=True``): each seed is a new map + a new type chart, and
held-in (training-region) vs held-out (test-region) scores are reported per
baseline alongside the generalization gap.

The core baselines (``random``, ``scripted``) need only numpy and always run. The
learned baselines (``ppo``, ``recurrent``) need the ``[rl]`` extra
(stable-baselines3 + sb3-contrib); if it is not installed they are skipped and the
core 2-row table is printed (non-fatal).

Usage:
    python scripts/benchmark.py                       # core baselines only
    pip install -e ".[rl]" && python scripts/benchmark.py --timesteps 20000
    python scripts/benchmark.py --train 64 --heldout 32
"""

from __future__ import annotations

import argparse
import time

import gymnasium as gym
import numpy as np

from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import PolicyFn
from critter_gym.region import heldout_seeds, train_seeds
from critter_gym.scoreboard import score_baselines

CFG = dict(grid_size=5, num_creatures=8, num_gyms=2, max_steps=50, patch_radius=4)


def make_env() -> CritterEnv:
    return CritterEnv(vary=True, **CFG)  # type: ignore[arg-type]


class _SeededReset(gym.Wrapper):
    """Reset cycles through a fixed pool of seeds (the learn pool, kept disjoint
    from the held-in eval set so the measured gap stays honest)."""

    def __init__(self, env: gym.Env, seeds: tuple[int, ...]) -> None:
        super().__init__(env)
        self._seeds = tuple(int(s) for s in seeds)
        self._i = 0

    def reset(self, *, seed=None, options=None):  # type: ignore[no-untyped-def]
        s = self._seeds[self._i % len(self._seeds)]
        self._i += 1
        return self.env.reset(seed=s, options=options)


def steps_per_second(min_steps: int = 50_000) -> float:
    env = make_env()
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
    learn_seeds: tuple[int, ...], timesteps: int
) -> dict[str, PolicyFn]:
    """Train PPO + recurrent PPO on the learn pool; return them as policies.

    Returns an empty dict (with a printed notice) if the ``[rl]`` extra is absent,
    so the report degrades to the core baselines instead of crashing.
    """
    try:
        from sb3_contrib import RecurrentPPO
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
    except ImportError:
        print('  (ppo/recurrent skipped — install the [rl] extra: pip install -e ".[rl]")\n')
        return {}

    def make_train_env() -> gym.Env:
        return _SeededReset(make_env(), learn_seeds)

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
    parser.add_argument("--train", type=int, default=64, help="training seed pool size")
    parser.add_argument("--heldout", type=int, default=32, help="held-out eval seed count")
    parser.add_argument("--timesteps", type=int, default=20_000, help="per learned baseline")
    args = parser.parse_args()

    n_eval = max(1, args.train // 4)
    pool = tuple(train_seeds(args.train))
    learn_seeds, heldin = pool[:-n_eval], pool[-n_eval:]
    heldout = tuple(heldout_seeds(args.heldout))

    rng = np.random.default_rng(0)
    baselines: dict[str, PolicyFn] = {
        "random": lambda o: random_policy(o, rng),
        "scripted": lambda o: greedy_policy(o, grid_size=int(CFG["grid_size"])),
    }
    print(
        f"CritterGym benchmark — procgen (vary=True) | "
        f"held-in={len(heldin)} held-out={len(heldout)}\n"
    )
    baselines.update(_learned_baselines(learn_seeds, args.timesteps))

    table = score_baselines(make_env, baselines, heldin, heldout)
    print(table.to_markdown())
    print(f"throughput: {steps_per_second():,.0f} steps/s/core")


if __name__ == "__main__":
    main()
