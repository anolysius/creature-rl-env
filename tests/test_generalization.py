"""Tests for the numpy-only generalization measurement harness (M2-EC4).

The harness is policy-agnostic, so we exercise it with the shipped baseline
policies (no torch / stable-baselines3 needed) — that is the whole point: the
measurement logic stays verifiable in the core CI.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from critter_gym import generalization as gen
from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import (
    EvalResult,
    GapReport,
    evaluate,
    format_report,
    measure_generalization,
    rollout,
    split_train_pool,
)
from critter_gym.region import heldout_seeds, train_seeds

CFG = dict(grid_size=6, num_creatures=6, num_gyms=2, max_steps=40, patch_radius=3)


def make_factory(vary: bool = True):
    def factory() -> CritterEnv:
        return CritterEnv(vary=vary, **CFG)  # type: ignore[arg-type]

    return factory


def greedy(obs: dict) -> int:
    return greedy_policy(obs, grid_size=CFG["grid_size"])


# -- AC4: determinism ---------------------------------------------------------


def test_rollout_is_deterministic() -> None:
    f = make_factory()
    assert rollout(f, greedy, seed=7) == rollout(f, greedy, seed=7)


# -- AC1 / arithmetic ---------------------------------------------------------


def test_evaluate_arithmetic() -> None:
    f = make_factory()
    seeds = list(train_seeds(5))
    res = evaluate(f, greedy, seeds)
    assert isinstance(res, EvalResult)
    assert res.n == 5
    assert res.seeds == tuple(seeds)
    assert res.mean == pytest.approx(float(np.mean(res.returns)))
    assert res.std == pytest.approx(float(np.std(res.returns)))


# -- AC5: gap measured on the procgen variant (vary=True) ---------------------


def test_measure_generalization_gap_on_procgen() -> None:
    f = make_factory(vary=True)
    rep = measure_generalization(f, greedy, train_seeds(4), heldout_seeds(4))
    assert isinstance(rep, GapReport)
    assert rep.gap == pytest.approx(rep.train.mean - rep.test.mean)
    assert rep.train.n == 4 and rep.test.n == 4
    # not vacuous: the headline measurement actually produced per-seed returns
    # and finite means on the procgen variant (new map + new type chart each seed).
    assert len(rep.train.returns) == 4 and len(rep.test.returns) == 4
    assert np.isfinite(rep.train.mean) and np.isfinite(rep.test.mean)
    assert np.isfinite(rep.gap)


# -- AC3: split-API leak guards at the call site ------------------------------


def test_train_arg_rejects_heldout_seeds() -> None:
    f = make_factory()
    with pytest.raises(ValueError, match="training region"):
        measure_generalization(f, greedy, heldout_seeds(3), heldout_seeds(3))


def test_test_arg_rejects_training_seeds() -> None:
    f = make_factory()
    with pytest.raises(ValueError, match="held-out"):
        measure_generalization(f, greedy, train_seeds(3), train_seeds(3))


# -- AC6: held-in eval ∩ learning seeds = ∅ (anti optimism-bias invariant) -----


def test_split_train_pool_is_disjoint_and_total() -> None:
    pool = tuple(train_seeds(20))
    learn, held_in = split_train_pool(pool, n_eval=5)
    assert len(held_in) == 5
    assert set(learn).isdisjoint(held_in)  # the load-bearing invariant
    assert set(learn) | set(held_in) == set(pool)  # nothing dropped
    assert all(s < 1_000_000 for s in learn + held_in)  # both in training region


def test_split_train_pool_rejects_oversized_eval() -> None:
    with pytest.raises(ValueError):
        split_train_pool(train_seeds(4), n_eval=4)  # leaves no learning seeds


# -- AC7: report contract (frozen keys + numbers in the rendered table) -------


def test_report_contract_keys_and_numbers() -> None:
    train = EvalResult(seeds=(0, 1), returns=(2.0, 4.0))  # mean 3.0
    test = EvalResult(seeds=(1_000_000,), returns=(1.0,))  # mean 1.0
    rep = GapReport(train=train, test=test)
    assert rep.gap == pytest.approx(2.0)

    d = rep.to_dict()
    assert set(d) == {"train_mean", "test_mean", "gap", "n_train", "n_test"}
    assert d["n_train"] == 2.0 and d["n_test"] == 1.0

    text = format_report(rep)
    assert "3.000" in text  # train_mean
    assert "1.000" in text  # test_mean
    assert "2.000" in text  # gap


# -- AC2: harness pulls in no learning dependency -----------------------------


def test_harness_is_numpy_only() -> None:
    src = inspect.getsource(gen)
    assert "import torch" not in src
    assert "stable_baselines3" not in src


def test_random_policy_also_works_through_harness() -> None:
    # policy-agnostic: a stochastic baseline runs too (uses its own rng).
    rng = np.random.default_rng(0)
    rep = measure_generalization(
        make_factory(), lambda o: random_policy(o, rng), train_seeds(3), heldout_seeds(3)
    )
    assert rep.train.n == 3 and rep.test.n == 3
