"""AC3 — environment-level (genre) generalization measurement API.

Verifies the env-level measurement runs train-family → unseen-family for a
family-agnostic policy and reports a gap. numpy-only; the gap is a *signal*, never a
pass threshold (two families is a foundation, not a genre-generalization proof).
"""

from __future__ import annotations

import numpy as np

from critter_gym.baselines import random_policy
from critter_gym.genre_generalization import (
    GenreGapReport,
    measure_genre_generalization,
)
from critter_gym.region import heldout_seeds
from critter_gym.registration import register_envs

register_envs()


def _random(rng):
    return lambda obs: random_policy(obs, rng)


def test_measure_genre_generalization_runs_train_to_unseen_family() -> None:
    rng = np.random.default_rng(0)
    report = measure_genre_generalization(
        _random(rng), train_family="critter", test_family="forage",
        seeds=heldout_seeds(8),
    )
    assert isinstance(report, GenreGapReport)
    assert report.train_family == "critter" and report.test_family == "forage"
    assert np.isfinite(report.train_mean) and np.isfinite(report.test_mean)
    assert np.isfinite(report.gap)


def test_report_markdown_renders_both_families_and_gap() -> None:
    rng = np.random.default_rng(1)
    md = measure_genre_generalization(
        _random(rng), "critter", "forage", heldout_seeds(4)
    ).to_markdown()
    assert "critter" in md and "forage" in md and "env-level gap" in md


def test_gap_is_signed_difference() -> None:
    r = GenreGapReport("a", "b", train_mean=3.0, test_mean=1.0)
    assert r.gap == 2.0


# -- AC4: multi-family (leave-one-out) env-level measurement --------------------

_SEEDS = tuple(heldout_seeds(8))


def test_leave_one_out_measures_three_families() -> None:  # AC4
    from critter_gym.genre_generalization import (
        LeaveOneOutGap,
        duel_aware_policy,
        measure_genre_generalization_loo,
    )

    gaps = measure_genre_generalization_loo(
        duel_aware_policy, ["critter", "forage", "duel"], _SEEDS
    )
    assert len(gaps) == 3
    held = {g.held_out for g in gaps}
    assert held == {"critter", "forage", "duel"}
    for g in gaps:
        assert isinstance(g, LeaveOneOutGap)
        assert "duel" not in g.train_families if g.held_out == "duel" else True
        assert np.isfinite(g.gap) and np.isfinite(g.train_mean) and np.isfinite(g.heldout_mean)


def test_two_family_pairwise_api_unregressed() -> None:  # AC4 (no regression)
    rng = np.random.default_rng(7)
    report = measure_genre_generalization(
        _random(rng), "critter", "forage", _SEEDS
    )
    assert isinstance(report, GenreGapReport)
    assert np.isfinite(report.gap)


# -- AC5: the gap on family C is SKILL-STRUCTURAL, not a difficulty confound -----

def test_family_c_gap_is_skill_structural_not_difficulty() -> None:  # AC5
    # The anti-confound discriminator (L1 measurement reviewer): on family C, a
    # C-appropriate policy scores HIGH while an A-tuned (always-attack) policy scores
    # LOW. So the env-level gap reflects a WRONG SKILL, not "C is just hard for any
    # policy" (which AC3's winnable-by-some-policy alone would not rule out).
    from critter_gym.genre_generalization import (
        duel_aware_policy,
        measure_genre_generalization_loo,
        type_attacker_policy,
    )

    # On family C directly: C-appropriate ≫ A-tuned (≈ pilot 4.3 vs 0.6).
    a_loo = measure_genre_generalization_loo(
        type_attacker_policy, ["critter", "forage", "duel"], _SEEDS
    )
    c_loo = measure_genre_generalization_loo(
        duel_aware_policy, ["critter", "forage", "duel"], _SEEDS
    )
    a_on_c = next(g.heldout_mean for g in a_loo if g.held_out == "duel")
    c_on_c = next(g.heldout_mean for g in c_loo if g.held_out == "duel")
    assert c_on_c > a_on_c, "C-appropriate policy must beat the A-tuned policy on family C"

    # And the held-out-duel gap is far larger for the A-tuned policy (skill mismatch)
    # than for the C-appropriate one (which transfers).
    a_gap_duel = next(g.gap for g in a_loo if g.held_out == "duel")
    c_gap_duel = next(g.gap for g in c_loo if g.held_out == "duel")
    assert a_gap_duel > c_gap_duel, "A-tuned shows a larger env-level gap on held-out duel"


# -- family-d-muster: 4-family leave-one-out -----------------------------------

def test_leave_one_out_measures_four_families() -> None:  # AC4
    from critter_gym.genre_generalization import (
        measure_genre_generalization_loo,
        muster_policy,
    )

    gaps = measure_genre_generalization_loo(
        muster_policy, ["critter", "forage", "duel", "muster"], _SEEDS
    )
    assert {g.held_out for g in gaps} == {"critter", "forage", "duel", "muster"}
    for g in gaps:
        assert np.isfinite(g.gap)
        if g.held_out == "muster":
            assert "muster" not in g.train_families
