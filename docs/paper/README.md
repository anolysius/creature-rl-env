# Paper draft — reproduction pointers

`critter-gym.md` is the arXiv writeup draft (M3-EC4). This file maps every quantitative
claim to its source, and labels each figure **CI-reproducible** (frozen by a test
assertion/gate) vs **run-derived** (a mean from a particular run; the test freezes only a
threshold). Honesty over headline: no figure is fabricated.

## Figure → source map

| Claim (paper §) | Figure | Source | Tier |
|---|---|---|---|
| Throughput numpy (§2) | ~266k–410k steps/s/core (≈5–8× 50k target) | env-validation report; `scripts/bench_throughput.py` (numpy rows) | run-derived |
| JAX vmap throughput (§6) | overworld ~186× / commit-battle ~1047× / non-commit-battle ~452× / full-env 34–73× / duel 40–83× (CPU) | `scripts/bench_throughput.py`; `scripts/reproduce_results.py`; archive `jax-throughput/0*-*/report.md` | run-derived |
| numpy↔JAX parity (§6) | 0 mismatch (all obs+reward+term+trunc), 4 families | `tests/test_jax_{parity,env_parity,family_parity,duel_parity,...}.py` | **CI-reproducible** (parity) |
| Oracle headroom (§4) | PPO 28% (default) / 21% (hard) of oracle, 5-run robust; hard: PPO < type_blind | `scripts/ppo_baseline.py --runs 5`; `critter_gym.headroom.classify_headroom`; archive `difficulty-scaling/03-ppo-headroom-rigor/report.md` | run-derived (classifier gate frac=0.75 is pre-registered) |
| Instance gap≈0 (§3) | held-in 40% vs held-out 45% boss-defeat | `scripts/killer_demo.py`; `docs/CHANGELOG.md` M3-EC6 entry | run-derived |
| Load-bearing gates (§4) | Gate0 `oracle−type_blind ≥ 0.20`, Gate1 `infer−probe ≥ 0.10`, 42 held-out seeds | `tests/test_reasoning_gate.py` (`GATE0_MIN`/`GATE1_MIN`, `HELD_OUT_SEEDS=range(1000,1042)`) | **CI-reproducible** (gates) |
| Load-bearing margins (§4) | observed ≈ 0.48 / ≈ 0.36 (oracle 1.00/type_blind 0.52; infer 0.84/probe 0.47) | run means; `docs/CHANGELOG.md` reasoning-load-bearing entry; memory `team-commit-makes-inference-load-bearing` | run-derived (test freezes only the gates) |
| Learnability ordering (§4) | gym-clear-only oracle/infer ≈4.19 ≫ type_blind 1.81 > probe 1.06; PPO ≈ infer | `critter_gym.learnability` (`measure_learnability`, gym-clear-only metric); `scripts/learnability.py`; archive `20-learnability-precision/report.md` | run-derived |
| Family C skill-structural (§5) | A-tuned gap ≈+3.9 vs C-appropriate ≈+0.2 (held-out duel); C winnable ≈4.3 | `critter_gym.genre_generalization` (`type_attacker_policy`/`duel_aware_policy`, LOO); archive `19-battle-system-family/report.md` | run-derived |
| Family D skill-structural (§5) | muster ≈1.42 ≫ rush 0.00 on D; muster ≤ rush on A | `critter_gym.genre_generalization` (`muster_policy`/`rush_policy`); archive `21-family-d-muster/report.md` | run-derived (within-family contrast) |
| Family B forgiving (§5) | A-tuned gap ≈ 0 (collection axis) | `critter_gym.genre_generalization`; archive `18-genre-generalization-foundation/` | run-derived |

## Honest-scope SSOT

The paper's scope and caveats follow `DESIGN.md` §3.1.1 (the project's honest-scope SSOT):
instance generalization (A) is measured; genre generalization (B) is a **foundation, not a
proof**. Any update to the claims must keep that distinction.

## Status

- **Draft.** Not a submission. The JAX port (throughput) and the tuned-PPO oracle-headroom are
  now done and folded into §6 / §4. Next steps (follow-up tasks): LaTeX/figures, a GPU throughput
  measurement (M4-EC3), more families + a learned policy on a held-out family, M3-EC5 OSS release.
