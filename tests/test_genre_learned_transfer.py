"""Smoke test for the learned genre-transfer experiment (genre-learned-transfer).

The real measurement — does a PPO policy trained on train families {critter, forage}
transfer to an UNSEEN family {muster}? — is heavy ([rl]) and lives in
``scripts/genre_learned_transfer.py``, exercised here only at a tiny budget via
``importorskip``. Also checks the obs-compatibility guard: after obs harmonization
(obs-harmonization task) all four families share one obs space, so the guard now
*accepts* duel — and the 4-family multi-env is constructible (the experiment is next).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest


def _load():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import genre_learned_transfer as script

    return script


def test_all_families_obs_compatible_after_harmonization() -> None:  # AC5
    script = _load()
    # After obs harmonization every family (incl. duel) shares one obs space, so a
    # single net can train across all four — duel is no longer rejected.
    script.assert_obs_compatible(["critter", "forage", "duel", "muster"])


def test_multifamily_env_constructs_with_duel() -> None:  # AC5 (smoke; experiment is next task)
    script = _load()
    families = ["critter", "forage", "duel", "muster"]
    script.assert_obs_compatible(families)
    env = script._MultiFamilyEnv(families, seeds=(0, 1, 2, 3))
    # the multi-family training env exposes the shared harmonized obs and cycles
    # through all four families (one per reset) without raising.
    seen = set()
    for _ in range(len(families)):
        obs, _ = env.reset()
        assert set(obs) == set(env.observation_space.spaces)
        seen.add(int(obs["in_battle"][0]))  # just touch the obs
    assert env.observation_space is not None


def test_train_and_transfer_smoke() -> None:  # AC2
    pytest.importorskip("stable_baselines3")
    script = _load()
    report = script.train_and_transfer(
        train_families=["critter", "forage"], heldout_family="muster",
        timesteps=256, n_heldin=2, n_heldout=2,
    )
    assert math.isfinite(report.heldin_mean)
    assert math.isfinite(report.heldout_mean)
    assert math.isfinite(report.gap)
    assert report.train_families == ("critter", "forage")
    assert report.heldout_family == "muster"
