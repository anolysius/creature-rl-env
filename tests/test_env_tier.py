"""Tests for the named difficulty-graded env tier API (monetization-surface #5).

These pin the *custom/hard env tier* sales surface (M5-EC2): curated `standard`/`hard` presets,
a validation guard that rejects insane or obviously-unwinnable knob combos, deterministic +
distinct tier envs, an honest difficulty descriptor, and a sealed-eval tie-in that carries the
difficulty levers `SealedEvalSet` accepts (incl. `patch_radius`/`num_gyms`) and drops only
`num_creatures` (an obs-bound max count, not a `SealedEvalSet` arg), documented honestly.
"""
from __future__ import annotations

import json

import numpy as np

from critter_gym.env_tier import (
    TierSpec,
    build_sealed,
    get_tier,
    make_tier_env,
    register_tier,
    sealed_config,
    tier_env_factory,
    tier_names,
    validate_tier_spec,
)
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.eval_harness import SealedEvalSet


def _valid_spec(name: str = "custom_ok", **over) -> TierSpec:
    base = dict(
        name=name, grid_size=10, num_gyms=3, num_creatures=5, max_steps=200,
        patch_radius=2, num_types=3, boss_hp=120, boss_atk=12, boss_def=12,
        commit_battles=False, harder_knobs=("grid_size",),
        difficulty_note="a custom tier for testing",
    )
    base.update(over)
    return TierSpec(**base)


# --- Step 1: validation guard --------------------------------------------------------

def test_valid_spec_passes():
    validate_tier_spec(_valid_spec())  # must not raise


def test_guard_rejects_nonpositive_knobs():
    for bad in ("grid_size", "boss_hp", "max_steps"):
        try:
            validate_tier_spec(_valid_spec(**{bad: 0}))
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad}=0")


def test_guard_rejects_too_few_types():
    # A hidden type chart needs at least 2 types to be inferable.
    try:
        validate_tier_spec(_valid_spec(num_types=1))
    except ValueError:
        return
    raise AssertionError("expected ValueError for num_types=1")


def test_guard_rejects_obviously_unwinnable():
    # max_steps=1 on a 16-grid cannot traverse to any gym -> unwinnable.
    try:
        validate_tier_spec(_valid_spec(grid_size=16, max_steps=1))
    except ValueError:
        return
    raise AssertionError("expected ValueError for unwinnable max_steps")


# --- Step 2: curated presets ---------------------------------------------------------

def test_builtin_presets_registered():
    names = tier_names()
    assert "standard" in names and "hard" in names


def test_presets_pass_guard():
    for name in ("standard", "hard"):
        validate_tier_spec(get_tier(name))  # must not raise


def test_register_idempotent_and_conflict():
    spec = _valid_spec("reg_test")
    register_tier("reg_test", spec)
    register_tier("reg_test", spec)  # idempotent
    try:
        register_tier("reg_test", _valid_spec("reg_test", grid_size=12))
    except ValueError:
        return
    raise AssertionError("expected ValueError re-registering a different spec")


def test_register_rejects_invalid_spec():
    try:
        register_tier("bad_tier", _valid_spec("bad_tier", num_types=1))
    except ValueError:
        return
    raise AssertionError("register_tier must apply the guard")


def test_get_unknown_tier_raises():
    try:
        get_tier("no_such_tier")
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown tier")


# --- Step 3: env factory + determinism ----------------------------------------------

def test_make_tier_env_builds_critter_env():
    env = make_tier_env("standard")
    assert isinstance(env, CritterEnv)


def test_tier_env_deterministic():
    o1, _ = make_tier_env("hard").reset(seed=7)
    o2, _ = make_tier_env("hard").reset(seed=7)
    assert all(np.array_equal(o1[k], o2[k]) for k in o1)


def test_hard_differs_from_standard():
    std, hard = get_tier("standard"), get_tier("hard")
    assert (std.grid_size, std.max_steps) != (hard.grid_size, hard.max_steps)
    # hard is at least as big/long as standard on its declared harder knobs.
    assert hard.grid_size >= std.grid_size


