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

## Boundaries (read before quoting)

- Scripted arms only so far (the `infer` arm is an inference *proxy*, not an LLM);
  one seed set; no robust threshold on the band itself.
- The real-LLM arena measurement is **not done in this task** — it costs quota and is
  gated on user approval. Until then, the engagement-vs-inference question is
  *instrumented*, not *answered*.
- Diagnostic instrument ≠ leaderboard config: arena numbers are for separating failure
  modes, not for ranking submissions.
