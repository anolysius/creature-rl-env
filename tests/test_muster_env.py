"""AC1–AC3/AC5 — family D (``MusterEnv``): collection-gated power (progression axis).

Families A/B/C differ on the collection mechanic (A action-collect, B contact-collect)
and the battle system (C type-agnostic duel). Family D changes the **progression**
axis: catching a creature buffs the party's attack, and bosses are strong enough that
you must **muster a collection before you can win** — collection and battle become a
dependency. So the load-bearing skill ("collect first, then fight") is distinct from
every other family, and is *useless* in family A (where catching gives no buff).

Verifies: contract + registration, structural distinctness from A, winnability via an
obs-only muster policy, and the policy-specific contrast (muster ≫ rush on D, muster ≈
rush on A) that makes D's env-level gap skill-structural rather than mere difficulty.
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np

from critter_gym.env_family import conforms, family_names, make_family
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.envs.muster_env import MUSTER_ATK, MusterEnv
from critter_gym.genre_generalization import muster_policy, nav_toward_gyms, rush_policy
from critter_gym.registration import register_envs

register_envs()

# Strong-boss calibration that makes mustering load-bearing (family identity).
DCFG = dict(vary=True, num_types=12, num_gyms=3, max_steps=200, num_creatures=8,
            boss_hp=300, boss_def=24)
SEEDS = [1_000_000 + i for i in range(12)]


def _gym_clears(make_env, policy, seed: int, max_steps: int = 200) -> float:
    env = make_env()
    obs, _ = env.reset(seed=int(seed))
    for _ in range(max_steps):
        obs, _r, term, trunc, _ = env.step(policy(obs))
        if term or trunc:
            break
    return float(sum(env._gym_defeated))


def test_muster_env_conforms_and_registered() -> None:  # AC1
    assert conforms(MusterEnv(**DCFG))
    assert {"critter", "forage", "duel", "muster"}.issubset(set(family_names()))
    assert conforms(make_family("muster"))


def test_catch_buffs_party_attack() -> None:  # AC2 (mechanic)
    env = MusterEnv(**DCFG)
    env.reset(seed=1_000_000)
    base = env._party[0].attack
    cr, cc = next(iter(env._creatures))
    # step onto an adjacent cell then CATCH from the creature tile.
    env._agent_pos = np.array([cr, cc], dtype=np.int64)
    env.step(4)  # CATCH on the creature tile
    assert env._party[0].attack == base + MUSTER_ATK
    assert env._caught == 1


def _battle_sig(make_env, seed, max_steps=200):
    env = make_env()
    obs, _ = env.reset(seed=int(seed))
    sig, entered = [], False
    for _ in range(max_steps):
        a = 0 if obs["in_battle"][0] == 1 else nav_toward_gyms(obs)
        obs, _r, term, trunc, _ = env.step(a)
        if obs["in_battle"][0] == 1:
            entered = True
        sig.append((int(obs["in_battle"][0]), int(obs["enemy_hp"][0])))
        if term or trunc:
            break
    return sig, entered


def test_structurally_distinct_from_family_a() -> None:  # AC2
    # nav_toward_gyms incidentally catches creatures (fallback), so in family D the
    # party gets buffed → battle (enemy_hp drop) differs from family A on same seed.
    distinct = False
    for s in SEEDS[:6]:
        a_sig, a_in = _battle_sig(lambda: CritterEnv(**DCFG), s)
        d_sig, d_in = _battle_sig(lambda: MusterEnv(**DCFG), s)
        if a_in and d_in and a_sig != d_sig:
            distinct = True
            break
    assert distinct, "family D battle dynamics must differ from A on some shared seed"


def test_muster_policy_winnable_from_observation() -> None:  # AC3
    total = sum(_gym_clears(lambda: MusterEnv(**DCFG), muster_policy, s) for s in SEEDS)
    assert total > 0, "family D must be winnable by an obs-only muster policy"


def test_muster_skill_is_load_bearing_on_d_and_useless_on_a() -> None:  # AC5
    # On family D: muster (collect-first) defeats more bosses than rush (fight-now),
    # because strong bosses require the collection buff → skill-structural.
    d_muster = np.mean([_gym_clears(lambda: MusterEnv(**DCFG), muster_policy, s) for s in SEEDS])
    d_rush = np.mean([_gym_clears(lambda: MusterEnv(**DCFG), rush_policy, s) for s in SEEDS])
    assert d_muster > d_rush, f"muster must beat rush on family D (got {d_muster} vs {d_rush})"
    # On family A: catching gives NO buff, so the muster skill is useless — muster does
    # not beat rush (the gap is specific to family D's mechanic, not navigation).
    a_muster = np.mean([_gym_clears(lambda: CritterEnv(**DCFG), muster_policy, s) for s in SEEDS])
    a_rush = np.mean([_gym_clears(lambda: CritterEnv(**DCFG), rush_policy, s) for s in SEEDS])
    assert a_muster <= a_rush + 0.1, f"muster skill useless on A (got {a_muster} vs {a_rush})"


def test_muster_v0_check_env_compliant() -> None:  # AC6 (6th gym id)
    from gymnasium.utils.env_checker import check_env

    check_env(gym.make("CritterGym-muster-v0").unwrapped, skip_render_check=True)
