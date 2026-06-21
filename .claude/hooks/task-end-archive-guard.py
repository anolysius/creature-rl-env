#!/usr/bin/env python3
"""
domain: lifecycle
task-end-archive-guard — PreToolUse Bash matcher.

task-end 의 archive 이동(`mv` / `git mv` → docs/_archive/…) 시 결정론적 사고를 차단.
직접 동기: gate-summary-card task-end 에서 (1) 기존 INITIATIVE.md 덮어쓰기
(2) NN- prefix 충돌(01- 중복) 을 하네스가 못 잡고 수동 정정한 사례 (rules/80 §C.9 incident→hook).

차단 조건 (우선순위 순 — 첫 매칭 1건만 보고, plan SUGGEST 흡수):
  1. prefix 충돌   — target NN-<slug> 의 NN- 가 같은 initiative 에 다른 slug 로 이미 존재
  2. INITIATIVE 덮어쓰기 — target basename == INITIATIVE.md 이고 이미 존재
  3. task-folder 덮어쓰기 — target NN-<slug> 디렉토리가 이미 존재 + 비어있지 않음

위반 시 exit 2 (BLOCK). 비매칭 즉시 exit 0 (마찰 0).
HARNESS_ARCHIVE_GUARD_OVERRIDE=1 시 통과 + stderr 경고 (rules/85 OVERRIDE 선례).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

ARCHIVE_RE = re.compile(r"docs/_archive/")
NN_SLUG_RE = re.compile(r"^(\d{2})-(.+)$")


def _project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path.cwd()


def parse_archive_move(command: str):
    """`mv` / `git mv` 명령에서 archive target(마지막 인자)을 추출. 비대상이면 None.

    보수적: 파싱 애매하면 None(통과). target 이 docs/_archive/ 를 포함할 때만 engage.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if not tokens:
        return None

    # `git mv …` 또는 `mv …` 만 — 단일 명령 가정 (파이프/`&&` 는 보수적 비매칭)
    if any(sep in command for sep in ("&&", "||", ";", "|")):
        return None
    if tokens[0] == "git" and len(tokens) >= 2 and tokens[1] == "mv":
        args = tokens[2:]
    elif tokens[0] == "mv":
        args = tokens[1:]
    else:
        return None

    # flag 제거 (-f, -v, --force 등)
    operands = [a for a in args if not a.startswith("-")]
    if len(operands) < 2:
        return None
    target = operands[-1].rstrip("/")  # 마지막 operand = target (다중 source 보수 해석)
    if not ARCHIVE_RE.search(target):
        return None
    return target


def classify_violation(target: str, root: Path):
    """target 에 대한 첫 위반(code, message) 반환, 없으면 None.

    우선순위: prefix 충돌 > INITIATIVE 덮어쓰기 > task-folder 덮어쓰기.
    """
    tpath = (root / target).resolve() if not os.path.isabs(target) else Path(target)
    base = tpath.name
    parent = tpath.parent

    # 1) prefix 충돌 — target 이 NN-<slug> 이고, 같은 부모에 다른 slug 의 동일 NN- 존재
    m = NN_SLUG_RE.match(base)
    if m:
        nn = m.group(1)
        if parent.is_dir():
            for sib in parent.iterdir():
                sm = NN_SLUG_RE.match(sib.name)
                if sm and sm.group(1) == nn and sib.name != base:
                    return (
                        "PREFIX_COLLISION",
                        f"NN- prefix '{nn}-' 가 이미 '{sib.name}' 에 사용됨. "
                        f"다음 빈 번호로 재지정하세요 (target='{base}').",
                    )

    # 2) INITIATIVE.md 덮어쓰기
    if base == "INITIATIVE.md" and tpath.exists():
        return (
            "INITIATIVE_OVERWRITE",
            f"기존 INITIATIVE.md 를 덮어씁니다 ({target}). "
            "이니셔티브 narrative 보호 — 기존 파일에 append 하거나 별 경로 사용.",
        )

    # 3) task-folder 덮어쓰기 (NN-<slug> 디렉토리 기존재 + 비어있지 않음)
    if m and tpath.is_dir():
        try:
            non_empty = any(tpath.iterdir())
        except OSError:
            non_empty = False
        if non_empty:
            return (
                "TARGET_NONEMPTY",
                f"target task 폴더가 이미 존재하고 비어있지 않습니다 ({target}). "
                "기존 archive task 덮어쓰기 위험 — 경로 확인.",
            )

    return None


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    tool_name = payload.get("tool_name", "")
    command = (payload.get("tool_input", {}).get("command") or "").strip()
    if tool_name != "Bash" or not command:
        return 0

    target = parse_archive_move(command)
    if not target:
        return 0

    if os.environ.get("HARNESS_ARCHIVE_GUARD_OVERRIDE") == "1":
        sys.stderr.write(
            "[task-end-archive-guard] OVERRIDE 활성 — archive 가드 우회 "
            "(HARNESS_ARCHIVE_GUARD_OVERRIDE=1). 사용자 명시 의도로 간주.\n"
        )
        return 0

    root = _project_root()
    violation = classify_violation(target, root)
    if violation is None:
        return 0

    code, message = violation
    sys.stderr.write(
        f"[task-end-archive-guard BLOCK] {code}\n"
        f"  {message}\n\n"
        "  본 가드 (rules/80 §H 후속 / task-end §6): archive 이동 시 사고 차단.\n"
        "  해결: 위 안내대로 경로 수정 후 재시도.\n"
        f"  명시 OVERRIDE: HARNESS_ARCHIVE_GUARD_OVERRIDE=1 {command}\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
