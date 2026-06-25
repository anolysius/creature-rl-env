"""JAX-native RL training loop on the vectorized env — M4 (throughput) demo.

The prior M4 tasks proved the env *ports* to functional JAX and *vmap*-vectorizes
(``jax_overworld`` / ``jax_battle`` / ``jax_env``, parity 0 mismatch, 34–1047x on CPU).
This module turns that benchmark number into a *demonstration*: a minimal **JAX-native**
actor-critic (A2C) whose policy, rollout, advantage and update all run **on-device under
``jit`` + ``vmap``**, so thousands of full episodes train in lock-step. Wrapping the JAX
env in an off-the-shelf (sb3) loop would shuttle every step across the host↔device
boundary and lose exactly the vmap speed we want to show — hence a from-scratch loop.

**Scope:** family A, commit-mode (``jax_env``). Reset (procgen) stays numpy; a fixed
*region bank* of training seeds is bridged once into a batched state, and episodes
auto-reset to their own bank entry (a jittable index-free reset — re-selecting the
seed's initial state), so the whole rollout stays inside ``lax.scan``.

This is a **demo / signal**, not a tuned benchmark: single run, CPU, A2C-lite, the
learning metric is mean reward-per-env-step (a clean monotone proxy for episode return).
See ``scripts/jax_rl_demo.py`` for the runnable demo (learning curve + throughput vs the
existing numpy/sb3 path). Requires the ``[jax]`` extra; the core + default test suite
stay numpy-only (this module is not imported by ``critter_gym.__init__`` and the test
``importorskip``s jax).
"""

from __future__ import annotations

import time
from typing import Callable, NamedTuple

import jax
import jax.numpy as jnp
import numpy as np
from jax import Array, random

from critter_gym.jax_env import (
    DEFAULT_CONFIG,
    JaxEnv,
    JaxEnvConfig,
    JaxEnvState,
    make_jax_env,
)
from critter_gym.region import Region, generate_region

# obs flatten dimension for the DEFAULT config: agent_pos(2) + local_patch 5x5(25) + 11.
# Other configs (e.g. a larger patch_radius) have a different patch size, so `train`
# derives the obs dim from the actual env at run time (see `_obs_dim`).
OBS_DIM = 2 + 25 + 11  # 38 (default config)
N_ACTIONS = 6
_MAX_STEPS = 200  # default-config episode-return scale (eval window)

Params = dict[str, Array]


class EnvSpec(NamedTuple):
    """A config-bound JAX env + the per-seed numpy region factory feeding its reset.

    Bundles the two halves that must agree on shape (gym count, grid, etc.) so `train`/
    `evaluate` can run on any config — the default world or the high-gym dynamic-range
    difficulty config (`difficulty_env_spec`) — with one argument.
    """

    env: JaxEnv
    region_fn: Callable[[int], Region]


def default_env_spec(*, num_types: int = 8) -> EnvSpec:
    """The default family-A commit world (grid 10, 3 gyms) — the jax-rl-demo config."""
    return EnvSpec(
        make_jax_env(DEFAULT_CONFIG),
        lambda s: generate_region(s, 10, 5, 3, vary=True, num_types=num_types),
    )


def difficulty_env_spec(
    *, num_gyms: int = 8, num_types: int = 12, super_mult: float = 3.0,
    grid: int = 6, max_creatures: int = 5, max_steps: int = 160, patch_radius: int = 5,
    boss_hp: int = 150, boss_atk: int = 16,
) -> EnvSpec:
    """The high-gym *dynamic-range* difficulty config (difficulty-dynamic-range), now
    JAX-vmappable (jax-difficulty-report / R5). gym count is fixed (``min_gyms==num_gyms``)
    so the wider, finer score range trains under ``vmap`` like the default world."""
    cfg = JaxEnvConfig(
        grid=grid, patch_radius=patch_radius, max_steps=max_steps, max_gyms=num_gyms,
        boss_hp=boss_hp, boss_atk=boss_atk,
    )
    return EnvSpec(
        make_jax_env(cfg),
        lambda s: generate_region(s, grid, max_creatures, num_gyms, vary=True,
                                  num_types=num_types, super_mult=super_mult,
                                  min_gyms=num_gyms),
    )


