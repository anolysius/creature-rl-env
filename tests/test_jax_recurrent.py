"""hard-benchmark/recurrent-baseline: a GRU A2C for partial-observability memory.

Smoke-tests the recurrent API under `importorskip` (CI stays numpy-only): GRU forward
shapes, a train-loop runs and produces a finite curve, and the recurrent eval shares the
feedforward eval's protocol (matched). The full memory-load-bearing measurement is
run-derived (`scripts/recurrent_baseline.py`), not a CI assertion. The feedforward path is
untouched — guarded by the existing `test_jax_train`/`test_jax_ppo`.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax.numpy as jnp  # noqa: E402
from jax import random  # noqa: E402

from critter_gym.jax_train import (  # noqa: E402
    OBS_DIM,
    TrainConfig,
    default_env_spec,
    evaluate_gym_clears_recurrent,
    gru_hidden_size,
    gru_init_params,
    gru_step,
    recurrent_a2c_loss,
    recurrent_policy_value,
    train_recurrent,
)


def test_gru_shapes_and_hidden_size() -> None:
    p = gru_init_params(random.PRNGKey(0), OBS_DIM, 32)
    assert gru_hidden_size(p) == 32
    h = gru_step(p, jnp.zeros((4, OBS_DIM)), jnp.zeros((4, 32)))
    assert h.shape == (4, 32)
    logits, value = recurrent_policy_value(p, h)
    assert logits.shape == (4, 6) and value.shape == (4,)


def test_recurrent_a2c_loss_is_finite_scalar() -> None:
    p = gru_init_params(random.PRNGKey(1), OBS_DIM, 16)
    T, B = 5, 3
    flat = jnp.zeros((T, B, OBS_DIM))
    actions = jnp.zeros((T, B), dtype=jnp.int32)
    rewards = jnp.ones((T, B))
    dones = jnp.zeros((T, B))
    h0 = jnp.zeros((B, 16))
    loss = recurrent_a2c_loss(p, flat, actions, rewards, dones, h0, 0.99, 0.01, 0.5)
    assert loss.shape == () and np.isfinite(float(loss))


def test_train_recurrent_smoke() -> None:
    """A tiny GRU A2C run trains on-device and yields a finite curve of the right length."""
    cfg = TrainConfig(batch=32, hidden=32, iters=40, rollout_len=16)
    res = train_recurrent(tuple(range(32)), cfg, seed=0)
    assert len(res.curve) == cfg.iters
    assert res.env_steps_per_s > 0
    assert all(np.isfinite(c) for c in res.curve)


def test_evaluate_gym_clears_recurrent_in_range() -> None:
    cfg = TrainConfig(batch=32, hidden=32, iters=10, rollout_len=16)
    res = train_recurrent(tuple(range(32)), cfg, seed=0)
    spec = default_env_spec()
    gc = evaluate_gym_clears_recurrent(res.params, tuple(range(32, 44)), steps=200, spec=spec)
    assert 0.0 <= gc <= 3.0  # default config has up to 3 gyms
