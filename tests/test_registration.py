"""Acceptance test for Gymnasium registration (AC2)."""

from __future__ import annotations

import gymnasium as gym

import critter_gym  # noqa: F401  (import registers the env id)
from critter_gym.envs.critter_env import CritterEnv


def test_make_returns_env() -> None:
    """AC2: gymnasium.make('CritterGym-v0') returns a working env."""
    env = gym.make("CritterGym-v0")
    obs, info = env.reset(seed=0)
    assert env.observation_space.contains(obs)
    env.close()


def test_make_unwrapped_is_critter_env() -> None:
    env = gym.make("CritterGym-v0")
    assert isinstance(env.unwrapped, CritterEnv)
    env.close()
