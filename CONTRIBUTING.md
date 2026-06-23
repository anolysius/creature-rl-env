# Contributing to CritterGym

CritterGym is a **benchmark/instrument**, not a game — every change should serve *measuring
agent capability*, keep rewards **verifiable** (RLVR / boolean subgoals), preserve the
**procgen train/test seed split**, and keep the core **fast and numpy-only**. See
[`DESIGN.md`](DESIGN.md) and [`CLAUDE.md`](CLAUDE.md) for the full north-star rules.

## Dev setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # ruff + mypy + pytest + build
# optional heavy extras: ".[rl]" (PPO), ".[viz]" (plots), ".[render]" (GIF)
```

## Checks (must pass before a PR)

```bash
pytest -q          # full suite (numpy-only core; [rl] tests importorskip-gated)
mypy src
ruff check .
python -m build
```

Keep the core dependency-light: heavy learning deps (torch / stable-baselines3 / matplotlib /
imageio) stay behind extras so the core CI runs numpy-only.

## Honesty discipline (the project's asset)

- Report results as **signals with caveats**, never as tuned headline numbers or proofs.
- Distinguish **CI-reproducible** figures (frozen by a test gate/assertion) from **run-derived**
  means. Don't present a run mean as if a test froze it.
- Keep the scope honest per [`DESIGN.md`](DESIGN.md) §3.1.1: instance generalization (A) is
  measured; genre generalization (B) is a *foundation*, not a proof. Pokémon is a metaphor, not
  a competitive claim.

## Task lifecycle

Work flows through a plan → evaluate → freeze → TDD → review → end lifecycle (SSOT:
`.claude/rules/80-task-lifecycle.md`). Branch from `main` (`feature/*`, `fix/*`, `docs/*`) and
open a PR; never commit directly to `main`. Every task appends one line to
[`docs/CHANGELOG.md`](docs/CHANGELOG.md).
