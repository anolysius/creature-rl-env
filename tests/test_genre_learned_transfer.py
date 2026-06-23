"""Smoke test for the learned genre-transfer experiment (genre-learned-transfer).

The real measurement — does a PPO policy trained on train families {critter, forage}
transfer to an UNSEEN family {muster}? — is heavy ([rl]) and lives in
``scripts/genre_learned_transfer.py``, exercised here only at a tiny budget via
``importorskip``. Also checks the obs-compatibility guard (only obs-identical families
can share one net; duel — which adds charge keys — must be rejected).
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


def test_obs_incompatible_family_rejected() -> None:  # AC3
    script = _load()
    # duel has extra obs keys → cannot share a single net with critter/forage/muster.
    with pytest.raises(ValueError):
        script.assert_obs_compatible(["critter", "forage", "duel"])
    # the obs-identical set is accepted.
    script.assert_obs_compatible(["critter", "forage", "muster"])


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
