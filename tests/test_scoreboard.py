"""Tests for the numpy-only baseline score-table builder (M3-EC1).

The builder is policy-agnostic, so the core CI exercises it with the shipped
``random``/``scripted`` baselines (no torch needed). A separate ``[rl]`` smoke
(skipped unless stable-baselines3 + sb3-contrib are installed) verifies that the
learned-baseline lazy-import path constructs and feeds the table without error.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from critter_gym import scoreboard as sb
from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.region import heldout_seeds, train_seeds
from critter_gym.scoreboard import ScoreTable, score_baselines

CFG = dict(grid_size=6, num_creatures=6, num_gyms=2, max_steps=40, patch_radius=3)


def make_factory(vary: bool = True):
    def factory() -> CritterEnv:
        return CritterEnv(vary=vary, **CFG)  # type: ignore[arg-type]

    return factory


def _core_policies():
    rng = np.random.default_rng(0)
    return {
        "random": lambda o: random_policy(o, rng),
        "scripted": lambda o: greedy_policy(o, grid_size=CFG["grid_size"]),
    }


# -- AC1 / AC6: table shape + report contract ---------------------------------


def test_score_table_shape_and_contract() -> None:
    table = score_baselines(make_factory(), _core_policies(), train_seeds(4), heldout_seeds(4))
    assert isinstance(table, ScoreTable)
    assert [r.name for r in table.rows] == ["random", "scripted"]  # insertion order

    d = table.to_dict()
    assert set(d) == {"random", "scripted"}
    for row in d.values():
        assert set(row) == {"train_mean", "test_mean", "gap", "n_train", "n_test"}
        assert row["n_train"] == 4 and row["n_test"] == 4

    md = table.to_markdown()
    assert "random" in md and "scripted" in md
    assert "train (held-in)" in md and "test (held-out)" in md and "gap" in md


# -- AC5: benchmark validity — the spread survives in table form --------------


def test_table_preserves_baseline_spread() -> None:
    table = score_baselines(make_factory(), _core_policies(), train_seeds(16), heldout_seeds(16))
    d = table.to_dict()
    # A valid benchmark keeps scripted *measurably* above random on held-out seeds.
    # A margin (not a bare `>`) keeps the validity signal from flickering on noise.
    assert d["scripted"]["test_mean"] > d["random"]["test_mean"] + 0.5


# -- AC4: determinism ---------------------------------------------------------


def test_score_table_is_deterministic() -> None:
    # scripted is deterministic; build twice and compare its row.
    pol = {"scripted": lambda o: greedy_policy(o, grid_size=CFG["grid_size"])}
    a = score_baselines(make_factory(), pol, train_seeds(4), heldout_seeds(4)).to_dict()
    b = score_baselines(make_factory(), pol, train_seeds(4), heldout_seeds(4)).to_dict()
    assert a == b


# -- AC3: split leak guard inherited from measure_generalization --------------


def test_score_baselines_inherits_leak_guard() -> None:
    with pytest.raises(ValueError, match="training region"):
        score_baselines(make_factory(), _core_policies(), heldout_seeds(3), heldout_seeds(3))


# -- AC2: builder pulls in no learning dependency -----------------------------


def test_scoreboard_is_numpy_only() -> None:
    src = inspect.getsource(sb)
    assert "import torch" not in src
    assert "stable_baselines3" not in src
    assert "sb3_contrib" not in src


# -- AC8: [rl] smoke — learned-baseline lazy-import path builds the table ------


def test_rl_baselines_smoke() -> None:
    PPO = pytest.importorskip("stable_baselines3").PPO
    RecurrentPPO = pytest.importorskip("sb3_contrib").RecurrentPPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    factory = make_factory()
    ppo = PPO("MultiInputPolicy", DummyVecEnv([factory]), n_steps=64, seed=0, verbose=0)
    rec = RecurrentPPO(
        "MultiInputLstmPolicy", DummyVecEnv([factory]), n_steps=64, seed=0, verbose=0
    )
    ppo.learn(64)
    rec.learn(64)

    rng = np.random.default_rng(0)
    policies = {
        "random": lambda o: random_policy(o, rng),
        "scripted": lambda o: greedy_policy(o, grid_size=CFG["grid_size"]),
        "ppo": lambda o: int(ppo.predict(o, deterministic=True)[0]),
        "recurrent": lambda o: int(rec.predict(o, deterministic=True)[0]),
    }
    table = score_baselines(factory, policies, train_seeds(2), heldout_seeds(2))
    assert {r.name for r in table.rows} == {"random", "scripted", "ppo", "recurrent"}
    assert all(set(v) == {"train_mean", "test_mean", "gap", "n_train", "n_test"}
               for v in table.to_dict().values())
