"""Named, difficulty-graded env tiers — the M5-EC2 custom/hard env sales surface (prototype).

The difficulty-scaling and hard-benchmark initiatives *measured* which knobs make CritterEnv
harder (grid size, horizon, view radius, boss stats). That knowledge lived only in initiative
docs; the knobs themselves are scattered across ``CritterEnv.__init__``. This module packages
them into a **curated, validated, reproducible tier API** a buyer can instantiate by name:

- :class:`TierSpec` — a serializable spec of a tier's knobs + a difficulty descriptor.
- :func:`validate_tier_spec` — the guard: reject insane or obviously-unwinnable knob combos.
- :func:`register_tier` / :func:`tier_names` / :func:`get_tier` — a small registry (same
  idempotent-register convention as :mod:`critter_gym.env_family`), pre-loaded with two curated
  presets: ``standard`` (the free-baseline difficulty) and ``hard`` (the measured hard config).
- :func:`make_tier_env` / :func:`tier_env_factory` — build a ``CritterEnv`` for a tier.
- :func:`sealed_config` / :func:`build_sealed` — tie a tier into a
  :class:`~critter_gym.eval_harness.SealedEvalSet` (parallels the #4 packaging surface).

**Honest scope (prototype).** The ``hard`` tier's difficulty is what was *measured*: a
feedforward PPO baseline reaches only ~11–16% of the scripted oracle on the grid16 config while
the oracle stays winnable (~2.81 gyms). Whether it is hard for a **SOTA/recurrent** agent is
**open (unmeasured)** — the tier descriptor says so, and this module never claims difficulty it
did not measure. The validation guard is a *static sanity* check, not a proof of winnability.
Real sale / pricing / hosting is a human gate.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, NamedTuple

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.eval_harness import SealedEvalSet

# CritterEnv knobs a TierSpec parametrizes (the difficulty-relevant subset).
_KNOBS = (
    "grid_size", "num_gyms", "num_creatures", "max_steps", "patch_radius",
    "num_types", "boss_hp", "boss_atk", "boss_def", "commit_battles",
)
# Of those, the ones SealedEvalSet.__init__ accepts. SealedEvalSet now carries the difficulty
# levers patch_radius / num_gyms, so a tier's sealed variant is faithful to the full tier env.
# Only num_creatures is dropped (it is not a SealedEvalSet arg — it is an obs-bound max count).
_SEALED_KNOBS = (
    "grid_size", "num_types", "max_steps", "boss_hp", "boss_atk", "boss_def", "commit_battles",
    "patch_radius", "num_gyms",
)
_SEALED_DROPPED = ("num_creatures",)


class TierSpec(NamedTuple):
    """A curated difficulty tier: its CritterEnv knobs + an honest difficulty descriptor.

    ``harder_knobs`` names the knobs that raise difficulty relative to ``standard``;
    ``difficulty_note`` states what was *measured* and flags what is unmeasured (open)."""

    name: str
    grid_size: int
    num_gyms: int
    num_creatures: int
    max_steps: int
    patch_radius: int
    num_types: int
    boss_hp: int
    boss_atk: int
    boss_def: int
    commit_battles: bool
    harder_knobs: tuple[str, ...]
    difficulty_note: str

    def knobs(self) -> dict[str, Any]:
        """The CritterEnv-constructor knob subset (no name/descriptor fields)."""
        return {k: getattr(self, k) for k in _KNOBS}

    def to_json(self) -> str:
        return json.dumps(self._asdict(), sort_keys=True)

    @classmethod
    def from_json(cls, s: str) -> TierSpec:
        d = dict(json.loads(s))
        d["harder_knobs"] = tuple(d["harder_knobs"])  # JSON list -> tuple
        return cls(**d)


def validate_tier_spec(spec: TierSpec) -> None:
    """Raise ``ValueError`` if ``spec`` is structurally insane or obviously unwinnable.

    This is a *static sanity* guard, not a proof of winnability: it rejects the clearly-broken
    (non-positive knobs, a single-type chart, a horizon too short to reach any gym) so a buyer
    cannot register a tier that cannot possibly be played."""
    for k in ("grid_size", "num_gyms", "num_creatures", "max_steps", "boss_hp"):
        if getattr(spec, k) <= 0:
            raise ValueError(f"{spec.name}: {k} must be positive (got {getattr(spec, k)})")
    if spec.patch_radius < 0:
        raise ValueError(f"{spec.name}: patch_radius must be >= 0 (got {spec.patch_radius})")
    if spec.boss_atk < 0 or spec.boss_def < 0:
        raise ValueError(f"{spec.name}: boss_atk/boss_def must be >= 0")
    if spec.num_types < 2:
        raise ValueError(f"{spec.name}: num_types must be >= 2 (a hidden chart needs >=2 types)")
    if spec.num_gyms > spec.grid_size * spec.grid_size:
        raise ValueError(f"{spec.name}: num_gyms exceeds grid cells")
    # Winnability sanity: need enough steps to plausibly traverse the map to the gyms. A single
    # crossing is ~grid_size steps; require room for at least a couple of gym visits.
    if spec.max_steps < 2 * spec.grid_size:
        raise ValueError(
            f"{spec.name}: max_steps={spec.max_steps} too small to traverse a "
            f"{spec.grid_size}x{spec.grid_size} grid (need >= {2 * spec.grid_size})"
        )


# --- curated preset registry (env_family convention) ---------------------------------

_TIERS: dict[str, TierSpec] = {}


def register_tier(name: str, spec: TierSpec) -> None:
    """Register tier ``name`` → ``spec`` after validating it (idempotent on an identical spec)."""
    validate_tier_spec(spec)
    if name in _TIERS and _TIERS[name] != spec:
        raise ValueError(f"tier {name!r} already registered with a different spec")
    _TIERS[name] = spec


def tier_names() -> list[str]:
    return sorted(_TIERS)


def get_tier(name: str) -> TierSpec:
    if name not in _TIERS:
        raise KeyError(f"unknown tier {name!r}; registered: {tier_names()}")
    return _TIERS[name]


_STANDARD = TierSpec(
    name="standard", grid_size=10, num_gyms=3, num_creatures=5, max_steps=200,
    patch_radius=2, num_types=3, boss_hp=120, boss_atk=12, boss_def=12,
    commit_battles=False, harder_knobs=(),
    difficulty_note=(
        "The free-baseline difficulty (CritterEnv defaults). A scripted oracle clears it "
        "comfortably; a feedforward PPO reaches a large fraction of oracle."
    ),
)
_HARD = TierSpec(
    name="hard", grid_size=16, num_gyms=3, num_creatures=5, max_steps=300,
    patch_radius=2, num_types=3, boss_hp=120, boss_atk=12, boss_def=12,
    commit_battles=False, harder_knobs=("grid_size", "max_steps"),
    difficulty_note=(
        "Measured hard config (larger map + longer horizon at a small fixed view). A feedforward "
        "PPO reaches only ~11-16% of the scripted oracle here (vs ~41% at grid10), while the "
        "oracle stays winnable (~2.81 gyms). OPEN (unmeasured): difficulty for a SOTA/recurrent "
        "agent is not yet established -- do not claim it as SOTA-hard."
    ),
)
register_tier("standard", _STANDARD)
register_tier("hard", _HARD)


# --- env factory ---------------------------------------------------------------------

def _resolve_knobs(name: str, overrides: dict[str, Any]) -> dict[str, Any]:
    """Tier knobs merged with validated overrides (rejects unknown or invalid knobs)."""
    unknown = set(overrides) - set(_KNOBS)
    if unknown:
        raise ValueError(f"unknown override knob(s): {sorted(unknown)}; allowed: {list(_KNOBS)}")
    spec = get_tier(name)
    merged = spec.knobs()
    merged.update(overrides)
    # Re-validate the merged result so an override can never bypass the guard.
    validate_tier_spec(spec._replace(**merged))
    return merged


def make_tier_env(name: str, *, seed: int | None = None, **overrides: Any) -> CritterEnv:
    """Build a ``CritterEnv`` for tier ``name`` (overrides merged + re-validated).

    ``vary=True`` so each seed yields a fresh procedural world (the benchmark's train/test
    split); if ``seed`` is given the env is reset to it before returning."""
    knobs = _resolve_knobs(name, overrides)
    env = CritterEnv(vary=True, **knobs)
    if seed is not None:
        env.reset(seed=seed)
    return env


def tier_env_factory(name: str, **overrides: Any) -> Callable[[], CritterEnv]:
    """A zero-arg factory building a fresh tier env (SealedEvalSet.env_factory convention)."""
    knobs = _resolve_knobs(name, overrides)
    return lambda: CritterEnv(vary=True, **knobs)


# --- sealed-eval tie-in --------------------------------------------------------------

def sealed_config(name: str) -> dict[str, Any]:
    """The tier's knobs restricted to what :class:`SealedEvalSet` accepts.

    ``SealedEvalSet`` carries the difficulty levers ``patch_radius``/``num_gyms``, so a tier's
    sealed variant is **faithful** to the full tier env. Only ``num_creatures`` is dropped
    (``_SEALED_DROPPED``) — it is not a ``SealedEvalSet`` arg (an obs-bound max count, not a
    world knob the eval parametrizes)."""
    spec = get_tier(name)
    return {k: getattr(spec, k) for k in _SEALED_KNOBS}


def build_sealed(name: str, master_seed: int, **overrides: Any) -> SealedEvalSet:
    """Build a :class:`SealedEvalSet` from tier ``name`` (supported knob subset + overrides).

    ``overrides`` may set tier knobs (re-validated through :func:`validate_tier_spec` — no guard
    bypass) or SealedEvalSet-specific args like ``n_worlds``. The sealed variant carries the
    difficulty levers ``patch_radius``/``num_gyms`` (faithful to the tier); only ``num_creatures``
    is dropped — see :func:`sealed_config`."""
    spec = get_tier(name)
    tier_over = {k: v for k, v in overrides.items() if k in _KNOBS}
    sealed_over = {k: v for k, v in overrides.items() if k not in _KNOBS}
    # Re-validate any tier-knob overrides through the guard so build_sealed cannot bypass it
    # (e.g. build_sealed(name, grid_size=-1) must raise, like make_tier_env does).
    if tier_over:
        validate_tier_spec(spec._replace(**tier_over))
    cfg = {k: tier_over.get(k, getattr(spec, k)) for k in _SEALED_KNOBS}
    cfg.update(sealed_over)
    return SealedEvalSet(master_seed=master_seed, **cfg)
