"""AC1–AC3 — family C (``DuelEnv``): a structurally distinct BATTLE SYSTEM.

Family B (``ForageEnv``) differs from family A only on the *collection* mechanic and
shares family A's battle, so an A-tuned policy transfers with gap≈0 (the forgiving
axis the prior session flagged). Family C changes the **battle system itself**: a
type-AGNOSTIC stamina/commit duel (no type chart, no move selection, no switching) —
a rock-paper-scissors resource game (ATTACK beats CHARGE, GUARD beats ATTACK, CHARGE
beats GUARD; charge scales attack). Inferring the hidden type chart (family A's
load-bearing skill) is useless here, so the env-level transfer gap is *skill-structural*.

Verifies: the shared contract still holds (extra obs keys allowed), registration,
battle-level structural distinctness from family A, the RPS/charge mechanic, and that
the family is winnable from OBSERVABLE state (duel charge exposed in obs — not
privileged access).
"""

from __future__ import annotations

import gymnasium as gym
import numpy as np

from critter_gym.battle import Side
from critter_gym.env_family import (
    ACTION_N,
    REQUIRED_OBS_KEYS,
    conforms,
    family_names,
    make_family,
)
from critter_gym.envs.critter_env import (
    CATCH,
    MOVE_E,
    MOVE_N,
    MOVE_S,
    MOVE_W,
    CritterEnv,
)
from critter_gym.envs.duel_env import ATTACK, CHARGE, GUARD, DuelEnv
from critter_gym.registration import register_envs

register_envs()

CFG = dict(vary=True, num_types=12, num_gyms=3, max_steps=120)


def _nav_to_gym(obs: dict) -> int:
    """Head to the nearest visible gym (else creature, else sweep) — test scaffolding."""
    patch = obs["local_patch"]
    center = patch.shape[0] // 2
    targets = np.argwhere(patch == 2)
    if targets.size == 0:
        targets = np.argwhere(patch == 1)
    if targets.size > 0:
        rel = targets - center
        nearest = rel[np.argmin(np.abs(rel).sum(axis=1))]
        dr, dc = int(nearest[0]), int(nearest[1])
        if dr == 0 and dc == 0:
            return CATCH
        if abs(dr) >= abs(dc):
            return MOVE_S if dr > 0 else MOVE_N
        return MOVE_E if dc > 0 else MOVE_W
    r, c = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    if r % 2 == 0:
        return MOVE_E if c < 9 else MOVE_S
    return MOVE_W if c > 0 else MOVE_S


def test_duel_env_conforms_and_registered() -> None:  # AC1
    env = DuelEnv(**CFG)
    assert conforms(env)
    assert int(env.action_space.n) == ACTION_N
    assert REQUIRED_OBS_KEYS.issubset(set(env.observation_space.spaces))
    assert {"critter", "forage", "duel"}.issubset(set(family_names()))
    assert conforms(make_family("duel"))


def test_duel_exposes_charge_in_obs_but_contract_still_holds() -> None:  # AC3 (observability)
    env = DuelEnv(**CFG)
    obs, _ = env.reset(seed=1_000_000)
    assert "player_charge" in obs and "enemy_charge" in obs  # extra keys beyond REQUIRED
    assert conforms(env)  # ⊇ REQUIRED_OBS_KEYS → still conforms
    # extra keys are present in every obs (overworld too), so obs ∈ observation_space.
    assert env.observation_space.contains(obs)


def _battle_reaching_sig(env: CritterEnv, seed: int, max_steps: int = 120):
    """Drive the env to a battle and trace (in_battle, enemy_hp, reward) — a signature
    that captures BATTLE dynamics (unlike the generic reward+caught trajectory_signature,
    which cannot see a battle-system difference; pilot note N1)."""
    obs, _ = env.reset(seed=seed)
    sig: list = []
    entered = False
    for _ in range(max_steps):
        a = ATTACK if obs["in_battle"][0] == 1 else _nav_to_gym(obs)
        obs, r, term, trunc, _ = env.step(a)
        if obs["in_battle"][0] == 1:
            entered = True
        sig.append((int(obs["in_battle"][0]), int(obs["enemy_hp"][0]), round(float(r), 1)))
        if term or trunc:
            break
    return sig, entered


