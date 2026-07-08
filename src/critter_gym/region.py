"""Procedural region generation + train/test seed split (DESIGN.md §3.1).

A *region* is the per-episode world content — creature positions, gym positions
and their boss types, and the agent start. ``generate_region`` is a pure function
of the seed (its own RNG), so the same seed always yields the same region — the
basis for reproducibility and, crucially, for a **train/test seed split** that
lets us measure generalization to *unseen* worlds (the project's moat vs. fixed
ROMs like Pokémon Red).

Only the *content* varies with the seed; obs-space-affecting dimensions
(``grid_size``) stay fixed and the env's obs bounds use the max counts, so every
seed's observation stays within a single fixed observation space (Procgen
convention).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from critter_gym.types import (
    NEUTRAL,
    SUPER_EFFECTIVE,
    ElementType,
    TypeChart,
    generate_typechart,
)

# Boss type sequence used in fixed (non-vary) mode — matches M1 behavior.
FIXED_BOSS_TYPES: list[ElementType] = [ElementType.GRASS, ElementType.GRASS, ElementType.WATER]

# The player's fixed starter team covers exactly these types (see party.starter_party).
# A procgen boss type is only placed if at least one starter type is *strictly*
# super-effective against it under the seed's chart — so every gym has an exploitable
# (inferred) answer, while which type wins stays hidden (inference still required).
_STARTER_TYPES: tuple[ElementType, ...] = (ElementType.FIRE, ElementType.WATER, ElementType.GRASS)

# Test seeds live at/above this offset; train seeds must stay strictly below it,
# so the two splits are structurally disjoint (no leakage).
TEST_SEED_OFFSET = 1_000_000

_MIN_CREATURES = 1
_MIN_GYMS = 1  # >= 1 keeps the env's termination contract valid (never 0 gyms)


@dataclass
class Region:
    """Per-episode world content produced by ``generate_region``."""

    grid_size: int
    creatures: list[tuple[int, int]]
    gyms: list[tuple[tuple[int, int], ElementType]]  # (position, boss PRIMARY type)
    agent_start: tuple[int, int]
    chart: TypeChart  # per-seed type-effectiveness table (hidden from obs)
    # Optional per-gym HIDDEN secondary boss type, parallel to ``gyms`` (deeper hidden-rule
    # inference — the agent sees only the primary; effectiveness is the product over both types).
    # Empty tuple = every boss is single-type (byte-identical to the historical world).
    boss_secondary_types: tuple[ElementType | None, ...] = ()


def generate_region(
    seed: int,
    grid_size: int = 10,
    max_creatures: int = 5,
    max_gyms: int = 3,
    *,
    vary: bool = False,
    num_types: int = 3,
    super_mult: float = SUPER_EFFECTIVE,
    min_gyms: int | None = None,
    boss_secondary: bool = False,
    boss_pool_size: int | None = None,
) -> Region:
    """Deterministically build a region from ``seed``.

    ``vary=False`` reproduces the fixed M1 world (exactly ``max_creatures``
    creatures and ``max_gyms`` gyms, the fixed boss sequence, the fixed 3-cycle
    chart). ``vary=True`` samples counts in ``[1, max]``, draws boss types and the
    matchup chart from the first ``num_types`` elements of the type pool. A larger
    ``num_types`` makes the per-seed chart far harder to *memorize* than a 3-cycle.
    Making chart *inference* load-bearing needed the team-commit battle economy: a
    scripted 4-arm gate now proves infer > probe there, while whether a *learned*
    policy acquires the inference is follow-up work (see DESIGN §3.1.1).

    ``min_gyms`` (vary mode only) raises the floor of the per-seed gym count from the
    default 1 to widen the **dynamic range** of the score (more gyms → a larger
    oracle-vs-blind spread → finer capability discrimination; difficulty-dynamic-range
    task / DESIGN §3.1.1). ``None`` keeps the historical floor (``_MIN_GYMS=1``);
    ``min_gyms == max_gyms`` fixes the count exactly. Recurrence (the boss pool) is
    preserved, so cross-gym inference stays load-bearing.

    Fixed mode uses exactly 3 types (M1); ``num_types != 3`` with ``vary=False`` is
    rejected (the fixed chart only defines the 3-cycle).
    """
    if num_types < 3 or num_types > len(ElementType):
        raise ValueError(f"num_types must be in [3, {len(ElementType)}], got {num_types}")
    if not vary and num_types != 3:
        raise ValueError("fixed (vary=False) world uses exactly 3 types (M1)")
    gym_floor = _MIN_GYMS
    if min_gyms is not None:  # validated only when explicitly set (None = historical behavior)
        gym_floor = int(min_gyms)
        if gym_floor < _MIN_GYMS or gym_floor > max_gyms:
            raise ValueError(
                f"min_gyms must be in [{_MIN_GYMS}, max_gyms={max_gyms}], got {min_gyms}"
            )

    rng = np.random.default_rng(seed)
    active_types = list(ElementType)[:num_types]
    chart = generate_typechart(seed, active_types, vary=vary, super_mult=super_mult)

    if vary:
        n_creatures = int(rng.integers(_MIN_CREATURES, max_creatures + 1))
        n_gyms = int(rng.integers(gym_floor, max_gyms + 1))
        # Only place boss types that at least one starter (party move) type can
        # *strictly* super-effect, so every gym has an inference-exploitable answer —
        # which one stays hidden. A NEUTRAL filter would be a no-op: a boss type is
        # itself a starter type, and effectiveness(t, t) == NEUTRAL, so `>= NEUTRAL`
        # never excludes anything. The eval only measures hidden-chart *inference* if
        # an exploitable super-effective move exists; otherwise even the oracle grinds
        # neutrally (attrition) and the discrimination signal collapses (matchup-validity).
        # Invariant relied on here: _STARTER_TYPES == the party's move types (party.py).
        exploitable = [
            t
            for t in active_types
            if any(chart.effectiveness(s, t) > NEUTRAL for s in _STARTER_TYPES)
        ]
        # Non-empty for every legal config: a tournament on n>=3 types has in-degree
        # sum C(n,2) >= n, so >= 1 type is beaten by another; the starter types span
        # all active types when num_types==3, and always include the F/W/G core that
        # beat each other, so at least the beaten core types qualify. Guard anyway —
        # an empty set would silently distort the world distribution.
        if not exploitable:
            raise ValueError(
                f"no inference-exploitable boss type for seed={seed}, num_types={num_types}: "
                "the party has no super-effective move against any candidate boss"
            )
        # Draw the episode's bosses from a small per-seed *pool* so types RECUR across
        # gyms — this gives cross-gym inference *room* (a matchup inferred once could be
        # reused on later gyms of that type). It does NOT, on its own, make inference
        # load-bearing — a pilot showed switch-cost can dominate (DESIGN §3.1.1, future
        # work). Pool ≈ half the gym count → ~2 gyms per type.
        # The recurrence pool caps per-episode boss-type *diversity*. Default (None) keeps the
        # historical formula (byte-identical); an explicit ``boss_pool_size`` overrides it to
        # sweep diversity at a fixed gym budget (diversity-dial: fewer types => more revisits =>
        # easier for a first-sight inferrer; more types => harder). Clamped to the exploitable set.
        if boss_pool_size is None:
            pool_size = min(len(exploitable), max(2, n_gyms // 2))
        else:
            pool_size = min(len(exploitable), max(1, int(boss_pool_size)))
        pool_idx = rng.choice(len(exploitable), size=pool_size, replace=False)
        pool = [exploitable[int(i)] for i in pool_idx]
        boss_types = [pool[int(rng.integers(0, pool_size))] for _ in range(n_gyms)]
    else:
        n_creatures, n_gyms = max_creatures, max_gyms
        boss_types = [FIXED_BOSS_TYPES[i % len(FIXED_BOSS_TYPES)] for i in range(n_gyms)]

    cells = grid_size * grid_size
    need = n_creatures + n_gyms + 1  # +1 for the agent start
    chosen = rng.choice(cells, size=need, replace=False)
    coords = [(int(c // grid_size), int(c % grid_size)) for c in chosen]

    creatures = coords[:n_creatures]
    gym_coords = coords[n_creatures : n_creatures + n_gyms]
    gyms = list(zip(gym_coords, boss_types))
    agent_start = coords[-1]

    # Optional HIDDEN secondary boss type per gym (deeper inference). Drawn AFTER the primary
    # placement so enabling it never perturbs the historical draw sequence (off => byte-identical).
    # Each secondary is a different active type than the primary; the effectiveness the agent
    # faces is the product over both types (numpy Battle handles this via multi_effectiveness).
    boss_secondary_types: tuple[ElementType | None, ...] = ()
    if boss_secondary:
        secondaries: list[ElementType | None] = []
        for primary in boss_types:
            others = [t for t in active_types if t != primary]
            secondaries.append(others[int(rng.integers(0, len(others)))] if others else None)
        boss_secondary_types = tuple(secondaries)

    return Region(grid_size, creatures, gyms, agent_start, chart, boss_secondary_types)


# -- train/test split ---------------------------------------------------------

def train_seeds(n: int, start: int = 0) -> range:
    """A contiguous block of ``n`` training seeds starting at ``start``.

    Raises if the block would overrun into the held-out range, which would leak
    test worlds into training.
    """
    if start < 0 or start + n > TEST_SEED_OFFSET:
        raise ValueError(
            f"train seeds [{start}, {start + n}) overrun TEST_SEED_OFFSET={TEST_SEED_OFFSET}"
        )
    return range(start, start + n)


def heldout_seeds(n: int) -> range:
    """A contiguous block of ``n`` held-out (test) seeds, disjoint from train.

    (Named ``heldout_seeds`` rather than ``test_seeds`` so pytest does not try to
    collect it as a test.)
    """
    return range(TEST_SEED_OFFSET, TEST_SEED_OFFSET + n)


def is_held_out(seed: int) -> bool:
    """Whether ``seed`` belongs to the held-out (test) range."""
    return seed >= TEST_SEED_OFFSET
