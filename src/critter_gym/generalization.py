"""Train-vs-test generalization measurement harness (M2-EC4, DESIGN.md §3.1).

Policy-agnostic and **numpy-only**. Implements the Procgen-style generalization
protocol: an agent is trained on a pool of *training* seeds, then evaluated on
both held-in (training-region) and held-out (test-region) seeds. The reported
``gap = heldin_mean - heldout_mean`` quantifies how much performance is lost when the
agent meets unseen maps + unseen type charts — the moat this benchmark measures.

This module deliberately carries **no learning dependency** (no torch /
stable-baselines3) so the measurement logic is importable and tested in the
numpy-only core CI. The PPO trainer (``scripts/train_ppo.py``) is one consumer
behind the optional ``[rl]`` extra.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.region import is_held_out

Obs = dict[str, np.ndarray]
PolicyFn = Callable[[Obs], int]
EnvFactory = Callable[[], CritterEnv]


def rollout(env_factory: EnvFactory, policy: PolicyFn, seed: int) -> float:
    """Run one full episode at a fixed ``seed``; return the total (undiscounted) reward.

    Deterministic in (env config, policy, seed): a fresh env is built and reset to
    ``seed`` every call, so a deterministic policy reproduces the same return.
    """
    env = env_factory()
    obs, _ = env.reset(seed=int(seed))
    total = 0.0
    done = False
    while not done:
        obs, reward, terminated, truncated, _ = env.step(policy(obs))
        total += float(reward)
        done = bool(terminated or truncated)
    return total


@dataclass(frozen=True)
class EvalResult:
    """Per-seed returns over an evaluation set (an immutable measurement record)."""

    seeds: tuple[int, ...]
    returns: tuple[float, ...]

    @property
    def mean(self) -> float:
        return float(np.mean(self.returns)) if self.returns else 0.0

    @property
    def std(self) -> float:
        return float(np.std(self.returns)) if self.returns else 0.0

    @property
    def n(self) -> int:
        return len(self.seeds)


def evaluate(env_factory: EnvFactory, policy: PolicyFn, seeds: Iterable[int]) -> EvalResult:
    """Evaluate ``policy`` over ``seeds`` (one episode each); return an :class:`EvalResult`."""
    seeds_t = tuple(int(s) for s in seeds)
    returns = tuple(rollout(env_factory, policy, s) for s in seeds_t)
    return EvalResult(seeds=seeds_t, returns=returns)


def split_train_pool(
    seeds: Iterable[int], n_eval: int
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Split a training seed pool into ``(learn, held_in_eval)``, **disjoint**.

    The last ``n_eval`` seeds become the held-in evaluation set; the rest are for
    learning. Both stay in the training region (caller passes ``train_seeds(...)``)
    and the two sets are disjoint *by construction* — the load-bearing invariant
    that keeps the generalization gap from being optimistically biased by
    evaluating on seeds the agent actually trained on.
    """
    pool = tuple(int(s) for s in seeds)
    if n_eval < 0:
        raise ValueError(f"n_eval must be non-negative, got {n_eval}")
    if n_eval >= len(pool):
        raise ValueError(f"n_eval={n_eval} leaves no learning seeds in a pool of {len(pool)}")
    if n_eval == 0:
        return pool, ()
    return pool[:-n_eval], pool[-n_eval:]


@dataclass(frozen=True)
class GapReport:
    """A train-vs-test generalization measurement (the M2-EC4 deliverable)."""

    train: EvalResult  # held-in (training-region) evaluation
    test: EvalResult  # held-out (test-region) evaluation

    @property
    def gap(self) -> float:
        """Procgen convention: ``heldin_mean - heldout_mean`` (positive ⇒ overfits)."""
        return self.train.mean - self.test.mean

    def to_dict(self) -> dict[str, float]:
        """Stable, leaderboard-ready row (the public M3-EC2 schema).

        ``heldin_mean`` is the mean over the **held-in** (training-region) eval seeds,
        not a score on the seeds actually learned — by design these are kept disjoint
        (see :func:`split_train_pool`) so the gap reflects distribution shift, not
        memorization. The keys are named for what they measure (held-in / held-out
        *evaluation*) so a leaderboard consumer can't misread them as training scores.
        """
        return {
            "heldin_mean": self.train.mean,
            "heldout_mean": self.test.mean,
            "gap": self.gap,
            "n_heldin": float(self.train.n),
            "n_heldout": float(self.test.n),
        }


def measure_generalization(
    env_factory: EnvFactory,
    policy: PolicyFn,
    train_seeds: Iterable[int],
    test_seeds: Iterable[int],
) -> GapReport:
    """Evaluate ``policy`` on held-in vs held-out seeds; return a :class:`GapReport`.

    ``train_seeds`` are held-in (training-region, ``< TEST_SEED_OFFSET``) and
    ``test_seeds`` are held-out (``>= TEST_SEED_OFFSET``). The split is enforced at
    the call site so a leaked seed can never silently flatter the gap (M2-EC3).

    This guards *region membership* only. It cannot see which seeds the policy was
    trained on, so keeping the held-in eval set disjoint from the learning seeds is
    the caller's responsibility — use :func:`split_train_pool` to carve both from a
    single ``train_seeds(...)`` pool (as ``scripts/train_ppo.py`` does).
    """
    train_t = tuple(int(s) for s in train_seeds)
    test_t = tuple(int(s) for s in test_seeds)

    leaked = [s for s in train_t if is_held_out(s)]
    if leaked:
        raise ValueError(
            "held-in/train eval seeds must be in the training region "
            f"(< TEST_SEED_OFFSET); got held-out seeds {leaked[:5]}"
        )
    mislabeled = [s for s in test_t if not is_held_out(s)]
    if mislabeled:
        raise ValueError(
            "test seeds must be held-out (>= TEST_SEED_OFFSET); "
            f"got training-region seeds {mislabeled[:5]}"
        )

    return GapReport(
        train=evaluate(env_factory, policy, train_t),
        test=evaluate(env_factory, policy, test_t),
    )


def format_report(report: GapReport) -> str:
    """Render a :class:`GapReport` as a human-readable markdown table."""
    d = report.to_dict()
    return (
        "| split | seeds | mean return |\n"
        "|---|---|---|\n"
        f"| held-in (train region) | {report.train.n} | {d['heldin_mean']:.3f} |\n"
        f"| held-out (test region) | {report.test.n} | {d['heldout_mean']:.3f} |\n"
        f"| **gap** (held-in − held-out) | | **{d['gap']:.3f}** |\n"
    )
