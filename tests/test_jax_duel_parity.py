"""AC1/AC2/AC3/AC4: numpy <-> JAX full-episode parity for family C (duel).

`make_jax_env(JaxEnvConfig(family=_FAM_DUEL, commit=False))` ports the **duel** family — a
structurally distinct, type-AGNOSTIC RPS/stamina battle — to the vectorized JAX env,
mirroring `DuelEnv(commit_battles=False)`:
  - overworld = family A (explicit CATCH-collect; `DuelEnv` doesn't override `_step_overworld`);
  - battle = ATTACK/CHARGE/GUARD against a deterministic boss (ATTACK if charged else CHARGE),
    with **simultaneous** damage (no speed order), `floor(attack × (1 + charge))` hits (no type
    chart / defense), charge accumulation, and a 40-turn stalemate cap (= loss).

The duel exposes real `player_charge`/`enemy_charge` obs (0-masked on the other families); the
parity battery includes a scripted *optimal* policy that beats the deterministic boss, so the
win → level-up → evolve economy is exercised (a non-vacuity guard pins ATTACK/CHARGE/GUARD,
the turn-cap loss, and the evolve path). Skipped when JAX is absent.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402

from critter_gym.envs.duel_env import DuelEnv  # noqa: E402
from critter_gym.jax_env import (  # noqa: E402
    _DUEL_TURN_CAP,
    _FAM_DUEL,
    JaxEnvConfig,
    make_jax_env,
)
from critter_gym.region import generate_region  # noqa: E402

_GRID, _NC, _NG = 10, 5, 3
_VARY_TYPES, _FIXED_TYPES = 8, 3

_OBS_KEYS = [
    "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved", "in_battle",
    "player_hp", "player_type", "player_level", "enemy_hp", "enemy_type",
    "player_charge", "enemy_charge",
]

_DUEL_ENV = make_jax_env(JaxEnvConfig(commit=False, family=_FAM_DUEL))


def _assert_obs_equal(np_obs, jx_obs, where: int) -> None:
    for k in _OBS_KEYS:
        assert np.array_equal(np.asarray(np_obs[k]), np.asarray(jx_obs[k])), (
            f"obs[{k}] differs @{where}"
        )


def _run_parity(np_env, jx_env, region, seed: int, policy, max_steps: int = 200) -> int:
    np_obs, _ = np_env.reset(seed=seed)
    state = jx_env.reset(region)
    step = jx_env.make_step()
    _assert_obs_equal(np_obs, jx_env.encode_obs(state), where=0)
    compared = 0
    for _ in range(max_steps):
        action = policy(np_env, np_obs)
        np_obs, r_np, term_np, trunc_np, _ = np_env.step(action)
        state, jx_obs, r_jx, term_jx, trunc_jx = step(state, jnp.int32(action))
        compared += 1
        _assert_obs_equal(np_obs, jx_obs, where=compared)
        assert float(r_np) == float(r_jx), f"reward differs @{compared}"
        assert bool(term_np) == bool(term_jx), f"terminated differs @{compared}"
        assert bool(trunc_np) == bool(trunc_jx), f"truncated differs @{compared}"
        if term_np or trunc_np:
            break
    return compared


def _gym_seeking(env, obs):
    """Overworld: head to the nearest undefeated gym. In battle: ATTACK."""
    if obs["in_battle"][0]:
        return 0
    ar, ac = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    targets = [pos for pos, i in env._gym_tiles.items() if not env._gym_defeated[i]]
    if not targets:
        return 5
    gr, gc = min(targets, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    if gr < ar:
        return 0
    if gr > ar:
        return 1
    if gc > ac:
        return 2
    if gc < ac:
        return 3
    return 5


def _charge_exploit(env, obs):
    """In battle: charge once, then unleash — exercises charge accumulation + a big hit."""
    if obs["in_battle"][0]:
        return 0 if int(obs["player_charge"][0]) >= 1 else 1
    return _gym_seeking(env, obs)


def _stalemate(env, obs):
    """In battle: always GUARD → mutual non-damage → hit the 40-turn cap (a loss)."""
    if obs["in_battle"][0]:
        return 2
    return _gym_seeking(env, obs)


def _duel_optimal(env, obs):
    """Beat the deterministic boss: GUARD when it will ATTACK (enemy_charge≥1), else ATTACK.

    This blocks every boss hit (boss telegraphs via its charge) while landing a hit each
    turn the boss is charging — so it wins (and, on a first win, levels to 2 and evolves)."""
    if obs["in_battle"][0]:
        return 2 if int(obs["enemy_charge"][0]) >= 1 else 0
    return _gym_seeking(env, obs)


_POLICIES = [
    ("gym_seeking", _gym_seeking),
    ("charge_exploit", _charge_exploit),
    ("stalemate", _stalemate),
    ("duel_optimal", _duel_optimal),
]


@pytest.mark.parametrize("vary", [False, True])
@pytest.mark.parametrize("seed", [0, 1, 2, 4, 7, 11])
def test_duel_parity_scripted(vary: bool, seed: int) -> None:
    nt = _VARY_TYPES if vary else _FIXED_TYPES
    region = generate_region(seed, _GRID, _NC, _NG, vary=vary, num_types=nt)
    for _name, pol in _POLICIES:
        env = DuelEnv(commit_battles=False, vary=vary, num_types=nt)
        assert _run_parity(env, _DUEL_ENV, region, seed, pol) > 0


@pytest.mark.parametrize("seed", [0, 1, 2, 7, 13])
def test_duel_parity_random(seed: int) -> None:
    rng = np.random.default_rng(7000 + seed)
    region = generate_region(seed, _GRID, _NC, _NG, vary=True, num_types=_VARY_TYPES)
    env = DuelEnv(commit_battles=False, vary=True, num_types=_VARY_TYPES)
    assert _run_parity(env, _DUEL_ENV, region, seed, lambda e, o: int(rng.integers(0, 6))) > 0


def test_duel_battery_is_non_vacuous() -> None:
    """Guard against a vacuous parity: confirm the battery actually drives the duel
    mechanics it claims to test — all three battle actions (ATTACK/CHARGE/GUARD), a
    turn-cap stalemate loss, and the win → evolve path (a win levels party[0] to 2,
    triggering `evolve`)."""
    saw = {"attack": False, "charge": False, "guard": False,
           "stalemate_loss": False, "win": False, "evolve": False}
    for vary in (False, True):
        nt = _VARY_TYPES if vary else _FIXED_TYPES
        for seed in range(12):
            for _name, pol in _POLICIES:
                env = DuelEnv(commit_battles=False, vary=vary, num_types=nt)
                obs, _ = env.reset(seed=seed)
                prev_ev = 0
                for _ in range(200):
                    a = pol(env, obs)
                    in_battle = bool(obs["in_battle"][0])
                    pre_turns = env._duel_turns
                    if in_battle:
                        eff = a if a in (0, 1, 2) else 2
                        saw["attack"] |= eff == 0
                        saw["charge"] |= eff == 1
                        saw["guard"] |= eff == 2
                    obs, r, term, trunc, _ = env.step(a)
                    # a stalemate loss: duel hit the cap and returned to overworld w/o reward
                    left_battle = in_battle and not bool(obs["in_battle"][0])
                    if left_battle and pre_turns + 1 >= _DUEL_TURN_CAP and r < 1.0:
                        saw["stalemate_loss"] = True
                    if r >= 1.0:
                        saw["win"] = True
                    if int(obs["evolved"][0]) > prev_ev:
                        saw["evolve"] = True
                    prev_ev = int(obs["evolved"][0])
                    if term or trunc:
                        break
    for key in ("attack", "charge", "guard", "stalemate_loss", "win", "evolve"):
        assert saw[key], f"battery never exercised {key!r} — parity may be vacuous on it"


def test_duel_jit_and_vmap() -> None:
    region = generate_region(0, _GRID, _NC, _NG, vary=True, num_types=_VARY_TYPES)
    step = _DUEL_ENV.make_step(jit=True)
    state = _DUEL_ENV.reset(region)
    state, obs, reward, term, trunc = step(state, jnp.int32(2))
    jax.block_until_ready(state.agent_pos)
    assert obs["local_patch"].shape == (5, 5)
    assert obs["player_charge"].shape == (1,)
    states = [
        _DUEL_ENV.reset(generate_region(s, _GRID, _NC, _NG, vary=True, num_types=_VARY_TYPES))
        for s in range(8)
    ]
    batched = jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *states)
    vstep = jax.jit(jax.vmap(_DUEL_ENV.step))
    bstate, bobs, br, bt, btr = vstep(batched, jnp.zeros((8,), jnp.int32))
    jax.block_until_ready(br)
    assert br.shape == (8,)
