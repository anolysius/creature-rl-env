"""Tests for the community leaderboard track (monetization-surface #10).

The public, self-reported competition track: seasonal public seed blocks (derived openly — no
secret), a submission schema that FORCES the `self_reported: true` honesty flag, a validator
(the future CI gate), and a ranking loader. The sealed track (#4–6 signed certificates) stays
the *proof* track; these tests pin the honesty and isolation invariants of the public one.
"""
from __future__ import annotations

import json

from critter_gym.community import (
    SCHEMA_VERSION,
    load_submissions,
    season_seeds,
    season_spec,
    validate_submission,
)
from critter_gym.eval_harness import _SEALED_BASE
from critter_gym.region import TEST_SEED_OFFSET, heldout_seeds


def _valid_sub(**over) -> dict:
    sub = {
        "schema_version": SCHEMA_VERSION,
        "season": 1,
        "model": "example-model",
        "submitter": "someone",
        "heldout_mean": 1.25,
        "n_worlds": 16,
        "spec": season_spec(),
        "reproduce": "python scripts/community_submit.py --demo",
        "date": "2026-07-02",
        "self_reported": True,
    }
    sub.update(over)
    return sub


# --- season seed derivation (open, deterministic, isolated) ----------------------------

def test_season_seeds_in_public_heldout_region():
    s = season_seeds(1, 100)
    assert all(TEST_SEED_OFFSET <= x < _SEALED_BASE for x in s)


def test_season_seeds_disjoint_from_sealed_region():
    # Even the last allowed season stays strictly below the sealed base (1.1M).
    s = season_seeds(99, 1000)
    assert max(s) < _SEALED_BASE


def test_season_seeds_disjoint_across_seasons():
    assert set(season_seeds(1, 1000)).isdisjoint(season_seeds(2, 1000))


def test_season_seeds_disjoint_from_default_heldout_block():
    # Boundary case (L1 SUGGEST): heldout_seeds has no upper guard; the design leaves room for
    # n up to 1000 before season 1 starts — make the implicit assumption an explicit test.
    assert set(season_seeds(1, 1000)).isdisjoint(heldout_seeds(1000))


def test_season_seeds_deterministic_and_open():
    assert list(season_seeds(3, 10)) == list(season_seeds(3, 10))
    assert season_seeds(1, 100).start == TEST_SEED_OFFSET + 1000


def test_season_seeds_guards():
    import pytest
    with pytest.raises(ValueError):
        season_seeds(0, 100)          # seasons are 1-based
    with pytest.raises(ValueError):
        season_seeds(1, 0)            # need at least one world
    with pytest.raises(ValueError):
        season_seeds(1, 1001)         # n > SEASON_SPAN would bleed into season 2
    with pytest.raises(ValueError):
        season_seeds(100, 1000)       # would touch the sealed region


# --- submission schema validation -------------------------------------------------------

def test_valid_submission_passes():
    assert validate_submission(_valid_sub()) == []


def test_missing_required_field_fails():
    sub = _valid_sub()
    del sub["model"]
    errors = validate_submission(sub)
    assert any("model" in e for e in errors)


def test_self_reported_flag_is_forced():
    # The public track cannot hide that it is self-reported — the schema forces the flag.
    errors = validate_submission(_valid_sub(self_reported=False))
    assert any("self_reported" in e for e in errors)


def test_spec_mismatch_fails():
    bad_spec = dict(season_spec())
    bad_spec["grid_size"] = 99  # a submission cannot claim scores on a different config
    errors = validate_submission(_valid_sub(spec=bad_spec))
    assert any("spec" in e for e in errors)


def test_score_sanity_bounds():
    # heldout_mean is a mean gym-clear count: 0 <= x <= num_gyms of the pinned spec.
    assert validate_submission(_valid_sub(heldout_mean=-0.1))
    assert validate_submission(_valid_sub(heldout_mean=99.0))


def test_bad_season_fails():
    errors = validate_submission(_valid_sub(season=0))
    assert any("season" in e for e in errors)


def test_wrong_schema_version_fails():
    errors = validate_submission(_valid_sub(schema_version=999))
    assert any("schema_version" in e for e in errors)


# --- loader + ranking --------------------------------------------------------------------

def test_load_submissions_ranks_and_skips_invalid(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(_valid_sub(model="a", heldout_mean=0.5)))
    (tmp_path / "b.json").write_text(json.dumps(_valid_sub(model="b", heldout_mean=2.0)))
    bad = _valid_sub(model="cheater")
    bad["self_reported"] = False
    (tmp_path / "c.json").write_text(json.dumps(bad))
    (tmp_path / "d.json").write_text("{not json")

    valid, rejected = load_submissions(tmp_path)
    assert [v["model"] for v in valid] == ["b", "a"]      # ranked by heldout_mean desc
    assert {name for name, _ in rejected} == {"c.json", "d.json"}


def test_load_submissions_empty_dir(tmp_path):
    valid, rejected = load_submissions(tmp_path)
    assert valid == [] and rejected == []


def test_committed_example_submission_validates():
    # The organizer example committed to the repo must always pass the validator.
    from pathlib import Path
    sub_dir = Path(__file__).resolve().parents[1] / "community" / "submissions"
    files = sorted(sub_dir.glob("*.json"))
    assert files, "expected at least the organizer example submission"
    for f in files:
        assert validate_submission(json.loads(f.read_text())) == [], f.name