class TrainConfig(NamedTuple):
    """Hyperparameters for the A2C demo (small by design — visible learning in seconds)."""

    batch: int = 256  # parallel envs == distinct training seeds in the region bank
    rollout_len: int = 32  # steps per lax.scan rollout (truncated A2C window)
    iters: int = 150
    hidden: int = 64
    gamma: float = 0.99
    lr: float = 3e-3
    ent_coef: float = 0.01
    vf_coef: float = 0.5


class TrainResult(NamedTuple):
    """Output of :func:`train` — params + the honest measurements the demo reports."""

    params: Params
    curve: tuple[float, ...]  # mean reward-per-env-step per iteration
    total_env_steps: int
    wall_time_s: float
    env_steps_per_s: float


def flatten_obs(obs: dict[str, Array]) -> Array:
    """The 13-key obs dict → a fixed (OBS_DIM,) float vector (deterministic, jittable)."""
    return jnp.concatenate([
        obs["agent_pos"].astype(jnp.float32),
        obs["local_patch"].reshape(-1).astype(jnp.float32),
        obs["caught"].astype(jnp.float32),
        obs["gyms_defeated"].astype(jnp.float32),
        obs["evolved"].astype(jnp.float32),
        obs["in_battle"].astype(jnp.float32),
        obs["player_hp"].astype(jnp.float32),
        obs["player_type"].astype(jnp.float32),
        obs["player_level"].astype(jnp.float32),
        obs["enemy_hp"].astype(jnp.float32),
        obs["enemy_type"].astype(jnp.float32),
        obs["player_charge"].astype(jnp.float32),
        obs["enemy_charge"].astype(jnp.float32),
    ])


def init_params(key: Array, obs_dim: int = OBS_DIM, hidden: int = 64) -> Params:
    """A tiny shared-trunk MLP: obs → tanh hidden → (policy logits, value)."""
    k1, k2, k3 = random.split(key, 3)
    scale = 0.1
    return {
        "w1": random.normal(k1, (obs_dim, hidden)) * scale,
        "b1": jnp.zeros((hidden,)),
        "wpi": random.normal(k2, (hidden, N_ACTIONS)) * scale,
        "bpi": jnp.zeros((N_ACTIONS,)),
        "wv": random.normal(k3, (hidden, 1)) * scale,
        "bv": jnp.zeros((1,)),
    }


def apply_policy(params: Params, x: Array) -> tuple[Array, Array]:
    """(..., OBS_DIM) → (logits (..., N_ACTIONS), value (...,))."""
    h = jnp.tanh(x @ params["w1"] + params["b1"])
    logits = h @ params["wpi"] + params["bpi"]
    value = (h @ params["wv"] + params["bv"])[..., 0]
    return logits, value


def build_region_bank(seeds: tuple[int, ...], spec: EnvSpec) -> JaxEnvState:
    """Bridge a fixed pool of seeds into one batched :class:`JaxEnvState` (the bank).

    Procgen runs in numpy once per seed here (not on the hot path); the result is
    stacked so the batched state has leading dim ``len(seeds)``. Returned as the
    auto-reset target *and* the rollout's initial state.
    """
    states = [spec.env.reset(spec.region_fn(s)) for s in seeds]
    return jax.tree_util.tree_map(lambda *xs: jnp.stack(xs), *states)


def _obs_dim(spec: EnvSpec, seed: int) -> int:
    """Flattened obs length for ``spec`` (depends on patch size → derived, not hardcoded)."""
    obs = spec.env.encode_obs(spec.env.reset(spec.region_fn(seed)))
    return int(flatten_obs(obs).shape[0])


def _reset_where(done: Array, fresh: Array, cur: Array) -> Array:
    """Per-env select: where an env is done, take its bank-initial leaf, else keep."""
    mask = done.reshape((done.shape[0],) + (1,) * (cur.ndim - 1))
    return jnp.where(mask, fresh, cur)


_Traj = tuple[Array, Array, Array, Array]
_Rollout = Callable[[Params, JaxEnvState, Array], tuple[JaxEnvState, _Traj]]


