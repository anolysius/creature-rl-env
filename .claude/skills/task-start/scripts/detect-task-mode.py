#!/usr/bin/env python3
"""
Harness mode tiering — deterministic mode 감지.

rules/80 §F 의 SSOT 구현. plan.md 의 frontmatter 의 `scope_paths` + `domains`
+ 명시 `mode` 를 읽어 quick-fix / standard / heavy 분류.

분기 룰 (priority 순, rules/80 §F.2 SSOT):
1. plan frontmatter `mode:` 명시 → 자동 감지 무시 (manual override)
2. 어떤 scope_paths 가 critical 매칭 + file_count >= 50 → heavy
3. 어떤 scope_paths 가 critical 매칭 → standard (file_count 무관, 회귀 위험 우선)
4. file_count >= 50 OR domains_count >= 3 → heavy
5. file_count <= 3 + 모든 path 가 low 매칭 → quick-fix
6. else → standard (default)

usage:
    python3 detect-task-mode.py <plan.md path>
    -> JSON {mode, reason, file_count, domains_count, max_criticality, manual_override}
"""

from __future__ import annotations

import json
import re
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
CRITICALITY_TABLE = REPO_ROOT / ".claude/data/path-criticality.json"


def load_criticality_table() -> dict[str, list[str]]:
    """`.claude/data/path-criticality.json` SSOT 로드."""
    with CRITICALITY_TABLE.open() as f:
        data = json.load(f)
    return {
        "critical": data.get("critical", []),
        "low": data.get("low", []),
    }


def parse_frontmatter(plan_path: Path) -> dict[str, Any]:
    """plan.md 의 YAML frontmatter (`--- ... ---`) 파싱.

    YAML 파서 의존 없이 단순 line-by-line — list, scalar 만 지원.
    """
    text = plan_path.read_text()
    if not text.startswith("---"):
        return {}

    end = text.find("\n---", 3)
    if end < 0:
        return {}

    fm_text = text[3:end].strip()
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in fm_text.split("\n"):
        if not line.strip() or line.strip().startswith("#"):
            continue

        # list item
        m = re.match(r"^\s+-\s+(.+)$", line)
        if m and current_list is not None:
            current_list.append(m.group(1).strip())
            continue

        # key: value 또는 key: (list start)
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$", line)
        if m:
            current_key = m.group(1)
            value = m.group(2).strip()
            if not value:
                # list start
                current_list = []
                result[current_key] = current_list
            else:
                # scalar — strip quotes / brackets
                v = value.strip("'\"")
                # inline list e.g. domains: [rl-env, render]
                if v.startswith("[") and v.endswith("]"):
                    items = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                    result[current_key] = items
                    current_list = None
                else:
                    result[current_key] = v
                    current_list = None

    return result


def match_criticality(path: str, table: dict[str, list[str]]) -> str:
    """단일 path 가 어느 criticality 인지.

    critical > low > medium 우선. 둘 다 매칭 시 critical.
    """
    for pat in table["critical"]:
        if fnmatch(path, pat):
            return "critical"
    for pat in table["low"]:
        if fnmatch(path, pat):
            return "low"
    return "medium"


def detect_mode(plan_path: Path) -> dict[str, Any]:
    """plan.md → mode 분류 결과 dict."""
    fm = parse_frontmatter(plan_path)

    scope_paths = fm.get("scope_paths", []) or []
    domains = fm.get("domains", []) or []
    manual_mode = fm.get("mode")

    table = load_criticality_table()
    file_count = len(scope_paths)
    domains_count = len(domains)
    criticalities = [match_criticality(p, table) for p in scope_paths]
    max_criticality = (
        "critical" if "critical" in criticalities
        else "medium" if "medium" in criticalities
        else "low" if criticalities  # all low
        else "medium"  # empty scope_paths
    )

    # 1. manual override
    if manual_mode in ("quick-fix", "standard", "heavy"):
        return {
            "mode": manual_mode,
            "reason": "manual override (frontmatter mode:)",
            "file_count": file_count,
            "domains_count": domains_count,
            "max_criticality": max_criticality,
            "manual_override": True,
        }

    # 2-3. critical scope
    if max_criticality == "critical":
        if file_count >= 50:
            return {
                "mode": "heavy",
                "reason": f"critical scope + {file_count} files",
                "file_count": file_count,
                "domains_count": domains_count,
                "max_criticality": max_criticality,
                "manual_override": False,
            }
        return {
            "mode": "standard",
            "reason": "critical scope (file count irrelevant)",
            "file_count": file_count,
            "domains_count": domains_count,
            "max_criticality": max_criticality,
            "manual_override": False,
        }

    # 4. heavy by file count or domains
    if file_count >= 50 or domains_count >= 3:
        return {
            "mode": "heavy",
            "reason": f"50+ files ({file_count}) or 3+ domains ({domains_count})",
            "file_count": file_count,
            "domains_count": domains_count,
            "max_criticality": max_criticality,
            "manual_override": False,
        }

    # 5. quick-fix
    if file_count > 0 and file_count <= 3 and max_criticality == "low":
        return {
            "mode": "quick-fix",
            "reason": f"{file_count} low-criticality files",
            "file_count": file_count,
            "domains_count": domains_count,
            "max_criticality": max_criticality,
            "manual_override": False,
        }

    # 6. default
    return {
        "mode": "standard",
        "reason": "default",
        "file_count": file_count,
        "domains_count": domains_count,
        "max_criticality": max_criticality,
        "manual_override": False,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: detect-task-mode.py <plan.md path>", file=sys.stderr)
        return 2
    plan_path = Path(sys.argv[1])
    if not plan_path.is_file():
        print(f"plan.md not found: {plan_path}", file=sys.stderr)
        return 2
    result = detect_mode(plan_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
