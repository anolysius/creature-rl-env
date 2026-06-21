#!/usr/bin/env python3
"""
detect-task-type — plan.md 의 frontmatter 분석 후 task_type 라벨 출력.

사용:
    python3 detect-task-type.py docs/_active/[<initiative>/]<slug>/plan.md

출력 (stdout JSON):
    {"task_type": "env|harness|general", "matched_pattern": "..."}

매칭 룰 (우선순위 순):
    1. scope_paths 에 \\.claude/(hooks|skills|agents|rules)/.* → harness
    2. scope_paths 에 src/.*/(envs|spaces|wrappers|registration)\\b → env
    3. else → general

frontmatter 의 `task_type:` manual override:
    명시되어 있으면 자동 감지 무시 + override 안내 stderr.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

RULES = [
    # (priority, label, rule_fn)
    # rule_fn(domains: list[str], scope_paths: list[str]) -> matched_pattern str | None
    # 우선순위: harness (.claude/*) > env (envs/spaces/wrappers) > general
    (
        "harness",
        lambda domains, paths: next(
            (
                p
                for p in paths
                if re.match(
                    r"\.claude/(hooks|skills|agents|rules)/.*",
                    p,
                )
            ),
            None,
        ),
    ),
    (
        "env",
        lambda domains, paths: next(
            (
                p
                for p in paths
                if re.search(
                    r"(^|/)(envs|spaces|wrappers)(/|$)|registration\.py$",
                    p,
                )
            ),
            None,
        ),
    ),
]


def parse_frontmatter(content: str) -> dict | None:
    """단순 YAML frontmatter parser (--- ... ---)."""
    m = re.match(r"---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return None
    fm_text = m.group(1)
    result: dict = {}
    current_key: str | None = None
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_key:
                result.setdefault(current_key, []).append(line[4:].strip())
        elif ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val:
                result[key] = val
                current_key = None
            else:
                current_key = key
                result[key] = []
    return result


def detect(plan_path: str) -> dict:
    if not os.path.exists(plan_path):
        return {"task_type": "general", "matched_pattern": None, "error": "plan.md not found"}

    with open(plan_path, encoding="utf-8") as f:
        content = f.read()

    fm = parse_frontmatter(content)
    if fm is None:
        return {"task_type": "general", "matched_pattern": None, "error": "frontmatter not found"}

    # manual override
    manual = fm.get("task_type")
    if isinstance(manual, str) and manual.strip():
        return {
            "task_type": manual.strip(),
            "matched_pattern": "manual override (frontmatter task_type)",
        }

    domains = fm.get("domains", []) or []
    scope_paths = fm.get("scope_paths", []) or []

    for label, rule_fn in RULES:
        matched = rule_fn(domains, scope_paths)
        if matched:
            return {"task_type": label, "matched_pattern": matched}

    return {"task_type": "general", "matched_pattern": None}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: detect-task-type.py <plan.md path>", file=sys.stderr)
        return 2
    result = detect(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
