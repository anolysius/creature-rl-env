#!/usr/bin/env python3
# domain: lifecycle
"""task-verify TDD wrapper — type_check / lint / unit_tests / build 실행 (Python).

사용:
    python3 run-tdd.py --acceptance type_check,lint,unit_tests
    python3 run-tdd.py --plan docs/_active/<slug>/plan.md

출력 (stdout, JSON):
    {"results": {"type_check": "pass", "lint": "fail", ...}, "details": {...}}

명령은 mypy / ruff / pytest 기반 (COMMANDS). 도구 미설치 시 result=fail +
"command not found" — 프로젝트 도구 변경 시 COMMANDS 만 수정.
"""
import sys
import io
import os
import json
import argparse
import subprocess
import re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent.parent.parent.parent  # repo root


# Acceptance ID → 명령 매핑 (Python 툴체인)
COMMANDS = {
    "type_check": ["mypy", "src"],
    "lint": ["ruff", "check", "."],
    "unit_tests": ["python3", "-m", "pytest", "-q"],
    "build": ["python3", "-m", "build"],
}


def run_command(cmd: list, timeout: int = 600) -> dict:
    """명령 실행 후 result dict 반환."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "exit": proc.returncode,
            "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-2000:] if proc.stderr else "",
            "result": "pass" if proc.returncode == 0 else "fail",
        }
    except subprocess.TimeoutExpired:
        return {
            "exit": -1,
            "result": "fail",
            "error": f"timeout after {timeout}s",
        }
    except FileNotFoundError as e:
        return {
            "exit": -1,
            "result": "fail",
            "error": f"command not found: {e}",
        }


def parse_plan_acceptance(plan_path: Path) -> list:
    """plan.md frontmatter 에서 lifecycle acceptance 추출."""
    if not plan_path.exists():
        return []
    text = plan_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    if end < 0:
        return []
    fm = text[:end]
    # acceptance.lifecycle: 안의 항목 추출 (간이)
    in_lifecycle = False
    items = []
    for line in fm.splitlines():
        if re.match(r"^\s*lifecycle\s*:", line):
            in_lifecycle = True
            continue
        if in_lifecycle:
            if re.match(r"^\s+-\s+", line):
                item = re.sub(r"^\s+-\s+", "", line).strip().strip('"\'')
                items.append(item)
            elif re.match(r"^\s*\w+\s*:", line) and not line.startswith("    -"):
                in_lifecycle = False  # next domain
    return items


def detect_acceptance_ids(items: list) -> list:
    """plan acceptance 항목에서 known ID 패턴 매칭."""
    ids = []
    for item in items:
        item_lower = item.lower()
        for cmd_id in COMMANDS:
            if cmd_id in item_lower or cmd_id.replace("_", " ") in item_lower or cmd_id.replace("_", "-") in item_lower:
                if cmd_id not in ids:
                    ids.append(cmd_id)
    return ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--acceptance", type=str, default=None,
                        help="콤마 구분 ID (type_check,lint,...). 미지정 시 plan 자동 추출")
    parser.add_argument("--plan", type=Path, default=None, help="plan.md 경로")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # 1) 실행할 acceptance ID 결정
    if args.acceptance:
        ids = [x.strip() for x in args.acceptance.split(",") if x.strip()]
    elif args.plan:
        items = parse_plan_acceptance(args.plan)
        ids = detect_acceptance_ids(items)
        if not ids:
            ids = ["type_check"]  # safe default
    else:
        # default: 핵심만 (type_check + lint)
        ids = ["type_check", "lint"]

    # 2) 검증
    valid_ids = [i for i in ids if i in COMMANDS]
    invalid = [i for i in ids if i not in COMMANDS]

    if args.dry_run:
        print(json.dumps({
            "would_run": valid_ids,
            "ignored_unknown": invalid,
            "commands": {i: COMMANDS[i] for i in valid_ids},
        }, ensure_ascii=False, indent=2))
        return

    # 3) 실행
    results = {}
    details = {}
    for acceptance_id in valid_ids:
        cmd = COMMANDS[acceptance_id]
        info = run_command(cmd, timeout=args.timeout)
        results[acceptance_id] = info["result"]
        details[acceptance_id] = info

    # 4) summary
    summary = {
        "results": results,
        "all_passed": all(r == "pass" for r in results.values()),
        "failed": [k for k, v in results.items() if v != "pass"],
        "details": details,
        "ignored_unknown": invalid,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
