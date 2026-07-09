"""Does commit-mode close the cycling-attrition path SE-only left open? (attrition-closure)

#6 (strict) FALSIFIED confound closure; #7 (SE-only) closed it only PARTIALLY — in non-commit
mode a fainted active force-switches through the party, so a no-inference policy eventually cycles
onto a super-effective member and grinds the boss down. #7's NOTE named the remaining axis:
commit-mode (no switching). This scout combines the two EXISTING opt-in knobs (commit_battles +
super_effective_only, NO engine change) and measures the no-inference `type_blind` arm across
{commit, non-commit} x {default, strict, SE-only} on the hard config, against the blind-luck floor
(`probe` = blind commit each fight) and the chart-knowing `oracle`.

Pre-registered (frozen in the plan/qa-checklist BEFORE the run):
  (a) CLOSED  iff type_blind(commit,SE-only) <= type_blind(non-commit,SE-only) - 0.25  (cycling
      advantage removed)  AND  type_blind(commit,SE-only) <= probe(commit,SE-only) + 0.5  (down to
      the blind-luck floor)  AND  oracle(commit,SE-only) >= 0.5*num_gyms  (still winnable).
  (b) NOT CLOSED  if the floor-proximity condition fails (grinding beyond luck persists).
  (c) TOO HARSH   if oracle is not winnable under commit+SE-only (unfair lever).

HONEST framing (read before quoting any number): scripted arms only, ONE deterministic seed set
(16 held-out seeds, no per-seed repeat / no run-to-run std), no learned/LLM agent. The realistic
target of "full closure" is NOT ~0 but the blind-luck floor (a single blind commit still
super-effects some bosses by the matchup distribution, so floor > 0) — do NOT read floor>0 as
failure. Direction is a SIGNAL; the learned/LLM no-inference grinder is a separate (money-gated)
question. Do NOT headline. numpy only (free, no [jax]/[rl]).

Run: `python scripts/attrition_closure_scout.py [--quick]`.
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import heldout_seeds

# Mirror hard_env_spec()/hard_benchmark_memory.py exactly.
GRID, NGYM, NTYPES, NCRE, STEPS, PR = 16, 5, 8, 6, 420, 2
ECONOMIES = {
    "default": dict(strict_battle=False, super_effective_only=False),
    "strict": dict(strict_battle=True, super_effective_only=False),
    "SE-only": dict(strict_battle=False, super_effective_only=True),
}


def _mean_clears(seeds, arm: str, *, commit: bool, econ: dict) -> float:
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=commit, vary=True, num_types=NTYPES, num_gyms=NGYM, grid_size=GRID,
        num_creatures=NCRE, max_steps=STEPS, patch_radius=PR, min_gyms=NGYM, **econ)
    return float(np.mean([run_episode(fac, reference_arm(arm), s).gyms_cleared for s in seeds]))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (fewer seeds)")
    a = p.parse_args()

    n_eval = 6 if a.quick else 16
    seeds = tuple(int(s) for s in heldout_seeds(n_eval))

    print("== Does commit-mode close the cycling-attrition path? (attrition-closure) ==")
    print(f"   hard config: grid {GRID}, 5x5 view, {NGYM} gyms, {STEPS} steps, num_types {NTYPES}; "
          f"{n_eval} held-out seeds; scripted arms only (numpy, deterministic)")
    print("   pre-registered (frozen before data): (a) CLOSED iff type_blind(commit,SE-only) <= "
          "type_blind(non-commit,SE-only)-0.25 AND <= probe(commit,SE-only)+0.5 AND "
          "oracle(commit,SE-only) winnable; (b) NOT CLOSED if floor cond fails; (c) TOO HARSH "
          "if oracle not winnable.")

    # 6-cell no-inference grid + the two anchors that make it interpretable.
    tb: dict[tuple[bool, str], float] = {}
    for commit in (False, True):
        for econ_name, econ in ECONOMIES.items():
            tb[(commit, econ_name)] = _mean_clears(seeds, "type_blind", commit=commit, econ=econ)
    oracle = _mean_clears(seeds, "oracle", commit=True, econ=ECONOMIES["SE-only"])
    probe_floor = _mean_clears(seeds, "probe", commit=True, econ=ECONOMIES["SE-only"])
    oracle_default = _mean_clears(seeds, "oracle", commit=True, econ=ECONOMIES["default"])

    print(f"  type_blind (no-inference) gym-clears / {NGYM}:")
    print(f"    {'economy':>8} | {'non-commit':>10} {'commit':>8} | commit removes (cycling gain)")
    for econ_name in ECONOMIES:
        nc, cm = tb[(False, econ_name)], tb[(True, econ_name)]
        print(f"    {econ_name:>8} | {nc:>10.2f} {cm:>8.2f} | {nc - cm:>+.2f}")
    tb_c_se = tb[(True, "SE-only")]
    tb_nc_se = tb[(False, "SE-only")]
    winnable = oracle >= 0.5 * NGYM

    print(f"  anchors (commit, SE-only): oracle {oracle:.2f} (winnable={winnable}, "
          f"default-econ oracle {oracle_default:.2f})   blind-luck floor (probe) {probe_floor:.2f}")
    print(f"  inference-load-bearing gap (oracle - type_blind) @ commit+SE-only: "
          f"{oracle - tb_c_se:.2f}  (widest = eval-validity max)")

    cyc_removed = tb_c_se <= tb_nc_se - 0.25
    at_floor = tb_c_se <= probe_floor + 0.5
    if not winnable:
        branch = "(c) TOO HARSH -> oracle not winnable under commit+SE-only (unfair lever)"
    elif cyc_removed and at_floor:
        branch = ("(a) CLOSED -> commit+SE-only removes the cycling grind AND sits at the "
                  "blind-luck floor; inference is ~the only path to a win")
    elif not at_floor:
        branch = ("(b) NOT CLOSED -> no-inference arm still exceeds the blind-luck floor "
                  "(grinding beyond a single blind commit persists)")
    else:
        branch = ("(?) partial -> floor reached but commit did not reduce vs non-commit "
                  "(cycling was not the active grind here)")
    print(f"  verdict: {branch}")
    print(f"    conditions: cycling-removed(commit<=non-commit-0.25)={cyc_removed} "
          f"[{tb_c_se:.2f} vs {tb_nc_se - 0.25:.2f}]   at-floor(commit<=probe+0.5)={at_floor} "
          f"[{tb_c_se:.2f} vs {probe_floor + 0.5:.2f}]   winnable={winnable}")
    print("  HONEST: scripted-arms-only, ONE deterministic seed set (no run-to-run std), no "
          "learned/LLM agent. Full-closure target is the blind-luck floor (probe), NOT ~0 — a "
          "single blind commit super-effects some bosses by the matchup distribution, so floor>0 "
          "is expected, not failure. Direction is a SIGNAL; do NOT headline. The learned/LLM "
          "no-inference grinder is a separate (money-gated) question.")


if __name__ == "__main__":
    main()
