"""Baseline score table — train+test scores across N policies (M3-EC1).

A thin, **numpy-only** orchestration layer over :mod:`critter_gym.generalization`:
run the train-vs-test gap measurement once per baseline policy and collect the
results into one table. This is the data foundation the leaderboard (M3-EC2),
measurement viz (M3-EC3), and killer demo (M3-EC6) build on.

Like the gap harness, this module carries **no learning dependency** (no torch /
stable-baselines3 / sb3-contrib): the *builder* is policy-agnostic and verified in
the numpy-only core CI with the shipped ``random``/``scripted`` baselines. The
learned baselines (PPO, recurrent PPO) are added by a consumer behind the ``[rl]``
extra (``scripts/benchmark.py``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from critter_gym.generalization import (
    EnvFactory,
    GapReport,
    PolicyFn,
    measure_generalization,
)


@dataclass(frozen=True)
class BaselineRow:
    """One baseline's train-vs-test measurement (a named :class:`GapReport`)."""

    name: str
    report: GapReport


@dataclass(frozen=True)
class ScoreTable:
    """Train+test scores across baselines (the M3-EC1 deliverable)."""

    rows: tuple[BaselineRow, ...]

    def to_dict(self) -> dict[str, dict[str, float]]:
        """``{baseline_name: GapReport.to_dict()}`` — leaderboard-ready (M3-EC2 hook).

        Per-baseline value keys are the :meth:`GapReport.to_dict` contract
        (``heldin_mean``/``heldout_mean``/``gap``/``n_heldin``/``n_heldout``). This
        layer only delegates, so any change to those keys propagates here from the
        single source in ``generalization.GapReport.to_dict``.
        """
        return {row.name: row.report.to_dict() for row in self.rows}

    def to_markdown(self) -> str:
        """Render as a human-readable table (one row per baseline)."""
        lines = [
            "| baseline | train (held-in) | test (held-out) | gap |",
            "|---|---|---|---|",
        ]
        for row in self.rows:
            d = row.report.to_dict()
            lines.append(
                f"| {row.name} | {d['heldin_mean']:.3f} | "
                f"{d['heldout_mean']:.3f} | {d['gap']:.3f} |"
            )
        return "\n".join(lines) + "\n"


def score_baselines(
    env_factory: EnvFactory,
    policies: Mapping[str, PolicyFn],
    train_seeds: Iterable[int],
    test_seeds: Iterable[int],
) -> ScoreTable:
    """Measure every baseline in ``policies`` over the same train/test seed split.

    Each baseline is evaluated with :func:`measure_generalization`, so the split
    leak guard (held-out seeds rejected from the train arg, and vice versa) is
    inherited unchanged — the table cannot be built on a leaked split. Insertion
    order of ``policies`` is preserved in the resulting rows.
    """
    # Materialize once so each baseline sees the same seeds (a one-shot iterable
    # would be exhausted after the first policy).
    train = tuple(int(s) for s in train_seeds)
    test = tuple(int(s) for s in test_seeds)
    rows = tuple(
        BaselineRow(name=name, report=measure_generalization(env_factory, policy, train, test))
        for name, policy in policies.items()
    )
    return ScoreTable(rows=rows)
