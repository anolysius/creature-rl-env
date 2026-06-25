"""AC1/AC2/AC4: tuned PPO (GAE + clipped surrogate + minibatch epochs) on the JAX env.

`gae` is a pure function with exact identities at the (gamma, lambda) extremes — tested
deterministically. `train_ppo` and `evaluate_gym_clears` are smoke-tested under
`importorskip` (a tiny budget that still shows the curve rise by the pre-registered R1
rule). Skipped when JAX is absent → the CI suite stays numpy-only.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("jax")

import jax.numpy as jnp  # noqa: E402

from critter_gym.jax_train import (  # noqa: E402
    PPOConfig,
    default_env_spec,
    evaluate_gym_clears,
    gae,
    learning_verdict,
    train_ppo,
)


def _np_gae(rewards, values, dones, last_value, gamma, lam):
    """Reference GAE in plain numpy (the spec the jax `gae` must match)."""
    T, B = rewards.shape
    adv = np.zeros((T, B))
    acc = np.zeros((B,))
    next_v = last_value.astype(float).copy()
    for t in range(T - 1, -1, -1):
        nonterm = 1.0 - dones[t]
        delta = rewards[t] + gamma * next_v * nonterm - values[t]
        acc = delta + gamma * lam * nonterm * acc
        adv[t] = acc
        next_v = values[t]
    return adv, adv + values


def test_gae_matches_numpy_reference() -> None:
    rng = np.random.default_rng(0)
    T, B = 8, 4
    rewards = rng.normal(size=(T, B)).astype(np.float32)
    values = rng.normal(size=(T, B)).astype(np.float32)
    dones = (rng.random((T, B)) < 0.2).astype(np.float32)
    last_value = rng.normal(size=(B,)).astype(np.float32)
    for gamma, lam in [(0.99, 0.95), (1.0, 1.0), (0.9, 0.0)]:
        a_ref, r_ref = _np_gae(rewards, values, dones, last_value, gamma, lam)
        a_jx, r_jx = gae(
            jnp.asarray(rewards), jnp.asarray(values), jnp.asarray(dones),
            jnp.asarray(last_value), gamma, lam,
        )
        assert np.allclose(np.asarray(a_jx), a_ref, atol=1e-4), f"adv @ {(gamma, lam)}"
        assert np.allclose(np.asarray(r_jx), r_ref, atol=1e-4), f"ret @ {(gamma, lam)}"


def test_gae_lambda1_gamma1_is_monte_carlo() -> None:
    """γ=1, λ=1, no dones, bootstrap 0 → returns_t = sum of future rewards (MC)."""
    T, B = 5, 2
    rewards = np.arange(T * B, dtype=np.float32).reshape(T, B)
    values = np.zeros((T, B), np.float32)
    dones = np.zeros((T, B), np.float32)
    last_value = np.zeros((B,), np.float32)
    _, returns = gae(
        jnp.asarray(rewards), jnp.asarray(values), jnp.asarray(dones),
        jnp.asarray(last_value), 1.0, 1.0,
    )
    mc = np.cumsum(rewards[::-1], axis=0)[::-1]  # suffix sums
    assert np.allclose(np.asarray(returns), mc, atol=1e-4)


def test_gae_lambda0_is_one_step_td() -> None:
    """λ=0 → adv_t = r_t + γ·V(s_{t+1})·nonterm − V(s_t) (1-step TD residual)."""
    T, B = 4, 3
    rng = np.random.default_rng(1)
    rewards = rng.normal(size=(T, B)).astype(np.float32)
    values = rng.normal(size=(T, B)).astype(np.float32)
    dones = np.zeros((T, B), np.float32)
    last_value = rng.normal(size=(B,)).astype(np.float32)
    adv, _ = gae(
        jnp.asarray(rewards), jnp.asarray(values), jnp.asarray(dones),
        jnp.asarray(last_value), 0.9, 0.0,
    )
    next_v = np.vstack([values[1:], last_value[None]])
    td = rewards + 0.9 * next_v - values
    assert np.allclose(np.asarray(adv), td, atol=1e-4)


def test_train_ppo_learns_smoke() -> None:
    """A tiny PPO run trains on-device and the curve rises (pre-registered R1 rule)."""
    cfg = PPOConfig(batch=64, rollout_len=16, iters=40, hidden=32,
                    epochs=2, num_minibatches=2)
    res = train_ppo(tuple(range(64)), cfg, seed=0)
    assert len(res.curve) == cfg.iters
    assert res.env_steps_per_s > 0
    branch, rise, _ = learning_verdict(res.curve)
    assert branch == "a", f"PPO did not learn (rise={rise:.4f})"


def test_evaluate_gym_clears_in_range() -> None:
    cfg = PPOConfig(batch=64, rollout_len=16, iters=10, hidden=32,
                    epochs=1, num_minibatches=1)
    res = train_ppo(tuple(range(64)), cfg, seed=0)
    spec = default_env_spec()
    gc = evaluate_gym_clears(res.params, tuple(range(64, 80)), steps=200, spec=spec)
    assert 0.0 <= gc <= 3.0  # default config has up to 3 gyms
