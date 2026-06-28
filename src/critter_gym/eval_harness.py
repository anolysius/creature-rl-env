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
from critter_gym.learnability import EnvPolicy, as_env_policy, reference_arm
from critter_gym.region import TEST_SEED_OFFSET

# Reserve the top of the held-out region for sealed eval blocks, so a sealed block never
# collides with the public ``heldout_seeds(n)`` range (which starts at TEST_SEED_OFFSET).
_SEALED_BASE = TEST_SEED_OFFSET + 100_000
_SEALED_SPAN = 800_000  # sealed offsets live in [_SEALED_BASE, _SEALED_BASE + _SEALED_SPAN)


@runtime_checkable
class Agent(Protocol):
    """A submission: maps an observation to an action. Same interface a learned policy or an
    LLM agent implements — ``act(obs) -> action_index``.

    **Optional ``reset()`` hook.** An agent *may* additionally define ``reset(self) -> None``;
    :func:`score_agent` calls it (duck-typed) at the start of *each* sealed episode, right after
    ``env.reset()``. Stateful agents (e.g. an LLM that accumulates a per-episode history) use it
    to clear memory so one sealed world's transcript cannot leak into the next — without it, a
    stateful submission would contaminate world B with world A's memory. Stateless agents simply
    omit it; the hook is skipped and behaviour is byte-identical to before."""

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
        commit_battles: bool = True, max_steps: int = 200,
        grid_size: int = 10, boss_hp: int = 120, boss_atk: int = 12, boss_def: int = 12,
    ) -> None:
        if n_worlds <= 0:
            raise ValueError("n_worlds must be positive")
        if max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if grid_size <= 0 or boss_hp <= 0:
            raise ValueError("grid_size and boss_hp must be positive")
        self.master_seed = int(master_seed)
        self.n_worlds = int(n_worlds)
        self.num_types = int(num_types)
        self.commit_battles = bool(commit_battles)
        # Episode length cap — the default 200 is the env's own default (byte-identical);
        # a small value bounds cost for a per-step LLM eval (each step is an API call).
        self.max_steps = int(max_steps)
        # World/battle knobs (defaults = CritterEnv defaults => byte-identical). Lowering
        # grid_size makes a world navigable for an LLM; tuning the boss lets us target an
        # *inference-gated* difficulty band (a chart-blind baseline fails, an expert wins).
        self.grid_size = int(grid_size)
        self.boss_hp = int(boss_hp)
        self.boss_atk = int(boss_atk)
        self.boss_def = int(boss_def)

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
        num_types, commit, steps = self.num_types, self.commit_battles, self.max_steps
        grid, b_hp, b_atk, b_def = self.grid_size, self.boss_hp, self.boss_atk, self.boss_def
        return lambda: CritterEnv(
            commit_battles=commit, vary=True, num_types=num_types, max_steps=steps,
            grid_size=grid, boss_hp=b_hp, boss_atk=b_atk, boss_def=b_def,
        )


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
    # In-context inference score, normalized between the chart-BLIND baseline (type_blind, 0)
    # and the chart-KNOWING expert (oracle, 1): (mean - type_blind) / (oracle - type_blind),
    # clamped to [0,1]. 0 = no better than playing without the hidden chart; 1 = expert. This
    # is the moat KPI — it measures un-gameable in-context hidden-rule inference on a sealed,
    # never-seen world. 0.0 when the band doesn't discriminate (oracle <= type_blind).
    inference_score: float


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
    # Optional per-episode reset (duck-typed) — a stateful agent clears its memory between
    # sealed worlds so world A's transcript can't leak into world B. Stateless submissions
    # (no `reset`) skip this and stay byte-identical.
    reset_fn = getattr(submission, "reset", None)

    # One episode per seed reads gyms / caught / evolved together (a single pass — the prior
    # separate `caught` re-run doubled per-step LLM calls for an LLM submission).
    plays = [_play_once(factory, policy, s, reset=reset_fn) for s in seeds]
    n = len(plays)
    mean_gyms = float(np.mean([gyms for gyms, _c, _e in plays]))
    cleared_rate = float(np.mean([gyms >= 1 for gyms, _c, _e in plays]))
    caught_rate = float(np.mean([c for _g, c, _e in plays]))
    evolved_rate = float(np.mean([e for _g, _c, e in plays]))

    def arm_mean(arm: str) -> float:  # scripted arms (free); same single-pass yardstick
        return float(np.mean([_play_once(factory, reference_arm(arm), s)[0] for s in seeds]))

    oracle_gyms = arm_mean("oracle") if "oracle" in reference else float("nan")
    blind_gyms = arm_mean("type_blind") if "type_blind" in reference else float("nan")
    frac = mean_gyms / oracle_gyms if oracle_gyms and oracle_gyms > 0 else 0.0

    # Inference score: where the submission lands between the chart-blind floor and expert
    # ceiling. Needs both arms and a discriminating band (oracle > type_blind); else 0.0.
    span = oracle_gyms - blind_gyms
    if span > 0 and not np.isnan(span):
        inference = (mean_gyms - blind_gyms) / span
        inference = float(min(1.0, max(0.0, inference)))
    else:
        inference = 0.0

    return Scorecard(
        n_worlds=n, mean_gyms_cleared=mean_gyms, cleared_rate=cleared_rate,
        caught_rate=caught_rate, evolved_rate=evolved_rate,
        frac_of_oracle=float(frac), oracle_gyms=oracle_gyms, type_blind_gyms=blind_gyms,
        inference_score=inference,
    )


def _play_once(
    factory: Callable[[], CritterEnv], policy: EnvPolicy, seed: int,
    *, reset: Callable[[], None] | None = None,
) -> tuple[int, bool, bool]:
    """Run one episode and read all three verifiable subgoals from the terminal step:
    ``(gyms_cleared, caught_any, evolved_any)``.

    A single pass — the policy is queried once per step, not twice (the prior design re-ran
    the whole episode just to read ``caught``, doubling per-step LLM calls). ``gyms_cleared``
    is ``info["subgoals"]["gyms_defeated"]`` (= ``sum(env._gym_defeated)``), so it matches the
    value the old ``run_episode`` path read — the metrics are numerically unchanged.

    ``reset`` (optional) is the submission's per-episode hook, called right after
    ``env.reset()`` so a stateful agent starts each sealed world with a clean memory."""
    env = factory()
    obs, _ = env.reset(seed=int(seed))
    if reset is not None:
        reset()
    info: dict = {"subgoals": {"caught": 0, "gyms_defeated": 0, "evolved": 0}}
    done = False
    while not done:
        obs, _r, term, trunc, info = env.step(policy(env, obs))
        done = bool(term or trunc)
    sg = info["subgoals"]
    return int(sg["gyms_defeated"]), int(sg["caught"]) >= 1, int(sg["evolved"]) >= 1
