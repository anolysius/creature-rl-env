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
    # Family B (genre-generalization-foundation): contact-collect collection mechanic
    # — a structurally distinct collection-RPG sharing the obs/action contract.
    register(
        id="CritterGym-forage-v0",
        entry_point="critter_gym.envs.forage_env:ForageEnv",
        kwargs={"vary": True, "num_types": 12, "num_gyms": 8, "max_steps": 400},
    )
    # Family C (battle-system-family): a structurally distinct BATTLE SYSTEM — a
    # type-agnostic stamina/commit duel (no type chart, no switching), a stronger
    # structural axis than family B's collection-only difference. Exposes the duel
    # charge as extra obs keys (contract-safe). See envs/duel_env.py.
    register(
        id="CritterGym-duel-v0",
        entry_point="critter_gym.envs.duel_env:DuelEnv",
        kwargs={"vary": True, "num_types": 12, "num_gyms": 8, "max_steps": 400},
    )
    # Family D (family-d-muster): collection-gated power — catching buffs party attack,
    # with strong bosses so you must muster a collection before you can win (a
    # progression-dependency axis distinct from B's collection and C's battle system).
    register(
        id="CritterGym-muster-v0",
        entry_point="critter_gym.envs.muster_env:MusterEnv",
        kwargs={
            "vary": True, "num_types": 12, "num_gyms": 8, "max_steps": 600,
            "num_creatures": 12, "boss_hp": 300, "boss_def": 24,
        },
    )
    _register_families()
    _REGISTERED = True


# Env-family registry (DESIGN §3.1.1 (B)): structurally distinct collection-RPGs on
# one obs/action contract, for environment-level (genre) generalization measurement.
# A shared world-gen config so the env-level comparison isolates the *mechanic*.
# NOTE: this family-registry config is intentionally smaller than the `*-v0` gym-id
# kwargs above — the registry is for fast env-level measurement (isolate the mechanic),
# the gym ids are the full-size playable variants. The two are separate on purpose.
_FAMILY_CFG: dict[str, object] = dict(vary=True, num_types=12, num_gyms=3, max_steps=120)


def _register_families() -> None:
    from critter_gym.env_family import register_family
    from critter_gym.envs.critter_env import CritterEnv
    from critter_gym.envs.duel_env import DuelEnv
    from critter_gym.envs.forage_env import ForageEnv
    from critter_gym.envs.muster_env import MusterEnv

    register_family("critter", lambda **kw: CritterEnv(**{**_FAMILY_CFG, **kw}))
    register_family("forage", lambda **kw: ForageEnv(**{**_FAMILY_CFG, **kw}))
    register_family("duel", lambda **kw: DuelEnv(**{**_FAMILY_CFG, **kw}))
    # Family D needs strong bosses + headroom to muster (its identity calibration), so
    # its registry factory overrides the shared world config accordingly.
    _MUSTER_CFG = {**_FAMILY_CFG, "boss_hp": 300, "boss_def": 24,
                   "num_creatures": 10, "max_steps": 220}
    register_family("muster", lambda **kw: MusterEnv(**{**_MUSTER_CFG, **kw}))
