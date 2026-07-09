"""Reference baseline policies for CritterGym (DESIGN.md §5).

These ship with the package so researchers have a common floor/ceiling to compare
learned agents against:

- ``random_policy`` — uniform random actions (the floor).
- ``greedy_policy`` — a scripted heuristic: chase the nearest visible creature and
  catch it; when none is visible, sweep the grid deterministically (boustrophedon).

Both are pure functions over the observation (numpy only — no learning deps), so
they double as a regression guard: a valid benchmark keeps ``greedy`` measurably
above ``random`` (see ``tests/test_baselines.py``).
"""

from __future__ import annotations

import numpy as np

from critter_gym.envs.critter_env import CATCH, MOVE_E, MOVE_N, MOVE_S, MOVE_W

Obs = dict[str, np.ndarray]


def random_policy(obs: Obs, rng: np.random.Generator) -> int:
    """Uniform random action. ``rng`` makes it reproducible."""
    return int(rng.integers(0, 6))


def greedy_policy(obs: Obs, grid_size: int = 10) -> int:
    """Scripted heuristic.

    1. If a creature sits on the agent's own tile, CATCH.
    2. Else if any creature is visible in the local patch, step toward the nearest.
    3. Else sweep the grid deterministically (boustrophedon) to explore.

    Stateless: exploration is derived from ``agent_pos`` alone, so the same
    observation always yields the same action (needed for determinism tests).
    """
    patch = obs["local_patch"]
    side = patch.shape[0]
    center = side // 2

    if patch[center, center] == 1:
        return CATCH

    visible = np.argwhere(patch == 1)
    if visible.size > 0:
        # Nearest visible creature, relative to the agent at the patch center.
        rel = visible - center
        nearest = rel[np.argmin(np.abs(rel).sum(axis=1))]
        dr, dc = int(nearest[0]), int(nearest[1])
        if abs(dr) >= abs(dc):
            return MOVE_S if dr > 0 else MOVE_N
        return MOVE_E if dc > 0 else MOVE_W

    # Nothing visible: boustrophedon sweep (even rows east, odd rows west, then down).
    r, c = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    if r % 2 == 0:
        return MOVE_E if c < grid_size - 1 else MOVE_S
    return MOVE_W if c > 0 else MOVE_S


def demo_policy(obs: Obs, grid_size: int = 10) -> int:
    """Demo-only scripted policy for the site's gameplay GIF — NOT a ranked baseline.

    ``greedy_policy`` (the ranked "scripted" baseline above — byte-identical, untouched)
    only chases creatures (patch == 1), so its GIF kept lawnmower-sweeping even with a
    gym on screen. This variant is *purposeful* for the demo: it also walks the shortest
    path toward a visible LIVE gym (patch == 2; defeated gyms are hidden from the patch
    by the env, so it cannot get stuck on a cleared one). Priorities:

    1. In battle: press the attack (action 0 — moves are clamped to battle moves).
    2. A creature on the agent's own tile: CATCH (one free step on the way).
    3. Nearest visible live gym: step toward it (same Manhattan step as the chase).
    4. Nearest visible creature: step toward it.
    5. Nothing visible: the same deterministic boustrophedon sweep as ``greedy_policy``.

    Stateless and deterministic. Ranked-baseline scores come from ``greedy_policy`` /
    ``random_policy`` only; changing this function never moves a published number.
    """
    if "in_battle" in obs and int(obs["in_battle"][0]):
        return 0
    patch = obs["local_patch"]
    side = patch.shape[0]
    center = side // 2

    if patch[center, center] == 1:
        return CATCH

    for target in (2, 1):  # live gym first, then creature — purposeful over opportunistic
        visible = np.argwhere(patch == target)
        if visible.size > 0:
            rel = visible - center
            nearest = rel[np.argmin(np.abs(rel).sum(axis=1))]
            dr, dc = int(nearest[0]), int(nearest[1])
            if abs(dr) >= abs(dc):
                return MOVE_S if dr > 0 else MOVE_N
            return MOVE_E if dc > 0 else MOVE_W

    r, c = int(obs["agent_pos"][0]), int(obs["agent_pos"][1])
    if r % 2 == 0:
        return MOVE_E if c < grid_size - 1 else MOVE_S
    return MOVE_W if c > 0 else MOVE_S
