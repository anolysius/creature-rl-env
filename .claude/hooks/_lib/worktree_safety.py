#!/usr/bin/env python3
"""
domain: lifecycle
worktree_safety — agent isolation 워크트리 자동 판단 분류.

`agent-worktree-stop-guard.py` 와 `agent-worktree-return-handler.py` 가
공용으로 사용. 명백히 안전한 폐기 케이스를 deterministic 하게 분류해
사용자 질의 단계 생략 또는 ASK_USER fallback 결정.

설계 원칙:
- 보수적 분류 — 의심스러우면 ASK_USER fallback
- 결정 트리 단순 (regex + size + count) — LLM 판단 없음
- escape: 환경변수 `HARNESS_WT_AUTO_DISCARD_DISABLE=1` 시 항상 ASK_USER

관련: docs/_active/agent-worktree-auto-decision-policy/plan.md (Step 1)
      .claude/rules/80-task-lifecycle.md §E.13
"""
from __future__ import annotations

import os
import re
import subprocess
from typing import Optional, TypedDict


# 자동 폐기 허용 임시 파일 패턴 (basename 매칭).
# L3 reviewer SUGGEST 흡수 — `test/sample/debug/synthetic`
# 은 진짜 prototype 파일명일 가능성이 있어 제외. 명백 throwaway 만 매칭.
TEMP_PATTERN = re.compile(
    r"^(tmp|temp|foo|bar)\.\w+$"
    r"|\.(tmp|swp|bak|log|pyc)$"
)

MAX_AUTO_DISCARD_FILES = 5

# 환경 변수로 자동 분류 비활성 가능 (사용자 보수 옵션)
DISABLE_ENV = "HARNESS_WT_AUTO_DISCARD_DISABLE"


class FileMeta(TypedDict):
    path: str           # worktree 내부 상대 경로
    size: int           # bytes
    type: str           # "untracked" | "modified" | "added" | ...


class WorktreeInfo(TypedDict, total=False):
    path: str                   # worktree 절대 경로
    rel_path: str               # repo root 기준 상대 경로
    branch: str
    head: str
    locked: bool
    changes: int                # uncommitted file 수
    commits_ahead: int
    files_meta: list[FileMeta]


class Classification(TypedDict):
    verdict: str                # "AUTO_DISCARD" | "ASK_USER"
    reason: str
    recommended_action: Optional[str]


def _is_temp_pattern(filename: str) -> bool:
    """파일 basename 이 임시 파일 패턴 매칭."""
    return bool(TEMP_PATTERN.match(os.path.basename(filename)))


def enrich_with_safety_meta(wt: WorktreeInfo, repo_root: Optional[str] = None) -> WorktreeInfo:
    """기존 worktree info 에 분류용 메타 추가.

    git status --porcelain 으로 uncommitted 파일별 size + type 수집,
    git rev-list 로 main 대비 commits_ahead 카운트.

    repo_root: 미지정 시 wt['path'] 의 git 저장소 root 자동 추론.
    """
    enriched: WorktreeInfo = dict(wt)  # type: ignore[assignment]
    abs_path = wt.get("path", "")

    # 1) uncommitted 파일별 메타
    files_meta: list[FileMeta] = []
    try:
        result = subprocess.run(
            ["git", "-C", abs_path, "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if len(line) < 4:
                    continue
                # porcelain format: "XY <filename>"
                xy = line[:2]
                fname = line[3:].strip()
                # rename 의 경우 "old -> new" 처리 — new 만 사용
                if " -> " in fname:
                    fname = fname.split(" -> ")[-1].strip()
                # 따옴표 unquote (특수문자 파일)
                if fname.startswith('"') and fname.endswith('"'):
                    fname = fname[1:-1]
                full = os.path.join(abs_path, fname)
                size = 0
                if os.path.isfile(full):
                    try:
                        size = os.path.getsize(full)
                    except OSError:
                        size = 0
                ftype = "untracked" if xy.strip() == "??" else "modified"
                files_meta.append({"path": fname, "size": size, "type": ftype})
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    enriched["files_meta"] = files_meta
    enriched["changes"] = len(files_meta)

    # 2) commits_ahead — main 대비
    commits_ahead = 0
    try:
        # HEAD 가 main 의 후손이 아닐 수 있어 symmetric diff 사용
        result = subprocess.run(
            ["git", "-C", abs_path, "rev-list", "--count", "main..HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            commits_ahead = int(result.stdout.strip() or 0)
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass

    enriched["commits_ahead"] = commits_ahead
    return enriched


def classify_worktree_safety(info: WorktreeInfo) -> Classification:
    """worktree info → AUTO_DISCARD / ASK_USER 분류.

    AUTO_DISCARD 조건 (모두 만족):
      1. commits_ahead == 0
      2. locked == False
      3. 모든 files_meta 가 (size == 0) ‖ (basename 임시 패턴 매칭)
      4. len(files_meta) <= 5

    그 외 → ASK_USER.

    환경변수 HARNESS_WT_AUTO_DISCARD_DISABLE=1 시 항상 ASK_USER.
    """
    if os.environ.get(DISABLE_ENV) == "1":
        return {
            "verdict": "ASK_USER",
            "reason": f"자동 분류 비활성 ({DISABLE_ENV}=1)",
            "recommended_action": None,
        }

    locked = info.get("locked", False)
    commits_ahead = info.get("commits_ahead", 0)
    files_meta = info.get("files_meta", [])
    n_changes = len(files_meta)

    # commits_ahead 우선 — 사용자 작업물 가능성
    if commits_ahead > 0:
        return {
            "verdict": "ASK_USER",
            "reason": f"commits ahead {commits_ahead} (사용자 작업물 가능)",
            "recommended_action": None,
        }

    if locked:
        return {
            "verdict": "ASK_USER",
            "reason": "lock 상태 (의도된 보존)",
            "recommended_action": None,
        }

    if n_changes > MAX_AUTO_DISCARD_FILES:
        return {
            "verdict": "ASK_USER",
            "reason": f"변경 파일 {n_changes}건 (한도 {MAX_AUTO_DISCARD_FILES} 초과)",
            "recommended_action": None,
        }

    if n_changes == 0:
        # 잔존 worktree 인데 uncommitted 0 — 정상 케이스 (그러나 commits_ahead=0 이면 자동 폐기 가능)
        return {
            "verdict": "AUTO_DISCARD",
            "reason": "uncommitted 변경 0건 + commits ahead 0",
            "recommended_action": "bash scripts/worktree/clean-agents.sh --force --yes",
        }

    # 모든 파일이 빈 파일 또는 임시 패턴
    safe_files = []
    unsafe_files = []
    for fm in files_meta:
        if fm.get("size", 0) == 0:
            safe_files.append(f"{fm['path']} (0 bytes)")
        elif _is_temp_pattern(fm.get("path", "")):
            safe_files.append(f"{fm['path']} (임시 패턴)")
        else:
            unsafe_files.append(fm["path"])

    if unsafe_files:
        return {
            "verdict": "ASK_USER",
            "reason": f"의미 파일 {len(unsafe_files)}건: {', '.join(unsafe_files[:3])}{'...' if len(unsafe_files) > 3 else ''}",
            "recommended_action": None,
        }

    return {
        "verdict": "AUTO_DISCARD",
        "reason": f"모든 변경 ({n_changes}건) 이 빈 파일 또는 임시 패턴: {', '.join(safe_files[:3])}{'...' if len(safe_files) > 3 else ''}",
        "recommended_action": "bash scripts/worktree/clean-agents.sh --force --yes",
    }
