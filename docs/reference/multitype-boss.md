# Multi-type gym boss (deeper inference lever) — reference

An opt-in difficulty lever for the hard-benchmark: a gym boss can carry a **hidden secondary
defending type**. The player-vs-boss effectiveness is the *product* over both types
(`TypeChart.multi_effectiveness`), but the observation reveals only the **primary** — so the
second type must be **inferred from battle outcomes** (deeper hidden-rule inference than a
single-type boss). The lever is **opt-in**; off is byte-identical to the historical single-type
world.

## How it works

- `region.generate_region(..., boss_secondary=True)` draws a per-gym secondary type (a different
  active type than the primary) into `Region.boss_secondary_types` (parallel to `gyms`). The
  secondary is drawn *after* the primary/coord placement, so enabling it never perturbs the
  historical draw sequence (off ⇒ byte-identical). Default off = empty tuple.
- `CritterEnv(boss_secondary=True)` / `party.gym_boss(..., secondary_type=t)` gives the boss two
  defending types; numpy `Battle` already computes the product (`multi_effectiveness`). The
  observed `enemy_type` stays the primary (shape unchanged — the secondary is hidden).
- The scripted **oracle** reads the boss's *full* types from env internals (`_boss_types`) and
  scores with `multi_effectiveness` — the chart-knowing expert. The `infer`/`probe` arms stay on
  the observed primary (the hidden type does not leak to them).
- JAX (`jax_env`): `gym_type2` (`(MAX_GYMS,)`, sentinel `-1` = single-type); the player→boss
  damage uses `_boss_def_eff = eff[m,d1] * (d2<0 ? 1 : eff[m,d2])`. The boss→player damage and
  the observation stay primary-only (the boss's move is the primary). numpy↔JAX parity is gated
  by `tests/test_jax_multitype_boss_parity.py` (parity 0). The standalone ports
  `jax_battle.py`/`jax_battle_full.py` are single-type only (not on the training path).

## Scout finding (1 seed — SIGNAL, not measurement)

`scripts/multitype_boss_scout.py --quick` at the grid16 hard config (recurrent PPO, 1 seed):

| config | oracle (winnable) | recurrent PPO | of oracle |
|---|---|---|---|
| single-type | 5.00 ✓ | 1.38 | 28% |
| multi-type | 3.62 ✓ | 0.88 | 24% |

The hidden second type lowers even the **oracle** ceiling (5.00 → 3.62 — the product effectiveness
shrinks the super-effective advantage) while staying winnable, and the learned agent's
oracle-fraction drops slightly (Δ ≈ +3.4 pp). Both are consistent with a *deeper* difficulty.

> **This is a raw single-seed signal with NO robust threshold.** Calling the multi-type boss
> "harder" requires a **multi-seed (≥3), pre-registered** measurement (`classify_headroom`) — the
> explicit **follow-up task** (`multitype-boss-headroom`). Honest labels: PPO (not SOTA), CPU,
> one seed, grid16 only; the oracle is a scripted ceiling proxy.

## Follow-up

- `multitype-boss-headroom` — the multi-seed, pre-registered headroom measurement (does the hidden
  secondary type robustly raise oracle headroom for a strong memory agent?).
