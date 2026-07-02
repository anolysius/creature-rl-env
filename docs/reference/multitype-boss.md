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

> **This was a raw single-seed signal with NO robust threshold.** The pre-registered multi-seed
> measurement below superseded it — and showed the scout's Δ was within run noise.

## Measured (multi-seed, pre-registered — multitype-boss-headroom)

`scripts/multitype_boss_headroom.py --runs 5` (recurrent PPO GRU h128, 250 iters, CPU; rules
frozen before the data: (A) `classify_headroom(frac=0.75, k=1.0)` on the multi-type config,
(B) `classify_depth` on per-run oracle fractions; runs expanded 3→5 on an inconclusive read,
thresholds unchanged — the #3 precedent):

| config | oracle (winnable) | recurrent PPO (5 runs) | of oracle |
|---|---|---|---|
| single-type | 5.00 ✓ | 1.60 ± 0.42 | 32% ± 8% |
| multi-type | 3.00 ✓ | 0.89 ± 0.36 | 30% ± 12% |

- **(A) `hard-for-memory-agent` ROBUST** on the multi-type config: mean+std 1.25 ≪ 0.75·oracle
  2.25. The multi-type world stays hard for the strongest agent we have, and stays winnable.
- **(B) depth: `inconclusive`** — the fraction gap shrank from +9.0 pp (3 runs) to **+2.4 pp**
  (5 runs), well inside the run noise (std 8%/12%). The scout's 1-seed Δ+3.4 pp **did not
  survive** multi-seed measurement. In *normalized* terms the learned agent is about equally far
  from its oracle on both configs — the hidden type lowers the expert ceiling (5.00 → 3.00) and
  the agent's raw score roughly proportionally, rather than selectively hurting the learner.

**Honest read**: the hidden secondary type is a *ceiling-lowering* lever (absolute difficulty up,
even for the oracle) but **not an established relative-depth lever** at this config/budget. Do not
claim "multi-type is deeper for learned agents" — the pre-registered verdict is inconclusive.
Labels: CPU, 5 runs, recurrent PPO (not SOTA), grid16 only, scripted-oracle ceiling proxy.

## Follow-up (open)

- The depth question stays open: a config where the hidden type binds harder (e.g. more types, a
  boss pool that punishes wrong commits more) might separate the fractions — a new scout would be
  needed before any further measurement spend.
