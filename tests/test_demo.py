"""Tests for the killer-demo recording pipeline (M3-EC6).

The recording + boss-defeat detection run in the core CI: a type-aware scripted
policy beats a gym on **seed=3 (training region)**, which verifies the *pipeline*
and *detection* — NOT generalization (the held-out boss-defeat is the non-CI
[rl] demo in scripts/killer_demo.py). GIF encoding is exercised behind
importorskip("imageio").
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from critter_gym import demo as demomod
from critter_gym.baselines import random_policy
from critter_gym.demo import EpisodeRecording, record_episode, save_demo
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.types import ElementType, TypeChart

_TYPES = list(ElementType)
_CHART = TypeChart()


def _type_aware_scripted(env: CritterEnv):
    """Overworld: walk to nearest gym. Battle: attack if super-effective else switch.
    Reads env internals + the FIXED chart — the same policy used in test_gym_battle."""

    def policy(obs: dict) -> int:
        if obs["in_battle"][0]:
            active = _TYPES[int(obs["player_type"][0])]
            enemy = _TYPES[int(obs["enemy_type"][0])]
            return 0 if _CHART.effectiveness(active, enemy) > 1.0 else 4
        ar, ac = int(env._agent_pos[0]), int(env._agent_pos[1])
        undefeated = [p for p, i in env._gym_tiles.items() if not env._gym_defeated[i]]
        if not undefeated:
            return 5  # NOOP
        tr, tc = min(undefeated, key=lambda p: abs(p[0] - ar) + abs(p[1] - ac))
        if tr < ar:
            return 0
        if tr > ar:
            return 1
        if tc > ac:
            return 2
        if tc < ac:
            return 3
        return 5

    return policy


# -- AC3: boss-defeat detection (pipeline verification, NOT generalization) ----


def test_records_a_gym_defeat_on_seed3() -> None:
    env = CritterEnv(render_mode="rgb_array")  # vary=False → FIXED chart, seed=3 beats a gym
    rec = record_episode(env, _type_aware_scripted(env), seed=3, max_steps=150)
    assert isinstance(rec, EpisodeRecording)
    assert rec.gyms_defeated >= 1  # the scripted policy beats a gym boss (train region)
    assert rec.boss_defeated == (rec.gyms_defeated == env.num_gyms)


# -- AC1/AC2: frame contract + determinism ------------------------------------


def test_frame_count_and_shape() -> None:
    env = CritterEnv(grid_size=6, num_gyms=2, max_steps=20, render_mode="rgb_array")
    rng = np.random.default_rng(0)
    rec = record_episode(env, lambda o: random_policy(o, rng), seed=1, max_steps=20)
    assert len(rec.frames) == rec.steps + 1  # reset frame + one per step
    assert all(f.shape == (6 * 16, 6 * 16, 3) and f.dtype == np.uint8 for f in rec.frames)


def test_recording_is_deterministic_for_fixed_seed() -> None:
    def run() -> EpisodeRecording:
        env = CritterEnv(grid_size=6, num_gyms=2, max_steps=40, render_mode="rgb_array")
        return record_episode(env, _type_aware_scripted(env), seed=11, max_steps=40)

    a, b = run(), run()
    assert a.steps == b.steps and a.gyms_defeated == b.gyms_defeated
    assert len(a.frames) == len(b.frames)
    assert all(np.array_equal(x, y) for x, y in zip(a.frames, b.frames))


# -- AC1: guard ---------------------------------------------------------------


def test_requires_rgb_array_env() -> None:
    env = CritterEnv()  # render_mode=None
    with pytest.raises(ValueError, match="rgb_array"):
        record_episode(env, lambda o: 5, seed=0)


# -- AC4: import isolation ----------------------------------------------------


def test_demo_is_numpy_only() -> None:
    src = inspect.getsource(demomod)
    assert "import torch" not in src
    assert "stable_baselines3" not in src
    assert "import imageio" not in src  # imageio is lazy inside render.save_gif


# -- AC5: [render] smoke — real GIF encoding ----------------------------------


def test_save_demo_writes_nonempty_gif(tmp_path) -> None:
    pytest.importorskip("imageio")
    env = CritterEnv(grid_size=6, num_gyms=2, max_steps=12, render_mode="rgb_array")
    rng = np.random.default_rng(0)
    rec = record_episode(env, lambda o: random_policy(o, rng), seed=2, max_steps=12)
    out = str(tmp_path / "demo.gif")
    path = save_demo(rec, out, fps=4)
    import os

    assert path == out and os.path.getsize(out) > 0
