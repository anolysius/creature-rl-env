#!/usr/bin/env python3
"""
domain: lifecycle
git-policy-guard — PreToolUse Bash matcher.

rules/85-git-policy.md 의 단방향 워크플로 정책을 Claude Code 가 실행하는
git 명령에 적용. _lib/git_policy.py 가 분류·파싱·판정 SSOT.

위반 시 exit 2 (BLOCK). cherry-pick 은 escape hatch (통과).
HARNESS_GIT_POLICY_OVERRIDE=1 시 통과 + stderr 경고.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "_lib"))

from git_policy import (  # noqa: E402
    is_violation,
    parse_cherry_pick,
    parse_merge_intent,
    parse_push_intent,
)


POLICY_DOC = (
    "본 정책 (rules/85-git-policy.md): qa/* 는 단방향 sink.\n"
    "  허용: feature/* → qa/*, main → qa/*\n"
    "  금지: qa/* → 어떤 브랜치도\n"
    "세부: docs/harness/explanation/git-branching-model.md"
)


def _current_branch() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if out.returncode == 0:
            return out.stdout.strip() or None
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def _read_input() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def _is_git_command(command: str) -> bool:
    stripped = command.lstrip()
    return stripped.startswith("git ") or stripped == "git"


def main() -> int:
    payload = _read_input()
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    command = (tool_input.get("command") or "").strip()

    # Bash matcher 만 처리. 다른 tool 은 통과.
    if tool_name != "Bash" or not command:
        return 0

    # git 명령이 아니면 통과
    if not _is_git_command(command):
        return 0

    # OVERRIDE — 사용자 명시 우회
    if os.environ.get("HARNESS_GIT_POLICY_OVERRIDE") == "1":
        sys.stderr.write(
            "[git-policy WARN] HARNESS_GIT_POLICY_OVERRIDE=1 — 정책 우회 통과. "
            "사용 후 환경변수 비활성 권장.\n"
        )
        return 0

    # cherry-pick 은 escape hatch
    if parse_cherry_pick(command):
        return 0

    # merge / pull 검사
    merge_intent = parse_merge_intent(command)
    if merge_intent is not None:
        current = _current_branch()
        violation = is_violation(merge_intent, current_branch=current)
        if violation is not None:
            sys.stderr.write(
                f"[git-policy BLOCK] {violation.detail}\n\n"
                f"{POLICY_DOC}\n\n"
                f"해결책:\n"
                f"  1. {violation.suggestion}\n"
                f"  2. 사용자 명시 OVERRIDE: HARNESS_GIT_POLICY_OVERRIDE=1 {command}\n"
            )
            return 2

    # push 검사
    push_intent = parse_push_intent(command)
    if push_intent is not None:
        violation = is_violation(push_intent)
        if violation is not None:
            sys.stderr.write(
                f"[git-policy BLOCK] {violation.detail}\n\n"
                f"{POLICY_DOC}\n\n"
                f"해결책:\n"
                f"  1. {violation.suggestion}\n"
                f"  2. 사용자 명시 OVERRIDE: HARNESS_GIT_POLICY_OVERRIDE=1 {command}\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
