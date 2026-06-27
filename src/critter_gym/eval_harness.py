"""Sealed held-out eval harness — the M5 contamination-proof eval product, in prototype.

CritterGym's load-bearing asset is that it **regenerates a fresh, never-seen world + hidden
rule-chart per evaluation, with verifiable (RLVR) rewards** (DESIGN §9 layer 1). The public
env is free (credibility, adoption); the scarce, monetizable thing is a **held-out eval the
submitter can neither see nor train on** (DESIGN §8, M5). This module prototypes that
mechanism:

- :class:`SealedEvalSet` — a *private* block of held-out worlds, picked deterministically
  from the held-out seed region (``seed >= TEST_SEED_OFFSET``) by a secret ``master_seed``.
  Same ``master_seed`` reproduces the block (auditable); a different one regenerates a fresh,
  disjoint block (so a leaked set is cheaply replaced).
- :func:`verify_sealed` — the **contamination guard**: it proves a submitter's declared
  training seeds are disjoint from the sealed eval block *and* live in the training region
  (``< TEST_SEED_OFFSET``). A fixed benchmark eventually leaks into training; here the guard
  makes "you could not have trained on this test" a *checkable* property — the trust we sell.
- :func:`score_agent` — runs a submitted agent on the sealed worlds and scores it with
  **verifiable subgoals only** (gym-clears, catch, evolve from ``info["subgoals"]`` /
  terminal env state), never a hand-tuned metric, plus its fraction of a scripted oracle on
  the *same* sealed worlds.

**Honest scope (prototype).** "Sealed" here is an in-process convention — the secret seeds
live inside the :class:`SealedEvalSet` object; a real hosted product needs server-side secret
seeds + a submission sandbox. Single machine, numpy ``CritterEnv`` (commit-v0), one config.
This demonstrates the *mechanism*, not a deployed service, customers, or revenue.
"""
from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Callable, NamedTuple, Protocol, Union, runtime_checkable

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.learnability import EnvPolicy, as_env_policy, reference_arm, run_episode
from critter_gym.region import TEST_SEED_OFFSET

# Reserve the top of the held-out region for sealed eval blocks, so a sealed block never
# collides with the public ``heldout_seeds(n)`` range (which starts at TEST_SEED_OFFSET).
_SEALED_BASE = TEST_SEED_OFFSET + 100_000
_SEALED_SPAN = 800_000  # sealed offsets live in [_SEALED_BASE, _SEALED_BASE + _SEALED_SPAN)


@runtime_checkable
class Agent(Protocol):
    """A submission: maps an observation to an action. Same interface a learned policy or an
    LLM agent implements — ``act(obs) -> action_index``."""

    def act(self, obs: object) -> int: ...


# A submission is either an obs-only Agent or an EnvPolicy (env, obs) -> action (e.g. a
# scripted reference arm). `score_agent` accepts both.
Submission = Union[Agent, EnvPolicy]


class SealedEvalSet:
    """A private, regenerable block of held-out worlds for one evaluation.

    ``master_seed`` is the evaluator's secret: it deterministically selects a contiguous block
    of held-out seeds (all ``>= TEST_SEED_OFFSET``) that the submitter never sees. The same
    ``master_seed`` reproduces the block (auditable re-run); a different one yields a fresh,
    disjoint block. ``num_types``/config bind the world generator so scoring is reproducible.
    """

    def __init__(
        self, master_seed: int, n_worlds: int = 16, *, num_types: int = 8,
        commit_battles: bool = True,
    ) -> None:
        if n_worlds <= 0:
            raise ValueError("n_worlds must be positive")
        self.master_seed = int(master_seed)
        self.n_worlds = int(n_worlds)
        self.num_types = int(num_types)
        self.commit_battles = bool(commit_battles)

    def _offset(self) -> int:
        """A secret, well-spread offset into the sealed region derived from ``master_seed``."""
        digest = hashlib.sha256(f"critter-sealed:{self.master_seed}".encode()).digest()
        return int.from_bytes(digest[:8], "big") % (_SEALED_SPAN - self.n_worlds)

    def _eval_seeds(self) -> tuple[int, ...]:
        """The private sealed block of held-out seeds (evaluator-only)."""
        base = _SEALED_BASE + self._offset()
        return tuple(range(base, base + self.n_worlds))

    def env_factory(self) -> Callable[[], CritterEnv]:
        """A fresh numpy ``CritterEnv`` (commit-v0) matching this set's config."""
        num_types, commit = self.num_types, self.commit_battles
        return lambda: CritterEnv(commit_battles=commit, vary=True, num_types=num_types)


class SealedCertificate(NamedTuple):
    """The contamination-guard verdict for a submission's declared training seeds."""

    ok: bool
    n_eval: int
    n_train: int
    overlap: int             # declared train seeds that fall inside the sealed eval block
    all_eval_held_out: bool  # every sealed seed is in the held-out region (>= TEST_SEED_OFFSET)
    train_in_region: bool    # every declared train seed is in the training region (< offset)


