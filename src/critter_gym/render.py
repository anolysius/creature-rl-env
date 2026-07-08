"""World rendering — turn env state into RGB frames (M3-EC6 foundation).

The killer demo (M3-EC6) shows the same agent beating a boss on an *unseen*
held-out seed. This module is the render half of that: a faithful, **numpy-only**
visualization of the world state as colored cells — grid, agent, creatures, gyms,
and a battle tint. Not game art (no sprites / animation / sound; CLAUDE.md keeps
art lowest-priority) — just the state a researcher needs to *see* the agent act.

``draw_frame`` is pure numpy and lives in the core; GIF assembly (``save_gif``)
needs an encoder, so imageio is imported lazily inside it and ships behind the
optional ``[render]`` extra (mirroring ``[rl]``/``[viz]``).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

import numpy as np

# RGB palette (state visualization, not art direction).
_BG = (30, 30, 40)  # background
_GRID = (60, 60, 75)  # cell grid lines
_CREATURE = (90, 200, 120)  # catchable creature
_GYM_ACTIVE = (220, 80, 80)  # undefeated gym (a gated checkpoint)
_GYM_DEFEATED = (110, 110, 110)  # cleared gym
_AGENT = (80, 140, 230)  # the agent (drawn on top)
_BATTLE = (210, 40, 40)  # border tint while a battle is live


def _fill(frame: np.ndarray, row: int, col: int, cell: int, color: tuple[int, int, int]) -> None:
    frame[row * cell : (row + 1) * cell, col * cell : (col + 1) * cell] = color


def draw_frame(
    grid_size: int,
    agent_pos: Sequence[int],
    creatures: Iterable[tuple[int, int]],
    gym_tiles: Mapping[tuple[int, int], int],
    gym_defeated: Sequence[bool],
    in_battle: bool = False,
    cell: int = 16,
) -> np.ndarray:
    """Render the world state to an ``(grid_size*cell, grid_size*cell, 3)`` uint8 frame.

    Pure function of the arguments — the same state always yields a byte-identical
    array. Drawing order (background → creatures → gyms → agent) makes the result
    independent of ``creatures`` iteration order: occupied tiles are distinct and
    the agent is drawn last, so overlaps never depend on set ordering.
    """
    side = grid_size * cell
    frame = np.empty((side, side, 3), dtype=np.uint8)
    frame[:] = _BG
    frame[:: cell, :] = _GRID  # horizontal grid lines
    frame[:, :: cell] = _GRID  # vertical grid lines

    for r, c in creatures:
        _fill(frame, r, c, cell, _CREATURE)
    for (r, c), idx in gym_tiles.items():
        cleared = 0 <= idx < len(gym_defeated) and gym_defeated[idx]
        _fill(frame, r, c, cell, _GYM_DEFEATED if cleared else _GYM_ACTIVE)
    _fill(frame, int(agent_pos[0]), int(agent_pos[1]), cell, _AGENT)

    if in_battle:
        b = max(1, cell // 4)
        frame[:b, :] = _BATTLE
        frame[-b:, :] = _BATTLE
        frame[:, :b] = _BATTLE
        frame[:, -b:] = _BATTLE
    return frame


def save_gif(frames: Sequence[np.ndarray], path: str, fps: int = 5, *, loop: int = 0) -> str:
    """Encode a frame sequence to an animated GIF at ``path``; return ``path``.

    ``loop=0`` (default) makes the GIF loop forever (the gameplay clip should never
    stop); a positive count plays that many times. imageio is imported lazily so this
    module stays importable (and the core stays numpy-only) without the ``[render]``
    extra; calling this without it raises ``ImportError``.
    """
    import imageio.v2 as imageio

    imageio.mimsave(path, list(frames), format="GIF", duration=1.0 / fps, loop=loop)
    return path
