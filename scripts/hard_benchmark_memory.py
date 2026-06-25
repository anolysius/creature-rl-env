"""Is the env hard *even for a strong memory agent*? (hard-benchmark/memory-headroom)

#1/#2 showed memory is load-bearing under partial observability and that recurrence
recovers part of the oracle headroom (at the grid-10 sweet spot a recurrent PPO reaches
~53% of oracle — so that config is *half-solved* by a memory agent). This script goes
**deeper** — a bigger map + longer horizon under the same 5x5 egocentric view (grid 16,
5 gyms, 420 steps; `jax_train.hard_env_spec`) — and asks whether the **strongest agent we
have (recurrent PPO)** still faces large oracle headroom there, i.e. whether the env is
hard not just for memoryless agents but for a *memory* agent too (absolute difficulty).

It reports feedforward PPO, recurrent PPO, and the scripted oracle on the SAME matched
greedy-eval yardstick (parity 0 vs numpy `CritterEnv` is gated by
`tests/test_jax_hard_config_parity.py`, so oracle and agent share the env).

Pre-registered decision rule (frozen in the plan/qa-checklist BEFORE the run): apply
`headroom.classify_headroom(frac=0.75, k=1.0)` (thresholds fixed before data) to the
**recurrent PPO** held-out gym-clears:
  hard-and-learnable (mean+std <= 0.75*oracle) -> (a) hard-for-memory-agent (PASS);
  ppo-closes      (mean-std >= 0.75*oracle) -> (b) memory-closes (reframe; stop for human);
  inconclusive                               -> need more seeds / config tweak.
Secondary (a footnote, not the conclusion): rec_mean > ff_mean => memory still helps.

Honest framing: CPU, few runs, ONE deep partial-obs config; the "strong agent" is a
recurrent PPO (a real baseline, not SOTA); the oracle is a scripted ceiling proxy; the
recurrent net is deliberately *narrower* than the feedforward one (h128 < h256), so a
recurrent gain is memory not capacity. Requires `[jax]` + `[rl]`.

Run: `python scripts/hard_benchmark_memory.py [--quick] [--runs N]`.
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import split_train_pool
from critter_gym.headroom import classify_headroom
from critter_gym.jax_train import (
    PPOConfig,
    evaluate_gym_clears,
    evaluate_gym_clears_recurrent,
    hard_env_spec,
    learning_verdict,
    train_ppo,
    train_recurrent_ppo,
)
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import heldout_seeds

# Must mirror hard_env_spec() exactly (num_creatures matched for parity).
GRID, NGYM, NTYPES, NCRE, STEPS = 16, 5, 8, 6, 420
HEADROOM_FRAC = 0.75  # frozen pre-data (qa-checklist AC3)


def _oracle(arm: str, seeds) -> float:
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=True, vary=True, num_types=NTYPES, num_gyms=NGYM,
        grid_size=GRID, num_creatures=NCRE, max_steps=STEPS, patch_radius=2, min_gyms=NGYM)
    return float(np.mean([run_episode(fac, reference_arm(arm), s).gyms_cleared
                          for s in seeds]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (small budget)")
    p.add_argument("--runs", type=int, default=3, help="PPO runs per arch (mean +/- std)")
    a = p.parse_args()

    batch, n_eval = 48, 16
    iters = 80 if a.quick else 300
    hidden_ff, hidden_rec = 256, 128

    spec = hard_env_spec()
    learn, _heldin = split_train_pool(tuple(range(batch)), n_eval)
    heldout = tuple(int(s) for s in heldout_seeds(n_eval))

    ff_gc, rec_gc, rec_rise = [], [], []
    for r in range(a.runs):
        ff = train_ppo(learn, PPOConfig(batch=len(learn), hidden=hidden_ff, iters=iters),
                       seed=r, spec=spec)
        rec = train_recurrent_ppo(learn, PPOConfig(batch=len(learn), hidden=hidden_rec,
                                                   iters=iters), seed=r, spec=spec)
        ff_gc.append(evaluate_gym_clears(ff.params, heldout, steps=STEPS, spec=spec))
        rec_gc.append(evaluate_gym_clears_recurrent(rec.params, heldout, steps=STEPS,
                                                    spec=spec))
        rec_rise.append(learning_verdict(rec.curve)[0])

    oracle = _oracle("oracle", heldout)
    blind = _oracle("type_blind", heldout)
    fm, fs = float(np.mean(ff_gc)), float(np.std(ff_gc))
    rm, rs = float(np.mean(rec_gc)), float(np.std(rec_gc))
    rec_learns = rec_rise.count("a") >= (a.runs + 1) // 2
    winnable = oracle >= 0.5 * NGYM

    hv = classify_headroom(rec_gc, oracle, frac=HEADROOM_FRAC, k=1.0)
    if hv.verdict == "hard-and-learnable":
        branch = "(a) hard-for-memory-agent ROBUST -> large oracle headroom even for recurrent PPO"
    elif hv.verdict == "ppo-closes":
        branch = "(b) memory-CLOSES -> not hard for the memory agent here (REFRAME, stop)"
    else:
        branch = f"(?) inconclusive ({hv.verdict}) -> more seeds / config tweak"

    print("== Is the env hard even for a strong MEMORY agent? (memory-headroom) ==")
    print(f"   deep partial-obs config: grid {GRID}, 5x5 view, {NGYM} gyms, {STEPS} steps, "
          f"PPO, runs={a.runs}, iters={iters}")
    print("   pre-registered (frozen): classify_headroom(frac=0.75,k=1.0) on recurrent PPO")
    print(f"  oracle {oracle:.2f}   type_blind {blind:.2f}   "
          f"(0.75*oracle = {HEADROOM_FRAC * oracle:.2f})   winnable={winnable}")
    print(f"  feedforward PPO (h{hidden_ff}) held-out {fm:.2f}+-{fs:.2f}  "
          f"({fm / max(oracle, 1e-9):.0%} of oracle)")
    print(f"  recurrent   PPO (GRU h{hidden_rec}) held-out {rm:.2f}+-{rs:.2f}  "
          f"({rm / max(oracle, 1e-9):.0%} of oracle)  learns={rec_learns}")
    print(f"  recurrent opt-bound mean+std {rm + rs:.2f}  vs  0.75*oracle "
          f"{HEADROOM_FRAC * oracle:.2f}")
    print(f"  secondary (memory still helps?): rec-ff {rm - fm:+.2f}")
    print(f"  verdict: {branch}")
    print("  honest: PPO(not SOTA)/CPU/few-run/ONE deep config; oracle=scripted proxy; "
          "recurrent net narrower (h128<h256) so gain=memory; matched greedy eval; grid16 only.")


if __name__ == "__main__":
    main()