def test_overrides_applied_and_validated():
    env = make_tier_env("standard", grid_size=12)
    assert env.grid_size == 12
    try:
        make_tier_env("standard", grid_size=-1)
    except ValueError:
        return
    raise AssertionError("make_tier_env must validate overrides")


def test_tier_env_factory_returns_thunk():
    factory = tier_env_factory("standard")
    assert isinstance(factory(), CritterEnv)


# --- Step 4: descriptor + sealed tie-in + honest meta -------------------------------

def test_descriptor_round_trip():
    spec = get_tier("hard")
    restored = TierSpec.from_json(spec.to_json())
    assert restored == spec


def test_hard_difficulty_note_is_honest():
    note = get_tier("hard").difficulty_note.lower()
    # Cites the measured evidence and flags the unmeasured claim as open.
    assert "oracle" in note
    assert "open" in note or "미측" in note or "unmeasured" in note
    # Precision (hard-note-precision): the note must acknowledge the recurrent measurement at
    # the RELATED deeper config (hard-benchmark #3/#5) while keeping this exact config open —
    # neither over-claiming (measured here) nor under-claiming (nothing known).
    assert "recurrent" in note
    assert "related" in note


def test_sealed_config_carries_difficulty_levers():
    # SealedEvalSet now carries patch_radius/num_gyms — a tier's sealed variant is faithful.
    cfg = sealed_config("hard")
    hard = get_tier("hard")
    assert cfg["patch_radius"] == hard.patch_radius
    assert cfg["num_gyms"] == hard.num_gyms
    assert cfg["grid_size"] == hard.grid_size


def test_build_sealed_maps_supported_knobs():
    sealed = build_sealed("hard", master_seed=123)
    assert isinstance(sealed, SealedEvalSet)
    hard = get_tier("hard")
    assert sealed.grid_size == hard.grid_size
    assert sealed.boss_hp == hard.boss_hp
    # The difficulty levers now reach the sealed eval (faithful to the tier).
    assert sealed.patch_radius == hard.patch_radius
    assert sealed.num_gyms == hard.num_gyms


def test_build_sealed_reflects_custom_tuned_levers():
    # The gap this fix closes: a CUSTOM tier tuning patch_radius/num_gyms to non-default values
    # is now faithfully carried into its sealed eval (previously dropped).
    from critter_gym.env_tier import TierSpec, register_tier
    spec = TierSpec(
        name="custom_levers", grid_size=12, num_gyms=5, num_creatures=6, max_steps=260,
        patch_radius=1, num_types=4, boss_hp=140, boss_atk=13, boss_def=13,
        commit_battles=False, harder_knobs=("patch_radius", "num_gyms"),
        difficulty_note="custom tier tuning view radius + gym count",
    )
    register_tier("custom_levers", spec)
    sealed = build_sealed("custom_levers", master_seed=1)
    assert sealed.patch_radius == 1
    assert sealed.num_gyms == 5


def test_build_sealed_accepts_overrides():
    sealed = build_sealed("standard", master_seed=1, n_worlds=4)
    assert sealed.n_worlds == 4


def test_build_sealed_validates_tier_knob_overrides():
    # A tier-knob override must go through the guard — no bypass (L3 BLOCK fix).
    for bad in ({"grid_size": -1}, {"num_types": 1}):
        try:
            build_sealed("standard", master_seed=1, **bad)
        except ValueError:
            continue
        raise AssertionError(f"build_sealed must validate tier override {bad}")


def test_sealed_config_drops_num_creatures():
    # num_creatures is not a SealedEvalSet arg either — it must be dropped.
    assert "num_creatures" not in sealed_config("hard")


def test_descriptor_json_is_actual_json():
    parsed = json.loads(get_tier("hard").to_json())
    assert parsed["name"] == "hard"
    assert isinstance(parsed["harder_knobs"], list)
