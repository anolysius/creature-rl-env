#!/usr/bin/env python3
# domain: lifecycle
"""task-evaluate paths 라우팅 — plan.md 의 영향 vertical agent 를 자동 선택.

사용:
    python3 .claude/skills/task-evaluate/scripts/route-evaluators.py <plan.md>

출력 (stdout, JSON):
    {"agents": ["@plan-reviewer", "@qa-verifier", "@<domain>-auditor"], ...}

vertical `@<domain>-auditor` 는 해당 agent 파일이 .claude/agents/ 에 존재할 때만
추가된다. 기본 하네스는 @plan-reviewer + @qa-verifier 만 보장 — 도메인 auditor 를
추가하면 자동 라우팅된다.
"""
import sys
import io
import os
import re
import json
import glob
from typing import List, Set
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent.parent.parent.parent  # repo root
CLAUDE_DIR = ROOT / ".claude"
RULES_DIR = CLAUDE_DIR / "rules"
AGENTS_DIR = CLAUDE_DIR / "agents"


def parse_frontmatter(text: str) -> dict:
    """Simple YAML frontmatter parser. domains:/scope_paths:/paths: list 만 지원."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm_text = text[3:end]
    result = {}
    current_key = None
    current_list = []
    for line in fm_text.splitlines():
        # key: value 단일 라인
        m = re.match(r"^(\w+)\s*:\s*(.*)$", line)
        if m:
            if current_key and current_list:
                result[current_key] = current_list
                current_list = []
            key, value = m.group(1), m.group(2).strip()
            if value:  # inline value
                # list inline ?
                if value.startswith("[") and value.endswith("]"):
                    items = [x.strip().strip('"\'') for x in value[1:-1].split(",")]
                    result[key] = [i for i in items if i]
                else:
                    result[key] = value.strip('"\'')
                current_key = None
            else:  # block list 시작 가능
                current_key = key
                current_list = []
        # 리스트 항목
        elif re.match(r"^\s+-\s+", line) and current_key:
            item = re.sub(r"^\s+-\s+", "", line).strip().strip('"\'')
            current_list.append(item)
    if current_key and current_list:
        result[current_key] = current_list
    return result


def agent_exists(agent_name: str) -> bool:
    """@plan-reviewer 형식 → file 존재 확인."""
    name = agent_name.lstrip("@")
    return (AGENTS_DIR / f"{name}.md").exists()


def load_rules() -> List[dict]:
    """rules/*.md 의 frontmatter 추출."""
    rules = []
    for path in sorted(RULES_DIR.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            if fm.get("domain") and fm.get("paths"):
                rules.append({
                    "id": fm.get("id", path.stem),
                    "domain": fm["domain"],
                    "paths": fm["paths"] if isinstance(fm["paths"], list) else [fm["paths"]],
                })
        except Exception:
            continue
    return rules


def path_match(rule_paths: List[str], plan_path: str) -> bool:
    """간단한 prefix/glob 매칭."""
    import fnmatch
    plan_norm = plan_path.replace("**/*", "").replace("/**", "")
    for rp in rule_paths:
        # rule path 의 ** 와 plan path 의 ** 모두 처리
        rp_norm = rp.replace("/**", "").replace("**/", "").replace("**", "*")
        plan_norm2 = plan_path.replace("/**", "").replace("**/", "").replace("**", "*")
        # 양쪽 다 fnmatch 시도
        if fnmatch.fnmatch(plan_norm2, rp_norm + "*"):
            return True
        if fnmatch.fnmatch(rp_norm, plan_norm2 + "*"):
            return True
        # 공통 prefix
        rp_parts = rp.split("*")[0].rstrip("/")
        plan_parts = plan_path.split("*")[0].rstrip("/")
        if rp_parts and plan_parts and (rp_parts.startswith(plan_parts) or plan_parts.startswith(rp_parts)):
            return True
    return False


def route(plan_path: str) -> dict:
    plan = Path(plan_path)
    if not plan.exists():
        return {"error": f"plan not found: {plan_path}", "agents": []}

    text = plan.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)

    # rules/80 §F.1 mode tiering — quick-fix 시 single reviewer (qa-verifier)
    # 분기 (≥2 reviewer 강제 §A.2 의 quick-fix 예외).
    mode = fm.get("mode", "standard")
    if mode == "quick-fix":
        return {
            "plan": str(plan),
            "mode": "quick-fix",
            "declared_domains": fm.get("domains", []),
            "scope_paths": fm.get("scope_paths", []),
            "agents": ["@qa-verifier"],
            "agent_count": 1,
            "reasoning": "quick-fix mode (rules/80 §F.1) — single reviewer (§A.2 예외)",
        }

    agents: List[str] = ["@plan-reviewer", "@qa-verifier"]  # lifecycle 무조건 (standard/heavy)
    seen: Set[str] = set(agents)

    # 1) 명시 도메인 → vertical auditor
    declared = fm.get("domains", [])
    if isinstance(declared, str):
        declared = [declared]
    for d in declared:
        # subdomain dot notation 처리: foo.bar → foo-bar-auditor or foo-auditor
        parts = d.split(".")
        candidates = []
        if len(parts) > 1:
            candidates.append(f"@{parts[0]}-{parts[1]}-auditor")  # foo-bar-auditor
        candidates.append(f"@{parts[0]}-auditor")                  # foo-auditor

        for agent in candidates:
            if agent_exists(agent) and agent not in seen:
                agents.append(agent)
                seen.add(agent)
                break

    # 2) scope_paths 매칭으로 보완
    scope_paths = fm.get("scope_paths", [])
    if isinstance(scope_paths, str):
        scope_paths = [scope_paths]

    rules = load_rules()
    for path in scope_paths:
        for rule in rules:
            if path_match(rule["paths"], path):
                agent = f"@{rule['domain']}-auditor"
                if agent_exists(agent) and agent not in seen:
                    agents.append(agent)
                    seen.add(agent)

    return {
        "plan": str(plan),
        "declared_domains": declared,
        "scope_paths": scope_paths,
        "agents": agents,
        "agent_count": len(agents),
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: route-evaluators.py <plan.md>"}, ensure_ascii=False))
        sys.exit(1)
    result = route(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
