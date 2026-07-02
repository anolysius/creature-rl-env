"""Community-track submission helper: validate a submission, or produce the organizer example.

Two modes:

    python scripts/community_submit.py --validate FILE     # the (future) CI gate: exit 0/1
    python scripts/community_submit.py --demo [--out FILE] # measure the free scripted baseline
                                                           # on season 1 and emit a valid JSON

`--demo` is the living template: it actually RUNS the free scripted baseline (the same
`greedy_policy` the main leaderboard scores) on the season-1 public block and writes a
schema-valid submission — copy it, swap in your own model's numbers (measured the same way),
and open a PR. Your run cost is yours (local); scores are SELF-REPORTED (honor system — the
schema forces the flag). Verified, contamination-proof results are the sealed track.

Operating the track (announcing submissions open, publishing, starting seasons) is a human
gate — this script is the technical artifact only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from critter_gym.community import SCHEMA_VERSION, season_seeds, season_spec, validate_submission
from critter_gym.leaderboard import BenchmarkSpec

_DEFAULT_OUT = Path(__file__).resolve().parents[1] / "community" / "submissions" / \
    "season1-scripted-baseline.json"


def _score_scripted(seeds, spec: BenchmarkSpec) -> float:
    """Mean held-out gym-clears of the free scripted baseline on ``seeds``.

    Same env + policy as the main leaderboard's 'scripted' entry, but the community metric is
    PURE mean gym-clears (RLVR-clean, bounded by num_gyms) on the season block — ranks are
    comparable *within* the community track; NOT directly comparable to the main board's
    return-based column (which also counts catches/evolutions on different seeds)."""
    from critter_gym.baselines import greedy_policy

    factory = spec.env_factory()
    clears = []
    for seed in seeds:
        env = factory()
        obs, _ = env.reset(seed=int(seed))
        done = False
        while not done:
            obs, _, term, trunc, _ = env.step(greedy_policy(obs, grid_size=spec.grid_size))
            done = bool(term or trunc)
        clears.append(int(sum(env._gym_defeated)))
    return float(np.mean(clears))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--validate", type=Path, help="validate a submission JSON (CI gate)")
    p.add_argument("--demo", action="store_true",
                   help="measure the scripted baseline on season 1 and write the example JSON")
    p.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    p.add_argument("--n-worlds", type=int, default=16, help="season worlds to score (demo)")
    a = p.parse_args()

    if a.validate:
        sub = json.loads(a.validate.read_text())
        errors = validate_submission(sub)
        if errors:
            print(f"INVALID ({a.validate.name}):")
            for e in errors:
                print(f"  - {e}")
            return 1
        print(f"VALID ({a.validate.name})")
        return 0

    if a.demo:
        spec = BenchmarkSpec()
        seeds = season_seeds(1, a.n_worlds)
        print(f"scoring the free scripted baseline on season 1 "
              f"({a.n_worlds} public worlds, seeds {seeds.start}..{seeds.stop - 1})...")
        mean = _score_scripted(seeds, spec)
        sub = {
            "schema_version": SCHEMA_VERSION,
            "season": 1,
            "model": "scripted-baseline (organizer example)",
            "submitter": "crittergym (organizer)",
            "heldout_mean": round(mean, 3),
            "n_worlds": a.n_worlds,
            "spec": season_spec(),
            "reproduce": f"python scripts/community_submit.py --demo --n-worlds {a.n_worlds}",
            "date": "2026-07-02",
            "self_reported": True,
        }
        assert validate_submission(sub) == [], "demo submission must be schema-valid"
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(sub, indent=2, sort_keys=True) + "\n")
        print(f"wrote {a.out}  (heldout_mean={sub['heldout_mean']})")
        print("self-reported (honor system) — verified results are the sealed track.")
        return 0

    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