def make_rollout(init_state: JaxEnvState, env: JaxEnv) -> _Rollout:
    """Build a jittable ``(params, state, keys) -> (state, traj)`` A2C rollout for ``env``.

    ``traj`` = (flat_obs, actions, rewards, dones), each leading-dim ``rollout_len``.
    Auto-reset returns done envs to their own bank-initial state, so the rollout is a
    single ``lax.scan`` over a continuing batch of full episodes.
    """
    venc = jax.vmap(env.encode_obs)
    vflat = jax.vmap(flatten_obs)
    vstep = jax.vmap(env.step)

    def scan_step(
        carry: tuple[JaxEnvState, Params], key: Array
    ) -> tuple[tuple[JaxEnvState, Params], _Traj]:
        state, params = carry
        flat = vflat(venc(state))
        logits, _ = apply_policy(params, flat)
        actions = random.categorical(key, logits)
        nstate, _, reward, term, trunc = vstep(state, actions)
        done = term | trunc
        nstate = jax.tree_util.tree_map(
            lambda fresh, cur: _reset_where(done, fresh, cur), init_state, nstate
        )
        return (nstate, params), (flat, actions, reward, done)

    def rollout(
        params: Params, state: JaxEnvState, keys: Array
    ) -> tuple[JaxEnvState, _Traj]:
        (state, _), traj = jax.lax.scan(scan_step, (state, params), keys)
        return state, traj

    return rollout


def _returns(rewards: Array, dones: Array, gamma: float) -> Array:
    """Discounted returns within the rollout window (bootstrap 0 — truncated A2C)."""
    def step(carry: Array, x: tuple[Array, Array]) -> tuple[Array, Array]:
        r, d = x
        carry = r + gamma * (1.0 - d) * carry
        return carry, carry
    init = jnp.zeros((rewards.shape[1],))
    _, out = jax.lax.scan(step, init, (rewards, dones.astype(jnp.float32)), reverse=True)
    return out


def a2c_loss(
    params: Params, flat: Array, actions: Array, rewards: Array, dones: Array,
    gamma: float, ent_coef: float, vf_coef: float,
) -> Array:
    """A2C loss = policy-gradient + value MSE − entropy bonus (recomputes from traj)."""
    logits, values = apply_policy(params, flat)
    logp_all = jax.nn.log_softmax(logits)
    logp = jnp.take_along_axis(logp_all, actions[..., None], axis=-1)[..., 0]
    returns = _returns(rewards, dones, gamma)
    adv = returns - values
    pg = -(logp * jax.lax.stop_gradient(adv)).mean()
    vl = 0.5 * (adv ** 2).mean()
    entropy = -(jnp.exp(logp_all) * logp_all).sum(-1).mean()
    return pg + vf_coef * vl - ent_coef * entropy


class _AdamState(NamedTuple):
    m: Params
    v: Params
    t: Array


def _adam_init(params: Params) -> _AdamState:
    z = jax.tree_util.tree_map(jnp.zeros_like, params)
    return _AdamState(z, jax.tree_util.tree_map(jnp.zeros_like, params), jnp.int32(0))


def _adam_step(
    params: Params, grads: Params, opt: _AdamState, lr: float,
    b1: float = 0.9, b2: float = 0.999, eps: float = 1e-8,
) -> tuple[Params, _AdamState]:
    t = opt.t + 1
    m = jax.tree_util.tree_map(lambda m, g: b1 * m + (1 - b1) * g, opt.m, grads)
    v = jax.tree_util.tree_map(lambda v, g: b2 * v + (1 - b2) * g * g, opt.v, grads)
    bc1 = 1 - b1 ** t
    bc2 = 1 - b2 ** t
    params = jax.tree_util.tree_map(
        lambda p, m, v: p - lr * (m / bc1) / (jnp.sqrt(v / bc2) + eps), params, m, v
    )
    return params, _AdamState(m, v, t)


_DEFAULT_CONFIG = TrainConfig()


