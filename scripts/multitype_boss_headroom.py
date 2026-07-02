"""Is the hidden multi-type boss ROBUSTLY deeper? (hard-benchmark/multitype-boss-headroom)

The #4 scout gave a 1-seed signal (oracle-fraction 28% single vs 24% multi, Delta +3.4pp) that a
hidden secondary boss type deepens difficulty. This script is the **pre-registered multi-seed
measurement** — two questions, rules FROZEN in the plan/qa-checklist BEFORE the data:

  (A) Absolute: is the multi-type config hard even for the strongest agent (recurrent PPO)?
      `classify_headroom(rec_multi_runs, oracle_multi, frac=0.75, k=1.0)` (same thresholds as #3):
        hard-and-learnable -> (a) hard-for-memory-agent ROBUST
        ppo-closes         -> (b) closes (reframe; stop for human)
        else               -> inconclusive (more seeds, thresholds unchanged)
  (B) Relative depth: is multi-type robustly deeper than single-type? Per-run ORACLE FRACTIONS
      (normalized — the two configs have different oracle ceilings), then `classify_depth`:
        deeper-robust  : mean(single) - mean(multi) > max(std) AND both winnable
        not-deeper     : gap <= 0 (the scout signal is refuted; reported as-is)
        inconclusive   : otherwise

Honest framing: CPU, few runs, recurrent PPO (a real baseline, not SOTA), ONE deep config
(grid16), scripted-oracle ceiling proxy. Whatever branch comes out is reported as-is.

Run: `python scripts/multitype_boss_headroom.py [--quick] [--runs N]`. Requires `[jax]` + `[rl]`.
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import split_train_pool
from critter_gym.headroom import classify_depth, classify_headroom
from critter_gym.jax_train import (
    PPOConfig,
    evaluate_gym_clears_recurrent,
    hard_env_spec,
    learning_verdict,
    multitype_hard_env_spec,
    train_recurrent_ppo,
)
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import heldout_seeds

# Must mirror hard_env_spec()/multitype_hard_env_spec() exactly (parity-gated configs).
GRID, NGYM, NTYPES, NCRE, STEPS, PR = 16, 5, 8, 6, 420, 2
HEADROOM_FRAC, HEADROOM_K = 0.75, 1.0  # frozen pre-data (plan / qa-checklist AC2)


def _oracle(seeds, *, boss_secondary: bool) -> float:
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=True, vary=True, num_types=NTYPES, num_gyms=NGYM, grid_size=GRID,
        num_creatures=NCRE, max_steps=STEPS, patch_radius=PR, min_gyms=NGYM,
        boss_secondary=boss_secondary)
    return float(np.mean([run_episode(fac, reference_arm("oracle"), s).gyms_cleared
                          for s in seeds]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast pilot smoke (small budget)")
    p.add_argument("--runs", type=int, default=3, help="recurrent-PPO runs per config")
    a = p.parse_args()

    batch, n_eval = 48, 16
    iters = 60 if a.quick else 250
    hidden = 128

    # Print the FROZEN rules BEFORE any data is computed (pre-registration discipline).
    print("== Is the hidden multi-type boss ROBUSTLY deeper? (multitype-boss-headroom) ==")
    print(f"   config: grid {GRID}, 5x5 view, {NGYM} gyms, {STEPS} steps; "
          f"recurrent PPO GRU h{hidden}, runs={a.runs}, iters={iters}, CPU")
    print(f"   pre-registered (frozen before data): (A) classify_headroom(frac={HEADROOM_FRAC}, "
          f"k={HEADROOM_K}) on multi-type recurrent PPO;")
    print("   (B) classify_depth on per-run oracle fractions: deeper-robust iff "
          "mean(single)-mean(multi) > max(std) AND both winnable; not-deeper iff gap <= 0.")

    learn, _heldin = split_train_pool(tuple(range(batch)), n_eval)
    heldout = tuple(int(s) for s in heldout_seeds(n_eval))

    oracle_single = _oracle(heldout, boss_secondary=False)
    oracle_multi = _oracle(heldout, boss_secondary=True)
    win_single = oracle_single >= 0.5 * NGYM
    win_multi = oracle_multi >= 0.5 * NGYM

    spec_single, spec_multi = hard_env_spec(), multitype_hard_env_spec()
    gc_single, gc_multi, rises = [], [], []
    for r in range(a.runs):
        cfg = PPOConfig(batch=len(learn), hidden=hidden, iters=iters)
        rs = train_recurrent_ppo(learn, cfg, seed=r, spec=spec_single)
        rm = train_recurrent_ppo(learn, cfg, seed=r, spec=spec_multi)
        gc_single.append(evaluate_gym_clears_recurrent(rs.params, heldout, steps=STEPS,
                                                       spec=spec_single))
        gc_multi.append(evaluate_gym_clears_recurrent(rm.params, heldout, steps=STEPS,
                                                      spec=spec_multi))
        rises.append((learning_verdict(rs.curve)[0], learning_verdict(rm.curve)[0]))
        print(f"  run {r}: single {gc_single[-1]:.2f}  multi {gc_multi[-1]:.2f}  "
              f"learns={rises[-1]}")

    frac_single = [g / max(oracle_single, 1e-9) for g in gc_single]
    frac_multi = [g / max(oracle_multi, 1e-9) for g in gc_multi]

    hv = classify_headroom(gc_multi, oracle_multi, frac=HEADROOM_FRAC, k=HEADROOM_K)
    dv = classify_depth(frac_single, frac_multi,
                        single_winnable=win_single, multi_winnable=win_multi)

    if hv.verdict == "hard-and-learnable":
        branch_a = "(a) hard-for-memory-agent ROBUST on the multi-type config"
    elif hv.verdict == "ppo-closes":
        branch_a = "(b) memory-CLOSES on multi-type (REFRAME, stop for human)"
    else:
        branch_a = "(?) inconclusive -> more seeds (thresholds unchanged)"

    print(f"\n  oracle: single {oracle_single:.2f} (winnable={win_single})   "
          f"multi {oracle_multi:.2f} (winnable={win_multi})")
    print(f"  recurrent PPO held-out gym-clears: single {np.mean(gc_single):.2f}"
          f"+-{np.std(gc_single):.2f}   multi {np.mean(gc_multi):.2f}+-{np.std(gc_multi):.2f}")
    print(f"  oracle fractions: single {dv.single_mean:.0%}+-{dv.single_std:.0%}   "
          f"multi {dv.multi_mean:.0%}+-{dv.multi_std:.0%}   gap {dv.gap * 100:+.1f}pp")
    print(f"  (A) headroom on multi: mean+std {hv.ppo_mean + hv.ppo_std:.2f} vs "
          f"{HEADROOM_FRAC}*oracle {HEADROOM_FRAC * oracle_multi:.2f} -> {branch_a}")
    print(f"  (B) depth: {dv.verdict}")
    print("  honest: CPU / few runs / recurrent PPO (not SOTA) / grid16 only / oracle = "
          "scripted proxy; thresholds frozen pre-data; whatever branch, reported as-is.")


if __name__ == "__main__":
    main()
