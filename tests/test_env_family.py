"""AC1/AC2 — env-family abstraction + a structurally distinct family B.

Verifies the shared collection-RPG contract (CritterEnv conforms, unchanged), the
family registry, and that family B (ForageEnv) is *structurally distinct* — the same
seed + same actions yields a different trajectory than family A, so it is not a seed
variant (genre-generalization-foundation).
"""

from __future__ import annotations

import gymnasium as gym
import pytest

from critter_gym.env_family import (
    ACTION_N,
    REQUIRED_OBS_KEYS,
    conforms,
    family_names,
    make_family,
    register_family,
    trajectory_signature,
)
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.envs.forage_env import ForageEnv
from critter_gym.registration import register_envs

register_envs()


def test_critter_env_conforms_to_contract_unchanged() -> None:
    # AC1: CritterEnv (family A) satisfies the shared contract as-is.
    env = CritterEnv(vary=True, num_types=12)
    assert conforms(env)
    assert REQUIRED_OBS_KEYS.issubset(set(env.observation_space.spaces))
    assert int(env.action_space.n) == ACTION_N


def test_forage_env_conforms_and_is_registered() -> None:
    assert conforms(ForageEnv(vary=True, num_types=12))
    assert {"critter", "forage"}.issubset(set(family_names()))
    assert conforms(make_family("critter"))
    assert conforms(make_family("forage"))


def test_register_family_idempotent_but_rejects_conflict() -> None:
    fn = lambda **kw: CritterEnv(**kw)  # noqa: E731
    register_family("dup", fn)
    register_family("dup", fn)  # same factory object → idempotent, no error
    with pytest.raises(ValueError):  # different factory under a taken name → error
        register_family("critter", lambda **kw: ForageEnv(**kw))


def _path_onto_nearest_creature(seed: int) -> list[int]:
    # Families share world-gen (same seed → same creatures + agent start), so a path
    # computed on one applies to both. Walk Manhattan-style onto the nearest creature.
    probe = make_family("critter")
    probe.reset(seed=seed)
    ar, ac = int(probe._agent_pos[0]), int(probe._agent_pos[1])
    cr, cc = min(probe._creatures, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
    moves: list[int] = []
    while ar != cr:
        moves.append(1 if cr > ar else 0)       # MOVE_S / MOVE_N
        ar += 1 if cr > ar else -1
    while ac != cc:
        moves.append(2 if cc > ac else 3)       # MOVE_E / MOVE_W
        ac += 1 if cc > ac else -1
    return moves


def test_family_b_is_structurally_distinct_not_a_seed_variant() -> None:
    # AC2: same seed + same actions → different trajectory between family A and B.
    # Walk onto the nearest creature, then CATCH: family B collects on the move-onto
    # step (contact), family A only after the trailing CATCH — so the (reward, caught)
    # signatures diverge. Structural difference, not a seed variant.
    seed = 1000
    actions = _path_onto_nearest_creature(seed) + [4]  # ... + CATCH
    a_sig = trajectory_signature(make_family("critter"), seed=seed, actions=actions)
    b_sig = trajectory_signature(make_family("forage"), seed=seed, actions=actions)
    assert a_sig != b_sig, "family B must diverge from A on the same seed+actions"


def test_forage_collects_by_contact_not_by_catch_action() -> None:
    # Mechanic check: stepping ONTO a creature tile collects it (+1); the CATCH
    # action on a creature tile does NOT (collection is by contact in family B).
    import numpy as np

    env = ForageEnv(vary=True, num_types=12, num_gyms=2)
    env.reset(seed=1000)
    cr, cc = next(iter(env._creatures))          # a creature tile
    before = env._caught
    # CATCH (action 4) while standing on the tile: inert in family B.
    env._agent_pos = np.array([cr, cc], dtype=np.int64)
    env.step(4)                                  # CATCH — inert in B
    assert env._caught == before
    # Now step ONTO the tile from an adjacent cell → contact-collect.
    env._creatures.add((cr, cc))                 # ensure present
    if cc > 0:
        env._agent_pos = np.array([cr, cc - 1], dtype=np.int64)
        env.step(2)                              # MOVE_E onto the creature
    else:
        env._agent_pos = np.array([cr, cc + 1], dtype=np.int64)
        env.step(3)                              # MOVE_W onto the creature
    assert env._caught == before + 1


def test_forage_env_id_check_env_compliant() -> None:
    from gymnasium.utils.env_checker import check_env

    check_env(gym.make("CritterGym-forage-v0").unwrapped, skip_render_check=True)