def train(
    seeds: tuple[int, ...], config: TrainConfig = _DEFAULT_CONFIG, *, seed: int = 0,
    spec: EnvSpec | None = None,
) -> TrainResult:
    """Train the A2C demo on a region bank of ``seeds``; return params + measurements.

    Everything inside the loop (rollout + grad + Adam) is ``jit``-compiled and ``vmap``-
    batched over ``config.batch`` envs. ``spec`` selects the env config (default world or
    `difficulty_env_spec()` for the high-gym dynamic-range config); the obs dim is derived
    from it. The learning curve is mean reward-per-env-step per iteration. Raises
    ImportError only transitively (callers gate with importorskip).
    """
    spec = spec or default_env_spec()
    bank = build_region_bank(seeds, spec)
    rollout = jax.jit(make_rollout(bank, spec.env))

    def grad_fn(p: Params, flat: Array, a: Array, r: Array, d: Array) -> Params:
        return jax.grad(a2c_loss)(
            p, flat, a, r, d, config.gamma, config.ent_coef, config.vf_coef
        )

    jgrad = jax.jit(grad_fn)

    key = random.PRNGKey(seed)
    key, pk = random.split(key)
    params = init_params(pk, _obs_dim(spec, seeds[0]), config.hidden)
    opt = _adam_init(params)
    state = bank

    curve: list[float] = []
    # warm-up compile (excluded from timing)
    key, rk = random.split(key)
    state, traj = rollout(params, state, random.split(rk, config.rollout_len))
    jax.block_until_ready(traj[0])

    start = time.perf_counter()
    for _ in range(config.iters):
        key, rk = random.split(key)
        state, traj = rollout(params, state, random.split(rk, config.rollout_len))
        flat, actions, rewards, dones = traj
        grads = jgrad(params, flat, actions, rewards, dones)
        params, opt = _adam_step(params, grads, opt, config.lr)
        curve.append(float(rewards.mean()))
    jax.block_until_ready(params["w1"])
    wall = time.perf_counter() - start

    total = config.iters * config.rollout_len * config.batch
    return TrainResult(
        params=params,
        curve=tuple(curve),
        total_env_steps=total,
        wall_time_s=wall,
        env_steps_per_s=total / wall,
    )


# =====================================================================================
# Tuned PPO (jax-ppo-tuned) — GAE(λ) + clipped surrogate + minibatch epochs + adv-norm.
# Additive: the A2C `train` above is untouched (jax-rl-demo / its tests are unchanged).
# =====================================================================================


class PPOConfig(NamedTuple):
    """PPO hyperparameters (small net by design; a baseline, not a SOTA sweep)."""

    batch: int = 256
    rollout_len: int = 32
    iters: int = 150
    hidden: int = 64
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip: float = 0.2
    lr: float = 3e-3
    ent_coef: float = 0.01
    vf_coef: float = 0.5
    epochs: int = 4
    num_minibatches: int = 4


def gae(
    rewards: Array, values: Array, dones: Array, last_value: Array,
    gamma: float, lam: float,
) -> tuple[Array, Array]:
    """Generalized Advantage Estimation over a ``(T, B)`` rollout (jittable, pure).

    ``last_value`` bootstraps past the window. Returns ``(advantages, returns)`` with
    ``returns = advantages + values``. Identities: ``(γ=1, λ=1)`` → Monte-Carlo returns
    (minus V), ``λ=0`` → 1-step TD residual — both covered by tests.
    """
    def step(carry: tuple[Array, Array], x: tuple[Array, Array, Array]
             ) -> tuple[tuple[Array, Array], Array]:
        gae_acc, next_value = carry
        r, v, d = x
        nonterm = 1.0 - d
        delta = r + gamma * next_value * nonterm - v
        gae_acc = delta + gamma * lam * nonterm * gae_acc
        return (gae_acc, v), gae_acc

    b = rewards.shape[1]
    init = (jnp.zeros((b,)), last_value)
    _, adv = jax.lax.scan(step, init, (rewards, values, dones.astype(jnp.float32)),
                          reverse=True)
    return adv, adv + values


_PPOTraj = tuple[Array, Array, Array, Array, Array, Array]
_PPORollout = Callable[
    [Params, JaxEnvState, Array], tuple[JaxEnvState, _PPOTraj, Array]
]


def make_ppo_rollout(init_state: JaxEnvState, env: JaxEnv) -> _PPORollout:
    """Build a jittable PPO rollout collecting ``(flat, actions, logp_old, values,
    rewards, dones)`` + a bootstrap ``last_value`` at the final state. Auto-resets done
    envs to their bank-initial state (single ``lax.scan``)."""
    venc = jax.vmap(env.encode_obs)
    vflat = jax.vmap(flatten_obs)
    vstep = jax.vmap(env.step)

    def scan_step(
        carry: tuple[JaxEnvState, Params], key: Array
    ) -> tuple[tuple[JaxEnvState, Params], _PPOTraj]:
        state, params = carry
        flat = vflat(venc(state))
        logits, value = apply_policy(params, flat)
        actions = random.categorical(key, logits)
        logp = jnp.take_along_axis(
            jax.nn.log_softmax(logits), actions[..., None], axis=-1
        )[..., 0]
        nstate, _, reward, term, trunc = vstep(state, actions)
        done = term | trunc
        nstate = jax.tree_util.tree_map(
            lambda fresh, cur: _reset_where(done, fresh, cur), init_state, nstate
        )
        return (nstate, params), (flat, actions, logp, value, reward, done)

    def rollout(
        params: Params, state: JaxEnvState, keys: Array
    ) -> tuple[JaxEnvState, _PPOTraj, Array]:
        (state, _), traj = jax.lax.scan(scan_step, (state, params), keys)
        _, last_value = apply_policy(params, vflat(venc(state)))
        return state, traj, last_value

    return rollout


