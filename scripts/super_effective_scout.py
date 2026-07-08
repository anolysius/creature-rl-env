"""Scout: does SUPER-EFFECTIVE-ONLY battle widen scripted discrimination? (super-effective-economy)

The strict scout (06-strict-battle) FALSIFIED confound closure: strict_battle zeroes only RESISTED
(< NEUTRAL) hits, so a type-blind agent still grinds bosses down with NEUTRAL chip damage (party
cycling + full-heal re-entry). ``super_effective_only=True`` closes that last door — only STRICTLY
super-effective (eff > NEUTRAL) hits deal damage, so landing the correct type is the ONLY path to a
win. It is a strict superset of strict_battle.

This scout measures, on two commit configs, the scripted arms (oracle / infer / type_blind) under
THREE economies (default / strict / SE-only) and prints the spread (oracle - type_blind) for each.
Two pre-registered questions (declared before the numbers):
  Q1 (widening): does SE-only widen the spread beyond strict/default? A wider spread hints SE-only
     is a sharper eval variant (candidate for a paid difficulty tier).
  Q2 (fairness):  does the oracle stay WINNABLE (>= half the gyms) under SE-only? If not, SE-only is
     "too harsh" — a FALSIFY of it as a fair lever, not a win. The non-commit attrition probe shows
     whether the neutral-grinding confound finally closes (-> ~0) under SE-only.

HONEST FRAMING (read before quoting any number): scripted arms only, ONE deterministic run per seed
set, no learned/LLM agent, NO robust threshold. Direction is a SIGNAL — any "SE-only is sharper"
claim needs a multi-seed, pre-registered measurement (follow-up). A flat/negative/unwinnable result
is reported AS-IS (falsify welcome). Do not headline these numbers.

Run: `python scripts/super_effective_scout.py [--quick]`. numpy only (free, no [jax]/[rl]).
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import heldout_seeds

NTYPES, PR = 8, 2
ARMS = ("oracle", "infer", "type_blind")
# Economy modes: label -> (strict_battle, super_effective_only). SE-only is a strict superset of
# strict (both flags may not be set together in the engine's dominance order, so we pass them
# exclusively here to name three distinct economies).
ECONOMIES = {
    "default": dict(strict_battle=False, super_effective_only=False),
    "strict": dict(strict_battle=True, super_effective_only=False),
    "SE-only": dict(strict_battle=False, super_effective_only=True),
}
CONFIGS = {
    "hard-commit grid16": dict(grid_size=16, num_gyms=5, num_creatures=6, max_steps=420),
    "base-commit grid10": dict(grid_size=10, num_gyms=3, num_creatures=5, max_steps=200),
}


def _mean_clears(seeds, arm: str, cfg: dict, econ: dict) -> float:
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=True, vary=True, num_types=NTYPES, patch_radius=PR,
        min_gyms=cfg["num_gyms"], **econ, **cfg)
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


def _attrition_clears(seeds, cfg: dict, econ: dict) -> float:
    """Non-commit (default M1 cycling) attrition probe — where cycling + min/neutral damage
    lets a no-inference policy grind bosses down (the confound SE-only targets)."""
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=False, vary=True, num_types=NTYPES, patch_radius=PR,
        min_gyms=cfg["num_gyms"], **econ, **cfg)
    return float(np.mean([run_episode(fac, _attrition_policy, s).gyms_cleared
                          for s in seeds]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (fewer seeds)")
    a = p.parse_args()

    n_eval = 6 if a.quick else 16
    seeds = tuple(int(s) for s in heldout_seeds(n_eval))

    print("== Super-effective-only scout (attrition-confound lever, strict follow-up) — SIGNAL ==")
    print(f"  5x5 view, commit battles, num_types {NTYPES}; {n_eval} held-out seeds; "
          f"scripted arms only (numpy, deterministic)")
    print("  Q1 (declared before numbers): SE-only spread(oracle-blind) > strict/default "
          "=> hints SE-only widens scripted discrimination.")
    print("  Q2 (declared before numbers): oracle stays winnable (>= half gyms) under SE-only "
          "=> fair lever; else FALSIFY (too harsh). attrition probe -> ~0 => confound closes.")

    for name, cfg in CONFIGS.items():
        rows: dict[str, dict[str, float]] = {}
        for econ_name, econ in ECONOMIES.items():
            rows[econ_name] = {arm: _mean_clears(seeds, arm, cfg, econ) for arm in ARMS}
        print(f"  [{name}] ({cfg['num_gyms']} gyms, {cfg['max_steps']} steps)")
        spreads: dict[str, float] = {}
        for econ_name in ECONOMIES:
            r = rows[econ_name]
            spread = r["oracle"] - r["type_blind"]
            spreads[econ_name] = spread
            winnable = r["oracle"] >= 0.5 * cfg["num_gyms"]
            print(f"    {econ_name:>8}: oracle {r['oracle']:.2f}  infer {r['infer']:.2f}  "
                  f"type_blind {r['type_blind']:.2f}  | spread(oracle-blind) {spread:.2f}"
                  f"  (oracle winnable={winnable})")
        d_se_strict = spreads["SE-only"] - spreads["strict"]
        d_se_default = spreads["SE-only"] - spreads["default"]
        print(f"    Q1 DELTA spread: SE-only - strict = {d_se_strict:+.2f}, "
              f"SE-only - default = {d_se_default:+.2f} gyms (> 0 hints SE-only widens further)")
        # attrition probe across all three economies (does neutral grinding finally die?)
        att = {en: _attrition_clears(seeds, cfg, ec) for en, ec in ECONOMIES.items()}
        print(f"    attrition probe (non-commit, always-attack, no inference): "
              f"default {att['default']:.2f} -> strict {att['strict']:.2f} -> "
              f"SE-only {att['SE-only']:.2f} gyms "
              f"(Q2 confound closes iff SE-only -> ~0)")
    print("  HONEST: scripted-arms-only RAW signal on one seed set — no learned agent, no robust "
          "threshold. A pre-registered multi-seed measurement is the FOLLOW-UP; do NOT headline "
          "these deltas. Q2 fairness: oracle MUST stay winnable for the lever to be fair (printed "
          "above) — if it drops below half, report SE-only as TOO HARSH (falsify), not a win.")
    print("  NOTE: SE-only zeroes NEUTRAL as well as resisted hits. Single-type worlds stay "
          "winnable (matchup guarantee #15 gives eff==super_mult>NEUTRAL), but SE-only + a hidden "
          "boss secondary can yield an exact-NEUTRAL ceiling => a structurally unwinnable gym. "
          "That caveat is a design boundary, reported not hidden.")


if __name__ == "__main__":
    main()
