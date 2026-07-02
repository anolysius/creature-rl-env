"""Scout: is a hidden multi-type boss a *deeper* difficulty lever? (hard-benchmark/multitype-boss)

hard-benchmark #1-#3 settled the memory axis (memory is load-bearing; the env is hard even for a
strong recurrent-PPO memory agent at grid16). The remaining "deeper" lever is inference DEPTH:
give each gym boss a HIDDEN secondary defending type (effectiveness = product over both types; the
observation reveals only the primary, so the second must be inferred from battle outcomes).

This is a **de-risked scout**, not a measurement. It (i) re-checks numpy<->JAX parity 0 at the
multi-type config (the correctness gate — a broken multi-type env would be misleading), (ii) trains
a recurrent PPO on the single-type and multi-type hard configs (learnable?), and (iii) prints the
oracle-fraction for each with the gap Delta.

HONEST FRAMING (read before quoting any number): this is ONE seed, a short budget, on CPU; the
oracle is a scripted ceiling proxy. The single-vs-multi Delta below is a RAW single-run signal with
NO robust threshold — calling multi-type "harder" requires a multi-seed (>=3), pre-registered
measurement, which is an explicit FOLLOW-UP task. Do not headline the Delta.

Run: `python scripts/multitype_boss_scout.py [--quick]`. Requires `[jax]` + `[rl]`.
"""
from __future__ import annotations

import argparse

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.jax_env import JaxEnvConfig, make_jax_env
from critter_gym.jax_train import (
    PPOConfig,
    evaluate_gym_clears_recurrent,
    hard_env_spec,
    learning_verdict,
    multitype_hard_env_spec,
    train_recurrent_ppo,
)
from critter_gym.learnability import reference_arm, run_episode
from critter_gym.region import generate_region, heldout_seeds

GRID, NGYM, NTYPES, NCRE, STEPS, PR = 16, 5, 8, 6, 420, 2


def _oracle(seeds, *, boss_secondary: bool) -> float:
    fac = lambda: CritterEnv(  # noqa: E731
        commit_battles=True, vary=True, num_types=NTYPES, num_gyms=NGYM, grid_size=GRID,
        num_creatures=NCRE, max_steps=STEPS, patch_radius=PR, min_gyms=NGYM,
        boss_secondary=boss_secondary)
    return float(np.mean([run_episode(fac, reference_arm("oracle"), s).gyms_cleared
                          for s in seeds]))


def _parity_ok(seed: int, steps: int) -> bool:
    """Quick inline parity 0 check on the multi-type config (a subset of the parity test)."""
    import jax.numpy as jnp
    env = CritterEnv(grid_size=GRID, num_creatures=NCRE, num_gyms=NGYM, max_steps=STEPS,
                     patch_radius=PR, vary=True, num_types=NTYPES, commit_battles=True,
                     min_gyms=NGYM, boss_secondary=True)
    jenv = make_jax_env(JaxEnvConfig(grid=GRID, patch_radius=PR, max_steps=STEPS, max_gyms=NGYM))
    region = generate_region(seed, GRID, NCRE, NGYM, vary=True, num_types=NTYPES,
                             min_gyms=NGYM, boss_secondary=True)
    obs, _ = env.reset(seed=seed)
    st = jenv.reset(region)
    step = jenv.make_step()
    rng = np.random.default_rng(9000 + seed)
    for _ in range(steps):
        a = int(rng.integers(0, 6))
        obs, r_np, t_np, tr_np, _ = env.step(a)
        st, jo, r_jx, t_jx, tr_jx = step(st, jnp.int32(a))
        if not (float(r_np) == float(r_jx) and bool(t_np) == bool(t_jx)):
            return False
        if not np.array_equal(np.asarray(obs["enemy_type"]), np.asarray(jo["enemy_type"])):
            return False
        if t_np or tr_np:
            break
    return True


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (tiny budget)")
    a = p.parse_args()

    iters = 40 if a.quick else 250
    hidden, batch, n_eval = 128, 32, 8
    heldout = tuple(int(s) for s in heldout_seeds(n_eval))
    learn = tuple(range(batch))

    print("== Multi-type boss scout (deeper inference lever) — SIGNAL, not measurement ==")
    parity = _parity_ok(0, steps=STEPS)
    print(f"  parity numpy<->JAX (multi-type, seed 0): {'0 mismatch OK' if parity else 'FAIL'}")

    # Oracle ceiling on each config (must stay winnable, else the lever is unfair).
    oracle_single = _oracle(heldout, boss_secondary=False)
    oracle_multi = _oracle(heldout, boss_secondary=True)

    # One recurrent-PPO run on each config (learnable? how far below oracle?).
    rec_single = train_recurrent_ppo(
        learn, PPOConfig(batch=batch, hidden=hidden, iters=iters), seed=0, spec=hard_env_spec())
    rec_multi = train_recurrent_ppo(
        learn, PPOConfig(batch=batch, hidden=hidden, iters=iters), seed=0,
        spec=multitype_hard_env_spec())
    gc_single = evaluate_gym_clears_recurrent(rec_single.params, heldout, steps=STEPS,
                                              spec=hard_env_spec())
    gc_multi = evaluate_gym_clears_recurrent(rec_multi.params, heldout, steps=STEPS,
                                             spec=multitype_hard_env_spec())
    frac_single = gc_single / max(oracle_single, 1e-9)
    frac_multi = gc_multi / max(oracle_multi, 1e-9)
    delta_pp = (frac_single - frac_multi) * 100.0

    lv_single = learning_verdict(rec_single.curve)[0]
    lv_multi = learning_verdict(rec_multi.curve)[0]
    print(f"  config: grid {GRID}, 5x5 view, {NGYM} gyms, {STEPS} steps; "
          f"recurrent PPO GRU h{hidden}, 1 seed, iters={iters}")
    print(f"  single-type: oracle {oracle_single:.2f} (winnable={oracle_single >= 0.5 * NGYM})  "
          f"rec {gc_single:.2f}  = {frac_single:.0%} of oracle  learns={lv_single}")
    print(f"  multi-type : oracle {oracle_multi:.2f} (winnable={oracle_multi >= 0.5 * NGYM})  "
          f"rec {gc_multi:.2f}  = {frac_multi:.0%} of oracle  learns={lv_multi}")
    print(f"  DELTA (single_frac - multi_frac) = {delta_pp:+.1f} pp  "
          f"(> 0 hints multi-type is harder for the learned agent)")
    print("  HONEST: 1-seed RAW signal, NO robust threshold. A >=3-seed, pre-registered "
          "(classify_headroom) measurement is the FOLLOW-UP task — do NOT headline this Delta.")
    print("  honest: PPO(not SOTA)/CPU/1-run/grid16 only; oracle=scripted proxy; second type "
          "hidden (inferred). Parity 0 gates that oracle(numpy) and agent(JAX) share the env.")


if __name__ == "__main__":
    main()
