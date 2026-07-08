"""Tests for the world renderer (M3-EC6 foundation).

The numpy-only frame drawing + env integration + import isolation run in the core
CI. GIF encoding is exercised behind ``importorskip("imageio")`` so it is verified
when the ``[render]`` extra is installed but never pulls imageio into the core.
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from critter_gym import render as rendermod
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.render import _AGENT, _GYM_ACTIVE, _GYM_DEFEATED, draw_frame

CELL = 16


def _frame(**kw) -> np.ndarray:
    base = dict(
        grid_size=4,
        agent_pos=(0, 0),
        creatures=[(1, 1)],
        gym_tiles={(2, 2): 0, (3, 3): 1},
        gym_defeated=[False, True],
    )
    base.update(kw)
    return draw_frame(**base)  # type: ignore[arg-type]


# -- AC1: frame contract + content --------------------------------------------


def test_frame_shape_and_dtype() -> None:
    frame = _frame()
    assert frame.shape == (4 * CELL, 4 * CELL, 3)
    assert frame.dtype == np.uint8


def test_agent_cell_is_agent_color() -> None:
    frame = _frame(agent_pos=(0, 0))
    # the agent occupies cell (0,0); its centre pixel is the agent color.
    assert tuple(frame[CELL // 2, CELL // 2]) == _AGENT


def test_active_and_defeated_gyms_differ() -> None:
    frame = _frame()
    active = tuple(frame[2 * CELL + CELL // 2, 2 * CELL + CELL // 2])  # gym idx 0 (active)
    cleared = tuple(frame[3 * CELL + CELL // 2, 3 * CELL + CELL // 2])  # gym idx 1 (defeated)
    assert active == _GYM_ACTIVE
    assert cleared == _GYM_DEFEATED
    assert active != cleared


def test_battle_tint_changes_frame() -> None:
    assert not np.array_equal(_frame(in_battle=False), _frame(in_battle=True))


# -- AC2: determinism ---------------------------------------------------------


def test_draw_frame_is_byte_identical() -> None:
    assert np.array_equal(_frame(), _frame())


def test_draw_frame_is_independent_of_input_order() -> None:
    # the docstring claims order-independence (agent drawn last over distinct tiles);
    # feeding the same tiles in a different order must yield a byte-identical frame.
    a = _frame(creatures=[(1, 1), (1, 2), (2, 1)], gym_tiles={(2, 2): 0, (3, 3): 1})
    b = _frame(creatures=[(2, 1), (1, 2), (1, 1)], gym_tiles={(3, 3): 1, (2, 2): 0})
    assert np.array_equal(a, b)


def test_env_render_is_byte_identical_for_fixed_seed() -> None:
    a = CritterEnv(render_mode="rgb_array")
    a.reset(seed=7)
    b = CritterEnv(render_mode="rgb_array")
    b.reset(seed=7)
    assert np.array_equal(a.render(), b.render())


# -- AC3: env integration -----------------------------------------------------


def test_render_mode_rgb_array_returns_frame() -> None:
    env = CritterEnv(grid_size=8, render_mode="rgb_array")
    env.reset(seed=0)
    frame = env.render()
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (8 * CELL, 8 * CELL, 3)


def test_render_mode_none_returns_none() -> None:
    env = CritterEnv()
    env.reset(seed=0)
    assert env.render() is None


def test_rgb_array_is_a_declared_render_mode() -> None:
    assert "rgb_array" in CritterEnv.metadata["render_modes"]


# -- AC5: import isolation ----------------------------------------------------


def test_render_has_no_toplevel_imageio_import() -> None:
    src = inspect.getsource(rendermod)
    header = src.split("def save_gif", 1)[0]
    assert "import imageio" not in header  # lazy: only inside save_gif


# -- AC6: [render] smoke — real GIF encoding ----------------------------------


def test_save_gif_writes_nonempty_file(tmp_path) -> None:
    pytest.importorskip("imageio")
    frames = [_frame(agent_pos=(0, 0)), _frame(agent_pos=(1, 0)), _frame(agent_pos=(2, 0))]
    out = str(tmp_path / "demo.gif")
    path = rendermod.save_gif(frames, out, fps=4)
    import os

    assert path == out
    assert os.path.getsize(out) > 0


# -- site-redesign: GIF loops forever by default -------------------------------


def test_save_gif_passes_infinite_loop(monkeypatch, tmp_path) -> None:
    """save_gif requests an infinite loop (GIF loop=0) so the gameplay clip never stops."""
    imageio = pytest.importorskip("imageio.v2")
    captured = {}

    def _fake_mimsave(path, frames, **kwargs):  # noqa: ANN001
        captured.update(kwargs)

    monkeypatch.setattr(imageio, "mimsave", _fake_mimsave)
    rendermod.save_gif([_frame(agent_pos=(0, 0))], str(tmp_path / "x.gif"), fps=4)
    assert captured.get("loop") == 0  # 0 = loop forever in the GIF spec


def test_saved_gif_has_infinite_loop_marker(tmp_path) -> None:
    """The encoded GIF carries the NETSCAPE loop extension with count 0 (infinite)."""
    pytest.importorskip("imageio")
    frames = [_frame(agent_pos=(i, 0)) for i in range(3)]
    out = str(tmp_path / "loop.gif")
    rendermod.save_gif(frames, out, fps=4)
    with open(out, "rb") as f:
        data = f.read()
    # NETSCAPE2.0 application extension present => a loop count is encoded.
    assert b"NETSCAPE2.0" in data
