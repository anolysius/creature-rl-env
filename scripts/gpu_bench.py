"""GPU-fair throughput bench (fused ``lax.scan`` rollout) — M4-EC3 (run on a GPU).

The repo's ``bench_throughput.py`` drives the env with a **python per-step loop** (one
``vmap`` dispatch per step). On a CPU that already reaches tens of millions of steps/s, but
on a GPU it is *dispatch-bound* — each step pays a host→device launch, so it badly *undersells*
the device. This bench instead fuses ``rollout_steps`` env steps into a single ``lax.scan`` that
is ``vmap``-batched and ``jit``-compiled — one kernel, no per-step host round-trip — which is
the **GPU-fair** measurement and exactly the pattern the RL loop (``jax_train.make_ppo_rollout``)
uses. It runs on any JAX backend: locally on CPU it is a sanity check (numbers finite, vmap ≥
numpy at large batch); the headline ≥10M steps/s GPU number (M4-EC3) comes from running this on
an NVIDIA GPU (see ``scripts/colab_gpu_bench.ipynb`` for a ready-to-run Colab notebook).

It imports only existing symbols (``jax_overworld`` / ``jax_train``), so it adds no product
code. Requires the ``[jax]`` extra.

Run: ``python scripts/gpu_bench.py [--quick]``  (prints numpy / jax-single / jax-vmap rows).
"""
from __future__ import annotations

import argparse
import time
from typing import Callable

import numpy as np

_GRID, _NC, _NG = 10, 5, 3


def bench_numpy_overworld(n_steps: int) -> float:
    """steps/s of the numpy overworld transition (battle excluded — reset on entry)."""
    from critter_gym.envs.critter_env import CritterEnv

    env = CritterEnv()
    env.reset(seed=0)
    rng = np.random.default_rng(0)
    start = time.perf_counter()
    for i in range(n_steps):
        env._step_overworld(int(rng.integers(0, 6)))
        if env._mode == "battle":
            env.reset(seed=i + 1)
    return n_steps / (time.perf_counter() - start)


def bench_numpy_fullenv(n_steps: int) -> float:
    """steps/s of the full numpy env (overworld + battle), auto-resetting on episode end."""
    from critter_gym.envs.critter_env import CritterEnv

    env = CritterEnv(commit_battles=True)
    env.reset(seed=0)
    rng = np.random.default_rng(0)
    start = time.perf_counter()
    for i in range(n_steps):
        _o, _r, term, trunc, _i = env.step(int(rng.integers(0, 6)))
        if term or trunc:
            env.reset(seed=i + 1)
    return n_steps / (time.perf_counter() - start)


def _fused_overworld_rate(batch: int, rollout_steps: int) -> float:
    """Fused vmap+lax.scan overworld rollout: (batch*rollout_steps)/wall (warm-timed)."""
    import jax
    import jax.numpy as jnp
    from jax import lax, vmap

    from critter_gym.jax_overworld import OverworldState, overworld_step, state_from_region
    from critter_gym.region import generate_region

    states = [state_from_region(generate_region(s, _GRID, _NC, _NG)) for s in range(batch)]
    bs = OverworldState(
        agent_pos=jnp.stack([s.agent_pos for s in states]),
        creature_mask=jnp.stack([s.creature_mask for s in states]),
        gym_mask=jnp.stack([s.gym_mask for s in states]),
        caught=jnp.stack([s.caught for s in states]),
        steps=jnp.stack([s.steps for s in states]),
    )
    acts = jnp.asarray(
        np.random.default_rng(0).integers(0, 6, size=(rollout_steps, batch)), jnp.int32
    )

    def step_fn(state: OverworldState, a: jnp.ndarray) -> tuple[OverworldState, None]:
        nstate = vmap(lambda st, ac: overworld_step(st, ac, contact=False)[0])(state, a)
        return nstate, None

    @jax.jit
    def run(state: OverworldState, acts_in: jnp.ndarray) -> jnp.ndarray:
        final, _ = lax.scan(step_fn, state, acts_in)
        return final.agent_pos

    jax.block_until_ready(run(bs, acts))  # warm / compile
    start = time.perf_counter()
    jax.block_until_ready(run(bs, acts))
    return batch * rollout_steps / (time.perf_counter() - start)


def _fused_fullenv_rate(batch: int, rollout_steps: int) -> float:
    """Fused vmap+lax.scan full-episode env rollout (random actions, no reset)."""
    import jax
    import jax.numpy as jnp
    from jax import lax, vmap

    from critter_gym.jax_env import JaxEnvState
    from critter_gym.jax_train import build_region_bank, default_env_spec

    spec = default_env_spec()
    bank = build_region_bank(tuple(range(batch)), spec)
    vstep = vmap(spec.env.step)
    acts = jnp.asarray(
        np.random.default_rng(1).integers(0, 6, size=(rollout_steps, batch)), jnp.int32
    )

    def step_fn(state: JaxEnvState, a: jnp.ndarray) -> tuple[JaxEnvState, None]:
        nstate, _o, _r, _t, _tr = vstep(state, a)
        return nstate, None

    @jax.jit
    def run(state: JaxEnvState, acts_in: jnp.ndarray) -> jnp.ndarray:
        final, _ = lax.scan(step_fn, state, acts_in)
        return final.agent_pos

    jax.block_until_ready(run(bank, acts))  # warm / compile
    start = time.perf_counter()
    jax.block_until_ready(run(bank, acts))
    return batch * rollout_steps / (time.perf_counter() - start)


def _print_slice(name: str, numpy_rate: float, rate_fn: Callable[[int, int], float],
                 batches: tuple[int, ...], rollout_steps: int) -> None:
    print(f"\n== {name} (fused lax.scan rollout; numpy / jax-single / jax-vmap) ==")
    print(f"  {'numpy single':<24}{numpy_rate:>16,.0f} steps/s   (baseline)")
    single = rate_fn(1, rollout_steps)
    print(f"  {'jax single (jit scan)':<24}{single:>16,.0f} steps/s   "
          f"({single / max(numpy_rate, 1e-9):.2f}x numpy)")
    for b in batches:
        r = rate_fn(b, rollout_steps)
        print(f"  {'jax vmap (batch=' + str(b) + ')':<24}{r:>16,.0f} steps/s   "
              f"({r / max(numpy_rate, 1e-9):,.0f}x numpy)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="fast smoke (smaller sizes)")
    args = parser.parse_args()

    numpy_steps = 20_000 if args.quick else 100_000
    rollout_steps = 200 if args.quick else 1000
    batches = (1024, 4096) if args.quick else (1024, 4096, 16384, 65536)

    try:
        import jax
        print(f"== GPU-fair throughput (fused scan) — JAX backend: {jax.default_backend()} ==")
    except ImportError:
        print("JAX not installed — `pip install \"jax[cuda12]\"` (GPU) or `critter_gym[jax]`.")
        return

    _print_slice("overworld slice", bench_numpy_overworld(numpy_steps),
                 _fused_overworld_rate, batches, rollout_steps)
    _print_slice("full-episode env (commit)", bench_numpy_fullenv(numpy_steps),
                 _fused_fullenv_rate, batches, rollout_steps)
    print("\n  (honest: vmap is the win — a single jitted env is not faster than numpy. "
          "On CPU this is a sanity check; the >=10M steps/s GPU number is M4-EC3.)")


if __name__ == "__main__":
    main()
