"""Acceptance tests for the minimal CritterEnv (AC3–AC6)."""

from __future__ import annotations

import numpy as np

from critter_gym.envs.critter_env import CATCH, MOVE_N, NOOP, CritterEnv


def _obs_equal(a: dict[str, np.ndarray], b: dict[str, np.ndarray]) -> bool:
    return a.keys() == b.keys() and all(np.array_equal(a[k], b[k]) for k in a)


def test_reset_and_step_signatures() -> None:
    """AC3: reset -> (obs, info); step -> 5-tuple; obs in observation_space."""
    env = CritterEnv()
    obs, info = env.reset(seed=0)
    assert env.observation_space.contains(obs)
    assert isinstance(info, dict)

    obs2, reward, terminated, truncated, info2 = env.step(NOOP)
    assert env.observation_space.contains(obs2)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info2, dict)


def test_reset_is_deterministic_for_same_seed() -> None:
    """AC4: same seed -> identical initial observation."""
    a, _ = CritterEnv().reset(seed=42)
    b, _ = CritterEnv().reset(seed=42)
    assert _obs_equal(a, b)


def test_different_seeds_differ() -> None:
    """Sanity: different seeds should generally produce different worlds."""
    a, _ = CritterEnv().reset(seed=1)
    b, _ = CritterEnv().reset(seed=2)
    assert not _obs_equal(a, b)


def test_catch_on_creature_tile_rewards_and_increments() -> None:
    """AC5: CATCH on a creature tile -> reward +1 and caught subgoal increments."""
    env = CritterEnv()
    env.reset(seed=7)
    target = next(iter(env._creatures))
    env._agent_pos = np.array(target, dtype=np.int64)

    obs, reward, _, _, info = env.step(CATCH)
    assert reward == 1.0
    assert info["subgoals"]["caught"] == 1
    assert int(obs["caught"][0]) == 1


def test_catch_on_empty_tile_gives_no_reward() -> None:
    """AC5: CATCH on an empty tile -> reward 0, no shaping."""
    env = CritterEnv()
    env.reset(seed=7)
    # Find an empty tile.
    empty = next(
        (r, c)
        for r in range(env.grid_size)
        for c in range(env.grid_size)
        if (r, c) not in env._creatures
    )
    env._agent_pos = np.array(empty, dtype=np.int64)
    _, reward, _, _, info = env.step(CATCH)
    assert reward == 0.0
    assert info["subgoals"]["caught"] == 0


def test_movement_is_not_rewarded() -> None:
    """AC5: moving yields zero reward (no dense shaping)."""
    env = CritterEnv()
    env.reset(seed=3)
    _, reward, _, _, _ = env.step(MOVE_N)
    assert reward == 0.0


def test_catching_does_not_terminate() -> None:
    """Termination evolved (gym-boss-progression): catch is a non-terminal subgoal.

    Catching every creature must NOT end the episode — only clearing the gyms does.
    """
    env = CritterEnv(num_creatures=4, num_gyms=2, max_steps=100)
    env.reset(seed=11)
    for tile in list(env._creatures):
        env._agent_pos = np.array(tile, dtype=np.int64)
        _, _, terminated, _, info = env.step(CATCH)
        assert terminated is False
    assert info["subgoals"]["caught"] == 4


def test_truncation_on_step_budget() -> None:
    """Exceeding the step budget -> truncated=True (no gyms cleared)."""
    env = CritterEnv(max_steps=5)
    env.reset(seed=0)
    truncated = False
    for _ in range(5):
        _, _, _, truncated, _ = env.step(NOOP)
    assert truncated is True


def test_too_many_entities_rejected() -> None:
    """Guard: creatures + gyms + agent must fit the grid."""
    try:
        CritterEnv(grid_size=3, num_creatures=8, num_gyms=2)
    except ValueError:
        return
    raise AssertionError("expected ValueError when the grid is overfilled")


def test_invalid_action_raises() -> None:
    env = CritterEnv()
    env.reset(seed=0)
    try:
        env.step(99)
    except ValueError:
        return
    raise AssertionError("expected ValueError for invalid action")
