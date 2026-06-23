"""obs harmonization — all four families share ONE observation space (obs-harmonization).

DESIGN §3.1.1 (B) needs a single (family-agnostic) policy net to act on every env
family. Before this task, ``duel`` (family C) exposed two extra charge keys, so it
could not share a net with the 11-key families — #26 ``genre_learned_transfer`` had to
*exclude* duel. This task harmonizes the obs: a shared superset (``HARMONIZED_OBS_KEYS``)
where the charge keys are masked to 0 on non-duel families and carry real values on duel.

These tests are the enabler's guard — they prove the obs space is uniform and that the
0-padding is *behaviorally inert* for the existing scripted reference policies (so the
harmonization changes the contract, not the dynamics). The 4-family learned-transfer
*experiment* is the NEXT task; here we only assert it is now *constructible*.
"""

from __future__ import annotations

import numpy as np

from critter_gym.env_family import (
    HARMONIZED_OBS_KEYS,
    REQUIRED_OBS_KEYS,
    family_names,
    make_family,
)
from critter_gym.envs.duel_env import MAX_CHARGE
from critter_gym.genre_generalization import (
    duel_aware_policy,
    muster_policy,
    nav_toward_gyms,
    rush_policy,
    type_attacker_policy,
)

_FAMILIES = ["critter", "forage", "duel", "muster"]
_NONDUEL = ["critter", "forage", "muster"]
_CHARGE_KEYS = ("player_charge", "enemy_charge")


def test_harmonized_keys_extend_required_with_charge() -> None:  # AC1
    assert REQUIRED_OBS_KEYS.issubset(HARMONIZED_OBS_KEYS)
    assert set(HARMONIZED_OBS_KEYS) - set(REQUIRED_OBS_KEYS) == set(_CHARGE_KEYS)


def test_all_four_families_share_one_obs_space() -> None:  # AC1
    """Every registered family exposes the *identical* harmonized obs key set."""
    for fam in _FAMILIES:
        assert fam in family_names()
        keys = set(make_family(fam).observation_space.spaces)
        assert keys == set(HARMONIZED_OBS_KEYS), f"{fam} keys {sorted(keys)}"


def test_nonduel_families_mask_charge_to_zero() -> None:  # AC2
    for fam in _NONDUEL:
        env = make_family(fam)
        obs, _ = env.reset(seed=0)
        for key in _CHARGE_KEYS:
            assert key in obs
            assert int(obs[key][0]) == 0, f"{fam}.{key} should be 0-masked"


def test_duel_preserves_real_charge_values() -> None:  # AC2
    env = make_family("duel")
    obs, _ = env.reset(seed=0)
    # the charge keys are wired to the duel's internal charge state, not constant 0.
    env._pcharge = MAX_CHARGE  # type: ignore[attr-defined]
    env._echarge = 1  # type: ignore[attr-defined]
    obs2 = env._obs()  # type: ignore[attr-defined]
    assert int(obs2["player_charge"][0]) == MAX_CHARGE
    assert int(obs2["enemy_charge"][0]) == 1


def test_scripted_policies_ignore_padded_charge_keys() -> None:  # AC3
    """The 0-padded charge keys must not change any scripted policy's decisions.

    For each non-duel family we step an episode under a policy and, at every obs, check
    that stripping the charge keys yields the identical action — i.e. the padding is
    behaviorally inert (it harmonizes the contract, not the dynamics).
    """
    policies = [
        nav_toward_gyms, type_attacker_policy, duel_aware_policy,
        rush_policy, muster_policy,
    ]
    for fam in _NONDUEL:
        for policy in policies:
            env = make_family(fam)
            obs, _ = env.reset(seed=1)
            for _ in range(40):
                stripped = {k: v for k, v in obs.items() if k not in _CHARGE_KEYS}
                assert policy(obs) == policy(stripped), f"{fam}/{policy.__name__}"
                obs, _, term, trunc, _ = env.step(policy(obs))
                if term or trunc:
                    break


def test_scripted_charge_arrays_are_int64() -> None:  # AC2 dtype hygiene
    for fam in _NONDUEL:
        obs, _ = make_family(fam).reset(seed=0)
        for key in _CHARGE_KEYS:
            assert obs[key].dtype == np.int64
