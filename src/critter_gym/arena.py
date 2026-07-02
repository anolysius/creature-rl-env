"""Arena measurement helpers — scripted band + submission telemetry (eval-product).

The arena (:class:`critter_gym.envs.ArenaEnv`) removes the exploration/survival confound;
this module reads the SAME inference signal on it that the sealed eval reads on the full
env: the super-effective-move rate, counted by :func:`eval_harness._super_effective_move`,
normalized by :func:`eval_harness.se_inference_score`, classified across runs by
:func:`inference_rigor.classify_inference` — **no new thresholds** are invented here.

Honest scope: the 4-arm band is scripted (the ``infer`` arm is an inference *proxy*, not
an LLM); the arena is a diagnostic probe, not a leaderboard config; a real-LLM arena run
spends the user's quota and is a separate, user-approved step.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import NamedTuple

from critter_gym.envs.arena_env import ArenaEnv
from critter_gym.eval_harness import InferenceTelemetry, _super_effective_move
from critter_gym.learnability import reference_arm

# Ceiling-to-floor order, same as eval_harness._BASELINE_ARMS.
ARENA_ARMS: tuple[str, ...] = ("oracle", "infer", "type_blind", "probe")


class ArenaArm(NamedTuple):
    """One scripted arm's arena outcome."""

    wins: float             # mean bout wins over the seeds (verifiable subgoal)
    se_rate: float          # super-effective-move rate (the inference signal)
    n_battle_moves: int     # telemetry denominator


def arena_factory(*, k_battles: int = 10, **env_knobs: object) -> Callable[[], ArenaEnv]:
    """A fresh-``ArenaEnv`` factory (mirrors ``SealedEvalSet.env_factory`` shape)."""
    return lambda: ArenaEnv(k_battles=k_battles, **env_knobs)


def _as_env_policy(submission: object) -> Callable:
    """Adapt a submission to the ``(env, obs) -> action`` runner.

    Objects with ``act(obs)`` (the LLM agents) are wrapped; plain callables are assumed
    to already take ``(env, obs)`` (the scripted reference arms).
    """
    act = getattr(submission, "act", None)
    if act is not None:
        return lambda _env, obs: act(obs)
    assert callable(submission)
    return submission


def _run_one(
    factory: Callable[[], ArenaEnv], policy: Callable, seed: int
) -> tuple[int, int, int]:
    """One arena episode: returns ``(wins, se_hits, n_battle_moves)``."""
    env = factory()
    obs, info = env.reset(seed=int(seed))
    se_hits = 0
    n_moves = 0
    done = False
    while not done:
        action = policy(env, obs)
        verdict = _super_effective_move(env, action)
        if verdict is not None:
            n_moves += 1
            se_hits += int(verdict)
        obs, _r, term, trunc, info = env.step(action)
        done = bool(term or trunc)
    return int(info["subgoals"]["gyms_defeated"]), se_hits, n_moves


def arena_band(
    seeds: Sequence[int], *, k_battles: int = 10, **env_knobs: object
) -> dict[str, ArenaArm]:
    """The scripted 4-arm inference band on the arena (per-world arm isolation,
    matching ``eval_harness._arm_band``: a fresh arm per seed, no cross-chart leaks)."""
    factory = arena_factory(k_battles=k_battles, **env_knobs)
    band: dict[str, ArenaArm] = {}
    for arm in ARENA_ARMS:
        total_wins = 0
        se_hits = 0
        n_moves = 0
        for seed in seeds:
            w, h, n = _run_one(factory, reference_arm(arm), seed)
            total_wins += w
            se_hits += h
            n_moves += n
        band[arm] = ArenaArm(
            wins=total_wins / len(seeds),
            se_rate=se_hits / n_moves if n_moves > 0 else 0.0,
            n_battle_moves=n_moves,
        )
    return band


def score_arena_telemetry(
    submission: object, seeds: Sequence[int], *, k_battles: int = 10, **env_knobs: object
) -> InferenceTelemetry:
    """A submission's super-effective-move rate on the arena (win-independent).

    Mirrors ``eval_harness.score_inference_telemetry``: one submission across the seeds,
    with the optional per-world ``reset()`` hook honored (memory isolation between worlds).
    """
    factory = arena_factory(k_battles=k_battles, **env_knobs)
    policy = _as_env_policy(submission)
    reset_fn = getattr(submission, "reset", None)
    se_hits = 0
    n_moves = 0
    for seed in seeds:
        if reset_fn is not None:
            reset_fn()
        _w, h, n = _run_one(factory, policy, seed)
        se_hits += h
        n_moves += n
    return InferenceTelemetry(
        super_effective_rate=se_hits / n_moves if n_moves > 0 else 0.0,
        n_battle_moves=int(n_moves),
    )
