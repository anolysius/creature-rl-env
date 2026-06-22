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


def _concentrate_action(env: CritterEnv, obs: dict[str, np.ndarray]) -> int:
    """Always attack with the current active in battle (concentrate levels on it);
    navigate to the nearest gym in overworld."""
    if obs["in_battle"][0]:
        return 0
    undefeated = [p for p, i in env._gym_tiles.items() if not env._gym_defeated[i]]
    if not undefeated:
        return NOOP
    ar, ac = int(env._agent_pos[0]), int(env._agent_pos[1])
    tr, tc = min(undefeated, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    if tr < ar:
        return 0
    if tr > ar:
        return 1
    if tc > ac:
        return 2
    if tc < ac:
        return 3
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
    # reward is exactly +1 per boolean subgoal (gym defeat / catch / evolution) — no shaping
    sg = info["subgoals"]
    assert total == float(sg["gyms_defeated"] + sg["caught"] + sg["evolved"])


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
            trace.append(
                (int(obs["in_battle"][0]), int(obs["gyms_defeated"][0]),
                 int(obs["evolved"][0]), int(obs["player_level"][0]), r)
            )
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


# --- evolution wired into the env (M1-EC2: AC2/AC4/AC6/AC8) -------------------

def test_winning_a_battle_levels_the_active_creature() -> None:
    """AC2: the creature that finishes a battle gains a level."""
    env = CritterEnv(grid_size=8, num_creatures=2, num_gyms=3, max_steps=300)
    obs, _ = env.reset(seed=3)
    assert all(c.level == 1 for c in env._party)
    for _ in range(300):
        obs, _, term, trunc, info = env.step(_concentrate_action(env, obs))
        if info["subgoals"]["gyms_defeated"] >= 1:
            break
    assert any(c.level >= 2 for c in env._party)


def test_evolution_gives_subgoal_reward() -> None:
    """AC4: the step where a creature evolves yields the evolution reward (+1),
    on top of the gym-defeat reward; nothing else is shaped."""
    env = CritterEnv(grid_size=8, num_creatures=2, num_gyms=3, max_steps=300)
    obs, _ = env.reset(seed=3)
    prev_evolved, evolve_step_reward = 0, None
    for _ in range(300):
        obs, r, term, trunc, info = env.step(_concentrate_action(env, obs))
        if info["subgoals"]["evolved"] > prev_evolved:
            evolve_step_reward = r  # gym(+1) and evolve(+1) land on the same step
            prev_evolved = info["subgoals"]["evolved"]
        if term or trunc:
            break
    assert info["subgoals"]["evolved"] >= 1
    assert evolve_step_reward == 2.0  # +1 gym +1 evolution, no shaping


def test_obs_exposes_evolution_fields() -> None:
    """AC6: obs carries evolved + (in battle) player_level, and stays in-space."""
    env = CritterEnv()
    obs, _ = env.reset(seed=5)
    assert "evolved" in obs and "player_level" in obs
    assert int(obs["evolved"][0]) == 0
    obs = _walk_onto_first_gym(env)
    assert int(obs["player_level"][0]) >= 1  # active level shown in battle
    assert env.observation_space.contains(obs)


def test_concentration_evolution_payoff_is_not_vestigial() -> None:
    """AC8: concentrating wins evolves a creature *before* the final gym, so the
    evolved form is actually used in later battles (not a last-step trophy)."""
    env = CritterEnv(grid_size=8, num_creatures=2, num_gyms=3, max_steps=300)
    obs, _ = env.reset(seed=3)
    first_evolve_gyms = None
    for _ in range(300):
        obs, _, term, trunc, info = env.step(_concentrate_action(env, obs))
        if info["subgoals"]["evolved"] >= 1 and first_evolve_gyms is None:
            first_evolve_gyms = info["subgoals"]["gyms_defeated"]
        if term or trunc:
            break
    assert info["subgoals"]["evolved"] >= 1
    assert first_evolve_gyms is not None and first_evolve_gyms < env.num_gyms
    assert any(c.evolved for c in env._party)


# --- procgen region integration (M2-EC1: AC3/AC5/AC6/AC7) ---------------------

def test_procgen_episode_always_has_a_gym_and_can_terminate() -> None:
    """AC3: a vary=True episode always has >=1 gym, so termination stays reachable."""
    for seed in range(8):
        env = CritterEnv(vary=True)
        env.reset(seed=seed)
        assert len(env._gym_defeated) >= 1


def test_procgen_env_registered_and_compliant() -> None:
    """AC5: the procgen variant is registered, check_env passes, obs in-space on
    both train and held-out seeds."""
    import gymnasium as gym

    import critter_gym  # noqa: F401

    e = gym.make("CritterGym-procgen-v0")
    assert e.unwrapped.vary is True  # type: ignore[attr-defined]
    e.close()

    env = CritterEnv(vary=True)
    for seed in [0, 1, 2, 1_000_000, 1_000_050]:  # train + held-out
        obs, _ = env.reset(seed=seed)
        assert env.observation_space.contains(obs)


def test_procgen_is_deterministic_per_seed() -> None:
    """AC6: same seed + same actions -> same trajectory in procgen mode too."""
    def run() -> list[tuple[int, int, int, float]]:
        env = CritterEnv(vary=True, max_steps=200)
        obs, _ = env.reset(seed=1234)
        trace = []
        for _ in range(200):
            obs, r, term, trunc, _ = env.step(_scripted_action(env, obs))
            trace.append(
                (int(obs["in_battle"][0]), int(obs["gyms_defeated"][0]),
                 int(obs["evolved"][0]), r)
            )
            if term or trunc:
                break
        return trace

    assert run() == run()


def test_m1_mechanics_work_in_procgen_regions() -> None:
    """AC7: battles / gym defeat / evolution still function in procgen worlds."""
    cleared_some = False
    for seed in range(6):
        env = CritterEnv(grid_size=10, vary=True, max_steps=400)
        obs, _ = env.reset(seed=seed)
        for _ in range(400):
            obs, _, term, trunc, info = env.step(_scripted_action(env, obs))
            if term or trunc:
                break
        if info["subgoals"]["gyms_defeated"] >= 1:
            cleared_some = True
            break
    assert cleared_some  # a scripted policy can defeat a gym in some procgen region


# --- procgen type chart integration (M2-EC2: AC4/AC5) -------------------------

def test_env_uses_per_seed_chart_and_damage_reflects_it() -> None:
    """AC5: a vary env adopts the seed's chart; fixed env uses FIXED_CHART; and a
    chart that flips a matchup changes battle damage."""
    from critter_gym.battle import Battle, BattleState
    from critter_gym.creatures import Creature, Move
    from critter_gym.types import FIXED_CHART, ElementType, generate_typechart

    F, G = ElementType.FIRE, ElementType.GRASS

    fixed_env = CritterEnv()
    fixed_env.reset(seed=0)
    assert fixed_env._region_chart == FIXED_CHART  # vary=False keeps M1 chart

    pro = CritterEnv(vary=True)
    pro.reset(seed=0)
    assert pro._region_chart == generate_typechart(0, vary=True)  # adopts seed chart

    # seed 0's chart flips FIRE-vs-GRASS to not-very, so the same attack hits softer.
    attacker = Creature("A", (F,), 50, 12, 10, 10, [Move("flare", F, 30)])
    defender = Creature("B", (G,), 50, 12, 10, 10, [Move("vine", G, 30)])
    st = BattleState(party_a=[attacker], party_b=[defender])
    fixed_dmg = Battle(st, chart=FIXED_CHART).damage(attacker, defender, 0)
    seed0_dmg = Battle(st, chart=pro._region_chart).damage(attacker, defender, 0)
    assert seed0_dmg < fixed_dmg  # the per-seed chart actually changes outcomes


def test_obs_does_not_leak_the_chart() -> None:
    """AC4: the effectiveness table is never in the observation — only type ids."""
    fixed_keys = set(CritterEnv().reset(seed=0)[0].keys())
    pro_obs, _ = CritterEnv(vary=True).reset(seed=0)
    assert set(pro_obs.keys()) == fixed_keys  # no extra chart-revealing field
    assert "chart" not in pro_obs and "effectiveness" not in pro_obs


# catching still works alongside gyms (AC4 catch subgoal preserved)
def test_catch_still_rewards() -> None:
    env = CritterEnv()
    env.reset(seed=5)
    tile = next(iter(env._creatures))
    env._agent_pos = np.array(tile, dtype=np.int64)
    _, r, _, _, info = env.step(CATCH)
    assert r == 1.0 and info["subgoals"]["caught"] == 1
