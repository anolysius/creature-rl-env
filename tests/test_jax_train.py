"""Smoke tests for the JAX-native A2C demo loop (M4 — jax-train).

CI stays numpy-only: jax is ``importorskip``ed, so these are skipped unless the
``[jax]`` extra is installed. They assert the loop *runs and updates* and the obs
flatten is deterministic — NOT learning quality (machine-dependent; that is the
demo script's job).
"""
from __future__ import annotations

import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402

from critter_gym import jax_train  # noqa: E402
from critter_gym.jax_env import encode_obs, jax_reset  # noqa: E402
from critter_gym.region import generate_region  # noqa: E402


def _single_obs():
    return encode_obs(jax_reset(generate_region(0, 10, 5, 3, vary=True, num_types=8)))


def test_flatten_obs_dim_and_deterministic():
    obs = _single_obs()
    v1 = jax_train.flatten_obs(obs)
    v2 = jax_train.flatten_obs(obs)
    assert v1.shape == (jax_train.OBS_DIM,)
    assert jnp.array_equal(v1, v2)  # same state → same vector
    assert jnp.all(jnp.isfinite(v1))


def test_train_runs_and_updates_params():
    cfg = jax_train.TrainConfig(batch=16, rollout_len=8, iters=4, hidden=16)
    key = jax.random.PRNGKey(0)
    before = jax_train.init_params(key, jax_train.OBS_DIM, cfg.hidden)
    result = jax_train.train(tuple(range(cfg.batch)), cfg, seed=0)

    # curve recorded per iteration, finite
    assert len(result.curve) == cfg.iters
    assert all(np.isfinite(x) for x in result.curve)
    assert result.total_env_steps == cfg.iters * cfg.rollout_len * cfg.batch
    assert result.env_steps_per_s > 0

    # params actually changed (some leaf differs from a fresh init of the same key)
    changed = any(
        not jnp.allclose(before[k], result.params[k]) for k in before
    )
    assert changed


def test_learning_verdict_rule():
    # rising curve with tiny late-window noise → branch "a"
    rising = tuple(float(x) for x in np.linspace(0.0, 1.0, 50))
    branch, rise, std_late = jax_train.learning_verdict(rising)
    assert branch == "a"
    assert rise > std_late >= 0.0
    # flat noisy curve → branch "b"
    rng = np.random.default_rng(0)
    flat = tuple(float(0.5 + 0.1 * x) for x in rng.standard_normal(50))
    branch_b, _, _ = jax_train.learning_verdict(flat)
    assert branch_b == "b"


def test_evaluate_returns_finite_scalar():
    cfg = jax_train.TrainConfig(batch=16, rollout_len=8, iters=2, hidden=16)
    result = jax_train.train(tuple(range(cfg.batch)), cfg, seed=0)
    # held-out seeds disjoint from training (0..15)
    ret = jax_train.evaluate(result.params, tuple(range(1000, 1008)), steps=20)
    assert np.isfinite(ret)
