"""Episode recording for the killer demo (M3-EC6).

Roll a policy through one episode, collect the rendered frames, and detect whether
a gym boss was beaten — so a demo can be assembled into a GIF (``save_demo`` →
:func:`critter_gym.render.save_gif`). The moat claim the demo visualizes is "the
same agent, an *unseen held-out* seed (new map + new type chart), still beats the
boss".

This module is **numpy-only at import time** (the GIF encoder, imageio, is lazy
inside ``render.save_gif`` behind the ``[render]`` extra). ``record_episode`` is the
CI-verifiable *pipeline*; ``scripts/killer_demo.py`` is the ``[rl]`` consumer that
trains an agent and produces the headline held-out GIF (not CI-gated).

Distinct from the eval rollouts in :mod:`critter_gym.generalization`: those measure
*return only* (no frames); recording here collects *frames + boss-defeat detection*.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.render import save_gif

Obs = dict[str, np.ndarray]
PolicyFn = Callable[[Obs], int]


@dataclass(frozen=True)
class EpisodeRecording:
    """One recorded episode: rendered frames + the subgoal outcome."""

    frames: tuple[np.ndarray, ...]  # reset frame + one per step; each (H, W, 3) uint8
    steps: int
    total_reward: float
    gyms_defeated: int
    boss_defeated: bool  # all gyms cleared (episode won, not truncated)
    seed: int


def _frame(env: CritterEnv) -> np.ndarray:
    f = env.render()
    assert f is not None  # guaranteed: caller checks render_mode == "rgb_array"
    return f


def record_episode(
    env: CritterEnv, policy: PolicyFn, seed: int, max_steps: int | None = None
) -> EpisodeRecording:
    """Roll ``policy`` through one episode from ``seed``, capturing a frame per step.

    Requires an ``rgb_array`` env. Boss defeat is read from the terminal ``info``
    (``remaining_gyms == 0`` ⇒ every gym cleared). Deterministic in (env, policy,
    seed) for a deterministic policy.
    """
    if env.render_mode != "rgb_array":
        raise ValueError("record_episode needs an env constructed with render_mode='rgb_array'")

    obs, info = env.reset(seed=int(seed))
    frames = [_frame(env)]
    total = 0.0
    steps = 0
    terminated = truncated = False
    while not (terminated or truncated):
        obs, reward, terminated, truncated, info = env.step(policy(obs))
        frames.append(_frame(env))
        total += float(reward)
        steps += 1
        if max_steps is not None and steps >= max_steps:
            break

    return EpisodeRecording(
        frames=tuple(frames),
        steps=steps,
        total_reward=total,
        gyms_defeated=int(info["subgoals"]["gyms_defeated"]),
        boss_defeated=int(info["remaining_gyms"]) == 0,
        seed=int(seed),
    )


def save_demo(recording: EpisodeRecording, path: str, fps: int = 5) -> str:
    """Encode a recording's frames to a GIF (delegates to ``render.save_gif``, ``[render]``)."""
    return save_gif(recording.frames, path, fps=fps)
