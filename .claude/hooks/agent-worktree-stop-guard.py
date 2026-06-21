#!/usr/bin/env python3
"""
domain: lifecycle
agent-worktree-stop-guard — Stop hook

세션 종료 시 잔존 격리 워크트리 (`.claude/worktrees/agent-*`) 가 있으면
exit 2 로 종료 차단. PostToolUse hook 이 놓친 경우의 마지막 안전망.

stdin: Stop event payload (사용 안 함, 형식 무관)
stdout: (none)
stderr: 잔존 worktree 요약 + 해결 방법 (차단 시만)
exit code:
  0 — 잔존 0건 (정상 종료 허용) 또는 HARNESS_ALLOW_AGENT_WT_LEAK=1 (escape hatch)
  2 — 잔존 ≥1건 (Stop 차단)

설계 원칙:
  - escape hatch 명시 (사용자 의도 보존 시 환경변수)
  - git worktree list 가 SSOT — 디스크 잔존만 있고 git 등록 안 된 경우는 skip
  - 차단 메시지에 회수/폐기/강제종료 3 옵션 명시

관련: docs/_active/agent-worktree-leak-prevention/plan.md (Step 2)
      .claude/rules/80-task-lifecycle.md §E.13
"""
import io
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

ESCAPE_ENV = "HARNESS_ALLOW_AGENT_WT_LEAK"


def list_agent_worktrees() -> list[dict]:
    """git worktree list --porcelain 파싱 → agent isolation worktree 만 추출."""
    try:
        result = subprocess.run(
            ["git", "-C", REPO_ROOT, "worktree", "list", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        # failsafe: hook 자체 오류로 세션 종료 마비를 막되, 진단을 위해 stderr 한 줄.
        print(f"[stop-guard] git worktree list 실패 ({type(e).__name__}) — 잔존 0 으로 간주", file=sys.stderr)
        return []
    if result.returncode != 0:
        print(f"[stop-guard] git worktree list rc={result.returncode} — 잔존 0 으로 간주", file=sys.stderr)
        return []

    worktrees = []
    current = {}
    for line in result.stdout.splitlines() + [""]:
        if line.startswith("worktree "):
            current = {"path": line[len("worktree "):].strip()}
        elif line.startswith("branch "):
            current["branch"] = line[len("branch "):].strip()
        elif line.startswith("HEAD "):
            current["head"] = line[len("HEAD "):].strip()
        elif line == "locked" or line.startswith("locked "):
            current["locked"] = True
        elif line == "":
            if current:
                rel = os.path.relpath(current["path"], REPO_ROOT) if current.get("path") else ""
                if WORKTREE_PATTERN.search(rel):
                    current["rel_path"] = rel
                    current.setdefault("locked", False)
                    worktrees.append(current)
            current = {}
    return worktrees


def count_changes(abs_path: str) -> int:
    if not os.path.isdir(abs_path):
        return 0
    try:
        result = subprocess.run(
            ["git", "-C", abs_path, "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return 0
        return len([l for l in result.stdout.splitlines() if l.strip()])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0


def main() -> int:
    try:
        if os.environ.get(ESCAPE_ENV) == "1":
            # escape hatch: 사용자 명시 의도. 잔존 있어도 통과.
            return 0

        leftover = list_agent_worktrees()
        if not leftover:
            return 0

        n = len(leftover)

        # 자동 판단 정책 (rules/80 §E.13) — 분류 라벨 prepend
        enriched = [enrich_with_safety_meta(wt) for wt in leftover]
        classifications = [classify_worktree_safety(info) for info in enriched]
        all_auto_discard = all(c["verdict"] == "AUTO_DISCARD" for c in classifications)
        label = "[AUTO_DISCARD_SAFE]" if all_auto_discard else "[ASK_USER]"

        print(f"{label} ✗ 미해결 격리 worktree {n}건 — 종료 차단", file=sys.stderr)
        for i, (wt, info, cls) in enumerate(zip(leftover, enriched, classifications), 1):
            rel = wt.get("rel_path", wt.get("path", "?"))
            branch = wt.get("branch", wt.get("head", "?"))
            if branch.startswith("refs/heads/"):
                branch = branch[len("refs/heads/"):]
            changes = info.get("changes", count_changes(wt.get("path", "")))
            commits_ahead = info.get("commits_ahead", 0)
            lock = " [locked]" if wt.get("locked") else ""
            ahead = f" | commits ahead: {commits_ahead}" if commits_ahead else ""
            print(
                f"  {i}. {rel}{lock}\n"
                f"     branch: {branch} | changes: {changes} files{ahead}\n"
                f"     판정: {cls['verdict']} — {cls['reason']}",
                file=sys.stderr,
            )

        if all_auto_discard:
            print(
                "\n  💡 자동 폐기 권장 (모두 명백히 안전):\n"
                "    → bash scripts/worktree/clean-agents.sh --force --yes\n"
                "    근거: 0-byte 빈 파일 또는 임시 패턴, commits ahead 0, lock 없음.\n"
                "    main 에이전트는 추가 질의 없이 즉시 실행 가능 (rules/80 §E.13 자동 판단 정책).\n"
                f"  보수 옵션: 환경변수 `HARNESS_WT_AUTO_DISCARD_DISABLE=1` 시 ASK_USER 강제 fallback.",
                file=sys.stderr,
            )
        else:
            print(
                "\n  해결 방법:\n"
                "    • 회수    : 변경을 현재 브랜치로 가져온 후 `bash scripts/worktree/clean-agents.sh --apply --yes`\n"
                "    • 폐기    : `bash scripts/worktree/clean-agents.sh --force --yes` (uncommitted 손실)\n"
                f"    • 강제 종료 : 환경변수 `{ESCAPE_ENV}=1` (사용자 의도 보존)",
                file=sys.stderr,
            )

        print(
            "\n  참고: rules/80 §E.13 (Agent isolation 워크트리 회수 규율 + 자동 판단 정책)",
            file=sys.stderr,
        )
        return 2
    except Exception as e:
        # failsafe: Stop hook 자체 오류로 세션 종료 마비 회피. 진단 위해 stderr 1줄 trace.
        # trade-off: 격리 worktree leak 통과 가능 — escape hatch (`HARNESS_ALLOW_AGENT_WT_LEAK=1`) 와
        # 동일한 graceful degrade 경로. Layer 2 PostToolUse hook 이 1차 방어선이므로 본 fallback 은 안전.
        print(f"[stop-guard] failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