def verify_sealed(
    declared_train_seeds: Sequence[int] | range, sealed: SealedEvalSet
) -> SealedCertificate:
    """Contamination guard: prove the submitter could not have trained on the sealed eval.

    ``ok`` iff (1) no declared training seed is in the sealed eval block (overlap 0) **and**
    (2) every declared training seed is in the training region (``< TEST_SEED_OFFSET``) — a
    "train" seed in the held-out region is itself illegal. This is what makes the sealed
    score *trustworthy*: leakage is detected, not assumed away.
    """
    train = {int(s) for s in declared_train_seeds}
    eval_seeds = set(sealed._eval_seeds())
    overlap = len(train & eval_seeds)
    all_eval_held_out = all(s >= TEST_SEED_OFFSET for s in eval_seeds)
    train_in_region = all(s < TEST_SEED_OFFSET for s in train)
    ok = overlap == 0 and train_in_region and all_eval_held_out
    return SealedCertificate(
        ok=ok, n_eval=len(eval_seeds), n_train=len(train), overlap=overlap,
        all_eval_held_out=all_eval_held_out, train_in_region=train_in_region,
    )


class Scorecard(NamedTuple):
    """An RLVR-verified scorecard for a submission on a sealed eval set.

    All fields derive from **verifiable subgoals** (gym-clears, catch, evolve), never a
    hand-tuned metric. ``frac_of_oracle`` is the submission's gym-clears as a fraction of a
    scripted oracle on the *same* sealed worlds (the headroom yardstick)."""

    n_worlds: int
    mean_gyms_cleared: float
    cleared_rate: float    # fraction of sealed worlds with >= 1 gym cleared
    caught_rate: float     # fraction with >= 1 creature caught
    evolved_rate: float    # fraction with >= 1 evolution
    frac_of_oracle: float  # mean_gyms_cleared / oracle's, on the same sealed worlds
    oracle_gyms: float
    type_blind_gyms: float


def _as_env_policy(submission: Submission) -> EnvPolicy:
    """Adapt a submission to the ``(env, obs) -> action`` runner.

    An :class:`Agent` (``act(obs) -> int``) is wrapped obs-only; an already-``EnvPolicy``
    callable (e.g. a scripted reference arm) is used as-is."""
    if isinstance(submission, Agent):
        return as_env_policy(submission.act)
    return submission  # an EnvPolicy: (env, obs) -> action


def score_agent(
    submission: Submission, sealed: SealedEvalSet,
    *, reference: tuple[str, ...] = ("oracle", "type_blind"),
) -> Scorecard:
    """Run ``submission`` on the sealed worlds and score it with verifiable subgoals.

    Scores the submission and the scripted ``reference`` arms (default oracle + type_blind) on
    the **same** sealed seeds, so ``frac_of_oracle`` is an honest same-yardstick comparison.
    """
    factory = sealed.env_factory()
    seeds = sealed._eval_seeds()
    policy = _as_env_policy(submission)

    outs = [run_episode(factory, policy, s) for s in seeds]
    n = len(outs)
    mean_gyms = float(np.mean([o.gyms_cleared for o in outs]))
    cleared_rate = float(np.mean([o.gyms_cleared >= 1 for o in outs]))
    # caught/evolved are read from terminal state via the episode outcome's evolution stream;
    # "caught" is inferred from a fresh re-run reading info["subgoals"] would double-run, so we
    # use the outcome's evolution count and a catch probe via the env's subgoal info.
    evolved_rate = float(np.mean([o.evolutions >= 1 for o in outs]))
    caught_rate = _caught_rate(factory, policy, seeds)

    def arm_mean(arm: str) -> float:
        return float(np.mean(
            [run_episode(factory, reference_arm(arm), s).gyms_cleared for s in seeds]
        ))

    oracle_gyms = arm_mean("oracle") if "oracle" in reference else float("nan")
    blind_gyms = arm_mean("type_blind") if "type_blind" in reference else float("nan")
    frac = mean_gyms / oracle_gyms if oracle_gyms and oracle_gyms > 0 else 0.0

    return Scorecard(
        n_worlds=n, mean_gyms_cleared=mean_gyms, cleared_rate=cleared_rate,
        caught_rate=caught_rate, evolved_rate=evolved_rate,
        frac_of_oracle=float(frac), oracle_gyms=oracle_gyms, type_blind_gyms=blind_gyms,
    )


def _caught_rate(
    factory: Callable[[], CritterEnv], policy: EnvPolicy, seeds: tuple[int, ...]
) -> float:
    """Fraction of sealed worlds where the policy caught >= 1 creature (RLVR subgoal).

    Reads ``info["subgoals"]["caught"]`` at the terminal step — a verifiable boolean stream."""
    caught = []
    for s in seeds:
        env = factory()
        obs, _ = env.reset(seed=int(s))
        info: dict = {"subgoals": {"caught": 0}}
        done = False
        while not done:
            obs, _r, term, trunc, info = env.step(policy(env, obs))
            done = bool(term or trunc)
        caught.append(int(info["subgoals"]["caught"]) >= 1)
    return float(np.mean(caught)) if caught else 0.0