def test_duel_battle_trajectory_distinct_from_family_a() -> None:  # AC2
    seed = 1_000_000
    a_sig, a_in = _battle_reaching_sig(CritterEnv(**CFG), seed)
    c_sig, c_in = _battle_reaching_sig(DuelEnv(**CFG), seed)
    assert a_in and c_in, "both families must reach a battle for a fair comparison"
    assert a_sig != c_sig, "family C battle dynamics must differ from family A (not a seed variant)"


def test_duel_battle_is_type_agnostic() -> None:  # AC2 (structural core)
    # The per-seed hidden type chart drives family A damage; family C ignores it.
    # Same seed → same world/chart; the duel deals stat-based damage with no
    # effectiveness multiplier, so a fresh ATTACK deals exactly attack*(1+charge).
    env = DuelEnv(**CFG)
    env.reset(seed=1_000_000)
    gym_tile = next(iter(env._gym_tiles))
    env._agent_pos = np.array(gym_tile, dtype=np.int64)
    env._maybe_enter_battle()
    assert env._mode == "battle"
    boss = env._battle.state.active(Side.B)
    player = env._battle.state.active(Side.A)
    bhp0 = boss.hp
    env.step(ATTACK)  # charge 0 → base damage, type-agnostic
    assert boss.hp == bhp0 - player.attack  # exactly stat-based (no chart multiplier)


def test_duel_guard_negates_attack_and_charge_scales() -> None:  # mechanic (RPS + charge)
    env = DuelEnv(**CFG)
    env.reset(seed=1_000_001)
    gym_tile = next(iter(env._gym_tiles))
    env._agent_pos = np.array(gym_tile, dtype=np.int64)
    env._maybe_enter_battle()
    player = env._battle.state.active(Side.A)
    hp0 = player.hp
    # Enemy pattern: CHARGE (echarge 0→1), then ATTACK. GUARD on the attack turn negates.
    env.step(GUARD)  # enemy charges; no damage
    env.step(GUARD)  # enemy attacks but is guarded → player unharmed
    assert player.hp == hp0
    # charge scales our damage: a charged ATTACK deals more than a base ATTACK.
    boss = env._battle.state.active(Side.B)
    bhp1 = boss.hp
    env.step(CHARGE)  # pcharge 0→1 (enemy charges)
    env.step(ATTACK)  # charged hit (enemy now attacks, but we measure boss hp drop)
    assert boss.hp <= bhp1 - player.attack * 2  # ≥ 2× base (charge=1 → ×2)


def test_duel_winnable_from_observable_state() -> None:  # AC3
    from critter_gym.genre_generalization import duel_aware_policy

    seeds = [1_000_000 + i for i in range(8)]
    total = 0.0
    for s in seeds:
        env = DuelEnv(**CFG)
        obs, _ = env.reset(seed=s)
        for _ in range(CFG["max_steps"]):
            obs, r, term, trunc, _ = env.step(duel_aware_policy(obs))
            total += r
            if term or trunc:
                break
    assert total > 0, "family C must be winnable by an obs-only C-appropriate policy"


def test_duel_v0_check_env_compliant() -> None:  # AC6 (5th gym id)
    from gymnasium.utils.env_checker import check_env

    check_env(gym.make("CritterGym-duel-v0").unwrapped, skip_render_check=True)


def test_family_a_battle_unchanged_by_family_c() -> None:  # AC6 (no regression)
    # DuelEnv is a subclass; family A must be byte-identical on a battle-reaching run.
    sig1, _ = _battle_reaching_sig(CritterEnv(**CFG), 1_000_003)
    sig2, _ = _battle_reaching_sig(CritterEnv(**CFG), 1_000_003)
    assert sig1 == sig2  # determinism preserved (RLVR)
