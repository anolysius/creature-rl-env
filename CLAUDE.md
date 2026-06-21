# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project identity
**CritterGym** = a procedurally-generated **creature-collection reinforcement-learning environment**
for benchmarking long-horizon agency, strategic reasoning, and generalization.

- **Customer = AI/RL researchers and frontier labs. NOT gamers.** This is not a game-sales business.
- **The product is a benchmark/environment**, not entertainment. Art, story, juice = lowest priority.
- Business model: free + open-source env (credibility & adoption) → monetize the scarce parts
  (private held-out eval sets, custom/harder environments, consulting) or fundraise/acqui-hire.
- See `DESIGN.md` for the full spec and positioning.

## Current repo state (read this first)
**Phase 0 — nothing of the product is built yet.** There is no `src/`, no `pyproject.toml`,
no env code. What *does* exist is:
- `DESIGN.md` — the env spec (world/procgen, obs/action spaces, battle, RLVR subgoals, perf targets).
- A **ported task-lifecycle harness** under `.claude/` + `docs/harness/` (see below).
- `HARNESS-PORT-MANIFEST.md` — what was ported, what was stripped, and **8 structural couplings
  to verify before first use** (section (c)). Consult it when wiring up tooling.

The harness's tooling assumes a target layout (`src/critter_gym/`, pytest, ruff, mypy) that does
**not exist yet**. When you build Phase 1, create `src/critter_gym/{envs,spaces,wrappers}/` and a
`pyproject.toml`; the harness criticality/guard configs already point there.

## Tech stack (planned, per DESIGN.md)
- **Python**, **Gymnasium API** (single-agent; PettingZoo later if battles go multi-agent).
- Engine: **CPU/NumPy first** for correctness → **port hot path to JAX** for throughput
  (Craftax lesson: speed is the adoption gate).
- Tests: **pytest**. Lint/types: **ruff** + **mypy**. Package layout: `src/critter_gym/`.

## North-star rules
1. Every feature must serve *measuring agent capability*, not *making a fun game*.
2. Rewards are **verifiable (RLVR)** — boolean subgoal completion, not hand-tuned dense shaping.
3. Procedural generation with **train/test seed split** is non-negotiable (the moat vs.
   fixed-ROM benchmarks like Pokémon Red). `reset(seed)` must reproduce a region exactly.
4. Keep the env **fast and vectorizable**. Throughput is a first-class requirement.
5. Open-source hygiene: anything shipped is reproducible (seeded configs, pinned deps).

## Commands
The only runnable code today is the harness (pure-Python, stdlib only). **pytest is not installed**;
the harness tests are `unittest`-based:

```bash
# Run all harness lib tests (hooks + skills helpers)
python3 -m unittest discover -s .claude/hooks/_lib -p 'test_*.py'
python3 -m unittest discover -s .claude/skills/_lib -p 'test_*.py'

# A single test module / case
python3 -m unittest .claude.hooks._lib.test_git_policy
python3 -m unittest -k <pattern>

# Many harness scripts self-test or run via __main__
python3 .claude/hooks/_lib/path_match.py        # self-tests
python3 .claude/skills/task-start/scripts/detect-task-mode.py <args>
```

Once product code exists, the harness's verify step (`task-verify/scripts/run-tdd.py`) will run:
`mypy src` · `ruff check .` · `pytest -q` · `python -m build`. Confirm/adjust those in
`run-tdd.py` `COMMANDS` when you add the toolchain (HARNESS-PORT-MANIFEST §(c)2).

## Task lifecycle (how work gets done here)
This repo runs a **9-step lifecycle with 3 loops (L1/L2/L3) and 2 human gates (G1/G2)**, driven by
skills. SSOT is `.claude/rules/80-task-lifecycle.md`; conceptual docs in `docs/harness/`.

1. `/task-start "<title>"` → `docs/_active/[<initiative>/]<slug>/plan.md`
2. `/task-evaluate` — **L1** plan eval (≥2 agents in parallel, single message)
3. **G1 (DoR)** — acceptance freeze + human confirm (gate summary card)
4. `/task-loop` — **L2-outer** TDD (Red-Green-Refactor, default max 2 iters)
5. `/task-verify` — **L2-inner** + **G2 (DoD)**
6. `/task-review` — **L3** multi-reviewer consensus (must be APPROVED before task-end)
7. `/task-end` — report.md + CHANGELOG append + active→archive move
8. review + commit + push

Vocabulary: **Initiative** (multi-task group) / **Task** (1 plan + 1 report = the lifecycle atom).
**Mode tiering** (rules/80 §F): `quick-fix` (1–3 low-criticality files) / `standard` (default) /
`heavy` (50+ files or 3+ domains) auto-detected from plan scope; every mode requires a CHANGELOG entry.

## Harness mechanics that will BLOCK you
Hooks are wired in `.claude/settings.json` and enforce the rules deterministically. Key blockers:
- **`harness-task-start-guard.py`** (PreToolUse Write|Edit): editing **`src/**` or `tests/**`
  without a frozen plan (`acceptance_freeze: true` covering the path) is **BLOCKED**. Auto-passes:
  non-product paths (`.claude/**`, `docs/**`), and trivial single-line edits. Override:
  `HARNESS_SKIP_HARNESS=1`.
- **`git-policy-guard.py`** (PreToolUse Bash): enforces rules/85 trunk model — work on
  `feature|fix|hotfix|chore|docs/*` → PR → `main`. **Never commit/push on `main`; branch first.**
  The `qa/*` one-way sink is OPTIONAL (sink is empty by default). Override: `HARNESS_GIT_POLICY_OVERRIDE=1`.
- **`task-end-archive-guard.py`** — guards the active→archive move ordering.
- **Agent worktree guards** — an `isolation: worktree` agent must be reconciled (recover/discard)
  in the same turn or the Stop hook blocks session end. Override: `HARNESS_ALLOW_AGENT_WT_LEAK=1`.
- `HARNESS_HOOKS_STRICT=0` (default) → violations warn; `=1` → block. Commit/push **only when asked**;
  co-author trailer per harness.

Some rules (archive-ref invariant, domain frontmatter, session metrics) are currently **advisory** —
their enforcing hooks were not ported (HARNESS-PORT-MANIFEST §(c)7). The rule text says
"if configured."

## Configs worth knowing
- `.claude/data/path-criticality.json` — critical/low path globs → drives mode tiering. Tune to real layout.
- `.claude/data/git-branch-prefixes.json` — branch-prefix whitelist (source/sink/trunk).
- `.claude/agents/` — only two reviewer agents ship: `plan-reviewer` (L1/L3) + `qa-verifier`
  (cheap, read-only, verdict-only).
