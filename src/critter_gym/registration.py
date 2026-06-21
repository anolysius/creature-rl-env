"""Gymnasium registration for CritterGym environments."""

from __future__ import annotations

from gymnasium.envs.registration import register

_REGISTERED = False


def register_envs() -> None:
    """Register CritterGym ids with Gymnasium (idempotent)."""
    global _REGISTERED
    if _REGISTERED:
        return
    register(
        id="CritterGym-v0",
        entry_point="critter_gym.envs.critter_env:CritterEnv",
    )
    _REGISTERED = True
