"""Opt-in ``super_effective_only`` battle economy (hard-benchmark/super-effective-economy).

``strict_battle`` zeroed only RESISTED (< NEUTRAL) hits, so NEUTRAL chip damage still let
attrition grind a boss down without inferring the chart (the §5-(i) confound persisted — the
strict scout falsified confound closure). ``super_effective_only=True`` goes one step further:
only STRICTLY super-effective (eff > NEUTRAL) hits deal damage — NEUTRAL *and* resisted deal 0.
Landing the correct super-effective type is now the ONLY path to a win. It is a strict superset
of ``strict_battle`` (everything strict zeroes, SE-only also zeroes, plus the NEUTRAL band).

Off (the default) must stay byte-identical to the legacy ``max(1, ...)`` economy.
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


def _battle(a: Creature, b: Creature, *, se_only: bool, max_turns: int = 200) -> Battle:
    state = BattleState(party_a=[a], party_b=[b])
    return Battle(state, chart=FIXED_CHART, max_turns=max_turns, super_effective_only=se_only)


# -- AC1: the super-effective-only rule ---------------------------------------


def test_se_only_neutral_damage_is_zero() -> None:
    # eff(FIRE, FIRE) == NEUTRAL. strict_battle would KEEP this (>= NEUTRAL); SE-only zeroes it.
    atk, dfn = _creature("a", (F,), F), _creature("b", (F,), F)
    assert _battle(atk, dfn, se_only=False).damage(atk, dfn, 0) >= 1  # legacy min-1 chip
    assert _battle(atk, dfn, se_only=True).damage(atk, dfn, 0) == 0  # neutral zeroed


def test_se_only_resisted_damage_is_zero() -> None:
    # FIXED chart: WATER beats FIRE => eff(FIRE, WATER) < NEUTRAL (resisted) => 0 under SE-only.
    atk, dfn = _creature("a", (F,), F), _creature("b", (W,), W)
    assert _battle(atk, dfn, se_only=True).damage(atk, dfn, 0) == 0


def test_se_only_super_effective_flows_unchanged() -> None:
    # eff(FIRE, GRASS) == super_mult > NEUTRAL: SE-only keeps it byte-identical to legacy.
    atk, dfn = _creature("a", (F,), F), _creature("b", (G,), G)
    legacy = _battle(atk, dfn, se_only=False).damage(atk, dfn, 0)
    assert _battle(atk, dfn, se_only=True).damage(atk, dfn, 0) == legacy
    assert legacy >= 1


def test_se_only_is_strict_superset() -> None:
    """SE-only zeroes the whole (resisted ∪ neutral) band; the only survivor is strictly-super."""
    atk = _creature("a", (F,), F)
    resisted = _creature("r", (W,), W)  # eff(F, W) < NEUTRAL
    neutral = _creature("n", (F,), F)   # eff(F, F) == NEUTRAL
    superx = _creature("s", (G,), G)    # eff(F, G) > NEUTRAL
    b_r = _battle(atk, resisted, se_only=True)
    b_n = _battle(atk, neutral, se_only=True)
    b_s = _battle(atk, superx, se_only=True)
    assert b_r.damage(atk, resisted, 0) == 0
    assert b_n.damage(atk, neutral, 0) == 0
    assert b_s.damage(atk, superx, 0) >= 1


def test_se_only_symmetric_both_directions() -> None:
    # Both sides obey the same engine rule: a non-super boss move also deals 0.
    player = _creature("p", (F,), F)   # FIRE move vs WATER boss: eff(F, W) resisted => 0
    boss = _creature("boss", (W,), F)  # FIRE move vs FIRE player: eff(F, F) neutral => 0
    b = _battle(player, boss, se_only=True)
    assert b.damage(player, boss, 0) == 0  # player -> boss (resisted)
    assert b.damage(boss, player, 0) == 0  # boss -> player (neutral, would flow under strict)


def test_se_only_multitype_neutral_product_zeroed() -> None:
    """Key divergence from strict: super*resisted == NEUTRAL flows under strict but is 0 here."""
    atk = _creature("a", (F,), F)
    neutral_pair = _creature("b", (W, G), W)  # eff = 0.5(F,W) * 2.0(F,G) = 1.0 == NEUTRAL
    super_pair = _creature("c", (G, G), G)    # eff = 2.0 * 2.0 = 4.0 > NEUTRAL
    assert _battle(atk, neutral_pair, se_only=True).damage(atk, neutral_pair, 0) == 0
    assert _battle(atk, super_pair, se_only=True).damage(atk, super_pair, 0) >= 1


def test_se_only_mutual_zero_stalemates_to_truncation() -> None:
    # Neither side strictly super-effects the other => 0 both ways => draw at max_turns.
    a = _creature("a", (F,), F)  # FIRE move vs WATER: resisted
    b = _creature("b", (W,), F)  # FIRE move vs FIRE: neutral
    battle = _battle(a, b, se_only=True, max_turns=5)
    move = BattleAction(ActionKind.MOVE, 0)
    result = battle.step(move, move)
    for _ in range(10):
        if result.terminated or result.truncated:
            break
        result = battle.step(move, move)
    assert result.truncated and not result.terminated
    assert result.winner is None
    assert a.hp == a.max_hp and b.hp == b.max_hp  # nobody took a scratch


# -- AC1 (default-off byte-identical) -----------------------------------------


def _trajectory(env: CritterEnv, seed: int, steps: int = 200) -> list:
    obs, _ = env.reset(seed=seed)
    rng = np.random.default_rng(1234)
    trace = []
    for _ in range(steps):
        a = int(rng.integers(0, 6))
        obs, r, term, trunc, _ = env.step(a)
        trace.append(
            (
                float(r), bool(term), bool(trunc),
                tuple(int(x) for x in obs["agent_pos"]),
                int(obs["gyms_defeated"][0]), int(obs["player_hp"][0]),
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
        CritterEnv(super_effective_only=False, **kw), seed
    )


# -- AC-Q2: single-type winnability is guaranteed; secondary is a measured caveat -----

_SWEEP_GRID, _SWEEP_NCRE, _SWEEP_NGYM, _SWEEP_NTYPES = 16, 6, 5, 8


def test_se_only_single_type_winnability_sweep() -> None:
    """Single-type bosses stay winnable under SE-only across 200 hard-config seeds.

    Matchup guarantee (#15): vary-mode boss types are drawn only from types some starter
    move STRICTLY super-effects, so for a single-type boss the best party move has
    eff == super_mult > NEUTRAL — damage flows under SE-only. This is the executable proof
    that SE-only does not make single-type worlds structurally unwinnable.
    """
    party_move_types = [c.moves[0].type for c in starter_party()]
    for seed in range(200):
        region = generate_region(
            seed, _SWEEP_GRID, _SWEEP_NCRE, _SWEEP_NGYM, vary=True,
            num_types=_SWEEP_NTYPES, min_gyms=_SWEEP_NGYM, boss_secondary=False,
        )
        for _, primary in region.gyms:
            best = max(region.chart.multi_effectiveness(mt, (primary,)) for mt in party_move_types)
            assert best > NEUTRAL, (
                f"seed {seed}: single-type boss ({primary}) has no strictly-super party move"
            )


def test_se_only_secondary_can_be_unwinnable_is_a_measured_finding() -> None:
    """HONEST Q2 caveat: with a hidden secondary, the best product can be exactly NEUTRAL
    (super*resisted == 1.0), which SE-only zeroes -> that gym is structurally unwinnable.

    This is NOT a bug: it is the falsifiable Q2 result that SE-only + boss_secondary is too
    harsh to be a fair lever. We assert that such a world *exists* so the caveat is grounded
    in a concrete seed rather than hand-waved. (single-type SE-only stays fair, above.)
    """
    party_move_types = [c.moves[0].type for c in starter_party()]
    found_exact_neutral_ceiling = False
    for seed in range(300):
        region = generate_region(
            seed, _SWEEP_GRID, _SWEEP_NCRE, _SWEEP_NGYM, vary=True,
            num_types=_SWEEP_NTYPES, min_gyms=_SWEEP_NGYM, boss_secondary=True,
        )
        secondaries = region.boss_secondary_types or (None,) * len(region.gyms)
        for (_, primary), secondary in zip(region.gyms, secondaries):
            def_types = (primary,) if secondary is None else (primary, secondary)
            best = max(region.chart.multi_effectiveness(mt, def_types) for mt in party_move_types)
            if best <= NEUTRAL:  # SE-only would zero every party move => unwinnable
                found_exact_neutral_ceiling = True
                break
        if found_exact_neutral_ceiling:
            break
    assert found_exact_neutral_ceiling, (
        "expected at least one secondary-boss world whose best party matchup is <= NEUTRAL "
        "(the SE-only unwinnability caveat) within 300 seeds"
    )


# -- engine wiring: env passes the flag through --------------------------------


def test_env_battle_inherits_se_only_flag() -> None:
    env = CritterEnv(super_effective_only=True)
    env.reset(seed=0)
    gym_pos = next(iter(env._gym_tiles))
    env._agent_pos = np.array(gym_pos, dtype=np.int64)
    env._maybe_enter_battle()
    assert env._battle is not None and env._battle.super_effective_only is True
