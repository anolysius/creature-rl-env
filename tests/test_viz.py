"""Tests for the measurement-viz layer (M3-EC3).

The data-shaping helpers and the import-isolation guard run in the core CI
(numpy-only). The actual matplotlib drawing is exercised behind
``importorskip("matplotlib")`` so it is verified when the ``[viz]`` extra is
installed but never pulls matplotlib into the numpy-only core.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from critter_gym import generalization, leaderboard, scoreboard
from critter_gym import viz as vizmod
from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.region import heldout_seeds, train_seeds
from critter_gym.scoreboard import score_baselines
from critter_gym.viz import (
    LearningCurve,
    gap_data,
    seed_distribution_data,
    spread_data,
)

CFG = dict(grid_size=6, num_creatures=6, num_gyms=2, max_steps=40, patch_radius=3)


def _table():
    def factory() -> CritterEnv:
        return CritterEnv(vary=True, **CFG)  # type: ignore[arg-type]

    rng = np.random.default_rng(0)
    policies = {
        "random": lambda o: random_policy(o, rng),
        "scripted": lambda o: greedy_policy(o, grid_size=CFG["grid_size"]),
    }
    return score_baselines(factory, policies, train_seeds(6), heldout_seeds(6))


# -- AC3: numpy-only data shaping ---------------------------------------------


def test_spread_data() -> None:
    names, means = spread_data(_table())
    assert names == ["random", "scripted"]
    assert len(means) == 2 and all(isinstance(m, float) for m in means)


def test_gap_data() -> None:
    names, heldin, heldout = gap_data(_table())
    assert names == ["random", "scripted"]
    assert len(heldin) == len(heldout) == 2


def test_seed_distribution_data_is_per_seed() -> None:
    dist = seed_distribution_data(_table())
    assert set(dist) == {"random", "scripted"}
    # one held-out return per eval seed (6 seeds)
    assert all(len(v) == 6 for v in dist.values())


def test_learning_curve_is_a_plain_container() -> None:
    curve = LearningCurve(timesteps=(1, 2), heldin_means=(0.5, 1.0), heldout_means=(0.3, 0.7))
    assert curve.timesteps == (1, 2)


# -- AC2: import isolation (dependency arrow points one way) ------------------


def test_viz_has_no_toplevel_matplotlib_import() -> None:
    src = inspect.getsource(vizmod)
    # matplotlib is imported lazily *inside* functions, never at module top level.
    header = src.split("def ", 1)[0]
    assert "import matplotlib" not in header


def test_measurement_modules_do_not_import_viz_or_matplotlib() -> None:
    for mod in (generalization, scoreboard, leaderboard):
        src = inspect.getsource(mod)
        assert "matplotlib" not in src
        assert "import viz" not in src and "critter_gym.viz" not in src


# -- AC4/AC5: [viz] smoke — real matplotlib drawing ---------------------------


def test_plot_functions_return_figures() -> None:
    pytest.importorskip("matplotlib")
    table = _table()
    spread = vizmod.plot_baseline_spread(table)
    gap = vizmod.plot_generalization_gap(table)
    seeds = vizmod.plot_seed_distributions(table)
    curve = vizmod.plot_learning_curve(
        LearningCurve(timesteps=(1, 2, 3), heldin_means=(0.0, 0.5, 1.0),
                      heldout_means=(0.0, 0.3, 0.6))
    )

    # non-vacuous: each figure has the expected content.
    assert len(spread.axes[0].patches) == 2  # one bar per baseline
    assert len(gap.axes[0].patches) == 4  # held-in + held-out × 2 baselines
    assert len(curve.axes[0].lines) == 2  # held-in + held-out lines
    # one box slot per baseline (verified via the tick labels we set).
    assert [t.get_text() for t in seeds.axes[0].get_xticklabels()] == ["random", "scripted"]


def test_agg_backend_is_headless() -> None:
    pytest.importorskip("matplotlib")
    vizmod.plot_baseline_spread(_table())
    import matplotlib

    assert matplotlib.get_backend().lower() == "agg"


def test_save_all_writes_nonempty_pngs(tmp_path) -> None:
    pytest.importorskip("matplotlib")
    curve = LearningCurve(timesteps=(1, 2), heldin_means=(0.1, 0.9), heldout_means=(0.1, 0.5))
    paths = vizmod.save_all(_table(), str(tmp_path), curve=curve)
    assert len(paths) == 4  # spread, gap, seed-dist, learning-curve
    for p in paths:
        import os

        assert os.path.getsize(p) > 0


def test_save_all_skips_learning_curve_when_absent(tmp_path) -> None:
    pytest.importorskip("matplotlib")
    paths = vizmod.save_all(_table(), str(tmp_path))
    assert len(paths) == 3  # no learning curve without a LearningCurve
