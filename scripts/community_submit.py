"""Community-track submission helper: validate, organizer example, or a real-LLM entry.

Three modes:

    python scripts/community_submit.py --validate FILE     # the (future) CI gate: exit 0/1
    python scripts/community_submit.py --demo [--out FILE] # measure the free scripted baseline
                                                           # on season 1 and emit a valid JSON
    python scripts/community_submit.py --llm --provider claude-cli --battle-memory \\
        --submitter you [--n-worlds 8] [--out FILE]        # measure a REAL LLM on the season
                                                           # spec and emit a valid JSON

`--demo` is the living template: it actually RUNS the free scripted baseline (the same
`greedy_policy` the main leaderboard scores) on the season-1 public block and writes a
schema-valid submission — copy it, swap in your own model's numbers (measured the same way),
and open a PR. Your run cost is yours (local); scores are SELF-REPORTED (honor system — the
schema forces the flag). Verified, contamination-proof results are the sealed track.

`--llm` scores an actual LLM agent (:mod:`critter_gym.llm_eval`) through the SAME shared
scorer (``community.score_submission_on_season`` — same env, season seeds and pure
gym-clears metric as every entry). ⚠️ QUOTA: every env step is one LLM call — up to
``n_worlds × max_steps`` (e.g. 8 × 200 = 1600) calls per run; the script prints the
projected count and proceeds, so size it (and approve the spend) yourself. Committing the
produced JSON into ``community/submissions/`` (actually entering the board) stays a human
decision.

Operating the track (announcing submissions open, publishing, starting seasons) is a human
gate — this script is the technical artifact only.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

from critter_gym.community import (
    SCHEMA_VERSION,
    build_submission,
    score_submission_on_season,
    season_seeds,
    season_spec,
    validate_submission,
)
from critter_gym.leaderboard import BenchmarkSpec

_SUBMISSIONS_DIR = Path(__file__).resolve().parents[1] / "community" / "submissions"
_DEFAULT_OUT = _SUBMISSIONS_DIR / "season1-scripted-baseline.json"


def _scripted_baseline_policy():
    """The free scripted baseline as an ``obs -> action`` policy (the main board's entry).

    The community metric itself (PURE mean gym-clears on the season block) lives in the
    shared scorer ``community.score_submission_on_season`` — the same loop an LLM entry
    scores through, so there is exactly one scoring path. Ranks are comparable *within*
    the community track; NOT directly comparable to the main board's return-based column."""
    from critter_gym.baselines import greedy_policy

    grid = BenchmarkSpec().grid_size
    return lambda obs: greedy_policy(obs, grid_size=grid)


def _build_llm_agent(a):
    """Provider + memory flags -> a fresh llm_eval agent (mirrors llm_eval_run.py)."""
    from critter_gym.llm_eval import (
        BattleMemoryLLMAgent,
        LLMAgent,
        StatefulLLMAgent,
        anthropic_complete,
        claude_cli_complete,
    )

    if a.provider == "claude-cli":
        complete = claude_cli_complete()
    else:
        complete = anthropic_complete(model=a.model)
    if a.battle_memory:
        return BattleMemoryLLMAgent(complete, window=a.window)
    if a.stateful:
        return StatefulLLMAgent(complete, window=a.window)
    return LLMAgent(complete)


def _run_llm_entry(a) -> int:
    """--llm mode: score a real LLM on the season spec and write a schema-valid JSON."""
    spec = season_spec()
    projected = a.n_worlds * spec["max_steps"]
    memory = ("battle-memory" if a.battle_memory else
              "stateful" if a.stateful else "stateless")
    print(f"scoring a REAL LLM on season {a.season} "
          f"({a.n_worlds} public worlds, provider={a.provider}, memory={memory})")
    print(f"  ⚠️  QUOTA: up to ~{projected} LLM calls (1 per env step, worst case "
          f"{a.n_worlds} x {spec['max_steps']}). Ctrl-C now if that spend is not approved.")

    agent = _build_llm_agent(a)

    def _progress(i: int, seed: int, clears: int) -> None:
        print(f"  [{i + 1}/{a.n_worlds}] seed={seed} clears={clears}", flush=True)

    mean = score_submission_on_season(
        agent, season=a.season, n_worlds=a.n_worlds, on_world=_progress
    )

    model_name = a.model_name or (
        "claude-cli (subscription default model)" if a.provider == "claude-cli" else a.model
    )
    reproduce = (f"python scripts/community_submit.py --llm --provider {a.provider}"
                 + (" --battle-memory" if a.battle_memory else "")
                 + (" --stateful" if a.stateful and not a.battle_memory else "")
                 + f" --season {a.season} --n-worlds {a.n_worlds}")
    sub = build_submission(
        model=model_name, submitter=a.submitter, heldout_mean=mean, n_worlds=a.n_worlds,
        season=a.season, reproduce=reproduce, date=a.date,
    )
    slug = re.sub(r"[^a-z0-9]+", "-", model_name.lower()).strip("-")[:40]
    out = a.out if a.out != _DEFAULT_OUT else _SUBMISSIONS_DIR / f"season{a.season}-{slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sub, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out}  (heldout_mean={sub['heldout_mean']} mean gym-clears, "
          f"self_reported=true)")
    print("entering the board = committing this file under community/submissions/ — that "
          "stays a human decision (honor system; verified results are the sealed track).")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--validate", type=Path, help="validate a submission JSON (CI gate)")
    p.add_argument("--demo", action="store_true",
                   help="measure the scripted baseline on season 1 and write the example JSON")
    p.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    p.add_argument("--n-worlds", type=int, default=16, help="season worlds to score")
    p.add_argument("--llm", action="store_true",
                   help="score a REAL LLM on the season spec and emit a valid JSON "
                        "(⚠️ quota: up to n_worlds x max_steps LLM calls)")
    p.add_argument("--provider", choices=("anthropic", "claude-cli"), default="claude-cli",
                   help="llm only: claude-cli=local Claude Code subscription; "
                        "anthropic=API (ANTHROPIC_API_KEY)")
    p.add_argument("--model", default="claude-opus-4-8",
                   help="llm only: Anthropic model id (--provider anthropic)")
    p.add_argument("--model-name", default=None,
                   help="llm only: the model label written into the submission JSON "
                        "(e.g. 'claude-fable-5 (claude-cli)')")
    p.add_argument("--stateful", action="store_true",
                   help="llm only: per-episode step memory (cleared between worlds)")
    p.add_argument("--battle-memory", action="store_true",
                   help="llm only: thicker agentic memory incl. per-move damage facts")
    p.add_argument("--window", type=int, default=8, help="llm only: memory window")
    p.add_argument("--season", type=int, default=1, help="llm only: season to score")
    p.add_argument("--submitter", default=None, help="llm only: submitter name (required)")
    p.add_argument("--date", default=_dt.date.today().isoformat(),
                   help="llm only: submission date (default: today)")
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

    if a.llm:
        if not a.submitter or not a.submitter.strip():
            p.error("--llm requires --submitter")
        return _run_llm_entry(a)

    if a.demo:
        seeds = season_seeds(1, a.n_worlds)
        print(f"scoring the free scripted baseline on season 1 "
              f"({a.n_worlds} public worlds, seeds {seeds.start}..{seeds.stop - 1})...")
        mean = score_submission_on_season(
            _scripted_baseline_policy(), season=1, n_worlds=a.n_worlds
        )
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
