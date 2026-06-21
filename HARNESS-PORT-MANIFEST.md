# Task-Lifecycle Harness Port — Manifest

Ported the **generic** task-lifecycle harness (9-step / L1·L2·L3 + G1·G2, multi-reviewer
evaluation, mode tiering, prompt-cache helpers, verdict aggregation, gate cards, self-retro)
from `sazo-ko-client-web` into `creature-rl-env` (CritterGym). All design-system (DS),
commerce, i18n, Tailwind, web/Next.js subject matter was stripped or adapted to the
Python / Gymnasium RL-environment domain.

All ported logic is verified: **13/13 Python test suites pass**, all scripts parse, all
hooks run without crashing, no copied module imports an uncopied module.

---

## (a) Files copied

### Skills (whole dirs, `SKILL.md` + `scripts/`)
| Target path | Notes |
|---|---|
| `.claude/skills/task-start/` | SKILL.md adapted; `scripts/detect-task-type.py` rewritten (env/harness/general), `detect-task-mode.py` + test adapted to RL paths |
| `.claude/skills/task-evaluate/` | SKILL.md adapted; `route-evaluators.py` genericized (self-adapting auditor routing), `aggregate-verdicts.py` unchanged |
| `.claude/skills/task-loop/` | SKILL.md adapted (TDD-guard softened to optional) |
| `.claude/skills/task-verify/` | SKILL.md adapted; `run-tdd.py` retargeted to mypy/ruff/pytest; `auto-fix.py` rewritten for ruff; `run-browser-check.py` genericized (optional web check) |
| `.claude/skills/task-review/` | SKILL.md adapted; `detect-review-profile.py` `PROFILE_REVIEWERS` → plan-reviewer/qa-verifier |
| `.claude/skills/task-end/` | SKILL.md adapted; `collect-token-usage.py` output path genericized; `collect-rules80-metrics.py` comment softened |
| `.claude/skills/_lib/` | `reviewer_prompt.py` rewritten (ds-reviewer/ds-auditor → plan-reviewer L1/L3); `verdict_equivalence.py`, `corpus.json` genericized; `gate_summary_card.py`, `qa_verifier_prompt.py`, `retro_proposals.py` clean (copied as-is) |

### Agents
- `.claude/agents/plan-reviewer.md` — DS axes → generic plan-quality axes
- `.claude/agents/qa-verifier.md` — DS examples → RL examples

### Rules
- `.claude/rules/80-task-lifecycle.md` — generic lifecycle kept; DS verticals/hooks/rules-refs adapted
- `.claude/rules/85-git-policy.md` — reframed: trunk (main) primary, `qa/*` sink now OPTIONAL
- `.claude/rules/_ownership.md` — responsibility map reduced to 80/85/_ownership

### Commands
- `.claude/commands/task-start.md`, `.claude/commands/task-end.md` — thin stubs pointing to skills (no DS content)

### Hooks (Python) — the 8 generic harness hooks + tests
- `agent-worktree-return-handler.py`, `agent-worktree-stop-guard.py`
- `git-policy-guard.py`, `harness-commit-guard.py`, `harness-commit-intent-record.py`
- `harness-task-intent-nudge.py`, `harness-task-start-guard.py`
- `task-end-archive-guard.py`, `test_task_end_archive_guard.py`

### Hooks `_lib` (only modules referenced by copied hooks, + their tests)
- `__init__.py`, `active_plan_scope.py` (+test), `commit_intent.py` (+test),
  `git_policy.py` (+test), `path_match.py`, `worktree_safety.py` (+test)
- (path_match has no separate test file in source; it self-tests via `__main__`)

### Data files (generic infrastructure — created/genericized, NOT DS token files)
- `.claude/data/git-branch-prefixes.json` — **created** (genericized: empty sink, no `qa`)
- `.claude/data/path-criticality.json` — **created** (genericized: CritterGym `src/` paths)
- `.claude/data/path-criticality.schema.json` — copied as-is (generic)

### Docs
- `docs/harness/explanation/{task-lifecycle, process-diagram, git-branching-model, master-plan, layer-architecture, cross-vertical-scenarios}.md`
- `docs/harness/how-to/{onboarding, verdict-equivalence, measure-token-usage}.md`

### Lifecycle path scaffolding (created)
- `docs/_active/.gitkeep`, `docs/_archive/.gitkeep`, `docs/CHANGELOG.md` (empty header)

### Settings
- `.claude/settings.json` — **new trimmed file** (see section (d))

---

## (b) DS references stripped / adapted (by category)

**Environment-variable rename (all copied python + rules + docs):** `SAZO_*` override
toggles → `HARNESS_*` (`HARNESS_SKIP_HARNESS`, `HARNESS_GIT_POLICY_OVERRIDE`,
`HARNESS_ALLOW_COMMIT`, `HARNESS_ARCHIVE_GUARD_OVERRIDE`, `HARNESS_ALLOW_AGENT_WT_LEAK`,
`HARNESS_WT_AUTO_DISCARD_DISABLE`). Hook logic preserved; only the toggle names changed.

