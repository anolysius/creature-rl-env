"""Reproducible benchmark leaderboard (M3-EC2).

Turns the M3-EC1 baseline score table (:mod:`critter_gym.scoreboard`) into a
**ranked, serializable, reproducible** leaderboard:

- :class:`BenchmarkSpec` pins everything needed to reproduce a run — the env
  config and the held-in / held-out evaluation seed counts (the procgen variant,
  ``vary=True``, is always used). Same spec → same eval seeds → same scores for a
  deterministic policy.
- :class:`Leaderboard` ranks baselines by **held-out** mean return (the headline
  metric of this benchmark: performance on *unseen* maps + type charts) and
  serializes to canonical JSON (with the spec embedded) and to markdown.

Like the layers it builds on, this module is **numpy-only** — no torch /
stable-baselines3. Learned baselines are supplied by a consumer behind the
``[rl]`` extra (``scripts/benchmark.py``).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.generalization import PolicyFn
from critter_gym.region import heldout_seeds, train_seeds
from critter_gym.scoreboard import score_baselines


@dataclass(frozen=True)
class BenchmarkSpec:
    """A pinned, reproducible benchmark *evaluation protocol* (the M3-EC2 ``config``).

    Pins everything on the environment side that affects the reported numbers — env
    config + the held-in / held-out eval seed sets (always ``vary=True``). It does
    **not** pin the agent's own randomness (a stochastic policy's RNG, an SB3
    ``seed=``): that is the submitter's responsibility. So a result reproduces
    exactly when the policy is deterministic; the spec guarantees the *protocol* is
    identical. Serialized into :meth:`Leaderboard.to_json` so a result is
    self-describing.
    """

    grid_size: int = 10
    num_creatures: int = 5
    num_gyms: int = 3
    max_steps: int = 200
    patch_radius: int = 2
    n_heldin: int = 100
    n_heldout: int = 100

    def env_factory(self) -> Callable[[], CritterEnv]:
        """A fresh procgen env (``vary=True``) built from this spec's config."""

        def factory() -> CritterEnv:
            return CritterEnv(
                grid_size=self.grid_size,
                num_creatures=self.num_creatures,
                num_gyms=self.num_gyms,
                max_steps=self.max_steps,
                patch_radius=self.patch_radius,
                vary=True,
            )

        return factory

    def heldin_eval_seeds(self) -> tuple[int, ...]:
        """Fixed held-in (training-region) evaluation seeds."""
        return tuple(train_seeds(self.n_heldin))

    def heldout_eval_seeds(self) -> tuple[int, ...]:
        """Fixed held-out (test-region) evaluation seeds — new maps + new charts."""
        return tuple(heldout_seeds(self.n_heldout))

    def to_dict(self) -> dict[str, int]:
        """Plain dict of the pinned config (for embedding in a result)."""
        return asdict(self)


DEFAULT_SPEC = BenchmarkSpec()


@dataclass(frozen=True)
class LeaderboardEntry:
    """One ranked baseline."""

    rank: int
    name: str
    heldin_mean: float
    heldout_mean: float
    gap: float


@dataclass(frozen=True)
class Leaderboard:
    """Baselines ranked by held-out mean (the M3-EC2 deliverable)."""

    spec: BenchmarkSpec
    entries: tuple[LeaderboardEntry, ...]

    def to_dict(self) -> dict[str, object]:
        """Canonical, reproducible result: pinned spec + ranked entries."""
        return {
            "spec": self.spec.to_dict(),
            "entries": [asdict(e) for e in self.entries],
        }

    def to_json(self) -> str:
        """Deterministic JSON (``sort_keys``) — same spec + policies → identical bytes."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    def to_markdown(self) -> str:
        """Ranked, human-readable leaderboard table."""
        lines = [
            "| rank | baseline | held-in | held-out | gap |",
            "|---|---|---|---|---|",
        ]
        for e in self.entries:
            lines.append(
                f"| {e.rank} | {e.name} | {e.heldin_mean:.3f} | "
                f"{e.heldout_mean:.3f} | {e.gap:.3f} |"
            )
        return "\n".join(lines) + "\n"


def run_benchmark(spec: BenchmarkSpec, policies: Mapping[str, PolicyFn]) -> Leaderboard:
    """Score every baseline on ``spec``'s pinned seeds and rank by held-out mean.

    Scoring goes through :func:`scoreboard.score_baselines`, so the split leak guard
    (held-in seeds must be training-region, held-out must be test-region) is
    inherited unchanged. Ranking is by held-out mean descending — the benchmark
    rewards generalization to unseen worlds, not in-distribution score. Ties break
    deterministically (smaller gap, then name) so the order never depends on the
    insertion order of ``policies``.
    """
    table = score_baselines(
        spec.env_factory(), policies, spec.heldin_eval_seeds(), spec.heldout_eval_seeds()
    )
    ranked = sorted(table.rows, key=lambda r: (-r.report.test.mean, r.report.gap, r.name))
    entries = tuple(
        LeaderboardEntry(
            rank=i + 1,
            name=row.name,
            heldin_mean=row.report.train.mean,
            heldout_mean=row.report.test.mean,
            gap=row.report.gap,
        )
        for i, row in enumerate(ranked)
    )
    return Leaderboard(spec=spec, entries=entries)
