"""AC1 — team-commit champion-selection action UX (learnability-measurement).

In a commit-mode boss fight the agent must *choose which creature to commit*
before fighting, informed by the observed ``enemy_type`` (and its inferred
matchup). This is the env-level action that lets a *learned* policy express the
``infer`` behavior the scripted gate proved possible.

Mechanic: on entering a commit battle a one-time **commit window** opens. While
open, action ``4`` cycles the committed champion (no battle turn elapses, the boss
does not attack — cycling only re-reads ``enemy_type``/``player_type``, never deals
or takes damage, so it is selection, not probing). The first move/pass **locks** the
champion; thereafter switches are no-ops (engine ``commit_mode``). Non-commit
battles are unchanged.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np

from critter_gym.battle import Side
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.registration import register_envs


def _commit_env(seed: int = 1000) -> tuple[CritterEnv, dict]:
    env = CritterEnv(vary=True, num_types=12, num_gyms=8, super_mult=3.0,
                     boss_hp=140, boss_atk=18, commit_battles=True)
    obs, _ = env.reset(seed=seed)
    return env, obs


def _walk_onto_first_gym(env: CritterEnv) -> dict[str, np.ndarray]:
    (gr, gc), _ = next(iter(env._gym_tiles.items()))
    if gr > 0:
        env._agent_pos = np.array([gr - 1, gc], dtype=np.int64)
        action = 1  # MOVE_S
    else:
        env._agent_pos = np.array([gr + 1, gc], dtype=np.int64)
        action = 0  # MOVE_N
    obs, *_ = env.step(action)
    return obs


def test_commit_window_cycles_champion_without_a_battle_turn() -> None:
    env, _ = _commit_env()
    obs = _walk_onto_first_gym(env)
    assert int(obs["in_battle"][0]) == 1
    before_active = env._battle.state.active_a
    before_turn = env._battle.state.turn
    before_hp = int(obs["player_hp"][0])

    obs, *_ = env.step(4)  # cycle champion
    assert env._battle.state.active_a != before_active     # champion changed
    assert env._battle.state.turn == before_turn           # no battle turn elapsed
    assert int(obs["player_hp"][0]) == before_hp           # boss did not attack (no probing)
    assert int(obs["in_battle"][0]) == 1                   # still selecting


def test_first_move_locks_the_champion() -> None:
    # Weak boss so the champion survives the post-lock turns — isolates the lock
    # mechanic (a strong boss could end the fight before we can re-check the active).
    env = CritterEnv(vary=True, num_types=12, num_gyms=8, super_mult=3.0,
                     boss_hp=400, boss_atk=1, commit_battles=True)
    env.reset(seed=1000)
    _walk_onto_first_gym(env)
    env.step(4)                                  # cycle once (window open)
    locked = env._battle.state.active_a
    env.step(0)                                  # a move LOCKS the champion + elapses a turn
    assert env._battle is not None and env._battle.state.turn >= 1
    # after lock, action 4 no longer changes the champion (engine commit_mode no-op)
    env.step(4)
    assert env._battle is not None and env._battle.state.active_a == locked


def test_enemy_type_observable_during_commit_window() -> None:
    env, _ = _commit_env()
    obs = _walk_onto_first_gym(env)
    pool_max = env.observation_space["enemy_type"].high[0]
    assert 0 <= int(obs["enemy_type"][0]) <= int(pool_max)
    assert int(obs["in_battle"][0]) == 1


def test_noncommit_battle_action4_still_switches_next_alive() -> None:
    # Regression: in a non-commit battle action 4 keeps its M1 meaning (switch to
    # next alive) — the commit window must not leak into the default economy.
    env = CritterEnv(vary=True, num_types=12, num_gyms=8)  # commit_battles=False
    env.reset(seed=1000)
    _walk_onto_first_gym(env)
    assert env._battle is not None
    before = env._battle.state.active_a
    n_alive = sum(not c.is_fainted for c in env._battle.state.party(Side.A))
    env.step(4)  # switch-next-alive (existing behavior), a real battle turn
    if n_alive > 1:
        assert env._battle is None or env._battle.state.active_a != before


def test_commit_v0_remains_check_env_compliant() -> None:
    from gymnasium.utils.env_checker import check_env

    register_envs()
    e = gym.make("CritterGym-commit-v0").unwrapped
    check_env(e, skip_render_check=True)
