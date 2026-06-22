"""AC3 — is infer-the-meta *load-bearing*? (reasoning-load-bearing, DESIGN §3.1.1)

The headline novelty of CritterGym is that the per-seed type chart is hidden, so a
good policy must *infer* matchups from experience. ``typechart-depth`` deepened the
chart but a pilot showed inference was not yet *load-bearing*: with the M1 battle
economy a "just attack / cycle the party" policy did as well as one that knew the
chart (free force-switch brute-forced the super-effective creature).

This test proves the **team-commit** battle economy (``Battle(commit_mode=True)``:
one committed champion, no mid-battle switching, no force-switch cycling) makes
inference load-bearing, via four scripted arms over an EPISODE of recurring-type
gym battles. Built on the product API only (numpy, no ``[rl]`` deps), with a fixed
held-out seed set so the gate is reproducible.

Two gates (thresholds set conservatively below the pilot's measured margins so N
seeds of variance stay comfortably inside):

  Gate 0 — type knowledge is decisive:   oracle_mean − type_blind_mean ≥ 0.20
  Gate 1 — inference beats probing:       infer_mean  − probe_mean      ≥ 0.10

Pilot margins (memory ``team-commit-makes-inference-load-bearing``): Gate0 ≈ 0.48,
Gate1 ≈ 0.36 — both ~3× the thresholds asserted here.
"""

from __future__ import annotations

import numpy as np

from critter_gym.battle import ActionKind, Battle, BattleAction, BattleState, Side
from critter_gym.creatures import Creature, Move
from critter_gym.types import SUPER_EFFECTIVE, ElementType, generate_typechart

# -- fixed, reproducible experiment config (coded as constants per AC3) --------
HELD_OUT_SEEDS = tuple(range(1000, 1042))  # 42 held-out seeds (N ≥ 40)
SUPER_MULT = 3.0                            # difficulty knob (pilot-verified sweet spot)
PARTY_SIZE = 4
BOSS_POOL = 3                               # small pool => boss types recur across battles
N_BOSSES = 8                                # gym battles per episode
P_HP, P_ATK, P_DEF = 50, 12, 10
B_HP, B_ATK, B_DEF = 140, 18, 12
POOL = list(ElementType)
ARMS = ("oracle", "type_blind", "probe", "infer")
GATE0_MIN = 0.20
GATE1_MIN = 0.10


def _move_action() -> BattleAction:
    return BattleAction(ActionKind.MOVE, 0)


def _make_party() -> list[Creature]:
    """One mono-type creature per type (each with a single move of its own type)."""
    return [
        Creature(f"C{i}-{t.value}", (t,), P_HP, P_ATK, P_DEF, 10, [Move(f"m{i}", t, 30)])
        for i, t in enumerate(POOL[:PARTY_SIZE])
    ]


def _make_boss(boss_type: ElementType) -> Creature:
    return Creature(
        f"Boss-{boss_type.value}", (boss_type,), B_HP, B_ATK, B_DEF, 8,
        [Move("strike", boss_type, 30)],
    )


def _fresh(c: Creature) -> Creature:
    return Creature(c.name, c.types, c.max_hp, c.attack, c.defense, c.speed,
                    list(c.moves), hp=c.max_hp)


def _best_creature(chart, party: list[Creature], boss: Creature) -> int:
    """Index of the party creature whose move is most effective vs the boss."""
    best_i, best_eff = 0, -1.0
    for i, c in enumerate(party):
        eff = chart.multi_effectiveness(c.moves[0].type, boss.types)
        if eff > best_eff:
            best_i, best_eff = i, eff
    return best_i


def _commit_lead(arm: str, chart, party, boss, memory, rng) -> int:
    """Which creature each arm commits to the boss (team-commit: no later switch)."""
    bt = boss.types[0]
    if arm == "oracle":                      # perfect chart knowledge (upper bound)
        return _best_creature(chart, party, boss)
    if arm == "type_blind":                  # ignores types — always the first creature
        return 0
    if arm == "infer":                       # reuse cross-battle memory; guess if unseen
        return memory.get(bt, int(rng.integers(0, len(party))))
    return int(rng.integers(0, len(party)))  # probe: can't probe under commit → guesses


def _run_battle(arm, chart, party, boss, memory, rng) -> bool:
    lead = _commit_lead(arm, chart, party, boss, memory, rng)
    state = BattleState(party_a=[_fresh(c) for c in party], party_b=[_fresh(boss)],
                        active_a=lead, active_b=0)
    battle = Battle(state, chart=chart, max_turns=50, commit_mode=True)
    while not (battle.terminated or battle.truncated):
        battle.step(_move_action(), _move_action())
    return battle.winner is Side.A


def _winnable_pool(chart, party, rng) -> list[ElementType]:
    """Boss types beatable by ≥1 starter (super-effective) — keeps every gym fair."""
    pool = list(rng.choice(POOL, size=BOSS_POOL, replace=False))
    out = []
    for bt in pool:
        boss = _make_boss(bt)
        i = _best_creature(chart, party, boss)
        if chart.multi_effectiveness(party[i].moves[0].type, boss.types) >= SUPER_MULT:
            out.append(bt)
    return out


def _episode_score(seed: int, arm: str) -> float:
    rng = np.random.default_rng(seed)
    chart = generate_typechart(seed, POOL, vary=True, super_mult=SUPER_MULT)
    party = _make_party()
    pool = _winnable_pool(chart, party, rng)
    if not pool:
        return 0.0
    boss_types = [pool[int(rng.integers(0, len(pool)))] for _ in range(N_BOSSES)]
    memory: dict[ElementType, int] = {}
    wins = 0
    for bt in boss_types:
        boss = _make_boss(bt)
        if _run_battle(arm, chart, party, boss, memory, rng):
            wins += 1
        # infer/probe learn the matchup once they have seen the boss type.
        memory.setdefault(bt, _best_creature(chart, party, boss))
    return wins / len(boss_types)


def _arm_means() -> dict[str, float]:
    return {
        arm: float(np.mean([_episode_score(s, arm) for s in HELD_OUT_SEEDS]))
        for arm in ARMS
    }


def test_difficulty_knob_distinct_from_m1() -> None:
    # Sanity: the experiment uses the amplified super multiplier, not the M1 default.
    assert SUPER_MULT != SUPER_EFFECTIVE


def test_gate0_type_knowledge_is_decisive() -> None:
    m = _arm_means()
    margin = m["oracle"] - m["type_blind"]
    assert margin >= GATE0_MIN, (
        f"Gate 0 FAILED: oracle {m['oracle']:.3f} − type_blind {m['type_blind']:.3f} "
        f"= {margin:.3f} < {GATE0_MIN}. Type knowledge is not decisive. arms={m}"
    )


def test_gate1_inference_beats_probing() -> None:
    m = _arm_means()
    margin = m["infer"] - m["probe"]
    assert margin >= GATE1_MIN, (
        f"Gate 1 FAILED: infer {m['infer']:.3f} − probe {m['probe']:.3f} "
        f"= {margin:.3f} < {GATE1_MIN}. Inference is not load-bearing. arms={m}"
    )


def test_arm_ordering_is_coherent() -> None:
    # The whole story in one assert: oracle ≥ infer > probe, and oracle > type_blind.
    m = _arm_means()
    assert m["oracle"] >= m["infer"] > m["probe"], f"incoherent arm ordering: {m}"
    assert m["oracle"] > m["type_blind"], f"oracle should beat type_blind: {m}"
