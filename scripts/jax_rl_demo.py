#!/usr/bin/env python3
"""RL learning demo on the JAX vectorized env — "speed is real", made visible (M4).

Trains the JAX-native A2C loop (``critter_gym.jax_train``) once on the vmap-batched
family-A commit-mode env, then prints **(1)** a learning curve (mean reward-per-env-step
per iteration, with the pre-registered learn/no-learn verdict) and **(2)** the training
throughput vs the *existing* numpy/sb3 path the repo uses (``scripts/learnability.py`` —
a single ``DummyVecEnv``). Optionally evaluates the trained policy on **held-out seeds**
(disjoint from training) to tie the speed demo to the generalization story.

**Honest framing (do not headline a single number):** this is a *demo / signal*, not a
tuned benchmark — single run, CPU, A2C-lite, the learning metric is reward-per-step (a
clean monotone proxy for episode return). "Faster" is the measured inequality
(vmap-rollout steps/s > sb3-collection steps/s); the win is from on-device ``vmap``
lock-step, consistent with ``bench_throughput.py``. The numpy baseline is the repo's
*existing* single-env sb3 path; many parallel sb3 processes would narrow the ratio but
stay below on-device vmap. GPU is out of scope (CPU here already shows the effect).

Run: ``pip install -e ".[jax,rl]"`` then ``python scripts/jax_rl_demo.py``
(``--quick`` for a fast smoke; ``--no-sb3`` to skip the slow baseline).
"""
from __future__ import annotations

import argparse
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iters", type=int, default=150)
    parser.add_argument("--batch", type=int, default=256)
    parser.add_argument("--quick", action="store_true", help="fast smoke (small sizes)")
    parser.add_argument("--no-sb3", action="store_true", help="skip the numpy/sb3 baseline")
    parser.add_argument("--no-eval", action="store_true", help="skip held-out eval")
    args = parser.parse_args()

    try:
        from critter_gym import jax_train
    except ImportError:
        print('This demo needs the [jax] extra:  pip install -e ".[jax]"', file=sys.stderr)
        return 2

    iters = 20 if args.quick else args.iters
    batch = 64 if args.quick else args.batch
    cfg = jax_train.TrainConfig(batch=batch, iters=iters)
    train_seeds = tuple(range(batch))

    print("== CritterGym JAX-native RL demo (CPU, single run — a signal, not a headline) ==")
    print(f"   family A commit-mode | batch(vmap)={batch} | rollout={cfg.rollout_len} "
          f"| iters={iters}\n")

    result = jax_train.train(train_seeds, cfg, seed=0)

    # (1) learning curve
    print("-- learning curve (mean reward / env-step) --")
    every = max(1, iters // 10)
    for i, r in enumerate(result.curve):
        if i % every == 0 or i == iters - 1:
            print(f"   iter {i:4d}   reward/step={r:.4f}   ep_return~={r * 200:.2f}")
    branch, rise, std_late = jax_train.learning_verdict(result.curve)
    early = sum(result.curve[: max(1, iters // 5)]) / max(1, iters // 5)
    late = sum(result.curve[-max(1, iters // 5):]) / max(1, iters // 5)
    verdict = ("LEARNS (rise clears late-window noise) — branch (a)"
               if branch == "a" else
               "no clear rise vs noise — branch (b): report throughput, learning=partial")
    print(f"\n   pre-registered R1 rule: rise={rise:.4f}  vs  std_late={std_late:.4f}")
    print(f"   verdict: {verdict}")
    print(f"   ep_return~  early={early * 200:.2f} -> late={late * 200:.2f}")

    # (2) throughput
    print("\n-- training throughput --")
    print(f"   jax vmap training-rollout : {result.env_steps_per_s:>14,.0f} env-steps/s "
          f"({result.total_env_steps:,} steps / {result.wall_time_s:.2f}s)")
    if not args.no_sb3:
        sps = _bench_sb3_collection(batch, n_steps=2048 if args.quick else 4096)
        if sps is not None:
            faster = result.env_steps_per_s > sps
            print(f"   numpy sb3 collection (repo): {sps:>14,.0f} env-steps/s "
                  "(single DummyVecEnv, the existing path)")
            print(f"   -> {'FASTER' if faster else 'NOT faster'} "
                  f"({result.env_steps_per_s / sps:.0f}x)  "
                  "[win = on-device vmap lock-step; CPU; single run]")

    # held-out eval (seed split: train 0..batch-1, eval held-out pool)
    if not args.no_eval:
        from critter_gym.region import heldout_seeds
        n_eval = 8 if args.quick else 16
        heldout = tuple(int(s) for s in heldout_seeds(n_eval))
        held = jax_train.evaluate(result.params, heldout)
        seen = jax_train.evaluate(result.params, train_seeds[:n_eval])
        print("\n-- generalization (greedy policy, episode return) --")
        print(f"   held-in (train seeds) : {seen:.2f}")
        print(f"   held-out (unseen seeds): {held:.2f}   "
              "[seed split; a signal, single run/N modest]")

    print("\n   Honest read: a JAX-native loop trains family A on CPU in seconds; the speed")
    print("   is real (on-device vmap), the learning is a signal (A2C-lite, single run).")
    return 0


def _bench_sb3_collection(n_envs_seeds: int, n_steps: int) -> float | None:
    """Throughput of the repo's existing numpy/sb3 training path (single DummyVecEnv)."""
    try:
        import warnings
        warnings.filterwarnings("ignore")
        import gymnasium as gym
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv

        from critter_gym.envs.critter_env import CritterEnv
    except ImportError:
        print("   (sb3 not installed — skip baseline; `pip install -e \".[rl]\"`)")
        return None

    class _Seeded(gym.Wrapper):  # type: ignore[type-arg]
        def __init__(self, env: gym.Env, seeds: tuple[int, ...]) -> None:
            super().__init__(env)
            self._seeds = seeds
            self._i = 0

        def reset(self, *, seed=None, options=None):  # type: ignore[no-untyped-def]
            s = self._seeds[self._i % len(self._seeds)]
            self._i += 1
            return self.env.reset(seed=s, options=options)

    def mk() -> gym.Env:
        return _Seeded(
            CritterEnv(commit_battles=True, vary=True, num_types=8),
            tuple(range(n_envs_seeds)),
        )

    model = PPO("MultiInputPolicy", DummyVecEnv([mk]), n_steps=512, verbose=0, seed=0)
    start = time.perf_counter()
    model.learn(n_steps, progress_bar=False)
    return n_steps / (time.perf_counter() - start)


if __name__ == "__main__":
    raise SystemExit(main())
