"""AC3: overworld throughput benchmark — numpy baseline vs JAX (single & vmap).

Measures steps/s of the *overworld* transition three ways and prints an honest
table:

  1. numpy  ``CritterEnv._step_overworld`` driven in a loop (the current engine),
  2. JAX    single-env ``jit`` step in a loop,
  3. JAX    ``vmap``-batched step over many envs at once.

**Honest framing (do not headline a single number):** JAX's win is *entirely* from
vectorization. A *single* env under ``jit`` is typically **slower** than numpy
(per-call dispatch overhead with no batching to amortize it). The throughput gain
appears only when ``vmap`` runs thousands of envs in lock-step — which is exactly the
"vectorizable" requirement (DESIGN §4). All rates are CPU here; a GPU would push the
vmap row much further (M4-EC3's >=10M steps/s GPU target is out of this task's scope,
though CPU vmap already approaches it). Numbers are a single machine, single run —
a *direction*, not a tuned benchmark.

Run: ``python scripts/bench_throughput.py`` (numpy rows always; JAX rows need the
``[jax]`` extra). ``--quick`` for a fast smoke.
"""

from __future__ import annotations

import argparse
import time

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.region import generate_region

_GRID, _NC, _NG = 10, 5, 3


def bench_numpy_overworld(n_steps: int) -> float:
    """steps/s of the numpy overworld transition (battle excluded: reset on entry)."""
    env = CritterEnv()
    env.reset(seed=0)
    rng = np.random.default_rng(0)
    start = time.perf_counter()
    for i in range(n_steps):
        action = int(rng.integers(0, 6))
        env._step_overworld(action)
        if env._mode == "battle":  # battle is out of this slice — reset to a fresh world
            env.reset(seed=i + 1)
    return n_steps / (time.perf_counter() - start)


def _bench_jax(n_single: int, batches: tuple[int, ...], steps_per_batch: int) -> list[str]:
    import jax
    import jax.numpy as jnp

    from critter_gym.jax_overworld import (
        OverworldState,
        make_step_fn,
        overworld_step,
        state_from_region,
    )

    lines: list[str] = []

    # --- single-env jit ---
    step = make_step_fn(contact=False)
    state = state_from_region(generate_region(0, _GRID, _NC, _NG))
    acts = np.random.default_rng(0).integers(0, 6, size=n_single)
    state, _, _ = step(state, jnp.int32(2))  # warm (compile)
    jax.block_until_ready(state.agent_pos)
    start = time.perf_counter()
    for i in range(n_single):
        state, _, _ = step(state, jnp.int32(int(acts[i])))
    jax.block_until_ready(state.agent_pos)
    single_rate = n_single / (time.perf_counter() - start)
    lines.append(("single (jit)", single_rate))

    # --- vmap-batched ---
    for batch in batches:
        states = [state_from_region(generate_region(s, _GRID, _NC, _NG)) for s in range(batch)]
        bs = OverworldState(
            agent_pos=jnp.stack([s.agent_pos for s in states]),
            creature_mask=jnp.stack([s.creature_mask for s in states]),
            gym_mask=jnp.stack([s.gym_mask for s in states]),
            caught=jnp.stack([s.caught for s in states]),
            steps=jnp.stack([s.steps for s in states]),
        )
        vstep = jax.jit(jax.vmap(lambda s, a: overworld_step(s, a, contact=False)))
        acts2 = jnp.asarray(
            np.random.default_rng(0).integers(0, 6, size=(steps_per_batch, batch)), jnp.int32
        )
        bs, _, _ = vstep(bs, acts2[0])  # warm
        jax.block_until_ready(bs.agent_pos)
        start = time.perf_counter()
        for i in range(steps_per_batch):
            bs, _, _ = vstep(bs, acts2[i])
        jax.block_until_ready(bs.agent_pos)
        rate = (batch * steps_per_batch) / (time.perf_counter() - start)
        lines.append((f"vmap (batch={batch})", rate))

    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="fast smoke (smaller sizes)")
    args = parser.parse_args()

    n_steps = 20_000 if args.quick else 100_000
    n_single = 10_000 if args.quick else 20_000
    batches = (1024,) if args.quick else (1024, 4096, 16384)
    steps_per_batch = 200 if args.quick else 1000

    print("== CritterGym overworld throughput (CPU, single run — a direction, not a headline) ==")
    np_rate = bench_numpy_overworld(n_steps)
    print(f"  {'numpy single':<22}{np_rate:>15,.0f} steps/s   (baseline)")

    try:
        rows = _bench_jax(n_single, batches, steps_per_batch)
    except ImportError:
        print("  (JAX not installed — `pip install critter_gym[jax]` for the JAX rows)")
        return
    for label, rate in rows:
        rel = rate / np_rate
        note = "SLOWER than numpy — single env has no batching to amortize jit dispatch" \
            if rel < 1 else f"{rel:.0f}x numpy"
        print(f"  {'jax ' + label:<22}{rate:>15,.0f} steps/s   ({note})")

    print("\n  Honest read: JAX's gain is from vmap vectorization, not per-env speed.")
    print("  A single jit env is slower than numpy; only batched (vmap) rollouts win.")

    # --- battle (commit-mode champion) ---
    print("\n== Commit-mode champion battle throughput (CPU, single run) ==")
    bn = bench_numpy_battle(n_steps)
    print(f"  {'numpy single':<22}{bn:>15,.0f} steps/s   (baseline)")
    try:
        brows = _bench_jax_battle(batches, steps_per_batch)
    except ImportError:
        print("  (JAX not installed — `pip install critter_gym[jax]` for the JAX rows)")
        return
    for label, rate in brows:
        print(f"  {'jax ' + label:<22}{rate:>15,.0f} steps/s   ({rate / bn:.0f}x numpy)")
    print("\n  (battle step is pure arithmetic → vmap vectorizes even better than overworld)")


