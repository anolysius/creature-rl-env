# Battle arena (engagement-confound-free probe) — reference

A diagnostic mode for one question the sealed LLM probe could not answer: is a
near-floor super-effective-move rate (~14%) "**cannot infer** the hidden chart" or
"**never sustains battle engagement**" (dies/wanders in the overworld before
accumulating battle experience)? The arena removes the second factor structurally —
no overworld, K consecutive battles — so a low SE-rate *in the arena* reads as
"does not infer".

## Mode contract

- `critter_gym.envs.ArenaEnv(k_battles=10, **CritterEnv kwargs)` — `reset` drops the
  agent straight into a gym battle; when a bout resolves (win, loss, or battle
  truncation) the next starts immediately; after `k_battles` bouts the episode
  terminates (`max_steps` truncation still applies).
- **The battle economy is untouched**: battle entry reuses the parent's
  `_maybe_enter_battle` (full-heal per bout, commit-window rules, all difficulty
  knobs — inherited, not copied), and each turn is the parent's `_step_battle`
  verbatim (rewards: +1 win, +1 evolution — RLVR).
- Bosses cycle the region's gyms in order (types RECUR → cross-battle inference stays
  possible); procgen, the hidden per-seed chart, the train/test seed split, and the
  matchup guarantee carry over verbatim.
- Obs contract unchanged (`in_battle=1` during bouts); `gyms_defeated` = cumulative
  bout **wins**, with its obs bound re-declared to `k_battles`.
  `info["arena"] = {battles_done, k_battles}`.
- Not a training path: **no JAX port** (same boundary as `llm_eval`); a probe, not a
  leaderboard config.

## Measurement frame (no new thresholds)

`critter_gym.arena` reads the same inference signal the sealed eval reads:

- SE-rate counted by `eval_harness._super_effective_move` (win-independent,
  attrition-proof), via `arena_band(seeds, k_battles, **knobs)` (scripted 4-arm band,
  per-world arm isolation) and `score_arena_telemetry(submission, seeds, ...)`
  (honors the `reset()` memory-isolation hook).
- Normalization by `eval_harness.se_inference_score` (type_blind → 0, oracle → 1),
  multi-run verdicts by `inference_rigor.classify_inference` (pre-registered
  thresholds) — **zero new thresholds invented**.
- Real-LLM entry point: `scripts/llm_eval_run.py --arena [--k-battles K]` — spends
  API/CLI quota, so an actual run is a separate **user-approved** step.

## Scripted band (12 held-out seeds, K=10, commit, num_types 8 — instrument check)

| arm | arena SE-rate | arena wins /10 | overworld SE-rate (sealed frame) |
|---|---|---|---|
| oracle (chart-knowing) | 100% | 10.00 | 100% |
| infer (proxy, not an LLM) | 96% | 9.17 | 87% |
| probe (blind guess) | 69% | 5.92 | 1% |
| type_blind (one champion) | 46% | 3.33 | 2% |

The instrument discriminates (oracle − type_blind = **+54 pp**) and stays winnable.
**Anchor shift (read before comparing):** the arena's floor anchors sit far above the
overworld's (46%/69% vs 2%/1%) — recurring boss types from the small per-seed pool
raise chance-level SE, and in the arena `probe` reads *above* `type_blind`. So an
arena SE-rate is only meaningful **against the arena band** (both anchors), never
against the overworld band, and arena scores must not be spliced into overworld
tables.

## Measured — Claude Fable 5 via claude-cli (2026-07-02, user-approved quota)

**Protocol (pre-registered before data):**
`python scripts/llm_eval_run.py --provider claude-cli --arena --battle-memory
--runs 3 --worlds 3 --k-battles 10 --max-steps 120`, then a **+2-run expansion with
thresholds unchanged** (the #3/#5 precedent for a borderline 3-run read). Per-run
`se_inference_score` against that run's own arena band; verdict by
`classify_inference` (frozen: infers ≥ 0.50 pessimistic, floor ≤ 0.10 optimistic,
k = 1.0). Model id **`claude-fable-5`** confirmed from the CLI's `modelUsage`
metadata (not self-report).

| | SE-rate | wins /10 | battle moves |
|---|---|---|---|
| oracle (chart-knowing) | 100% | 10.00 | 60 |
| infer (proxy, not an LLM) | 97% | 9.33 | 58 |
| type_blind / probe (chance anchors) | 40% / 40% | 3.33 | 50 |
| **Claude Fable 5 (battle-memory)** | **48%** | — | 42–46 per run |

**Verdict:** per-run scores 0.12 ± 0.04 (3 runs) and 0.15 ± 0.02 (+2 runs); exact
moment combination (same command, seeds, deterministic band) gives
**0.132 ± 0.037 (n = 5) → INCONCLUSIVE** — and *terminally* so: with the mean at
0.132 > floor_eps 0.10, even zero variance could never satisfy the floor bound, and
infers (≥ 0.50) is far out of reach. More runs cannot change the verdict, so the
measurement closes honestly at 5 runs.

**Reading (per the interpretation rules declared before the data):**

1. **The engagement hypothesis is rejected as the main explanation.** With battles
   guaranteed (42–46 battle moves per run — comparable to the scripted arms' 50–60),
   Fable 5's SE-rate stayed ~8 pp above the chance anchors (48% vs 40%), far below
   the inferring proxy (97%). The overworld near-floor SE-rate was not primarily an
   exploration/survival artifact; the in-context inference deficit is real.
2. **But "robustly at the chart-blind floor" would also be an overclaim** — the
   above-chance margin is small yet consistent across all 5 runs (the model was seen
   reusing observed damage from its battle notes). Honest label: *a weak, consistent
   above-chance signal, far from inference*.

**Boundaries of this measurement:** one config, one 3-world seed set, claude-cli
backend, battle-memory agent, scripted-proxy band; the 5-run combination uses the
printed (2-decimal) run moments — the verdict is robust to that rounding (worst-case
bounds stay outside both thresholds).

## Boundaries (read before quoting)

- The `infer` arm is an inference *proxy*, not an LLM; one seed set; no robust
  threshold on the band itself.
- The engagement-vs-inference question is now **measured** (see above): engagement is
  not the explanation; the verdict on inference itself is a terminal INCONCLUSIVE —
  a weak, consistent above-chance signal, far from the expert.
- Diagnostic instrument ≠ leaderboard config: arena numbers are for separating failure
  modes, not for ranking submissions (a leaderboard entry runs the community season
  spec instead).
