# CritterGym

> A procedurally-generated **creature-collection reinforcement-learning environment** for
> benchmarking long-horizon agency, strategic reasoning, and generalization — in one fast,
> headless, Gymnasium-compatible package.

**Status:** Phase 0 — design & validation. Nothing built yet. See [`DESIGN.md`](./DESIGN.md).

## Why
Existing game-based RL benchmarks force a trade-off: Pokémon Red is long-horizon but a fixed ROM
(no generalization); Crafter/Craftax generalize and are fast but short-to-medium horizon; Procgen
nails generalization but is shallow; NetHack is a brutal but opaque frontier. CritterGym targets
the empty cell: **procedural generation (→ generalization) + long horizon + strategic adversarial
play (type-matchup meta) + verifiable subgoal rewards (RLVR-friendly)**.

## Positioning
*Procgen's generalization rigor × Pokémon's long horizon × Crafter's one-env-many-skills ×
Craftax's JAX speed.*

## Roadmap
- **Phase 0 (now):** design doc → community feedback ("would you use it?")
- **Phase 1:** dumbest-possible env (Gymnasium) → full subgoal chain + procgen
- **Phase 2:** baselines + leaderboard + arXiv writeup; open-source (MIT); list on Prime Intellect Hub
- **Phase 3:** held-out eval sets / custom envs / fundraise

## License
MIT (planned).
