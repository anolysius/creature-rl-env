"""Gymnasium registration for CritterGym environments."""

from __future__ import annotations

from gymnasium.envs.registration import register

_REGISTERED = False


def register_envs() -> None:
    """Register CritterGym ids with Gymnasium (idempotent)."""
    global _REGISTERED
    if _REGISTERED:
        return
    register(
        id="CritterGym-v0",
        entry_point="critter_gym.envs.critter_env:CritterEnv",
    )
    # Procedural variant: seed varies region content + a per-seed hidden type chart
    # over a *deep* 12-type pool (far harder to memorize than the M1 3-cycle), with
    # more gyms whose boss types recur from a per-seed pool. Train/test seed split
    # enables generalization measurement (DESIGN.md §3.1). NOTE: making chart
    # *inference* provably load-bearing (vs reaction) needs a battle-economy redesign
    # — tracked as future work (a pilot showed switch-cost dominates), see DESIGN §3.1.1.
    register(
        id="CritterGym-procgen-v0",
        entry_point="critter_gym.envs.critter_env:CritterEnv",
        kwargs={
            "vary": True,
            "num_types": 12,
            "num_gyms": 8,  # more gyms so boss types recur within an episode
            "max_steps": 400,  # room to traverse + battle more gyms
        },
    )
    # team-commit variant: the procgen world PLUS the battle-economy redesign that
    # makes inferring the hidden chart load-bearing (reasoning-load-bearing, DESIGN
    # §3.1.1). Boss fights commit one champion (no switching / no force-switch
    # cycling), a higher super-effective multiplier + stronger bosses punish a wrong
    # type pick, and boss types recur so an inferred matchup pays off. A scripted
    # 4-arm gate (tests/test_reasoning_gate.py) shows infer > probe on held-out
    # seeds; whether a *learned* policy acquires the inference is follow-up work.
    register(
        id="CritterGym-commit-v0",
        entry_point="critter_gym.envs.critter_env:CritterEnv",
        kwargs={
            "vary": True,
            "num_types": 12,
            "num_gyms": 8,
            "max_steps": 400,
            "super_mult": 3.0,
            "boss_hp": 140,
            "boss_atk": 18,
            "commit_battles": True,
        },
    )
    _REGISTERED = True
