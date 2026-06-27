"""Tests for the sealed held-out eval harness (eval-product/sealed-eval-harness).

The harness is the M5-enabler prototype of a *contamination-proof* eval: a private block
of held-out worlds the submitter never sees, RLVR-verified scoring, and a contamination
guard that proves the submitter could not have trained on the eval. These tests pin the
moat-load-bearing invariants: the sealed block is held-out + deterministic + regenerable,
the guard catches a train/eval leak, and scoring uses only verifiable subgoals.
"""
from __future__ import annotations

from critter_gym.eval_harness import (
    Scorecard,
    SealedEvalSet,
    score_agent,
    verify_sealed,
)
from critter_gym.learnability import reference_arm
from critter_gym.region import TEST_SEED_OFFSET, is_held_out


# --- AC1: sealed held-out block (private, deterministic, regenerable) ---------
def test_eval_seeds_are_all_held_out() -> None:
    s = SealedEvalSet(master_seed=7, n_worlds=12)
    seeds = s._eval_seeds()
    assert len(seeds) == 12
    assert all(is_held_out(x) for x in seeds)  # every world is in the test region (>=1M)


def test_eval_seeds_deterministic_same_master() -> None:
    a = SealedEvalSet(master_seed=7, n_worlds=12)._eval_seeds()
    b = SealedEvalSet(master_seed=7, n_worlds=12)._eval_seeds()
    assert a == b  # same master_seed -> same sealed block (reproducible)


def test_eval_seeds_regenerate_different_master() -> None:
    a = set(SealedEvalSet(master_seed=7, n_worlds=12)._eval_seeds())
    b = set(SealedEvalSet(master_seed=8, n_worlds=12)._eval_seeds())
    assert a != b  # a different master_seed yields a fresh, different block


# --- AC2: contamination guard (the moat mechanic) ----------------------------
def test_verify_sealed_clean_train_ok() -> None:
    s = SealedEvalSet(master_seed=1, n_worlds=8)
    cert = verify_sealed(declared_train_seeds=range(0, 5000), sealed=s)
    assert cert.ok is True
    assert cert.overlap == 0
    assert cert.all_eval_held_out is True
    assert cert.n_eval == 8


def test_verify_sealed_catches_leak() -> None:
    # A submitter who (dishonestly or accidentally) trained on the sealed eval seeds.
    s = SealedEvalSet(master_seed=1, n_worlds=8)
    leaked = list(range(0, 100)) + list(s._eval_seeds())  # includes the sealed block
    cert = verify_sealed(declared_train_seeds=leaked, sealed=s)
    assert cert.ok is False
    assert cert.overlap == 8  # all 8 sealed seeds detected in the declared train set


def test_verify_sealed_rejects_out_of_region_train() -> None:
    # Declaring "train" seeds in the held-out region is itself illegal (train must be <1M).
    s = SealedEvalSet(master_seed=1, n_worlds=8)
    cert = verify_sealed(declared_train_seeds=[0, 1, TEST_SEED_OFFSET + 999], sealed=s)
    assert cert.ok is False


# --- AC3 + AC4: RLVR-verified scoring + submission interface ------------------
def test_score_agent_oracle_beats_random_and_rates_bounded() -> None:
    s = SealedEvalSet(master_seed=3, n_worlds=8)

    oracle_card = score_agent(reference_arm("oracle"), s)  # EnvPolicy reference
    random_card = score_agent(_RandomAgent(seed=0), s)

    assert isinstance(oracle_card, Scorecard)
    assert oracle_card.n_worlds == 8
    # oracle is a strong reference; it should out-clear a random agent on the sealed worlds.
    assert oracle_card.mean_gyms_cleared > random_card.mean_gyms_cleared
    # RLVR rates are proper fractions; frac_of_oracle is non-negative.
    for card in (oracle_card, random_card):
        assert 0.0 <= card.cleared_rate <= 1.0
        assert 0.0 <= card.caught_rate <= 1.0
        assert 0.0 <= card.evolved_rate <= 1.0
        assert card.frac_of_oracle >= 0.0
    # The sealed certificate travels with the scorecard.
    assert card.n_worlds == 8


def test_score_agent_obs_only_interface() -> None:
    """An obs-only `Agent` (act(obs)->int) is accepted — same interface an LLM agent uses."""
    s = SealedEvalSet(master_seed=5, n_worlds=6)
    card = score_agent(_RandomAgent(seed=1), s)
    assert card.n_worlds == 6
    assert card.frac_of_oracle >= 0.0


class _RandomAgent:
    """A trivial obs-only submission: act(obs) -> action (Agent Protocol)."""

    def __init__(self, seed: int) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)

    def act(self, obs: object) -> int:
        return int(self._rng.integers(0, 6))