def ppo_loss(
    params: Params, flat: Array, actions: Array, logp_old: Array, adv: Array,
    returns: Array, clip: float, ent_coef: float, vf_coef: float,
) -> Array:
    """PPO clipped-surrogate loss (+ value MSE − entropy) on a minibatch.

    Advantages are normalized per minibatch. ``ratio = exp(logp − logp_old)``; the
    surrogate is ``min(ratio·A, clip(ratio, 1±ε)·A)`` (maximized → negated for descent).
    """
    logits, values = apply_policy(params, flat)
    logp_all = jax.nn.log_softmax(logits)
    logp = jnp.take_along_axis(logp_all, actions[..., None], axis=-1)[..., 0]
    adv_n = (adv - adv.mean()) / (adv.std() + 1e-8)
    ratio = jnp.exp(logp - logp_old)
    unclipped = ratio * adv_n
    clipped = jnp.clip(ratio, 1.0 - clip, 1.0 + clip) * adv_n
    pg = -jnp.minimum(unclipped, clipped).mean()
    vl = 0.5 * ((values - returns) ** 2).mean()
    entropy = -(jnp.exp(logp_all) * logp_all).sum(-1).mean()
    return pg + vf_coef * vl - ent_coef * entropy


_DEFAULT_PPO_CONFIG = PPOConfig()


def train_ppo(
    seeds: tuple[int, ...], config: PPOConfig = _DEFAULT_PPO_CONFIG, *, seed: int = 0,
    spec: EnvSpec | None = None,
) -> TrainResult:
    """Train a tuned PPO on a region bank of ``seeds``; return params + measurements.

    Each iteration: one ``vmap`` rollout → GAE(λ) advantages → ``epochs`` passes of
    ``num_minibatches`` clipped-surrogate updates (all on-device under ``jit``). ``spec``
    selects the env config (default world or ``difficulty_env_spec()``); the obs dim is
    derived from it. The curve is mean reward-per-env-step per iteration (same proxy as
    the A2C demo, so the two are directly comparable)."""
    spec = spec or default_env_spec()
    bank = build_region_bank(seeds, spec)
    rollout = jax.jit(make_ppo_rollout(bank, spec.env))

    @jax.jit
    def update(
        params: Params, opt: _AdamState, flat: Array, actions: Array, logp_old: Array,
        adv: Array, returns: Array,
    ) -> tuple[Params, _AdamState]:
        grads = jax.grad(ppo_loss)(
            params, flat, actions, logp_old, adv, returns,
            config.clip, config.ent_coef, config.vf_coef,
        )
        return _adam_step(params, grads, opt, config.lr)

    key = random.PRNGKey(seed)
    key, pk = random.split(key)
    params = init_params(pk, _obs_dim(spec, seeds[0]), config.hidden)
    opt = _adam_init(params)
    state = bank

    n = config.rollout_len * config.batch
    mb = n // config.num_minibatches
    curve: list[float] = []

    # warm-up compile (excluded from timing)
    key, rk = random.split(key)
    state, traj, last_value = rollout(params, state, random.split(rk, config.rollout_len))
    jax.block_until_ready(traj[0])

    start = time.perf_counter()
    for _ in range(config.iters):
        key, rk = random.split(key)
        state, traj, last_value = rollout(
            params, state, random.split(rk, config.rollout_len)
        )
        flat, actions, logp_old, values, rewards, dones = traj
        adv, returns = gae(rewards, values, dones, last_value, config.gamma,
                           config.gae_lambda)
        # flatten (T, B, ...) → (T*B, ...) for minibatching
        fb = flat.reshape((n, -1))
        ab, lb = actions.reshape((n,)), logp_old.reshape((n,))
        advb, retb = adv.reshape((n,)), returns.reshape((n,))
        for _e in range(config.epochs):
            key, sk = random.split(key)
            perm = random.permutation(sk, n)
            for i in range(config.num_minibatches):
                idx = perm[i * mb:(i + 1) * mb]
                params, opt = update(
                    params, opt, fb[idx], ab[idx], lb[idx], advb[idx], retb[idx]
                )
        curve.append(float(rewards.mean()))
    jax.block_until_ready(params["w1"])
    wall = time.perf_counter() - start

    total = config.iters * config.rollout_len * config.batch
    return TrainResult(
        params=params, curve=tuple(curve), total_env_steps=total,
        wall_time_s=wall, env_steps_per_s=total / wall,
    )


