#!/usr/bin/env python3
"""The killer demo (M3-EC6): same agent, an *unseen held-out* seed, beats the boss.

Trains an agent on training seeds of the procgen variant, then drops it on a
**held-out** seed (a map + type chart it has never seen) and records the episode to
a GIF. This is the visual proof of the moat — generalization that a fixed-ROM
benchmark structurally cannot show.

NOT part of the CI suite: it needs the ``[rl]`` (stable-baselines3) and ``[render]``
(imageio) extras, and whether the agent actually beats the boss depends on training
quality. The recording pipeline itself is CI-verified (tests/test_demo.py).

Usage:
    pip install -e ".[rl,render]"
    python scripts/killer_demo.py --timesteps 80000 --out killer_demo.gif
"""

from __future__ import annotations

import argparse
import sys
import warnings

import gymnasium as gym

from critter_gym.demo import record_episode, save_demo
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.region import heldout_seeds, train_seeds

CFG = dict(grid_size=6, num_creatures=6, num_gyms=2, max_steps=80, patch_radius=3)


class _SeededReset(gym.Wrapper):
    """Reset cycles through a fixed pool of training seeds."""

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
    parser.add_argument("--timesteps", type=int, default=80_000)
    parser.add_argument("--out", default="killer_demo.gif")
    parser.add_argument("--seed-index", type=int, default=0, help="which held-out seed to demo")
    args = parser.parse_args()

    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
    except ImportError:
        print('This demo needs the [rl] extra:  pip install -e ".[rl,render]"', file=sys.stderr)
        return 2

    warnings.filterwarnings("ignore")

    learn_seeds = tuple(train_seeds(64))

    def make_train_env() -> gym.Env:
        return _SeededReset(CritterEnv(vary=True, **CFG), learn_seeds)  # type: ignore[arg-type]

    print(f"training PPO on {len(learn_seeds)} train seeds ({args.timesteps:,} steps)...")
    model = PPO("MultiInputPolicy", DummyVecEnv([make_train_env]), n_steps=512, seed=0, verbose=0)
    model.learn(args.timesteps)

    # Drop the trained agent on an UNSEEN held-out seed (new map + new type chart).
    demo_seed = list(heldout_seeds(args.seed_index + 1))[args.seed_index]
    env = CritterEnv(vary=True, render_mode="rgb_array", **CFG)  # type: ignore[arg-type]

    def ppo_policy(obs: dict) -> int:
        return int(model.predict(obs, deterministic=True)[0])

    rec = record_episode(env, ppo_policy, demo_seed)
    try:
        save_demo(rec, args.out)
    except ImportError:
        print('  (GIF skipped — install the [render] extra: pip install -e ".[render]")')

    print(
        f"\nheld-out seed {demo_seed} | gyms_defeated={rec.gyms_defeated} "
        f"| boss_defeated={rec.boss_defeated} | frames={len(rec.frames)} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
