#!/usr/bin/env python3
"""
domain: lifecycle
agent-worktree-return-handler — PostToolUse hook (matcher: Agent)

Agent tool 호출 결과에서 isolation worktree 경로 (`.claude/worktrees/agent-*`)
를 감지하여 main 에이전트에게 회수 결정을 강제한다. 감지 시 stderr 로
가시화 메시지 출력 — main 의 다음 turn 컨텍스트에 반영.

stdin: {"tool_name": "Agent", "tool_input": {...}, "tool_response": {...}, ...}
stdout: 가시화 메시지 (감지 시만 — Claude Code 가 다음 turn 에 surface)
stderr: (none)
exit code: 항상 0 (deny 아님 — 가시화만)

stdout 사용 근거: Claude Code PostToolUse hook 명세상 exit 0 + stdout 은
다음 turn 에 assistant 컨텍스트로 주입되어 후속 결정 강제 가능. stderr 는
exit 2 (block) 시에만 surface 되며 exit 0 에서는 transcript 에만 표시 → 메인
에이전트 turn 컨텍스트 미주입. 다른 PostToolUse 알림 훅과 동일 패턴.

설계 원칙:
  - false positive 최소화: tool_response 에 worktree 경로 패턴 매칭될 때만 출력
  - tool_response 구조 변경에 robust: 정규식 + JSON traversal 양쪽 fallback
  - 디렉토리 실제 존재 + git tracked worktree 확인 후에만 알림

관련: docs/_active/agent-worktree-leak-prevention/plan.md (Step 1)
      .claude/rules/80-task-lifecycle.md §E.13
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# 자동 판단 정책 (rules/80 §E.13)
sys.path.insert(0, os.path.join(REPO_ROOT, ".claude", "hooks", "_lib"))
from worktree_safety import classify_worktree_safety, enrich_with_safety_meta  # noqa: E402

WORKTREE_PATTERN = re.compile(r"\.claude/worktrees/agent-[a-f0-9]+")


def detect_worktree_paths(payload: dict) -> set[str]:
    """tool_response 에서 worktree 경로 후보 추출. 정규식 기반 (구조 무관)."""
    blob = json.dumps(payload, ensure_ascii=False)
    return set(WORKTREE_PATTERN.findall(blob))


def is_tracked_worktree(rel_path: str) -> bool:
    """git worktree list 에 등록된 경로인지 확인."""
    abs_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.isdir(abs_path):
        return False
    try:
        result = subprocess.run(
            ["git", "-C", REPO_ROOT, "worktree", "list", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return False
        return abs_path in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def collect_worktree_info(rel_path: str) -> dict:
    """변경 카운트 + 브랜치 + lock 상태 수집."""
    abs_path = os.path.join(REPO_ROOT, rel_path)
    info = {"path": rel_path, "changes": 0, "branch": "?", "locked": False}
    try:
        status = subprocess.run(
            ["git", "-C", abs_path, "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        if status.returncode == 0:
            lines = [l for l in status.stdout.splitlines() if l.strip()]
            info["changes"] = len(lines)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    try:
        branch = subprocess.run(
            ["git", "-C", abs_path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if branch.returncode == 0:
            info["branch"] = branch.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    # lock 확인 — .git/worktrees/<name>/locked 파일 존재 시 locked
    name = os.path.basename(rel_path)
    lock_marker = os.path.join(REPO_ROOT, ".git", "worktrees", name, "locked")
    info["locked"] = os.path.exists(lock_marker)
    return info


def emit_reminder(infos: list[dict]) -> None:
    n = len(infos)

    # 자동 판단 정책 (rules/80 §E.13)
    enriched = [enrich_with_safety_meta(info) for info in infos]
    classifications = [classify_worktree_safety(e) for e in enriched]
    all_auto_discard = all(c["verdict"] == "AUTO_DISCARD" for c in classifications)
    label = "[AUTO_DISCARD_SAFE]" if all_auto_discard else "[ASK_USER]"

    lines = [f"{label} ⚠ Agent isolation worktree 반환 감지 ({n}건)"]
    for i, (info, e, cls) in enumerate(zip(infos, enriched, classifications), 1):
        lock = " [locked]" if info["locked"] else ""
        commits_ahead = e.get("commits_ahead", 0)
        ahead = f" | commits ahead: {commits_ahead}" if commits_ahead else ""
        lines.append(f"  {i}. {info['path']}{lock}")
        lines.append(f"     branch: {info['branch']} | changes: {info['changes']} files{ahead}")
        lines.append(f"     판정: {cls['verdict']} — {cls['reason']}")
    lines.append("")

    if all_auto_discard:
        lines.append("  💡 자동 폐기 권장 (명백히 안전):")
        lines.append("    → bash scripts/worktree/clean-agents.sh --force --yes")
        lines.append("    main 에이전트는 추가 질의 없이 즉시 실행 가능 (rules/80 §E.13).")
    else:
        lines.append("  다음 user prompt 전 결정 필요:")
        lines.append("    (1) 회수 → 변경을 현재 브랜치로 cherry-pick / patch / 직접 commit")
        lines.append("    (2) 폐기 → bash scripts/worktree/clean-agents.sh --apply --yes")
        lines.append("    (3) 보존 → 사용자 명시 승인 후 lock 유지 (의도된 보존만)")

    lines.append("")
    lines.append("  참고: rules/80 §E.13 (Agent isolation 워크트리 회수 규율 + 자동 판단 정책)")
    print("\n".join(lines))


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return 0

    if payload.get("tool_name") != "Agent":
        return 0

    candidates = detect_worktree_paths(payload)
    if not candidates:
        return 0

    valid = [p for p in candidates if is_tracked_worktree(p)]
    if not valid:
        return 0

    infos = [collect_worktree_info(p) for p in sorted(valid)]
    emit_reminder(infos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
