"""Does recurrence close the *PPO* headroom under partial observability?
(hard-benchmark/recurrent-ppo)

`recurrent-baseline` (hard-benchmark #1) showed memory is load-bearing *inside A2C* on a
partially observed world (5x5 egocentric view on grid 10): feedforward A2C reached ~18% of
the scripted oracle vs ~46% for a recurrent GRU A2C. But Q1's headroom (`ppo-headroom-rigor`
/ `headroom-baseline-strength`) was measured with the stronger **PPO** — leaving the clean
connection open: *does recurrence close the PPO headroom too?*

This script answers it at **Q1's exact partial-obs config** (`default_env_spec`: grid 10,
a 5x5 view, vary'd type chart, num_types 8 — the same config `ppo_baseline.py --configs
default` uses). It trains a feedforward PPO (`train_ppo`) and a recurrent GRU PPO
(`train_recurrent_ppo`, sequence-preserving env-axis minibatch + hidden replay) and compares
their held-out gym-clears on the SAME matched greedy-eval yardstick (feedforward
`evaluate_gym_clears` / recurrent `evaluate_gym_clears_recurrent` — identical protocol,
only the action selection differs) against the scripted oracle on byte-identical numpy
regions (parity 0).

Pre-registered decision rule (frozen in the plan/qa-checklist BEFORE the run):
  memory is **load-bearing under PPO** iff  rec_mean - ff_mean > max(rec_std, ff_std).
  Additionally, if the recurrent PPO reaches  >= 0.75 * oracle  it **closes** the headroom
  (a headline reframe) — report and stop for a human.

Honest framing: CPU, few runs, one partial-obs config; the recurrent net is *narrower*
(h128) than the feedforward one (h256), so any recurrent gain is from memory, not capacity
(a built-in non-vacuity guard); the oracle is a scripted ceiling *proxy*. This is the PPO
analogue of `recurrent_baseline.py` (A2C). Requires `[jax]` + `[rl]`.

Run: `python scripts/recurrent_ppo_baseline.py [--quick] [--runs N]`.
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import split_train_pool
from critter_gym.jax_train import (
    PPOConfig,
    default_env_spec,
    evaluate_gym_clears,
    evaluate_gym_clears_recurrent,
    learning_verdict,
    train_ppo,
    train_recurrent_ppo,
)
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import heldout_seeds

STEPS = 200  # default-config episode length (Q1 default config)
HEADROOM_FRAC = 0.75  # rec >= 0.75*oracle => headroom CLOSES (reframe; stop for human)


def _oracle(arm: str, seeds) -> float:
    """Mean held-out gym-clears of a scripted reference ``arm`` (numpy commit-v0, num_types 8)."""
    fac = lambda: CritterEnv(commit_battles=True, vary=True, num_types=8)  # noqa: E731
    return float(np.mean([run_episode(fac, reference_arm(arm), s).gyms_cleared
                          for s in seeds]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (small budget)")
    p.add_argument("--runs", type=int, default=3, help="PPO runs per arch (mean +/- std)")
    a = p.parse_args()

    batch = 48
    n_eval = 16
    iters = 60 if a.quick else 250
    hidden_ff, hidden_rec = 256, 128

    spec = default_env_spec(num_types=8)  # Q1 default config: grid10, 5x5 view, partial obs
    learn, _heldin = split_train_pool(tuple(range(batch)), n_eval)
    heldout = tuple(int(s) for s in heldout_seeds(n_eval))

    ff_gc, rec_gc, ff_rise, rec_rise = [], [], [], []
    for r in range(a.runs):
        ff = train_ppo(learn, PPOConfig(batch=len(learn), hidden=hidden_ff, iters=iters),
                       seed=r, spec=spec)
        rec = train_recurrent_ppo(learn, PPOConfig(batch=len(learn), hidden=hidden_rec,
                                                   iters=iters), seed=r, spec=spec)
        ff_gc.append(evaluate_gym_clears(ff.params, heldout, steps=STEPS, spec=spec))
        rec_gc.append(evaluate_gym_clears_recurrent(rec.params, heldout, steps=STEPS,
                                                    spec=spec))
        ff_rise.append(learning_verdict(ff.curve)[0])
        rec_rise.append(learning_verdict(rec.curve)[0])

    oracle = _oracle("oracle", heldout)
    blind = _oracle("type_blind", heldout)
    fm, fs = float(np.mean(ff_gc)), float(np.std(ff_gc))
    rm, rs = float(np.mean(rec_gc)), float(np.std(rec_gc))
    load_bearing = (rm - fm) > max(rs, fs)
    closes = rm >= HEADROOM_FRAC * oracle
    ff_learns = ff_rise.count("a") >= (a.runs + 1) // 2
    rec_learns = rec_rise.count("a") >= (a.runs + 1) // 2

    print("== Does recurrence close the PPO headroom under partial observability? "
          "(recurrent-ppo) ==")
    print(f"   Q1 default config (partial obs): grid 10, 5x5 view, vary num_types 8, "
          f"3 gyms, PPO, runs={a.runs}, iters={iters}")
    print("   pre-registered: load-bearing iff rec_mean - ff_mean > max(std); "
          "rec >= 0.75*oracle => CLOSES (reframe)")
    print(f"  oracle {oracle:.2f}   type_blind {blind:.2f}   "
          f"(0.75*oracle = {HEADROOM_FRAC * oracle:.2f})")
    print(f"  feedforward PPO (h{hidden_ff}) held-out {fm:.2f}+-{fs:.2f}  "
          f"({fm / max(oracle, 1e-9):.0%} of oracle)  learns={ff_learns}")
    print(f"  recurrent   PPO (GRU h{hidden_rec}) held-out {rm:.2f}+-{rs:.2f}  "
          f"({rm / max(oracle, 1e-9):.0%} of oracle)  learns={rec_learns}")
    print(f"  memory effect (rec - ff): {rm - fm:+.2f}   vs max(std) {max(rs, fs):.2f}")
    if closes:
        verdict = "(c) headroom-CLOSES -> recurrence reaches >=0.75*oracle (REFRAME, stop)"
    elif load_bearing:
        verdict = "(a) recurrence-helps-PPO (memory load-bearing under PPO, robust)"
    else:
        verdict = "(b) recurrence-neutral-PPO (no robust memory effect at this PPO budget)"
    print(f"  verdict: {verdict}")
    print("  honest: PPO/CPU/few-run/one partial-obs config; FF net is WIDER (h256>h128) so "
          "gain=memory not capacity; oracle=scripted proxy; matched greedy eval.")


if __name__ == "__main__":
    main()