def evaluate_gym_clears(
    params: Params, seeds: tuple[int, ...], *, steps: int = _MAX_STEPS,
    spec: EnvSpec | None = None,
) -> float:
    """Mean gym-clear count of the greedy policy over ``seeds`` (no reset).

    Reads ``gyms_defeated`` at the final step — monotonic within an episode and stable
    after termination (a defeated gym can't be re-entered), so this is the episode's
    gym-clear count. Matches the metric of the scripted oracle arms
    (``learnability.measure_learnability`` gym-clear means), enabling an honest
    PPO-vs-oracle *headroom* comparison on the same yardstick."""
    spec = spec or default_env_spec()
    bank = build_region_bank(seeds, spec)
    venc = jax.vmap(spec.env.encode_obs)
    vflat = jax.vmap(flatten_obs)
    vstep = jax.vmap(spec.env.step)

    def step(
        carry: JaxEnvState, _: Array
    ) -> tuple[JaxEnvState, None]:
        logits, _v = apply_policy(params, vflat(venc(carry)))
        actions = jnp.argmax(logits, axis=-1)
        nstate, _o, _r, _t, _tr = vstep(carry, actions)
        return nstate, None

    @jax.jit
    def run(state: JaxEnvState) -> Array:
        final, _ = jax.lax.scan(step, state, jnp.arange(steps))
        return jax.vmap(spec.env.encode_obs)(final)["gyms_defeated"][:, 0]

    return float(run(bank).mean())


def learning_verdict(curve: tuple[float, ...]) -> tuple[str, float, float]:
    """Pre-registered R1 decision rule (frozen before data) → branch + (rise, std_late).

    Compares the first vs last 20% of the curve: branch ``"a"`` ("learns + fast") iff
    ``mean_late − mean_early >= std_late`` (rise clears the late-window noise), else
    ``"b"`` (throughput headline, learning reported as a partial signal). Importable so
    the demo and a test apply the *same* rule mechanically.
    """
    n = len(curve)
    w = max(1, n // 5)
    early = np.asarray(curve[:w], dtype=float)
    late = np.asarray(curve[-w:], dtype=float)
    rise = float(late.mean() - early.mean())
    std_late = float(late.std())
    return ("a" if rise >= std_late else "b"), rise, std_late


def evaluate(
    params: Params, seeds: tuple[int, ...], *, steps: int = _MAX_STEPS,
    spec: EnvSpec | None = None,
) -> float:
    """Mean episode return of the greedy policy over ``seeds`` (no reset, masked at done).

    Used to report held-out-seed performance (seeds disjoint from training) — ties the
    speed demo to the generalization story. Deterministic (argmax actions). ``spec``
    selects the env config (default world unless given).
    """
    spec = spec or default_env_spec()
    bank = build_region_bank(seeds, spec)
    venc = jax.vmap(spec.env.encode_obs)
    vflat = jax.vmap(flatten_obs)
    vstep = jax.vmap(spec.env.step)

    def step(
        carry: tuple[JaxEnvState, Array, Array], _: Array
    ) -> tuple[tuple[JaxEnvState, Array, Array], None]:
        state, ret, alive = carry
        logits, _v = apply_policy(params, vflat(venc(state)))
        actions = jnp.argmax(logits, axis=-1)
        nstate, _o, reward, term, trunc = vstep(state, actions)
        ret = ret + reward * alive
        alive = alive * (1.0 - (term | trunc).astype(jnp.float32))
        return (nstate, ret, alive), None

    n = len(seeds)
    init = (bank, jnp.zeros((n,)), jnp.ones((n,)))

    @jax.jit
    def run(carry: tuple[JaxEnvState, Array, Array]) -> Array:
        (_s, ret, _a), _ = jax.lax.scan(step, carry, jnp.arange(steps))
        return ret

    return float(run(init).mean())
