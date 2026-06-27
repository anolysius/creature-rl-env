"""Demo: the sealed held-out eval harness (eval-product/sealed-eval-harness).

Shows the M5 contamination-proof eval *mechanism* end-to-end:
  1. An evaluator registers a SEALED eval set (a private block of held-out worlds chosen by a
     secret master_seed — the submitter never sees these seeds).
  2. Submitters (here: scripted oracle / type_blind / a random agent) are scored with
     verifiable subgoals only (gym-clears, catch, evolve) + their fraction of the oracle.
  3. The contamination guard verifies a submitter could NOT have trained on the sealed eval —
     and catches a leak attempt.

Honest scope: a prototype. "Sealed" is an in-process convention (the secret lives in the
object); a real product needs server-side secret seeds + a submission sandbox. numpy
CritterEnv (commit-v0), one config, single machine. This is the mechanism, not a service.

Run: `python scripts/eval_harness_demo.py`.
"""
from __future__ import annotations

import numpy as np

from critter_gym.eval_harness import SealedEvalSet, score_agent, verify_sealed
from critter_gym.learnability import reference_arm


class RandomAgent:
    """A trivial obs-only submission: act(obs) -> action (the Agent interface)."""

    def __init__(self, seed: int = 0) -> None:
        self._rng = np.random.default_rng(seed)

    def act(self, obs: object) -> int:
        return int(self._rng.integers(0, 6))


def main() -> None:
    # 1. Evaluator registers a sealed eval set (secret master_seed -> private held-out block).
    sealed = SealedEvalSet(master_seed=20260626, n_worlds=16, num_types=8)

    print("== Sealed held-out eval (contamination-proof, prototype) ==")
    print(f"  sealed set: {sealed.n_worlds} private held-out worlds "
          f"(master_seed={sealed.master_seed}, num_types={sealed.num_types})")
    print("  (the submitter never sees these seeds; a new master_seed regenerates a fresh set)")

    # 2. Score submissions on the SAME sealed worlds (verifiable subgoals only).
    submissions = {
        "oracle (scripted ref)": reference_arm("oracle"),
        "type_blind (scripted ref)": reference_arm("type_blind"),
        "random agent (act(obs))": RandomAgent(seed=0),
    }
    print("\n  submission                     gyms   cleared%  caught%  evolved%  of-oracle")
    for name, sub in submissions.items():
        c = score_agent(sub, sealed)
        print(f"  {name:<30} {c.mean_gyms_cleared:>5.2f}   "
              f"{c.cleared_rate:>6.0%}  {c.caught_rate:>6.0%}  {c.evolved_rate:>7.0%}  "
              f"{c.frac_of_oracle:>8.0%}")
    print(f"  (oracle gym-clears {score_agent(reference_arm('oracle'), sealed).oracle_gyms:.2f} "
          "= the headroom yardstick on these sealed worlds)")

    # 3. Contamination guard: prove "you could not have trained on this test".
    print("\n== Contamination guard (the moat mechanic) ==")
    honest = verify_sealed(declared_train_seeds=range(0, 50_000), sealed=sealed)
    print(f"  honest submitter (train seeds 0..50k):  ok={honest.ok}  "
          f"overlap={honest.overlap}  (eval all held-out: {honest.all_eval_held_out})")

    leaked = list(range(0, 100)) + list(sealed._eval_seeds())  # trained on the sealed block
    caught = verify_sealed(declared_train_seeds=leaked, sealed=sealed)
    print(f"  LEAK attempt (train includes sealed seeds):  ok={caught.ok}  "
          f"overlap={caught.overlap}  <- detected, score rejected")

    print("\n  honest boundary: prototype — in-process sealing, single machine, numpy, one "
          "config; no hosted service, customers, or revenue. Demonstrates the mechanism.")


if __name__ == "__main__":
    main()
