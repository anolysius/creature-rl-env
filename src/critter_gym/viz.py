"""Measurement visualization for the benchmark (M3-EC3).

Plots the four benchmark charts a *researcher* reads — **not** game-world art
(customer = RL researchers, NOT gamers; see CLAUDE.md):

- baseline spread       — held-out mean per baseline (is the benchmark non-trivial?)
- generalization gap    — held-in vs held-out per baseline (how much is memorized?)
- seed distribution     — per-seed held-out return spread (variance across worlds)
- learning curve        — held-in / held-out mean over training timesteps

Isolation mirrors the rest of the stack: the **plot-ready data shaping is
numpy-only** (tested in the core CI), while **matplotlib is imported lazily inside
the plot functions** so the module stays importable without it. matplotlib itself
lives behind the optional ``[viz]`` extra; the measurement modules
(``generalization``/``scoreboard``/``leaderboard``) never import this module — the
dependency arrow points only one way (viz → measurement).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from critter_gym.scoreboard import ScoreTable

if TYPE_CHECKING:  # avoid importing matplotlib at module load (keeps core numpy-only)
    from matplotlib.figure import Figure


@dataclass(frozen=True)
class LearningCurve:
    """Held-in / held-out mean return over training timesteps (a pure container).

    Populated by a training loop (``scripts/train_ppo.py``); kept dependency-free so
    the plotting logic is testable in the core CI with synthetic data.
    """

    timesteps: tuple[int, ...]
    heldin_means: tuple[float, ...]
    heldout_means: tuple[float, ...]


# -- numpy-only data shaping (no matplotlib) ----------------------------------


def spread_data(table: ScoreTable) -> tuple[list[str], list[float]]:
    """(names, held-out means) for the baseline-spread bar chart."""
    return (
        [row.name for row in table.rows],
        [row.report.test.mean for row in table.rows],
    )


def gap_data(table: ScoreTable) -> tuple[list[str], list[float], list[float]]:
    """(names, held-in means, held-out means) for the generalization-gap chart."""
    return (
        [row.name for row in table.rows],
        [row.report.train.mean for row in table.rows],
        [row.report.test.mean for row in table.rows],
    )


def seed_distribution_data(table: ScoreTable) -> dict[str, tuple[float, ...]]:
    """{baseline: per-seed held-out returns} for the seed-distribution chart."""
    return {row.name: row.report.test.returns for row in table.rows}


# -- matplotlib drawing (lazy import, Agg backend) ----------------------------


def _new_axes() -> tuple[Figure, Any]:
    """A fresh (Figure, Axes) on the headless Agg backend (no display needed)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    return fig, ax


def plot_baseline_spread(table: ScoreTable) -> Figure:
    """Bar chart of held-out mean return per baseline."""
    names, means = spread_data(table)
    fig, ax = _new_axes()
    ax.bar(names, means, color="tab:blue")
    ax.set_ylabel("held-out mean return")
    ax.set_title("Baseline spread (held-out)")
    return fig


def plot_generalization_gap(table: ScoreTable) -> Figure:
    """Grouped bars of held-in vs held-out mean per baseline."""
    import numpy as np

    names, heldin, heldout = gap_data(table)
    x = np.arange(len(names))
    width = 0.4
    fig, ax = _new_axes()
    ax.bar(x - width / 2, heldin, width, label="held-in")
    ax.bar(x + width / 2, heldout, width, label="held-out")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("mean return")
    ax.set_title("Generalization gap (held-in vs held-out)")
    ax.legend()
    return fig


def plot_seed_distributions(table: ScoreTable) -> Figure:
    """Box plot of per-seed held-out returns per baseline (variance across worlds)."""
    data = seed_distribution_data(table)
    names = list(data)
    fig, ax = _new_axes()
    ax.boxplot([list(data[n]) for n in names])
    # set tick labels separately (boxplot's `labels`/`tick_labels` kwarg name
    # changed across matplotlib 3.7–3.9; this is version-stable).
    ax.set_xticks(range(1, len(names) + 1))
    ax.set_xticklabels(names)
    ax.set_ylabel("held-out return per seed")
    ax.set_title("Seed distribution (held-out)")
    return fig


def plot_learning_curve(curve: LearningCurve) -> Figure:
    """Two lines — held-in and held-out mean return — over training timesteps."""
    fig, ax = _new_axes()
    ax.plot(curve.timesteps, curve.heldin_means, marker="o", label="held-in")
    ax.plot(curve.timesteps, curve.heldout_means, marker="o", label="held-out")
    ax.set_xlabel("timesteps")
    ax.set_ylabel("mean return")
    ax.set_title("Learning curve")
    ax.legend()
    return fig


def save_all(
    table: ScoreTable, outdir: str, curve: LearningCurve | None = None
) -> list[str]:
    """Render every chart to PNGs under ``outdir``; return the written paths.

    The learning curve is included only when a :class:`LearningCurve` is supplied
    (it needs a real training run). Figures are closed after saving so a long batch
    does not leak matplotlib state.
    """
    import os

    import matplotlib.pyplot as plt

    os.makedirs(outdir, exist_ok=True)
    figs: list[tuple[str, Figure]] = [
        ("baseline_spread.png", plot_baseline_spread(table)),
        ("generalization_gap.png", plot_generalization_gap(table)),
        ("seed_distribution.png", plot_seed_distributions(table)),
    ]
    if curve is not None:
        figs.append(("learning_curve.png", plot_learning_curve(curve)))

    paths: list[str] = []
    for name, fig in figs:
        path = os.path.join(outdir, name)
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)
    return paths
