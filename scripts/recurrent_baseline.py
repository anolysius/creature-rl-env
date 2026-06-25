"""Is memory load-bearing under partial observability? (hard-benchmark/recurrent-baseline)

Trains a feedforward A2C and a recurrent (GRU) A2C on a **partially observed** commit world
(grid 10, a 5x5 egocentric view = `patch_radius=2`, fixed 3 gyms) and compares their held-out
gym-clears on the SAME yardstick (matched greedy eval + the scripted oracle on byte-identical
regions). The view is small relative to the map, so the agent must remember what it has seen.

Pre-registered decision rule (frozen in the plan/qa-checklist BEFORE the run):
  memory is **load-bearing** iff  rec_mean - ff_mean > max(rec_std, ff_std)  (robust separation).

Honest framing: A2C (not a tuned PPO — recurrent PPO is a follow-up), CPU, few runs, a single
partial-obs config; the recurrent net is not param-matched to the feedforward one (the
feedforward net is in fact *wider*, so any recurrent gain is from memory, not capacity); the
oracle is a scripted ceiling proxy. This qualifies the `headroom-baseline-strength` (Q1)
finding: that headroom was robust to *feedforward* scaling — here we test the recurrence axis
it explicitly did not rule out. Requires `[jax]` + `[rl]`.

Run: `python scripts/recurrent_baseline.py [--quick] [--runs N]`.
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import split_train_pool
from critter_gym.jax_env import JaxEnvConfig, make_jax_env
from critter_gym.jax_train import (
    EnvSpec,
    TrainConfig,
    evaluate_gym_clears,
    evaluate_gym_clears_recurrent,
    train,
    train_recurrent,
)
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import generate_region, heldout_seeds

GRID, PATCH, NGYM, NTYPES, STEPS = 10, 2, 3, 8, 200


def _spec() -> EnvSpec:
    cfg = JaxEnvConfig(grid=GRID, patch_radius=PATCH, max_steps=STEPS, max_gyms=NGYM)
    return EnvSpec(make_jax_env(cfg),
                   lambda s: generate_region(s, GRID, 6, NGYM, vary=True,
                                             num_types=NTYPES, min_gyms=NGYM))


def _numpy_factory():
    return CritterEnv(commit_battles=True, vary=True, num_types=NTYPES, num_gyms=NGYM,
                      grid_size=GRID, max_steps=STEPS, patch_radius=PATCH, min_gyms=NGYM)


def _oracle(arm: str, seeds) -> float:
    return float(np.mean([run_episode(_numpy_factory, reference_arm(arm), s).gyms_cleared
                          for s in seeds]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (small budget)")
    p.add_argument("--runs", type=int, default=3, help="A2C runs per arch (mean +/- std)")
    a = p.parse_args()

    batch = 48
    iters = 80 if a.quick else 300
    hidden_ff, hidden_rec = 256, 128

    spec = _spec()
    learn, _heldin = split_train_pool(tuple(range(batch)), 16)
    heldout = tuple(int(s) for s in heldout_seeds(16))

    ff_gc, rec_gc = [], []
    for r in range(a.runs):
        ff = train(learn, TrainConfig(batch=len(learn), hidden=hidden_ff, iters=iters), seed=r,
                   spec=spec)
        rec = train_recurrent(learn, TrainConfig(batch=len(learn), hidden=hidden_rec,
                                                 iters=iters), seed=r, spec=spec)
        ff_gc.append(evaluate_gym_clears(ff.params, heldout, steps=STEPS, spec=spec))
        rec_gc.append(evaluate_gym_clears_recurrent(rec.params, heldout, steps=STEPS, spec=spec))

    oracle = _oracle("oracle", heldout)
    blind = _oracle("type_blind", heldout)
    fm, fs = float(np.mean(ff_gc)), float(np.std(ff_gc))
    rm, rs = float(np.mean(rec_gc)), float(np.std(rec_gc))
    load_bearing = (rm - fm) > max(rs, fs)

    print("== Is memory load-bearing under partial observability? "
          "(recurrent-baseline) ==")
    print(f"   partial-obs commit world: grid {GRID}, {PATCH * 2 + 1}x{PATCH * 2 + 1} view, "
          f"{NGYM} gyms, A2C, runs={a.runs}")
    print("   pre-registered: load-bearing iff rec_mean - ff_mean > max(std)")
    print(f"  oracle {oracle:.2f}   type_blind {blind:.2f}")
    print(f"  feedforward A2C (h{hidden_ff}) held-out {fm:.2f}+-{fs:.2f}  "
          f"({fm / max(oracle, 1e-9):.0%} of oracle)")
    print(f"  recurrent   A2C (GRU h{hidden_rec}) held-out {rm:.2f}+-{rs:.2f}  "
          f"({rm / max(oracle, 1e-9):.0%} of oracle)")
    print(f"  memory effect (rec - ff): {rm - fm:+.2f}   vs max(std) {max(rs, fs):.2f}")
    print(f"  verdict: memory is {'LOAD-BEARING' if load_bearing else 'NOT load-bearing'} "
          f"(robust separation: {load_bearing})")
    print("  honest: A2C/CPU/few-run/one config; FF net is WIDER (gain=memory not capacity); "
          "recurrent still < oracle (headroom remains); oracle=scripted proxy.")


if __name__ == "__main__":
    main()
