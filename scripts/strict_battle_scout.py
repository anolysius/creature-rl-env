"""Scout: does STRICT battle widen scripted discrimination? (hard-benchmark/strict-battle)

The default battle economy clamps damage to ``max(1, ...)``, so a type-blind agent can grind
gyms down by attrition — the oracle-vs-blind gym-clear spread understates how load-bearing
type inference really is (paper §5 limitation (i)). ``strict_battle=True`` zeroes resisted
(< NEUTRAL effectiveness) hits: a wrong commit can no longer chip a boss to death.

This scout measures, on the hard commit config (grid16), the scripted arms
(oracle / infer / type_blind) with strict OFF vs ON and prints the spread
(oracle - type_blind) for each. A widened spread hints strict is a sharper eval variant
(candidate for a paid tier); a flat/negative result is reported as-is (falsify welcome).

HONEST FRAMING (read before quoting any number): scripted arms only, ONE deterministic run
per seed set, no learned agent, NO robust threshold. Direction here is a SIGNAL — any
"strict is sharper" claim requires a multi-seed, pre-registered measurement (follow-up task).
Do not headline these numbers.

Run: `python scripts/strict_battle_scout.py [--quick]`. numpy only (free, no [jax]/[rl]).
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import heldout_seeds

NTYPES, PR = 8, 2
ARMS = ("oracle", "infer", "type_blind")
# Two commit configs (reference arms are commit-v0 policies): the deep hard config
# (grid16, the #3/#5 measurement world) and the base grid10 commit world.
CONFIGS = {
    "hard-commit grid16": dict(grid_size=16, num_gyms=5, num_creatures=6, max_steps=420),
    "base-commit grid10": dict(grid_size=10, num_gyms=3, num_creatures=5, max_steps=200),
}


def _mean_clears(seeds, arm: str, cfg: dict, *, strict: bool) -> float:
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=True, vary=True, num_types=NTYPES, patch_radius=PR,
        min_gyms=cfg["num_gyms"], strict_battle=strict, **cfg)
    return float(np.mean([run_episode(fac, reference_arm(arm), s).gyms_cleared
                          for s in seeds]))


def _attrition_policy(env: CritterEnv, obs) -> int:
    """Type-blind attrition: in battle always slam move 0 (never switch, never infer);
    in the overworld walk to the nearest live gym. The §5-(i) confound incarnate."""
    if obs["in_battle"][0]:
        return 0
    ar, ac = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    targets = [pos for pos, i in env._gym_tiles.items() if not env._gym_defeated[i]]
    if not targets:
        return 5
    gr, gc = min(targets, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    if gr != ar:
        return 0 if gr < ar else 1
    if gc != ac:
        return 2 if gc > ac else 3
    return 5


def _attrition_clears(seeds, cfg: dict, *, strict: bool) -> float:
    """Non-commit (default M1 economy) attrition probe — where cycling + min-damage
    lets a no-inference policy grind bosses down (the confound strict targets)."""
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=False, vary=True, num_types=NTYPES, patch_radius=PR,
        min_gyms=cfg["num_gyms"], strict_battle=strict, **cfg)
    return float(np.mean([run_episode(fac, _attrition_policy, s).gyms_cleared
                          for s in seeds]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (fewer seeds)")
    a = p.parse_args()

    n_eval = 6 if a.quick else 16
    seeds = tuple(int(s) for s in heldout_seeds(n_eval))

    print("== Strict-battle scout (attrition-confound lever) — SIGNAL, not measurement ==")
    print(f"  5x5 view, commit battles, num_types {NTYPES}; {n_eval} held-out seeds; "
          f"scripted arms only (numpy, deterministic)")

    for name, cfg in CONFIGS.items():
        rows: dict[bool, dict[str, float]] = {}
        for strict in (False, True):
            rows[strict] = {arm: _mean_clears(seeds, arm, cfg, strict=strict) for arm in ARMS}
        print(f"  [{name}] ({cfg['num_gyms']} gyms, {cfg['max_steps']} steps)")
        for strict in (False, True):
            r = rows[strict]
            spread = r["oracle"] - r["type_blind"]
            label = "strict ON " if strict else "strict OFF"
            print(f"    {label}: oracle {r['oracle']:.2f}  infer {r['infer']:.2f}  "
                  f"type_blind {r['type_blind']:.2f}  | spread(oracle-blind) {spread:.2f}"
                  f"  (winnable={r['oracle'] >= 0.5 * cfg['num_gyms']})")
        d_spread = (rows[True]["oracle"] - rows[True]["type_blind"]) - (
            rows[False]["oracle"] - rows[False]["type_blind"])
        print(f"    DELTA spread (ON - OFF) = {d_spread:+.2f} gyms "
              f"(> 0 hints strict widens scripted discrimination)")
        att_off = _attrition_clears(seeds, cfg, strict=False)
        att_on = _attrition_clears(seeds, cfg, strict=True)
        print(f"    non-commit attrition probe (always-attack, no inference): "
              f"OFF {att_off:.2f} -> ON {att_on:.2f} gyms "
              f"({att_off - att_on:+.2f} = attrition wins strict removes)")
    print("  HONEST: scripted-arms-only RAW signal on one seed set — no learned agent, "
          "no robust threshold. A pre-registered multi-seed measurement is the FOLLOW-UP "
          "task; do NOT headline this delta. Oracle must stay winnable for the lever "
          "to be fair (printed above).")
    print("  NOTE: strict zeroes only RESISTED (< NEUTRAL) hits by design. NEUTRAL chip "
          "damage, party cycling, and full-heal battle re-entry are untouched — if the "
          "attrition probe shows ~+0.00, the attrition confound PERSISTS via neutral "
          "grinding. Report that as a falsify of the lever's premise; do NOT claim the "
          "confound closed. A stronger variant (e.g. only-super-effective damage, or no "
          "re-entry heal) is a separate design decision, not this scout's call.")


if __name__ == "__main__":
    main()