**Reviewer agents:** all `@ds-reviewer` / `@ds-auditor` / `@ds-migrator` / `@ds-guardian`
references → `@plan-reviewer` / `@qa-verifier` (the only two agents shipped). `reviewer_prompt.py`
`VALID_AGENTS` reduced to `("plan-reviewer", "qa-verifier")`; the `ds-reviewer L3` and
`ds-auditor L1` prompt templates were replaced with a generic `plan-reviewer L3` (code-review)
template; `detect-review-profile.py` `PROFILE_REVIEWERS` all map to plan-reviewer+qa-verifier.

**Vertical domain enum:** `ds` / `i18n` / `business.*` / `security` → `rl-env` / `render` /
`agents` / `perf` (in rules/80 §B.7, route-evaluators, reviewer_prompt SHARED_GUIDELINES,
detect-task-mode/type, and all docs). `lifecycle` and `qa` kept (generic).

**DS machinery removed/genericized:** design tokens / primitive→semantic / hex / Tailwind /
Pretendard / component inventory & specs / 8-axis DS audit / `tokens.css` / `_theme.css` /
`sazo-components` / i18n Sheets pipeline / qa-deploy / `qa/kr`,`qa/global` / swagger / `sazo.kr`.

**Per-file specifics (scripts):**
- `task-verify/scripts/run-tdd.py` — `COMMANDS` was `pnpm check-types/lint/test/build-*:qa` → `mypy src` / `ruff check .` / `pytest -q` / `python -m build`.
- `task-verify/scripts/auto-fix.py` — was hex→token / primitive→semantic / eslint / prettier (calling `tokenize-migrate.mjs`); **fully rewritten** to ruff `format` + `lint_fix` whitelist with trailing-whitespace detector.
- `task-verify/scripts/run-browser-check.py` — sazo.kr / `:3100` / `/cart` defaults removed; baseline/local now neutral localhost; key off `affects_ui` only (no `apps/` heuristic).
- `task-start/scripts/detect-task-type.py` — `screen` (page.tsx) / `i18n-migration` rules removed → `env` (envs/spaces/wrappers/registration) + `harness`.
- `task-start/scripts/detect-task-mode.py` + `test-detect-task-mode.py` — fixtures retargeted to `src/critter_gym/...` Python paths; criticality table genericized.
- `task-evaluate/scripts/route-evaluators.py` — docstring/comments genericized; routing logic was already self-adapting (only adds `@<domain>-auditor` if the agent file exists).
- `task-end/scripts/collect-token-usage.py` — default output path `docs/_active/ds-harness/...` → `docs/_artifacts/token-usage-actuals.json`.

**Per-file specifics (_lib):**
- `hooks/_lib/active_plan_scope.py` — **STRUCTURAL**: `_TARGET_PREFIXES` was `("apps/","packages/")` → `("src/",)` (else the bypass guard would never fire). Test fixtures retargeted to `src/critter_gym/...`.
- `hooks/_lib/git_policy.py`, `path_match.py`, `__init__.py`, `worktree_safety.py` — docstring/comment DS examples genericized.
- `hooks/_lib/test_git_policy.py` — `qa/*` sink **kept as a self-contained test fixture** (verifies the sink mechanism even though the live config sink is empty); commerce branch names + the SAZO incident comment removed; documented in the test docstring.
- `skills/_lib/reviewer_prompt.py` + `test_reviewer_prompt.py` — see "Reviewer agents".
- `skills/_lib/verdict_equivalence.py` + `corpus.json` + `test_verdict_equivalence.py` — golden known-issue fixtures (primitive/hex/font violations) → RL violations (nondeterministic reset, observation-space dtype change, non-SMART acceptance); reviewers → plan-reviewer/qa-verifier.

**Docs** (master-plan, cross-vertical-scenarios, layer-architecture, task-lifecycle,
process-diagram, git-branching-model, onboarding, verdict-equivalence, measure-token-usage):
SAZO product identity → CritterGym; DS/i18n/commerce running examples → RL examples; pnpm/Next.js
commands → Python (pytest/ruff/mypy, `src/`, `tests/`); removed links to uncopied files
(`.claude/context/`, `design_docs/`, `packages/`, ds-* skills, `ds-token-override.md`, `qa-deploy.md`).

---

## (c) STRUCTURAL couplings needing human review

1. **`auto-fix.py` rewrite (verify).** The original was a thin wrapper over a Node
   `tokenize-migrate.mjs` + eslint/prettier. It was fully rewritten to call `ruff format` /
   `ruff check --fix` (best-effort; fails soft if ruff absent). **Confirm ruff is your intended
   formatter/linter** and add it to dev deps. If you use black/isort instead, edit `WHITELIST_FIXES`.

2. **`run-tdd.py` `COMMANDS` (verify).** Now `mypy src` / `ruff check .` / `pytest -q` /
   `python -m build`. **Confirm these match your project layout** (e.g. `mypy src` assumes a `src/`
   layout; pytest assumes default discovery). Edit `COMMANDS` if your toolchain differs.

