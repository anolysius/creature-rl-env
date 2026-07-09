"""AC2 + AC3: baselines exist, return valid actions, and produce a spread.

The spread guard (greedy > random > 0) is the load-bearing assertion that the
environment is a *valid benchmark* — neither trivial (random already maxes out)
nor impossible (no policy beats chance). It runs on held-out seeds the policies
never "trained" on, mirroring the generalization protocol.
"""

from __future__ import annotations

import numpy as np

from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.envs.critter_env import CritterEnv

HELDOUT = range(50_000, 50_100)


def _rollout_mean(policy, seeds) -> float:
    totals = []
    for s in seeds:
        # num_gyms=0 isolates the catch baseline (the overworld navigation +
        # catch behavior these policies target); gym battles are exercised in
        # tests/test_gym_battle.py.
        env = CritterEnv(num_gyms=0)
        obs, _ = env.reset(seed=s)
        done = False
        g = 0.0
        while not done:
            obs, r, term, trunc, _ = env.step(policy(obs))
            g += r
            done = term or trunc
        totals.append(g)
    return float(np.mean(totals))


def test_policies_return_valid_actions() -> None:
    env = CritterEnv(num_gyms=0)
    obs, _ = env.reset(seed=0)
    rng = np.random.default_rng(0)
    for _ in range(50):
        for action in (random_policy(obs, rng), greedy_policy(obs, env.grid_size)):
            assert env.action_space.contains(action)
        obs, _, term, trunc, _ = env.step(greedy_policy(obs, env.grid_size))
        if term or trunc:
            obs, _ = env.reset(seed=0)


def test_baseline_spread_makes_env_a_valid_benchmark() -> None:
    rng = np.random.default_rng(0)
    random_mean = _rollout_mean(lambda o: random_policy(o, rng), HELDOUT)
    greedy_mean = _rollout_mean(lambda o: greedy_policy(o, 10), HELDOUT)
    # Max attainable catch score is the creature count (num_gyms=0 here).
    cap = CritterEnv(num_gyms=0).num_creatures

    # Margins scale with the cap so the guard survives env-param changes
    # (a fixed absolute margin would go brittle if the cap moves).
    assert random_mean > 0, "env unsolvable even by chance"
    assert greedy_mean > random_mean, "no spread — env may be trivial/broken"
    assert greedy_mean >= 0.5 * cap, "scripted policy is not meaningfully competent"
    assert greedy_mean <= cap, "scripted policy exceeds the max attainable score"


# -- demo_policy (demo-gif-purposeful): the site-GIF policy also walks toward gyms ----
#
# greedy_policy (the RANKED baseline above — byte-identical, untouched) only chases
# creatures, so its GIF kept sweeping with a gym on screen. demo_policy is demo-only:
# in-battle attack > catch on own tile > nearest LIVE gym > nearest creature > sweep.


def _demo_obs(patch: np.ndarray, pos: tuple[int, int] = (0, 0), in_battle: int = 0) -> dict:
    return {
        "local_patch": patch,
        "agent_pos": np.array(pos, dtype=np.int64),
        "in_battle": np.array([in_battle], dtype=np.int64),
    }


def _patch5(**cells: int) -> np.ndarray:
    """5x5 patch (center 2,2); cells like r0c2=2 place value 2 at (0, 2)."""
    patch = np.zeros((5, 5), dtype=np.int8)
    for key, val in cells.items():
        r, c = int(key[1]), int(key[3])
        patch[r, c] = val
    return patch


def test_demo_policy_steps_toward_visible_gym() -> None:
    from critter_gym.baselines import demo_policy
    from critter_gym.envs.critter_env import MOVE_E, MOVE_N, MOVE_S

    # Gym 2 tiles east of center (2,2) -> shortest-path step is EAST.
    assert demo_policy(_demo_obs(_patch5(r2c4=2))) == MOVE_E
    # Gym straight north -> NORTH.
    assert demo_policy(_demo_obs(_patch5(r0c2=2))) == MOVE_N
    # Diagonal tie (dr==dc) resolves vertical-first like the creature chase.
    assert demo_policy(_demo_obs(_patch5(r4c4=2))) == MOVE_S


def test_demo_policy_prefers_gym_over_creature() -> None:
    from critter_gym.baselines import demo_policy
    from critter_gym.envs.critter_env import MOVE_E

    # Creature is CLOSER (1 west) than the gym (2 east) — the demo still goes gym-first.
    assert demo_policy(_demo_obs(_patch5(r2c4=2, r2c1=1))) == MOVE_E


def test_demo_policy_catches_on_own_tile_before_gym() -> None:
    from critter_gym.baselines import demo_policy
    from critter_gym.envs.critter_env import CATCH

    assert demo_policy(_demo_obs(_patch5(r2c2=1, r2c4=2))) == CATCH


def test_demo_policy_attacks_in_battle() -> None:
    from critter_gym.baselines import demo_policy

    # In battle the overworld patch is irrelevant: always press the attack (action 0).
    assert demo_policy(_demo_obs(_patch5(r2c4=2), in_battle=1)) == 0


def test_demo_policy_chases_creature_when_no_gym_visible() -> None:
    from critter_gym.baselines import demo_policy
    from critter_gym.envs.critter_env import MOVE_W

    assert demo_policy(_demo_obs(_patch5(r2c0=1))) == MOVE_W


def test_demo_policy_sweeps_like_greedy_when_nothing_visible() -> None:
    from critter_gym.baselines import demo_policy

    empty = _patch5()
    for pos in [(0, 0), (0, 7), (1, 0), (1, 4), (3, 7)]:
        expected = greedy_policy(_demo_obs(empty, pos=pos), grid_size=8)
        assert demo_policy(_demo_obs(empty, pos=pos), grid_size=8) == expected


def test_demo_policy_returns_valid_actions_in_env() -> None:
    from critter_gym.baselines import demo_policy

    env = CritterEnv()  # gyms present: exercises the gym-seeking + battle branches
    obs, _ = env.reset(seed=0)
    for _ in range(80):
        action = demo_policy(obs, env.grid_size)
        assert env.action_space.contains(action)
        obs, _, term, trunc, _ = env.step(action)
        if term or trunc:
            break
