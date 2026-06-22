"""AC1: the env passes Gymnasium's standard compliance checker."""

from __future__ import annotations

from gymnasium.utils.env_checker import check_env

from critter_gym.envs.critter_env import CritterEnv


def test_check_env_passes() -> None:
    # Raises on any API-contract violation. The env now ships an rgb_array renderer,
    # so the render check runs (no skip) and validates the frame contract too.
    check_env(CritterEnv(render_mode="rgb_array"))