def bench_numpy_battle(n_steps: int) -> float:
    """steps/s of the numpy commit-mode champion battle (re-seed a fresh fight on end)."""
    from critter_gym.battle import (
        ActionKind,
        Battle,
        BattleAction,
        BattleState,
        Side,
        scripted_opponent,
    )
    from critter_gym.party import gym_boss, starter_party
    from critter_gym.types import ElementType, TypeChart

    chart = TypeChart()

    def fresh() -> Battle:
        st = BattleState(party_a=starter_party(), party_b=gym_boss(ElementType.GRASS))
        return Battle(st, chart=chart, commit_mode=True)

    battle = fresh()
    cnt = 0
    start = time.perf_counter()
    while cnt < n_steps:
        if battle.terminated or battle.truncated:
            battle = fresh()
            continue
        battle.step(
            BattleAction(ActionKind.MOVE, 0), scripted_opponent(battle.state, Side.B, chart)
        )
        cnt += 1
    return cnt / (time.perf_counter() - start)


def _bench_jax_battle(batches: tuple[int, ...], steps_per_batch: int) -> list[str]:
    import jax
    import jax.numpy as jnp

    from critter_gym.jax_battle import (
        ChampionBattleState,
        champion_battle_step,
        params_from_creatures,
    )
    from critter_gym.party import gym_boss, starter_party
    from critter_gym.types import ElementType, TypeChart

    champ = starter_party()[0]
    boss = gym_boss(ElementType.GRASS)[0]
    p = params_from_creatures(champ, boss, TypeChart())
    rows: list[str] = []
    for batch in batches:
        params = jax.tree_util.tree_map(
            lambda x, b=batch: jnp.broadcast_to(x, (b,) + x.shape), p
        )
        state = ChampionBattleState(
            champ_hp=jnp.full((batch,), float(champ.hp), jnp.float32),
            boss_hp=jnp.full((batch,), float(boss.hp), jnp.float32),
            turn=jnp.zeros((batch,), jnp.int32),
            done=jnp.zeros((batch,), jnp.bool_),
            winner=jnp.zeros((batch,), jnp.int32),
        )
        vstep = jax.jit(jax.vmap(champion_battle_step))
        state = vstep(state, params)  # warm
        jax.block_until_ready(state.champ_hp)
        start = time.perf_counter()
        for _ in range(steps_per_batch):
            state = vstep(state, params)
        jax.block_until_ready(state.champ_hp)
        rate = (batch * steps_per_batch) / (time.perf_counter() - start)
        rows.append((f"vmap (batch={batch})", rate))
    return rows


if __name__ == "__main__":
    main()
