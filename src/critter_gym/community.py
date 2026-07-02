"""Community leaderboard track — seasonal public exam sets + self-reported submissions.

The **public** half of the two-track design (monetization-surface #10). Anyone can run their
own model locally on a *seasonal public seed block* (derived openly below — no secret, anyone
can reproduce the exact worlds), produce a small submission JSON, and appear on the site's
community leaderboard. The **sealed** track (:mod:`critter_gym.eval_package` /
:mod:`eval_marketplace`, #4–6) stays the *proof* track: public-track scores are
**self-reported (honor system)** — the schema forces a ``self_reported: true`` flag so that
fact can never be hidden, and the site labels it permanently.

**Seasons.** Because worlds are procedurally generated, a *fresh* public exam set can be issued
per season (a fixed benchmark cannot do this): ``season_seeds(season)`` derives a public block
inside the held-out region, structurally disjoint from the training region, from the default
public block (``region.heldout_seeds``), from every other season, and from the **sealed**
region (seeds ≥ 1.1M) where the paid, contamination-proof evals live. Rotating seasons resets
the race (fun) and bounds how long memorizing a public set stays useful (honesty).

Operating the track (announcing submissions open, publishing the page, starting a season,
registering on a hub) is a **human gate** — this module is the technical artifact only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from critter_gym.leaderboard import BenchmarkSpec
from critter_gym.region import TEST_SEED_OFFSET

SCHEMA_VERSION = 1

#: Each season owns a SEASON_SPAN-wide slot; season s starts at TEST_SEED_OFFSET + s*SPAN.
#: Season 0 does not exist — the [TEST_SEED_OFFSET, +SPAN) slot is left to the default public
#: block (`region.heldout_seeds`), so seasons never collide with it (boundary-tested).
SEASON_SPAN = 1000
#: Public held-out room before the sealed region begins (eval_harness._SEALED_BASE = 1.1M).
_PUBLIC_SPAN = 100_000

#: Required submission fields -> expected type. `self_reported` is validated to be exactly
#: True — the public track cannot pretend to be verified.
_REQUIRED: dict[str, type] = {
    "schema_version": int,
    "season": int,
    "model": str,
    "submitter": str,
    "heldout_mean": float,
    "n_worlds": int,
    "spec": dict,
    "reproduce": str,
    "date": str,
    "self_reported": bool,
}


def season_seeds(season: int, n: int = 100) -> range:
    """The public exam block for ``season`` (1-based): ``n`` seeds, openly derived.

    Guards keep every season inside the public held-out room: disjoint from the training
    region, the default public block, every other season, and the sealed region (≥ 1.1M)."""
    if season < 1:
        raise ValueError(f"season must be >= 1 (got {season})")
    if not 1 <= n <= SEASON_SPAN:
        raise ValueError(f"n must be in [1, {SEASON_SPAN}] (got {n})")
    if season * SEASON_SPAN + n > _PUBLIC_SPAN:
        raise ValueError(
            f"season {season} with n={n} would leave the public region "
            f"(needs season*{SEASON_SPAN}+n <= {_PUBLIC_SPAN})"
        )
    start = TEST_SEED_OFFSET + season * SEASON_SPAN
    return range(start, start + n)


def season_spec() -> dict[str, int]:
    """The pinned community benchmark spec (the default ``BenchmarkSpec``) as a dict.

    A submission must carry exactly this spec — scores on a different config don't rank."""
    return BenchmarkSpec().to_dict()


def validate_submission(sub: dict[str, Any]) -> list[str]:
    """Validate a community submission dict; returns a list of errors (empty = valid).

    This is the (future) CI gate for submission PRs: required fields and types, the exact
    schema version, a legal season, the pinned spec verbatim, a sane score range, and the
    forced ``self_reported: true`` honesty flag."""
    errors: list[str] = []
    for field, typ in _REQUIRED.items():
        if field not in sub:
            errors.append(f"missing required field: {field}")
            continue
        value = sub[field]
        if typ is float:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{field} must be a number")
        elif not isinstance(value, typ) or (typ is int and isinstance(value, bool)):
            errors.append(f"{field} must be {typ.__name__}")
    if errors:
        return errors

    if sub["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    try:
        season_seeds(sub["season"], 1)
    except ValueError as e:
        errors.append(f"season invalid: {e}")
    if sub["spec"] != season_spec():
        errors.append("spec must equal the pinned community spec (season_spec())")
    max_score = season_spec()["num_gyms"]
    if not 0.0 <= float(sub["heldout_mean"]) <= float(max_score):
        errors.append(f"heldout_mean must be in [0, {max_score}] (mean gym-clears)")
    if sub["n_worlds"] < 1:
        errors.append("n_worlds must be >= 1")
    if not sub["model"].strip() or not sub["submitter"].strip() or not sub["reproduce"].strip():
        errors.append("model/submitter/reproduce must be non-empty")
    if sub["self_reported"] is not True:
        errors.append("self_reported must be true — the public track is honor-system")
    return errors


def load_submissions(directory: Path | str) -> tuple[list[dict], list[tuple[str, list[str]]]]:
    """Load, validate and rank all ``*.json`` submissions in ``directory``.

    Returns ``(valid, rejected)``: valid submissions sorted by season then ``heldout_mean``
    descending (then model name, deterministically); rejected as ``(filename, errors)`` so a
    build can report *why* a file did not rank instead of silently dropping it."""
    directory = Path(directory)
    valid: list[dict] = []
    rejected: list[tuple[str, list[str]]] = []
    for f in sorted(directory.glob("*.json")):
        try:
            sub = json.loads(f.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            rejected.append((f.name, [f"not valid JSON: {e}"]))
            continue
        errors = validate_submission(sub)
        if errors:
            rejected.append((f.name, errors))
        else:
            valid.append(sub)
    valid.sort(key=lambda s: (s["season"], -float(s["heldout_mean"]), s["model"]))
    return valid, rejected
