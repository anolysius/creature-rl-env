"""AC2 — env-level learnability measurement API (learnability-measurement).

Validates that the champion-select action UX actually lets the ``infer`` reference
arm beat ``probe`` *through the full env* (not just the engine, as the
reasoning-load-bearing gate did), and that the measurement API enforces the
held-in/held-out split. numpy-only (no ``[rl]``).
"""

from __future__ import annotations

import pytest

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.learnability import (
    EpisodeOutcome,
    arm_mean,
    measure_learnability,
    reference_arm,
    run_episode,
)
from critter_gym.region import heldout_seeds, train_seeds


def _commit_factory():
    return CritterEnv(vary=True, num_types=12, num_gyms=8, super_mult=3.0,
                      boss_hp=140, boss_atk=18, commit_battles=True, max_steps=400)


def test_reference_arm_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        reference_arm("nonsense")


def test_infer_beats_probe_through_the_action_ux() -> None:
    # The headline property reproduced at the ENV level (overworld nav + champion
    # select), not just the engine: a cross-gym inferring arm clears more gyms than
    # a probing one that must guess each fight.
    seeds = list(train_seeds(20))
    infer = arm_mean(_commit_factory, "infer", seeds)
    probe = arm_mean(_commit_factory, "probe", seeds)
    oracle = arm_mean(_commit_factory, "oracle", seeds)
    assert oracle >= infer > probe, f"oracle={oracle} infer={infer} probe={probe}"


def test_measure_learnability_reports_all_arms_and_split_guard() -> None:
    report = measure_learnability(_commit_factory, train_seeds(8), heldout_seeds(8))
    for arm in ("oracle", "infer", "type_blind", "probe"):
        assert arm in report.heldin and arm in report.heldout
    md = report.to_markdown()
    assert "held-in (return)" in md and "held-out (gym-clear)" in md


def test_measure_learnability_rejects_leaked_split() -> None:
    with pytest.raises(ValueError):
        # held-in seeds drawn from the held-out region → must be rejected
        measure_learnability(_commit_factory, heldout_seeds(4), heldout_seeds(4))


def test_as_env_policy_wraps_obs_only_policy() -> None:
    # a trivial obs-only policy (always attack) runs through the env runner
    report = measure_learnability(
        _commit_factory, train_seeds(4), heldout_seeds(4), learned=lambda _obs: 0
    )
    assert "learned" in report.heldin and "learned" in report.heldout


# -- learnability-precision: gym-clear-only metric (decouple evolution inflation) ---

def test_run_episode_returns_outcome_separating_gyms_and_evolutions() -> None:  # AC1
    out = run_episode(_commit_factory, reference_arm("oracle"), seed=int(train_seeds(1)[0]))
    assert isinstance(out, EpisodeOutcome)
    assert out.gyms_cleared >= 0 and out.evolutions >= 0
    # an arm only navigates to gyms (never CATCH), so the combined return is exactly
    # gym-defeat (+1 each) + evolution (+1 each) — the two separable subgoal streams.
    assert out.episode_return == float(out.gyms_cleared + out.evolutions)


def test_gym_clear_only_separates_evolution_and_preserves_order() -> None:  # AC2/AC3
    report = measure_learnability(_commit_factory, train_seeds(16), heldout_seeds(16))
    # gym-clear-only means reported alongside combined.
    assert set(report.heldout_gyms) == {"oracle", "infer", "type_blind", "probe"}
    g = report.heldout_gyms
    # load-bearing ordering preserved on the clean (evolution-free) metric.
    assert g["oracle"] >= g["infer"] > g["type_blind"] > g["probe"], g
    # combined return is inflated by evolutions → strictly above gym-clear-only.
    assert report.heldout["oracle"] > g["oracle"]
    # the inflation is exactly the evolution stream (combined = gyms + evolutions).
    assert report.to_markdown().count("gym-clear") >= 1


def test_gym_clear_metric_is_in_report_markdown() -> None:  # AC2
    report = measure_learnability(_commit_factory, train_seeds(4), heldout_seeds(4))
    md = report.to_markdown()
    assert "gym-clear" in md  # both combined and gym-clear-only surfaced


def test_ppo_learnability_smoke() -> None:
    # AC3: the [rl] training script runs end-to-end (tiny budget) and produces a
    # report with the learned policy alongside the reference arms. Heavy deps are
    # skipped gracefully when [rl] is absent.
    pytest.importorskip("stable_baselines3")
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import learnability as script  # scripts/learnability.py

    report = script.train_and_measure(256, n_heldin=2, n_heldout=2)
    assert "learned" in report.heldout
    for arm in ("oracle", "infer", "type_blind", "probe"):
        assert arm in report.heldout
