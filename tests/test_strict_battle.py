"""Opt-in ``strict_battle`` variant (hard-benchmark/strict-battle).

Default battle economy clamps every hit to ``max(1, ...)`` — even a resisted
(effectiveness < NEUTRAL) attack chips at least 1 HP, so pure attrition can win
gyms without any type inference (paper §5 limitation (i)). ``strict_battle=True``
zeroes resisted damage (symmetrically, both directions) so landing effective hits
becomes load-bearing. Off (the default) must stay byte-identical.
"""

from __future__ import annotations

import numpy as np
import pytest

from critter_gym.battle import ActionKind, Battle, BattleAction, BattleState
from critter_gym.creatures import Creature, Move
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.party import starter_party
from critter_gym.region import generate_region
from critter_gym.types import FIXED_CHART, NEUTRAL, ElementType

F, W, G = ElementType.FIRE, ElementType.WATER, ElementType.GRASS


def _creature(name: str, types: tuple, move_type: ElementType, power: int = 30) -> Creature:
    return Creature(name, types, 50, 12, 10, 10, [Move("m", move_type, power)])


def _battle(a: Creature, b: Creature, *, strict: bool, max_turns: int = 200) -> Battle:
    state = BattleState(party_a=[a], party_b=[b])
    return Battle(state, chart=FIXED_CHART, max_turns=max_turns, strict_battle=strict)


# -- AC2: the strict rule -----------------------------------------------------


def test_strict_resisted_damage_is_zero() -> None:
    # FIXED chart: WATER beats FIRE => effectiveness(FIRE, WATER) < NEUTRAL (resisted).
    atk, dfn = _creature("a", (F,), F), _creature("b", (W,), W)
    assert _battle(atk, dfn, strict=False).damage(atk, dfn, 0) >= 1  # legacy min-1 chip
    assert _battle(atk, dfn, strict=True).damage(atk, dfn, 0) == 0


@pytest.mark.parametrize("def_type", [F, G])  # eff(F, F) = NEUTRAL, eff(F, G) = super
def test_strict_effective_damage_unchanged(def_type: ElementType) -> None:
    atk, dfn = _creature("a", (F,), F), _creature("b", (def_type,), def_type)
    legacy = _battle(atk, dfn, strict=False).damage(atk, dfn, 0)
    assert _battle(atk, dfn, strict=True).damage(atk, dfn, 0) == legacy
    assert legacy >= 1


def test_strict_is_symmetric_both_directions() -> None:
    # Boss-side attacks obey the same engine rule: a resisted boss move deals 0.
    player = _creature("p", (F,), F)  # FIRE defender resists GRASS (FIRE beats GRASS)
    boss = _creature("boss", (W,), G)  # WATER-typed boss swinging a GRASS move
    b = _battle(player, boss, strict=True)
    assert b.damage(boss, player, 0) == 0  # boss -> player resisted
    assert b.damage(player, boss, 0) == 0  # player -> boss resisted (F vs W)


def test_strict_multitype_product_rule() -> None:
    # Two defending types multiply: super * resisted = NEUTRAL keeps damage flowing,
    # neutral * resisted < NEUTRAL zeroes it.
    atk = _creature("a", (F,), F)
    neutral_pair = _creature("b", (W, G), W)  # 0.5 * 2.0 = 1.0
    resisted_pair = _creature("c", (W, F), W)  # 0.5 * 1.0 = 0.5
    b1 = _battle(atk, neutral_pair, strict=True)
    b2 = _battle(atk, resisted_pair, strict=True)
    assert b1.damage(atk, neutral_pair, 0) >= 1
    assert b2.damage(atk, resisted_pair, 0) == 0


def test_strict_mutual_zero_stalemates_to_truncation() -> None:
    # Both sides resisted => damage 0 both ways => the battle truncates at max_turns
    # with no winner (the pre-existing draw path; the env then leaves battle).
    a = _creature("a", (F,), F)  # FIRE move vs WATER defender: resisted
    b = _creature("b", (W,), G)  # GRASS move vs FIRE defender: resisted
    battle = _battle(a, b, strict=True, max_turns=5)
    move = BattleAction(ActionKind.MOVE, 0)
    result = battle.step(move, move)
    for _ in range(10):
        if result.terminated or result.truncated:
            break
        result = battle.step(move, move)
    assert result.truncated and not result.terminated
    assert result.winner is None
    assert a.hp == a.max_hp and b.hp == b.max_hp  # nobody took a scratch


# -- AC1: default-off is byte-identical ---------------------------------------


def _trajectory(env: CritterEnv, seed: int, steps: int = 200) -> list:
    obs, _ = env.reset(seed=seed)
    rng = np.random.default_rng(1234)
    trace = []
    for _ in range(steps):
        a = int(rng.integers(0, 6))
        obs, r, term, trunc, _ = env.step(a)
        trace.append(
            (
                float(r),
                bool(term),
                bool(trunc),
                tuple(int(x) for x in obs["agent_pos"]),
                int(obs["gyms_defeated"][0]),
                int(obs["player_hp"][0]),
                int(obs["enemy_hp"][0]),
            )
        )
        if term or trunc:
            break
    return trace


@pytest.mark.parametrize("seed", [0, 7])
def test_default_off_matches_explicit_false(seed: int) -> None:
    kw = dict(vary=True, num_types=8, commit_battles=True, min_gyms=3)
    assert _trajectory(CritterEnv(**kw), seed) == _trajectory(
        CritterEnv(strict_battle=False, **kw), seed
    )


# -- AC3: winnability sweep (no unwinnable world under strict) ------------------

_SWEEP_GRID, _SWEEP_NCRE, _SWEEP_NGYM, _SWEEP_NTYPES = 16, 6, 5, 8


@pytest.mark.parametrize("boss_secondary", [False, True])
def test_strict_winnability_sweep(boss_secondary: bool) -> None:
    """Every boss in 200 hard-config seeds has a party move with strict damage > 0.

    Relies on the matchup guarantee (#15): vary-mode boss types are drawn only from
    types some starter move strictly super-effects; with a hidden secondary the
    product is still >= super_mult * 0.5 >= NEUTRAL. This sweep is the executable
    proof that guarantee actually covers strict mode (damage flows iff eff >= NEUTRAL).
    """
    party_move_types = [c.moves[0].type for c in starter_party()]
    for seed in range(200):
        region = generate_region(
            seed, _SWEEP_GRID, _SWEEP_NCRE, _SWEEP_NGYM, vary=True,
            num_types=_SWEEP_NTYPES, min_gyms=_SWEEP_NGYM, boss_secondary=boss_secondary,
        )
        secondaries = region.boss_secondary_types or (None,) * len(region.gyms)
        for (_, primary), secondary in zip(region.gyms, secondaries):
            def_types = (primary,) if secondary is None else (primary, secondary)
            best = max(
                region.chart.multi_effectiveness(mt, def_types) for mt in party_move_types
            )
            assert best >= NEUTRAL, (
                f"seed {seed}: boss {def_types} resists every party move under strict"
            )


# -- engine wiring: env passes the flag through --------------------------------


def test_env_battle_inherits_strict_flag() -> None:
    env = CritterEnv(strict_battle=True)
    env.reset(seed=0)
    # March the agent onto the first gym tile to open a battle.
    gym_pos = next(iter(env._gym_tiles))
    env._agent_pos = np.array(gym_pos, dtype=np.int64)
    env._maybe_enter_battle()
    assert env._battle is not None and env._battle.strict_battle is True
