"""Is the env hard even for a materially STRONGER memory agent? (hard-benchmark/sota-headroom)

#3 (memory-headroom) measured a recurrent PPO (GRU h128) at ~43% of oracle on the hard config
(grid16, 5x5 view, 5 gyms, 420 steps) and called it hard-and-learnable ROBUST. But #3's
recurrent net was *deliberately narrow* (h128 < feedforward h256, to isolate memory from
capacity), leaving a confound: is the 43% headroom real absolute difficulty, or did we simply
under-power the agent? This script attacks that confound — it scales the recurrent PPO up in
capacity+budget (a pre-registered width x budget sweep) on the SAME config and re-runs the
identical pre-registered `classify_headroom(frac=0.75, k=1.0)` on the BEST non-tiny config.

Pre-registered (frozen in the plan/qa-checklist BEFORE the run):
  - sweep grid: tiny=GRU h128 (=#3), wide=h256, wider=h384; budget base 300 / long 600 iters.
  - best = the non-tiny config with the highest held-out mean (the credible strongest scaled).
  - verdict: classify_scaled_headroom(frac=0.75, k=1.0) with a non-vacuity guard (best > tiny):
      (a) hard-and-learnable -> hard even for the best scaled baseline (STRENGTHENS #3);
      (b) ppo-closes         -> #3's headroom was partly capacity-weakness (REFRAME, stop);
      (c) exceeds oracle     -> scripted oracle isn't a valid ceiling here;
      (!) vacuous            -> best scaled didn't beat tiny (underfit) -> verdict withheld.
  - runs=3 default; escalate to 5 if opt-bound is within +/-0.3 gym of 0.75*oracle (thresholds
    stay frozen).

HONEST framing (read before quoting any number): CPU, few runs, ONE deep config. The "stronger
agent" is still a SCALED recurrent PPO — NOT a larger architecture class, NOT GPU-scale compute,
NOT a SOTA algorithm. A robust result STRENGTHENS the "hard" claim but does NOT prove
SOTA-hardness (that stays OPEN). The oracle is a scripted ceiling proxy; matched greedy eval;
grid16 only. Requires `[jax]` + `[rl]`.

Run: `python scripts/sota_headroom.py [--quick] [--runs N]`. Full budget is CPU-heavy (GRU
hidden-replay is width^2) — run the full sweep in the background.
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import split_train_pool
from critter_gym.headroom import classify_scaled_headroom
from critter_gym.jax_train import (
    PPOConfig,
    evaluate_gym_clears_recurrent,
    hard_env_spec,
    learning_verdict,
    train_recurrent_ppo,
)
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import heldout_seeds

# Must mirror hard_env_spec() exactly (num_creatures matched for parity), as in #3.
GRID, NGYM, NTYPES, NCRE, STEPS = 16, 5, 8, 6, 420
HEADROOM_FRAC = 0.75  # frozen pre-data (qa-checklist)
TINY_LABEL = "tiny GRU h128"


def _oracle(arm: str, seeds) -> float:
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=True, vary=True, num_types=NTYPES, num_gyms=NGYM,
        grid_size=GRID, num_creatures=NCRE, max_steps=STEPS, patch_radius=2, min_gyms=NGYM)
    return float(np.mean([run_episode(fac, reference_arm(arm), s).gyms_cleared
                          for s in seeds]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (small budget/widths)")
    p.add_argument("--runs", type=int, default=3, help="recurrent PPO runs per config (mean+/-std)")
    a = p.parse_args()

    batch, n_eval = 48, 16
    base_iters, long_iters = (40, 60) if a.quick else (300, 600)
    # Pre-registered sweep grid (frozen): tiny=#3 published, wide/wider = scaled capacity+budget.
    # --quick shrinks widths too so the smoke stays cheap; the FULL grid is the frozen one.
    if a.quick:
        grid = [(TINY_LABEL, 128, base_iters), ("wide GRU h192", 192, long_iters)]
    else:
        grid = [(TINY_LABEL, 128, base_iters), ("wide GRU h256", 256, long_iters),
                ("wider GRU h384", 384, long_iters)]

    spec = hard_env_spec()
    learn, _heldin = split_train_pool(tuple(range(batch)), n_eval)
    heldout = tuple(int(s) for s in heldout_seeds(n_eval))

    print("== Is the env hard even for a materially STRONGER memory agent? (sota-headroom) ==")
    print(f"   deep partial-obs config: grid {GRID}, 5x5 view, {NGYM} gyms, {STEPS} steps, "
          f"recurrent PPO, runs={a.runs}")
    print("   pre-registered (frozen before data): sweep {tiny h128 / wide / wider} x "
          f"{{{base_iters},{long_iters}}} iters; best=non-tiny highest held-out mean; "
          "classify_scaled_headroom(frac=0.75,k=1.0) with non-vacuity guard (best>tiny).")

    sweep: dict[str, list[float]] = {}
    learns: dict[str, bool] = {}
    for label, hidden, iters in grid:
        gc, rises = [], []
        for r in range(a.runs):
            res = train_recurrent_ppo(
                learn, PPOConfig(batch=len(learn), hidden=hidden, iters=iters), seed=r, spec=spec)
            gc.append(evaluate_gym_clears_recurrent(res.params, heldout, steps=STEPS, spec=spec))
            rises.append(learning_verdict(res.curve)[0])
        sweep[label] = gc
        learns[label] = rises.count("a") >= (a.runs + 1) // 2

    oracle = _oracle("oracle", heldout)
    blind = _oracle("type_blind", heldout)
    winnable = oracle >= 0.5 * NGYM
    v = classify_scaled_headroom(sweep, oracle, tiny_label=TINY_LABEL, frac=HEADROOM_FRAC, k=1.0)

    if not v.non_vacuous:
        branch = "(!) VACUOUS -> best scaled config did not beat tiny (underfit); verdict withheld"
    elif v.exceeds:
        branch = "(c) EXCEEDS oracle -> scripted oracle is not a valid ceiling for this config"
    elif v.verdict == "hard-and-learnable":
        branch = ("(a) headroom-ROBUST -> hard even for the best SCALED recurrent PPO "
                  "(STRENGTHENS #3; SOTA still OPEN)")
    elif v.verdict == "ppo-closes":
        branch = "(b) headroom-CLOSES -> #3's headroom was partly capacity-weakness (REFRAME, stop)"
    else:
        branch = f"(?) inconclusive ({v.verdict}) -> more runs / budget"

    print(f"  oracle {oracle:.2f}   type_blind {blind:.2f}   "
          f"(0.75*oracle = {HEADROOM_FRAC * oracle:.2f})   winnable={winnable}")
    for label, _h, _i in grid:
        gc = sweep[label]
        m, s = float(np.mean(gc)), float(np.std(gc))
        tag = " <- #3 baseline" if label == TINY_LABEL else ""
        print(f"  {label:>16} held-out {m:.2f}+-{s:.2f}  ({m / max(oracle, 1e-9):.0%} of oracle) "
              f" learns={learns[label]}{tag}")
    print(f"  best scaled = {v.strong_label!r}: mean {v.strong_mean:.2f} "
          f"(opt-bound mean+std {v.strong_mean + v.strong_std:.2f} vs 0.75*oracle "
          f"{HEADROOM_FRAC * oracle:.2f}); non_vacuous={v.non_vacuous} exceeds={v.exceeds}")
    print(f"  #3 h128 vs best scaled: {v.tiny_mean:.2f} -> {v.strong_mean:.2f} "
          f"({(v.strong_mean - v.tiny_mean):+.2f} gyms from scaling)")
    print(f"  verdict: {branch}")
    print("  HONEST: SCALED recurrent PPO (NOT a larger arch class / GPU-scale / SOTA algo); "
          "CPU; few runs; ONE deep config; oracle=scripted proxy; matched greedy eval; grid16 "
          "only. A robust result STRENGTHENS 'hard' but does NOT prove SOTA-hardness (OPEN). "
          "Do NOT headline.")


if __name__ == "__main__":
    main()
