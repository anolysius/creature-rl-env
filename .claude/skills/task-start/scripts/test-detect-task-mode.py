#!/usr/bin/env python3
"""
detect-task-mode.py 의 7 fixture + aggregate-verdicts.py 통합 1 fixture.

Acceptance A1 + A9 검증 — harness-mode-tiering task.

usage:
    python3 test-detect-task-mode.py
    python3 test-detect-task-mode.py --include-aggregator
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
_spec = importlib.util.spec_from_file_location("detect_task_mode", SCRIPT_DIR / "detect-task-mode.py")
_module = importlib.util.module_from_spec(_spec)  # type: ignore
_spec.loader.exec_module(_module)  # type: ignore
detect_mode = _module.detect_mode


def write_plan(tmpdir: Path, frontmatter_yaml: str) -> Path:
    """fixture plan.md 생성."""
    plan = tmpdir / "plan.md"
    plan.write_text(f"---\n{frontmatter_yaml}---\n\n# fixture plan\n")
    return plan


FIXTURES = [
    # 1. quick-fix — 1 docs file
    (
        "quick-fix: 1 docs file",
        """slug: x
domains: [lifecycle]
scope_paths:
  - docs/explanation/foo.md
""",
        "quick-fix",
    ),
    # 2. quick-fix — 3 test files
    (
        "quick-fix: 3 test files",
        """slug: x
domains: [lifecycle]
scope_paths:
  - tests/test_foo.py
  - tests/test_bar.py
  - tests/test_baz.py
""",
        "quick-fix",
    ),
    # 3. standard — 8 mixed medium files
    (
        "standard: 8 mixed medium files",
        """slug: x
domains: [rl-env]
scope_paths:
  - src/critter_gym/render/foo.py
  - src/critter_gym/render/bar.py
  - src/critter_gym/utils/page.py
  - src/critter_gym/utils/layout.py
  - src/critter_gym/agents/baz.py
  - src/critter_gym/agents/qux.py
  - src/critter_gym/io/foo.py
  - src/critter_gym/io/bar.py
""",
        "standard",
    ),
    # 4. standard — 1 critical env file (critical, file count irrelevant)
    (
        "standard: 1 critical env file",
        """slug: x
domains: [rl-env]
scope_paths:
  - src/critter_gym/envs/critter_env.py
""",
        "standard",
    ),
    # 5. heavy — 60 files cross-vertical
    (
        "heavy: 60 files",
        "slug: x\ndomains: [rl-env]\nscope_paths:\n"
        + "".join(f"  - src/critter_gym/render/x{i}.py\n" for i in range(60)),
        "heavy",
    ),
    # 6. heavy — 10 files + 4 domains (multi-vertical)
    (
        "heavy: 4 domains",
        """slug: x
domains: [rl-env, render, agents, perf]
scope_paths:
  - src/critter_gym/render/a.py
  - src/critter_gym/render/b.py
  - src/critter_gym/render/c.py
  - src/critter_gym/render/d.py
  - src/critter_gym/render/e.py
  - src/critter_gym/render/f.py
  - src/critter_gym/render/g.py
  - src/critter_gym/render/h.py
  - src/critter_gym/render/i.py
  - src/critter_gym/render/j.py
""",
        "heavy",
    ),
    # 7. manual override — 1 docs file but mode: standard
    (
        "manual override: docs file forced to standard",
        """slug: x
mode: standard
domains: [lifecycle]
scope_paths:
  - docs/foo.md
""",
        "standard",
    ),
]


def run_fixtures() -> tuple[int, int]:
    passed = 0
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for name, fm_yaml, expected in FIXTURES:
            plan_path = write_plan(tmpdir, fm_yaml)
            result = detect_mode(plan_path)
            actual = result["mode"]
            if actual == expected:
                print(f"✓ PASS: {name} → {actual} ({result['reason']})")
                passed += 1
            else:
                print(f"✗ FAIL: {name} → expected {expected}, got {actual}")
                print(f"  result: {json.dumps(result, ensure_ascii=False)}")
                failed += 1
    return passed, failed


def run_aggregator_integration() -> tuple[int, int]:
    """A9 — quick-fix mode + single APPROVE → aggregator 통과 (≥2 reviewer 강제 우회).

    검증 채널:
    1. route-evaluators.py 가 quick-fix plan 받으면 ['@qa-verifier'] (1개) 반환
    2. aggregate-verdicts.py 가 single APPROVE verdict 받아도 APPROVED decision 반환
       (decision 계산 자체엔 mode 무관 — N agent 무차별 처리)
    """
    import subprocess

    aggregator = REPO_ROOT / ".claude/skills/task-evaluate/scripts/aggregate-verdicts.py"
    router = REPO_ROOT / ".claude/skills/task-evaluate/scripts/route-evaluators.py"
    if not aggregator.is_file() or not router.is_file():
        print("⚠ SKIP: aggregator/router 미존재 (Step 3 진행 후 활성)")
        return 0, 0

    passed = 0
    failed = 0

    with tempfile.TemporaryDirectory() as tmp:
        plan = Path(tmp) / "plan.md"
        plan.write_text(
            "---\nslug: x\nmode: quick-fix\ndomains: [lifecycle]\n"
            "scope_paths:\n  - docs/foo.md\n---\n"
        )

        # 1. router → quick-fix 시 [@qa-verifier] (1개) 반환
        r = subprocess.run(["python3", str(router), str(plan)], capture_output=True, text=True)
        try:
            d = json.loads(r.stdout)
            if d.get("mode") == "quick-fix" and d.get("agents") == ["@qa-verifier"]:
                print("✓ PASS: router quick-fix → [@qa-verifier] only")
                passed += 1
            else:
                print(f"✗ FAIL: router quick-fix expected [@qa-verifier], got {d.get('agents')}")
                failed += 1
        except Exception as e:
            print(f"✗ FAIL: router output parse error: {e}")
            failed += 1

        # 2. aggregator → single APPROVE → APPROVED decision
        r = subprocess.run(
            ["python3", str(aggregator)],
            input="APPROVE\n", capture_output=True, text=True,
        )
        try:
            d = json.loads(r.stdout)
            if d.get("decision") == "APPROVED":
                print(f"✓ PASS: aggregator single APPROVE → APPROVED ({d.get('decision')})")
                passed += 1
            else:
                print(f"✗ FAIL: aggregator single APPROVE expected APPROVED, got {d.get('decision')}")
                failed += 1
        except Exception as e:
            print(f"✗ FAIL: aggregator output parse error: {e}")
            failed += 1

    return passed, failed


REPO_ROOT = SCRIPT_DIR.resolve().parents[3]


def main() -> int:
    print("=== detect-task-mode 7 fixture ===")
    passed, failed = run_fixtures()
    total = passed + failed

    if "--include-aggregator" in sys.argv:
        print("\n=== aggregator 통합 fixture (A9) ===")
        agg_p, agg_f = run_aggregator_integration()
        passed += agg_p
        failed += agg_f
        total = passed + failed

    print(f"\n{passed}/{total} PASS")
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
