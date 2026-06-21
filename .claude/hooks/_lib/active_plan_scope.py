#!/usr/bin/env python3
# domain: lifecycle
"""active_plan_scope — 하네스 우회 게이트의 공유 결정 로직.

rules/80 §A.6.1 (기능 요청 선제 제안) 의 **결정론 hook 격상** 코어.
harness-task-start-guard.py (PreToolUse Write|Edit) 와 harness-task-intent-nudge.py
(UserPromptSubmit) 가 공유.

핵심 판정:
  - is_target_path     : src/** (제품 소스) 만 게이트 대상
  - is_trivial_edit    : 단일라인 ∧ ≤120 비공백자 변경은 자동 통과 (§A.6.1 "한 줄 수정")
  - find_covering_plan : docs/_active/**/plan.md 중 acceptance_freeze:true ∧
                         scope_paths(fnmatch) 가 file_path 커버하는 plan
  - decide             : 위를 종합 — gated(True=BLOCK) + 사유
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

_LIB_DIR = Path(__file__).resolve().parent
import sys
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from path_match import match_any, normalize  # noqa: E402

TRIVIAL_EDIT_MAX_CHARS = 120
# 제품 소스 prefix — 게이트 대상. CritterGym 은 src/ 단일.
_TARGET_PREFIXES = ("src/",)


def _project_root(project_root: Optional[str]) -> str:
    return project_root or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _rel(file_path: str, project_root: Optional[str]) -> str:
    """file_path 를 project_root 기준 상대 경로(정규화)로."""
    root = normalize(_project_root(project_root)).rstrip("/")
    p = normalize(file_path)
    if p.startswith(root + "/"):
        p = p[len(root) + 1:]
    return p.lstrip("/")


def is_target_path(file_path: str, project_root: Optional[str] = None) -> bool:
    """제품 소스(src/**) 인가 — 게이트 대상 여부."""
    rel = _rel(file_path, project_root)
    return rel.startswith(_TARGET_PREFIXES)


def _nonspace_len(s: str) -> int:
    return len("".join(s.split()))


def is_trivial_edit(tool_name: str, tool_input: dict) -> bool:
    """단일라인 ∧ ≤TRIVIAL_EDIT_MAX_CHARS 비공백자 변경 = trivial (자동 통과).

    Write(신규 파일 생성)는 trivial 아님 — 항상 게이트 대상.
    """
    if tool_name != "Edit":
        return False
    old = tool_input.get("old_string", "") or ""
    new = tool_input.get("new_string", "") or ""
    if "\n" in old or "\n" in new:
        return False
    return max(_nonspace_len(old), _nonspace_len(new)) <= TRIVIAL_EDIT_MAX_CHARS


def _parse_frontmatter(text: str) -> dict:
    """plan.md frontmatter 파싱 (yaml 의존 없이 acceptance_freeze + scope_paths 만)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm = {"acceptance_freeze": None, "scope_paths": []}
    in_scope = False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("scope_paths:"):
            in_scope = True
            continue
        if in_scope:
            stripped = line.strip()
            if stripped.startswith("- "):
                val = stripped[2:].strip()
                # 인라인 주석 제거 (예: "path  # comment")
                if "#" in val:
                    val = val.split("#", 1)[0].strip()
                if val:
                    fm["scope_paths"].append(val)
                continue
            # 들여쓰기 없는 새 키 → scope 블록 종료
            if line and not line[0].isspace():
                in_scope = False
        if line.startswith("acceptance_freeze:"):
            fm["acceptance_freeze"] = line.split(":", 1)[1].strip()
    return fm


# public alias — 다른 hook(nudge)에서 frontmatter 파싱 재사용 (private 직접 참조 회피)
def parse_plan_frontmatter(text: str) -> dict:
    """plan.md frontmatter 파싱 (acceptance_freeze + scope_paths). public API."""
    return _parse_frontmatter(text)


def find_covering_plan(file_path: str, active_dir=None,
                       project_root: Optional[str] = None) -> Optional[Path]:
    """frozen(acceptance_freeze:true) plan 중 scope_paths 가 file_path 를 커버하는 것."""
    root = _project_root(project_root)
    active = Path(active_dir) if active_dir else Path(root) / "docs" / "_active"
    if not active.exists():
        return None
    rel = _rel(file_path, project_root)
    for plan in sorted(active.rglob("plan.md")):
        try:
            fm = _parse_frontmatter(plan.read_text(encoding="utf-8"))
        except OSError:
            continue
        if (fm.get("acceptance_freeze") or "").lower() != "true":
            continue
        if fm.get("scope_paths") and match_any(rel, fm["scope_paths"]):
            return plan
    return None


def decide(tool_name: str, tool_input: dict, active_dir=None,
           project_root: Optional[str] = None) -> Tuple[bool, str]:
    """게이트 종합 결정. 반환 (gated, reason). gated=True → BLOCK.

    PASS 조건 (우선순위):
      1. 비대상 경로(.claude/** · docs/** 등)        → PASS
      2. trivial edit (단일라인 ∧ ≤120자)            → PASS
      3. frozen plan 이 scope 로 커버                 → PASS
      4. else                                          → BLOCK
    """
    file_path = tool_input.get("file_path", "") or ""
    if not file_path:
        return False, "file_path 없음 — 게이트 대상 아님"
    if not is_target_path(file_path, project_root):
        return False, "비대상 경로 (src/ 아님)"
    if is_trivial_edit(tool_name, tool_input):
        return False, "trivial edit (단일라인 ≤120자)"
    plan = find_covering_plan(file_path, active_dir=active_dir, project_root=project_root)
    if plan is not None:
        return False, f"frozen plan 커버: {plan}"
    return True, "frozen plan 없이 제품 소스 변경 — 하네스 우회"