3. **`active_plan_scope._TARGET_PREFIXES = ("src/",)` (verify).** The harness-bypass guard
   (`harness-task-start-guard.py`) only fires on edits under `src/`. If your product code lives
   elsewhere (e.g. a flat package or `critter_gym/` at repo root), update this tuple or the guard
   won't protect those paths.

4. **`path-criticality.json` glob lists (tune).** Genericized to `src/critter_gym/{envs,spaces,
   wrappers}/**`, `registration.py`, `pyproject.toml`, `scripts/**` as *critical*; docs/tests/md as
   *low*. These drive mode-tiering (quick-fix/standard/heavy). Tune to your real layout.

5. **`git-branch-prefixes.json` sink is empty + rules/85 reframed (decide).** The shipped git
   model is trunk-based (`feature/fix/hotfix/chore/docs → PR → main`). The `qa/*` one-way-sink is
   documented as an OPTIONAL pattern. The `git_policy` engine + `test_git_policy.py` still fully
   support a sink (the test uses a `qa` fixture). **If you never add an integration branch, the
   sink half of rules/85 / git-branching-model.md is inert** (harmless). If you do, add `"qa"` to
   the `sink` array.

6. **Local git hooks NOT ported.** `scripts/githooks/{pre-push,pre-commit,pre-merge-commit,
   install.sh}` were out of the copy scope. rules/85 + git-branching-model.md mark them
   "(optional, not included)". Only the Claude Code PreToolUse `git-policy-guard.py` enforces the
   branch policy. If you want human-run-git enforcement, port those scripts separately.

7. **Rule-intent hooks referenced as "if configured".** rules/80 §A.12 (archive-ref invariant),
   §B.7 (domain frontmatter), §D (session metrics) originally pointed to `ds-archive-ref-check.py`
   / `ds-frontmatter-domain-check.py` / `ds-broken-link-check.py` / `ds-session-report.py`, which
   were **not** ported. The rule TEXT is kept but softened to "(enforced by a project-specific
   PostToolUse/Stop hook, if configured)". **These rules are currently advisory — no hook enforces
   them.** Author those hooks if you want enforcement.

8. **TDD guard is advisory.** task-loop / task-verify SKILL.md reference an optional `tdd-guard`
   that is not wired here. TDD is encouraged but not hook-enforced.

---

## (d) Final settings.json hook wiring

`env`: `HARNESS_HOOKS_DEBUG=0`, `HARNESS_HOOKS_STRICT=0`, `PYTHONIOENCODING=utf-8`.

| Event | Matcher | Hooks |
|---|---|---|
| UserPromptSubmit | (all) | `harness-task-intent-nudge.py`, `harness-commit-intent-record.py` |
| PreToolUse | `Write\|Edit` | `harness-task-start-guard.py` |
| PreToolUse | `Bash` | `git-policy-guard.py`, `task-end-archive-guard.py`, `harness-commit-guard.py` |
| PostToolUse | `Agent` | `agent-worktree-return-handler.py` |
| Stop | (all) | `agent-worktree-stop-guard.py` |

All 8 referenced hook paths exist (verified). **Dropped** from source settings: all
`ds-*` hooks (session-snapshot/report, context-router, token-guard, primitive-check,
accessibility-check, migration-warn, archive-ref, broken-link, button-slot, svg-raw,
component-duplicate, spec-validator, inventory-refresh, frontmatter-domain, component-reuse,
compact-preserve), all `a11y-*`, all `i18n-*`. **Dropped** from `permissions.deny`: all
rules referencing DS/token/design_docs/i18n-locale files. `permissions.allow` adapted from
pnpm/Tailwind to Python (pytest/ruff/mypy) and `Edit/Write` scoped to `src/`,`tests/`,`docs/`.
Generic safety denies kept (`rm -rf`, force-push, `reset --hard`).

---

## (e) Residual grep hits (after adaptation)

A sweep for `design_docs|sazo-components|tailwind|i18n|swagger|SAZO_|sazo.kr|pnpm|brand-N|
tokens.css|packages/sazo|디자인 시스템|ds-(reviewer|auditor|...)` over `.claude/` + `docs/`
returns **only 2 intentional meta-references**:

1. `.claude/settings.json:117` `$description` — sentence stating "DS/a11y/i18n/token hooks
   intentionally absent" (documents the exclusion).
2. `.claude/rules/85-git-policy.md:175` change-history row — records the port adaptation,
   intentionally naming the old `SAZO_GIT_POLICY_OVERRIDE` → `HARNESS_GIT_POLICY_OVERRIDE` rename.

**Intentional non-DS fixtures retained** (documented, not couplings):
- `test_git_policy.py` — `qa/global`,`qa/kr` as sink-mechanism test fixtures.
- `test_worktree_safety.py` — `.tsx` filenames as generic file-path fixtures for the temp-file
  classifier (any extension works; these exercise the "real prototype" narrowing case).
- `detect-review-profile.py` `CODE_STYLE_EXTS` — still lists web extensions; harmless because all
  profiles route to the same two reviewers (a `.py` change routes via `code`/`harness-tooling`).
