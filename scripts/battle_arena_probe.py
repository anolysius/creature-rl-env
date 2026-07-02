"""Battle-arena probe — scripted validation of the engagement-confound-free band.

WHY: the LLM probe's super-effective-move rate sat near the chart-blind floor (~14%),
but that number cannot distinguish "cannot infer the hidden chart" from "never sustains
battle engagement" (dies/wanders in the overworld before accumulating battle turns).
The arena (`critter_gym.envs.ArenaEnv`) removes the second factor structurally: K
consecutive battles, no overworld.

This script validates the instrument with the scripted arms (free, deterministic): it
prints the 4-arm SE-rate band on the arena next to the same band on the full overworld
env. A sound instrument shows (i) the arena band still discriminates (oracle >>
type_blind) and (ii) arms collect battle moves without any navigation.

HONEST FRAMING: scripted arms only — the `infer` arm is an inference *proxy*, not an
LLM; one seed set, no robust threshold; the arena is a DIAGNOSTIC, not a leaderboard
config. The real-LLM arena run spends the user's API/CLI quota and is a separate,
user-approved step (`scripts/llm_eval_run.py --arena`). Do not headline these numbers.

Run: `python scripts/battle_arena_probe.py [--quick]`. numpy only (free).
"""
from __future__ import annotations

import argparse

from critter_gym.arena import ARENA_ARMS, arena_band
from critter_gym.eval_harness import SealedEvalSet, inference_baseline
from critter_gym.region import heldout_seeds

KNOBS = dict(commit_battles=True, vary=True, num_types=8, num_gyms=3, num_creatures=5,
             grid_size=10, max_steps=600)
K_BATTLES = 10

_LABELS = {
    "oracle": "oracle (chart-KNOWING expert)",
    "infer": "infer (inference proxy, NOT an LLM)",
    "type_blind": "type_blind (chart-BLIND floor)",
    "probe": "probe (blind guess)",
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (fewer seeds)")
    a = p.parse_args()
    n = 4 if a.quick else 12
    seeds = tuple(int(s) for s in heldout_seeds(n))

    print("== Battle-arena probe — engagement-confound-free inference band (scripted) ==")
    print(f"   arena: {K_BATTLES} consecutive battles, no overworld; commit battles, "
          f"num_types 8; {n} held-out seeds")

    band = arena_band(seeds, k_battles=K_BATTLES, **KNOBS)
    print("  -- ARENA (no overworld: every decision is a battle decision) --")
    for arm in ARENA_ARMS:
        r = band[arm]
        print(f"  {_LABELS[arm]:<36} SE-rate {r.se_rate:>4.0%}  wins {r.wins:.2f}/{K_BATTLES}"
              f"  ({r.n_battle_moves} battle moves)")

    # The same scripted band on the full overworld env (the sealed-eval frame), for the
    # side-by-side read: how much of each arm's move budget the overworld eats.
    sealed = SealedEvalSet(master_seed=20260702, n_worlds=n, num_types=8, max_steps=200)
    over = inference_baseline(sealed)
    print("  -- OVERWORLD reference (sealed frame: navigation + battles) --")
    for arm in ARENA_ARMS:
        ab = over.arms[arm]
        print(f"  {_LABELS[arm]:<36} SE-rate {ab.se_rate:>4.0%}  "
              f"({ab.n_battle_moves} battle moves)")

    spread = band["oracle"].se_rate - band["type_blind"].se_rate
    print(f"  ARENA spread (oracle - type_blind SE-rate) = {spread:+.0%} "
          f"(must be > 0 for the instrument to discriminate)")
    print("  HONEST: scripted arms only (infer = proxy, NOT an LLM); one seed set, no "
          "robust threshold; diagnostic instrument, not a leaderboard. The real-LLM "
          "arena run costs API/CLI quota -> separate, user-approved step "
          "(llm_eval_run.py --arena). Do NOT headline these numbers.")


if __name__ == "__main__":
    main()
