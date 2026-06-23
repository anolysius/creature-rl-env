"""Collection-RPG env *family* abstraction — the substrate for genre generalization.

Instance-level generalization (held-out *seeds* of one generator) is what
:mod:`critter_gym.generalization` measures today. **Genre** generalization (DESIGN
§3.1.1 (B)) is the harder claim: generalizing across *structurally distinct*
collection-RPGs — an **environment-level** split (train on some env families, test on
an unseen family). That requires (a) more than one env and (b) a shared obs/action
contract so a single policy can act on every family.

This module is the *foundation* (first slice of an initiative-scale effort): it
formalises the contract every family must satisfy and a registry of families. It
does **not** by itself prove genre generalization — two families is a foundation,
not a claim (see :mod:`critter_gym.genre_generalization` and the task report).

A "family" = a structurally distinct rule system (different collection / battle /
progression mechanic) that nonetheless exposes the same observation and action
spaces, so the env-level split is measured on one interface.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from gymnasium import spaces

# The obs keys every collection-RPG family must expose (CritterEnv's contract).
REQUIRED_OBS_KEYS: frozenset[str] = frozenset(
    {
        "agent_pos", "local_patch", "caught", "gyms_defeated", "evolved",
        "in_battle", "player_hp", "player_type", "player_level",
        "enemy_hp", "enemy_type",
    }
)

# Harmonized obs (obs-harmonization task). A *single* family-agnostic policy net needs
# one identical observation space across every family (DESIGN §3.1.1 (B)). Family C
# (duel) needs two extra "charge" keys to be playable from observation; rather than let
# that fork the obs space (which forced #26 to exclude duel), every family exposes the
# same superset — the charge keys are masked to 0 on families that don't use them and
# carry real values on duel. This is a contract change, not a dynamics change: the
# 0-padding is behaviorally inert for policies that already read charge via ``.get``.
CHARGE_OBS_KEYS: frozenset[str] = frozenset({"player_charge", "enemy_charge"})
MAX_CHARGE_OBS = 2  # obs upper bound for charge keys; must be ≥ duel_env.MAX_CHARGE.
HARMONIZED_OBS_KEYS: frozenset[str] = REQUIRED_OBS_KEYS | CHARGE_OBS_KEYS

ACTION_N = 6  # Discrete(6): MOVE{N,S,E,W} / CATCH / NOOP, reinterpreted in battle.


@runtime_checkable
class CollectionRPGEnv(Protocol):
    """Structural contract a collection-RPG family must satisfy.

    Deliberately about the *interface* (obs/action spaces), not the dynamics — the
    whole point is that families differ in dynamics while sharing this contract, so
    one policy can be evaluated across all of them.
    """

    observation_space: spaces.Dict
    action_space: spaces.Discrete

    def reset(self, *, seed: int | None = ..., options: dict | None = ...) -> tuple: ...
    def step(self, action: int) -> tuple: ...


def conforms(env: object) -> bool:
    """True if ``env`` exposes the shared collection-RPG contract.

    Checks the obs Dict keys ⊇ REQUIRED_OBS_KEYS and a Discrete(ACTION_N) action
    space — the contract that lets one policy act on every family.
    """
    obs_space = getattr(env, "observation_space", None)
    act_space = getattr(env, "action_space", None)
    if not isinstance(obs_space, spaces.Dict) or not isinstance(act_space, spaces.Discrete):
        return False
    if int(act_space.n) != ACTION_N:
        return False
    return REQUIRED_OBS_KEYS.issubset(set(obs_space.spaces))


# -- family registry ----------------------------------------------------------
EnvThunk = Callable[..., object]  # (**kwargs) -> a CollectionRPGEnv instance
_FAMILIES: dict[str, EnvThunk] = {}


def register_family(name: str, factory: EnvThunk) -> None:
    """Register a family ``name`` → ``factory`` (idempotent on identical re-register)."""
    if name in _FAMILIES and _FAMILIES[name] is not factory:
        raise ValueError(f"family {name!r} already registered with a different factory")
    _FAMILIES[name] = factory


def family_names() -> list[str]:
    return sorted(_FAMILIES)


def make_family(name: str, **kwargs: object) -> object:
    """Build a fresh env for family ``name`` (kwargs forwarded to the factory)."""
    if name not in _FAMILIES:
        raise KeyError(f"unknown family {name!r}; registered: {family_names()}")
    return _FAMILIES[name](**kwargs)


def trajectory_signature(env: object, seed: int, actions: list[int]) -> list[float]:
    """Run ``actions`` from ``reset(seed)`` and return a per-step reward+caught trace.

    Two families that produce *different* signatures for the **same seed and actions**
    are structurally distinct — not reducible to a seed variant. Used by the family-B
    structural-distinctness test (genre-generalization-foundation AC2).
    """
    obs, _ = env.reset(seed=seed)  # type: ignore[attr-defined]
    sig: list[float] = [float(obs["caught"][0])]
    for a in actions:
        obs, reward, terminated, truncated, _ = env.step(a)  # type: ignore[attr-defined]
        sig.append(float(reward))
        sig.append(float(obs["caught"][0]))
        if terminated or truncated:
            break
    return sig
