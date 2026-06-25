"""hard-benchmark/recurrent-ppo: a GRU PPO with sequence-preserving minibatching.

PPO normally flattens ``(T, B)`` and shuffles **across time**, which breaks recurrence
(the hidden state is sequential). The recurrent PPO here minibatches over the **env axis
(B) only**, keeping each env's time sequence (T) intact, and replays the GRU hidden from a
stored ``h0`` per minibatch. These tests are the **correctness gate** (AC1) — a broken
recurrent PPO would yield a *misleading* "memory doesn't help" result, so we prove the
hidden replay is faithful and the env-axis minibatch does not corrupt the sequence
*before* trusting any comparison number. The full ff-vs-rec PPO measurement is run-derived
(`scripts/recurrent_ppo_baseline.py`), not a CI assertion. The feedforward / A2C / tuned-PPO
/ recurrent-A2C paths are untouched (guarded by their existing tests). CI stays numpy-only.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
from jax import random  # noqa: E402

from critter_gym.jax_train import (  # noqa: E402
    OBS_DIM,
    PPOConfig,
    _obs_dim,
    build_region_bank,
    default_env_spec,
    gru_init_params,
    learning_verdict,
    make_recurrent_ppo_rollout,
    recurrent_ppo_loss,
    recurrent_replay,
    train_recurrent_ppo,
)


def test_recurrent_ppo_loss_is_finite_scalar() -> None:
    p = gru_init_params(random.PRNGKey(0), OBS_DIM, 8)
    t, b, h = 5, 4, 8
    flat = jnp.zeros((t, b, OBS_DIM))
    actions = jnp.zeros((t, b), dtype=jnp.int32)
    logp_old = jnp.zeros((t, b))
    adv = jnp.ones((t, b))
    returns = jnp.ones((t, b))
    dones = jnp.zeros((t, b))
    h0 = jnp.zeros((b, h))
    loss = recurrent_ppo_loss(p, flat, actions, logp_old, adv, returns, dones, h0,
                              0.2, 0.01, 0.5)
    assert loss.shape == () and np.isfinite(float(loss))


def test_recurrent_replay_env_axis_permutation_invariant() -> None:
    """AC1(b): minibatching over the ENV axis (any subset/order) must not change per-env
    outputs — replay(perm-ed inputs) == replay(...)[:, perm]. This proves the time axis is
    NOT shuffled (each env's sequence stays intact), so shuffling B for minibatches is safe.
    """
    t, b, h = 7, 5, 8
    p = gru_init_params(random.PRNGKey(2), OBS_DIM, h)
    flat = random.normal(random.PRNGKey(3), (t, b, OBS_DIM))
    dones = (random.uniform(random.PRNGKey(4), (t, b)) < 0.25).astype(jnp.float32)
    h0 = random.normal(random.PRNGKey(5), (b, h))

    logits, values = recurrent_replay(p, flat, dones, h0)
    perm = jnp.array([3, 1, 4, 0, 2])
    lp, vp = recurrent_replay(p, flat[:, perm], dones[:, perm], h0[perm])

    assert jnp.allclose(lp, logits[:, perm], atol=1e-4)
    assert jnp.allclose(vp, values[:, perm], atol=1e-4)


def test_recurrent_ppo_rollout_replay_matches() -> None:
    """AC1(a): the loss's hidden replay reproduces the rollout's policy outputs.

    Replaying the GRU from the rollout's ``h0`` with the **same** params must give back the
    stored ``logp_old`` and ``values`` (tol 1e-4). If it didn't, the clipped surrogate's
    ``ratio = exp(logp_new − logp_old)`` would start ≠ 1 even before any update — a silent
    recurrence break. Also checks the rollout returns the un-mutated ``h0`` and a bootstrap.
    """
    spec = default_env_spec()
    seeds = tuple(range(8))
    bank = build_region_bank(seeds, spec)
    obs_dim = _obs_dim(spec, 0)
    p = gru_init_params(random.PRNGKey(0), obs_dim, 16)
    rollout = jax.jit(make_recurrent_ppo_rollout(bank, spec.env))

    h0 = jnp.zeros((len(seeds), 16))
    keys = random.split(random.PRNGKey(1), 6)
    _state, _h, traj, last_value, h0_out = rollout(p, bank, h0, keys)
    flat, actions, logp_old, values, _rewards, dones = traj

    logits, vals = recurrent_replay(p, flat, dones, h0_out)
    logp_all = jax.nn.log_softmax(logits)
    logp = jnp.take_along_axis(logp_all, actions[..., None], axis=-1)[..., 0]

    assert jnp.allclose(h0_out, h0)  # rollout exposes the start hidden unchanged
    assert jnp.allclose(logp, logp_old, atol=1e-4)
    assert jnp.allclose(vals, values, atol=1e-4)
    assert last_value.shape == (len(seeds),)
    assert np.all(np.isfinite(np.asarray(last_value)))


def test_train_recurrent_ppo_smoke() -> None:
    """A tiny GRU PPO run trains on-device, produces a finite curve, and `learning_verdict`
    (the pre-registered R1 rule) is computable on it (AC2 is run-derived, not asserted)."""
    cfg = PPOConfig(batch=32, hidden=32, iters=30, rollout_len=16, num_minibatches=4)
    res = train_recurrent_ppo(tuple(range(32)), cfg, seed=0)
    assert len(res.curve) == cfg.iters
    assert res.env_steps_per_s > 0
    assert all(np.isfinite(c) for c in res.curve)
    branch, _rise, _std = learning_verdict(res.curve)
    assert branch in ("a", "b")
