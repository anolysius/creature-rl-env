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


def test_widened_train_loo_smoke() -> None:  # AC1/AC3 — widened-train LOO incl. duel
    pytest.importorskip("stable_baselines3")
    script = _load()
    families = ["critter", "forage", "duel", "muster"]
    folds = script.train_and_transfer_loo(
        families, timesteps=256, n_heldin=2, n_heldout=2, seed=0,
    )
    # one fold per family held out; each is a TransferReport on the shared gap metric.
    assert [f.heldout_family for f in folds] == families
    for f in folds:
        assert math.isfinite(f.gap)
        # the held-out family is never in its own train set (family-level split).
        assert f.heldout_family not in f.train_families
        # duel is now trainable/evaluable in LOO (impossible before obs harmonization).
        assert len(f.train_families) == len(families) - 1
    # duel is held out in its own fold (so excluded there) yet trained on in the others —
    # both only possible post-harmonization.
    duel_fold = next(f for f in folds if f.heldout_family == "duel")
    assert "duel" not in duel_fold.train_families
    assert any("duel" in f.train_families for f in folds if f.heldout_family != "duel")


def test_widened_train_loo_multirun_smoke() -> None:  # AC1/AC3 — multi-run robustness
    pytest.importorskip("stable_baselines3")
    script = _load()
    families = ["critter", "forage", "duel", "muster"]
    folds = script.train_and_transfer_loo_multirun(
        families, timesteps=256, n_runs=2, n_heldin=2, n_heldout=2, base_seed=0,
    )
    assert [f.heldout_family for f in folds] == families
    for f in folds:
        assert f.n_runs == 2
        # per-fold aggregates across runs: mean + std (run-to-run variance) are finite.
        assert math.isfinite(f.gap_mean) and math.isfinite(f.gap_std)
        assert math.isfinite(f.heldin_mean) and math.isfinite(f.heldin_std)
        assert math.isfinite(f.heldout_mean) and math.isfinite(f.heldout_std)
        assert f.gap_std >= 0.0
        assert f.heldout_family not in f.train_families


def test_improved_policy_config_smoke_and_deterministic() -> None:  # AC1/AC4 — (a') knobs
    pytest.importorskip("stable_baselines3")
    script = _load()
    # the improved knobs (bigger net + deterministic large-key obs scaling) run and stay
    # backward-compatible; same seed → identical result (no running-stats nondeterminism).
    kw = dict(timesteps=256, n_heldin=2, n_heldout=2, seed=0,
              net_arch=[32, 32], scale_obs=True)
    r1 = script.train_and_transfer(["critter", "forage"], "muster", **kw)
    r2 = script.train_and_transfer(["critter", "forage"], "muster", **kw)
    assert math.isfinite(r1.heldin_mean) and math.isfinite(r1.gap)
    assert r1.heldin_mean == r2.heldin_mean  # deterministic (AC4)
    assert r1.heldout_mean == r2.heldout_mean
    # bare baseline still works (knobs default off — backward compat).
    base = script.train_and_transfer(["critter", "forage"], "muster",
                                     timesteps=256, n_heldin=2, n_heldout=2, seed=0)
    assert math.isfinite(base.heldin_mean)
