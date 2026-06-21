"""AC1: the env passes Gymnasium's standard compliance checker."""

from __future__ import annotations

from gymnasium.utils.env_checker import check_env

from critter_gym.envs.critter_env import CritterEnv


def test_check_env_passes() -> None:
    # Raises on any API-contract violation; skip_render_check since we ship no renderer yet.
    check_env(CritterEnv(), skip_render_check=True)
