"""PPO baseline + oracle-headroom report (jax-ppo-tuned, KR1).

Trains the **tuned PPO** (`critter_gym.jax_train.train_ppo`: GAE(λ) + clipped surrogate +
minibatch epochs) on two commit-mode configs — the default world and the high-gym
*dynamic-range* hard config — and reports, on held-out seeds, how close the learned policy
gets to a **scripted oracle ceiling** (the *headroom* that makes the benchmark a hard one).

Pre-registered decision rules (frozen in the plan/qa-checklist BEFORE this was run):
  R1 (learns): `learning_verdict` — late-window mean clears early by > late-window noise.
  R2 (PPO >= A2C): tuned PPO held-out return >= the A2C-lite return at equal budget.
  R3 (headroom): on held-out gym-clears, PPO <= 0.75 * oracle  -> "hard-and-learnable";
                 PPO >= 0.75 * oracle  -> "PPO nearly closes it (less hard)" (reframe).

Honest framing: CPU, single (or few) run, a tiny shared-trunk MLP — a *baseline and a
signal*, not a SOTA sweep. The oracle is a scripted ceiling *proxy* (it sees gym positions
+ the per-seed chart), so "headroom" is measured against that proxy, not a true optimum.
The PPO (JAX) and oracle (numpy) run on byte-identical regions (parity 0), so their
gym-clear means are on the same yardstick. Requires `[jax]` + `[rl]`.

Run: `python scripts/ppo_baseline.py [--quick] [--runs N]`.
"""

from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import split_train_pool
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import heldout_seeds

HEADROOM_FRAC = 0.75  # R3: PPO < 0.75*oracle => headroom (frozen pre-data, qa-checklist)


def _oracle_gym_clears(env_factory, arm: str, seeds) -> float:
    """Mean held-out gym-clears of a scripted reference ``arm`` (numpy commit-v0)."""
    outs = [run_episode(env_factory, reference_arm(arm), s).gyms_cleared for s in seeds]
    return float(np.mean(outs)) if outs else float("nan")


def _config(name: str):
    """(EnvSpec, numpy CritterEnv factory [same regions], eval steps, num_gyms)."""
    from critter_gym.jax_train import default_env_spec, difficulty_env_spec

    if name == "default":
        spec = default_env_spec(num_types=8)
        factory = lambda: CritterEnv(commit_battles=True, vary=True, num_types=8)  # noqa: E731
        return spec, factory, 200, 3
    if name == "hard":
        spec = difficulty_env_spec()  # grid6, 8 gyms, num_types12, super_mult3, boss150/16
        factory = lambda: CritterEnv(  # noqa: E731
            commit_battles=True, vary=True, num_types=12, super_mult=3.0, num_gyms=8,
            grid_size=6, max_steps=160, patch_radius=5, boss_hp=150, boss_atk=16,
            min_gyms=8,
        )
        return spec, factory, 160, 8
    raise ValueError(name)


def _run_config(name: str, *, batch: int, n_eval: int, iters: int, runs: int) -> None:
    from critter_gym.jax_train import (
        PPOConfig,
        TrainConfig,
        evaluate,
        evaluate_gym_clears,
        learning_verdict,
        train,
        train_ppo,
    )

    spec, factory, steps, num_gyms = _config(name)
    pool = tuple(range(batch))
    learn, heldin = split_train_pool(pool, n_eval)
    heldout = tuple(int(s) for s in heldout_seeds(n_eval))
    pcfg = PPOConfig(batch=len(learn), iters=iters)
    acfg = TrainConfig(batch=len(learn), iters=iters)

    ppo_out_gc, ppo_in_gc, ppo_out_ret, a2c_out_ret, rises = [], [], [], [], []
    for r in range(runs):
        ppo = train_ppo(learn, pcfg, seed=r, spec=spec)
        a2c = train(learn, acfg, seed=r, spec=spec)
        ppo_out_gc.append(evaluate_gym_clears(ppo.params, heldout, steps=steps, spec=spec))
        ppo_in_gc.append(evaluate_gym_clears(ppo.params, heldin, steps=steps, spec=spec))
        ppo_out_ret.append(evaluate(ppo.params, heldout, steps=steps, spec=spec))
        a2c_out_ret.append(evaluate(a2c.params, heldout, steps=steps, spec=spec))
        rises.append(learning_verdict(ppo.curve)[1])
    oracle_gc = _oracle_gym_clears(factory, "oracle", heldout)
    blind_gc = _oracle_gym_clears(factory, "type_blind", heldout)

    p_out = float(np.mean(ppo_out_gc))
    p_in = float(np.mean(ppo_in_gc))
    p_ret = float(np.mean(ppo_out_ret))
    a_ret = float(np.mean(a2c_out_ret))
    gap = p_in - p_out
    headroom = oracle_gc - p_out
    r1_branch = "a" if float(np.mean(rises)) > 0 else "b"
    r2 = "PPO>=A2C" if p_ret >= a_ret else "PPO<A2C (no-improve)"
    r3 = ("hard-and-learnable" if p_out <= HEADROOM_FRAC * oracle_gc
          else "PPO nearly closes (reframe)")

    pm = (lambda xs: f"{np.mean(xs):.2f}±{np.std(xs):.2f}") if runs > 1 else (
        lambda xs: f"{np.mean(xs):.2f}")
    pct = p_out / max(oracle_gc, 1e-9)
    print(f"\n== {name} config (commit-mode, {num_gyms} gyms, CPU, runs={runs}) ==")
    print(f"  PPO held-out gym-clears  {pm(ppo_out_gc)}"
          f"   (held-in {pm(ppo_in_gc)}, gap {gap:+.2f})")
    print(f"  PPO held-out return      {pm(ppo_out_ret)}"
          f"   vs A2C-lite {pm(a2c_out_ret)}  -> {r2}")
    print(f"  oracle gym-clears        {oracle_gc:.2f}   type_blind {blind_gc:.2f}")
    print(f"  headroom (oracle - PPO)  {headroom:+.2f}"
          f"   ({p_out:.2f} = {pct:.0%} of oracle)")
    print(f"  R1 learn={r1_branch}  R2 {r2}  R3 {r3}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="fast smoke (small budget)")
    parser.add_argument("--runs", type=int, default=1, help="PPO/A2C runs to average")
    parser.add_argument("--configs", nargs="+", default=["default", "hard"])
    args = parser.parse_args()

    batch = 96 if args.quick else 192
    n_eval = 16 if args.quick else 32
    iters = 60 if args.quick else 200

    print("== PPO baseline + oracle-headroom (a baseline/signal, not a SOTA sweep) ==")
    print("   pre-registered: R1 learns / R2 PPO>=A2C / R3 PPO<0.75*oracle => headroom")
    for name in args.configs:
        _run_config(name, batch=batch, n_eval=n_eval, iters=iters, runs=args.runs)


if __name__ == "__main__":
    main()
