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


# -- LLM entry wiring (eval-product/community-llm-entry) --------------------------


def test_score_submission_on_season_reproduces_demo_number():
    # The shared scorer with the scripted-baseline policy must reproduce the committed
    # organizer example (0.75 on 16 season-1 worlds) — proving --demo and an LLM entry
    # score through the SAME env/seeds/metric (no second scoring loop).
    from critter_gym.baselines import greedy_policy
    from critter_gym.community import score_submission_on_season
    from critter_gym.leaderboard import BenchmarkSpec

    grid = BenchmarkSpec().grid_size
    mean = score_submission_on_season(
        lambda obs: greedy_policy(obs, grid_size=grid), season=1, n_worlds=16
    )
    assert round(mean, 3) == 0.75


def test_score_submission_resets_agent_per_world():
    from critter_gym.community import score_submission_on_season

    class FakeAgent:
        def __init__(self) -> None:
            self.resets = 0

        def act(self, obs) -> int:
            return 0

        def reset(self) -> None:
            self.resets += 1

    agent = FakeAgent()
    score_submission_on_season(agent, season=1, n_worlds=3)
    assert agent.resets == 3  # memory isolation: one reset per world (sealed-track rule)


def test_llm_agent_end_to_end_submission_is_schema_valid():
    # AC2: a (fake-completed) llm_eval agent scored by the shared scorer, assembled by
    # build_submission, must pass the CI validator — zero real LLM calls.
    from critter_gym.community import build_submission, score_submission_on_season
    from critter_gym.llm_eval import StatefulLLMAgent

    calls: list[str] = []

    def fake_complete(prompt: str) -> str:
        calls.append(prompt)
        return "0"

    agent = StatefulLLMAgent(fake_complete, window=4)
    mean = score_submission_on_season(agent, season=1, n_worlds=2)
    sub = build_submission(
        model="fake-llm (unit test)", submitter="ci", heldout_mean=mean, n_worlds=2,
        season=1, reproduce="pytest tests/test_community.py", date="2026-07-03",
    )
    assert validate_submission(sub) == []
    assert sub["self_reported"] is True
    assert len(calls) > 0  # every decision went through the (fake) LLM


def test_build_submission_rejects_invalid():
    import pytest

    from critter_gym.community import build_submission

    with pytest.raises(ValueError):
        build_submission(
            model="x", submitter="y", heldout_mean=99.0,  # out of [0, num_gyms]
            n_worlds=1, season=1, reproduce="cmd", date="2026-07-03",
        )


def test_runner_exposes_llm_flag_without_calling_llm():
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "scripts/community_submit.py", "--help"],
        capture_output=True, text=True, check=True,
    )
    assert "--llm" in out.stdout and "--provider" in out.stdout


def test_score_submission_on_world_callback():
    # AC2 (cli-complete-retry): on_world fires once per world with (idx0, seed, clears);
    # default None stays byte-identical (all earlier tests run without it).
    from critter_gym.community import score_submission_on_season, season_seeds

    seen: list[tuple[int, int, int]] = []
    score_submission_on_season(
        lambda obs: 5, season=1, n_worlds=3,
        on_world=lambda i, seed, clears: seen.append((i, seed, clears)),
    )
    expected_seeds = list(season_seeds(1, 3))
    assert [s[0] for s in seen] == [0, 1, 2]
    assert [s[1] for s in seen] == expected_seeds
    assert all(isinstance(s[2], int) and 0 <= s[2] <= 3 for s in seen)


def test_llm_progress_line_format(capsys):
    # AC4 (cli-complete-retry): the --llm per-world progress line format, exercised via
    # the same callback wiring the script installs (no LLM involved).
    from critter_gym.community import score_submission_on_season

    n = 2

    def _progress(i: int, seed: int, clears: int) -> None:
        print(f"  [{i + 1}/{n}] seed={seed} clears={clears}", flush=True)

    score_submission_on_season(lambda obs: 5, season=1, n_worlds=n, on_world=_progress)
    out = capsys.readouterr().out.splitlines()
    import re
    assert len(out) == n
    assert all(re.fullmatch(r"  \[\d/2\] seed=\d+ clears=\d", line) for line in out)
