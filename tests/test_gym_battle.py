"""AC1–AC8: gym-boss progression — battle wired into the env as gated checkpoints."""

from __future__ import annotations

import numpy as np

from critter_gym.envs.critter_env import CATCH, NOOP, CritterEnv
from critter_gym.types import ElementType, TypeChart

TYPES = list(ElementType)
_CHART = TypeChart()


# --- test-local scripted policy (overworld navigation + type-aware battle) ----

def _scripted_action(env: CritterEnv, obs: dict[str, np.ndarray]) -> int:
    if obs["in_battle"][0]:
        active = TYPES[int(obs["player_type"][0])]
        enemy = TYPES[int(obs["enemy_type"][0])]
        return 0 if _CHART.effectiveness(active, enemy) > 1.0 else 4  # attack else switch
    undefeated = [p for p, i in env._gym_tiles.items() if not env._gym_defeated[i]]
    if not undefeated:
        return NOOP
    ar, ac = int(env._agent_pos[0]), int(env._agent_pos[1])
    tr, tc = min(undefeated, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    if tr < ar:
        return 0  # MOVE_N
    if tr > ar:
        return 1  # MOVE_S
    if tc > ac:
        return 2  # MOVE_E
    if tc < ac:
        return 3  # MOVE_W
    return NOOP


def _walk_onto_first_gym(env: CritterEnv) -> dict[str, np.ndarray]:
    """Position the agent adjacent to a gym and step onto it; returns the obs."""
    (gr, gc), _ = next(iter(env._gym_tiles.items()))
    if gr > 0:
        env._agent_pos = np.array([gr - 1, gc], dtype=np.int64)
        action = 1  # MOVE_S
    else:
        env._agent_pos = np.array([gr + 1, gc], dtype=np.int64)
        action = 0  # MOVE_N
    obs, *_ = env.step(action)
    return obs


# --- AC1: gym placement -------------------------------------------------------

def test_gyms_placed_deterministically() -> None:
    a, b = CritterEnv(), CritterEnv()
    a.reset(seed=5)
    b.reset(seed=5)
    assert len(a._gym_tiles) == a.num_gyms
    assert a._gym_tiles == b._gym_tiles  # same seed -> same placement
    assert set(a._gym_tiles).isdisjoint(a._creatures)  # gyms != creature tiles
    obs, _ = CritterEnv().reset(seed=5)
    assert int(obs["gyms_defeated"][0]) == 0


# --- AC2: mode transition -----------------------------------------------------

def test_stepping_onto_gym_enters_battle() -> None:
    env = CritterEnv()
    obs, _ = env.reset(seed=5)
    assert int(obs["in_battle"][0]) == 0
    obs = _walk_onto_first_gym(env)
    assert int(obs["in_battle"][0]) == 1
    assert obs["enemy_hp"][0] > 0  # battle obs is populated
    assert env.observation_space.contains(obs)  # AC7: obs valid in battle mode


# --- AC3: agent-controlled battle ---------------------------------------------

def test_battle_advances_one_turn_per_step() -> None:
    env = CritterEnv()
    env.reset(seed=5)
    _walk_onto_first_gym(env)
    assert env._battle is not None
    turn_before = env._battle.state.turn
    env.step(0)  # use a battle move
    assert env._battle is None or env._battle.state.turn == turn_before + 1


# --- AC4: RLVR subgoal reward -------------------------------------------------

def test_defeating_gym_rewards_once_and_increments_subgoal() -> None:
    env = CritterEnv(grid_size=8, num_creatures=2, num_gyms=2, max_steps=300)
    obs, _ = env.reset(seed=3)
    total, gym_reward_steps = 0.0, 0
    for _ in range(300):
        obs, r, term, trunc, info = env.step(_scripted_action(env, obs))
        total += r
        if r == 1.0 and not obs["in_battle"][0]:
            gym_reward_steps += 1
        if term or trunc:
            break
    assert info["subgoals"]["gyms_defeated"] >= 1
    # reward is exactly +1 per gym defeated (no dense shaping, no catches taken here)
    assert total == float(info["subgoals"]["gyms_defeated"] + info["subgoals"]["caught"])


def test_movement_and_battle_turns_are_unrewarded() -> None:
    env = CritterEnv()
    env.reset(seed=5)
    _, r_move, _, _, _ = env.step(0)
    assert r_move == 0.0
    _walk_onto_first_gym(env)
    _, r_turn, _, _, _ = env.step(NOOP)  # a passive battle turn
    assert r_turn == 0.0


# --- AC5: termination ---------------------------------------------------------

def test_clearing_all_gyms_terminates() -> None:
    env = CritterEnv(grid_size=8, num_creatures=2, num_gyms=2, max_steps=300)
    obs, _ = env.reset(seed=3)
    terminated = False
    for _ in range(300):
        obs, _, terminated, truncated, info = env.step(_scripted_action(env, obs))
        if terminated or truncated:
            break
    assert terminated and info["subgoals"]["gyms_defeated"] == env.num_gyms


def test_losing_battle_returns_to_overworld_without_reward() -> None:
    env = CritterEnv()
    env.reset(seed=5)
    _walk_onto_first_gym(env)
    total = 0.0
    for _ in range(env._battle.max_turns + 5):  # type: ignore[union-attr]
        _, r, _, _, obs_info = env.step(NOOP)  # never attack -> guaranteed loss
        total += r
        if env._mode == "overworld":
            break
    assert env._mode == "overworld"
    assert total == 0.0
    assert not any(env._gym_defeated)  # the gym was not cleared


# --- AC6: determinism ---------------------------------------------------------

def test_same_seed_same_trajectory_with_battles() -> None:
    def run() -> list[tuple[int, int, float]]:
        env = CritterEnv(grid_size=8, num_creatures=2, num_gyms=2, max_steps=300)
        obs, _ = env.reset(seed=3)
        trace = []
        for _ in range(300):
            obs, r, term, trunc, _ = env.step(_scripted_action(env, obs))
            trace.append((int(obs["in_battle"][0]), int(obs["gyms_defeated"][0]), r))
            if term or trunc:
                break
        return trace

    assert run() == run()


# --- AC8: scripted clears at least one gym ------------------------------------

def test_scripted_policy_clears_at_least_one_gym() -> None:
    env = CritterEnv(grid_size=8, num_creatures=2, num_gyms=2, max_steps=300)
    obs, _ = env.reset(seed=3)
    info: dict = {"subgoals": {"gyms_defeated": 0}}
    for _ in range(300):
        obs, _, term, trunc, info = env.step(_scripted_action(env, obs))
        if term or trunc:
            break
    assert info["subgoals"]["gyms_defeated"] >= 1


# catching still works alongside gyms (AC4 catch subgoal preserved)
def test_catch_still_rewards() -> None:
    env = CritterEnv()
    env.reset(seed=5)
    tile = next(iter(env._creatures))
    env._agent_pos = np.array(tile, dtype=np.int64)
    _, r, _, _, info = env.step(CATCH)
    assert r == 1.0 and info["subgoals"]["caught"] == 1
