# CLAUDE.md — CritterGym

## Project identity
**CritterGym** = a procedurally-generated **creature-collection reinforcement-learning environment**
for benchmarking long-horizon agency, strategic reasoning, and generalization.

- **Customer = AI/RL researchers and frontier labs. NOT gamers.** This is not a game-sales business.
- **The product is a benchmark/environment**, not entertainment. Art, story, juice = lowest priority.
- Business model: free + open-source env (credibility & adoption) → monetize the scarce parts
  (private held-out eval sets, custom/harder environments, consulting) or fundraise/acqui-hire.
- See `DESIGN.md` for the full spec and positioning.

## Tech stack
- **Python**. RL ecosystem standard.
- **Gymnasium API** (single-agent; PettingZoo later if battles go multi-agent).
- Engine: **CPU/NumPy first** for correctness → **port hot path to JAX** for throughput
  (Craftax lesson: speed is the adoption gate).
- Tests: **pytest**. Lint/types: **ruff** + **mypy**. Package layout: `src/critter_gym/`.

## North-star rules
1. Every feature must serve *measuring agent capability*, not *making a fun game*.
2. Rewards are **verifiable (RLVR)** — boolean subgoal completion, not hand-tuned dense shaping.
3. Procedural generation with **train/test seed split** is non-negotiable (it's the whole moat
   vs. fixed-ROM benchmarks like Pokémon Red).
4. Keep the env **fast and vectorizable**. Throughput is a first-class requirement.
5. Open-source hygiene: anything shipped is reproducible (seeded configs, pinned deps).

## Task lifecycle (ported harness)
Standard flow — see `.claude/rules/80-task-lifecycle.md` and `docs/harness/`:
1. `/task-start "<title>"` — creates `docs/_active/<slug>/plan.md`
2. `/task-evaluate` — **L1** plan eval (≥2 agents parallel)
3. **G1 (DoR)** — acceptance freeze + confirm
4. `/task-loop` — **L2-outer** TDD (Red-Green-Refactor, max ~5)
5. `/task-verify` — **L2-inner** + **G2 (DoD)**
6. `/task-review` — **L3** multi-reviewer consensus
7. `/task-end` — report.md + CHANGELOG append + active→archive
8. review + commit + push

Vocabulary: **Initiative** (multi-task group) / **Task** (1 plan + 1 report, the lifecycle atom).
Git: branch before implementing; never work on the default branch.

## Git policy
See `.claude/rules/85-git-policy.md`. Commit/push only when asked. Co-author trailer per harness.
