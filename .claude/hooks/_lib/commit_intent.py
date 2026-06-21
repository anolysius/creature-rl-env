#!/usr/bin/env python3
# domain: lifecycle
"""commit_intent — commit-authorization gate 의 공유 결정 로직.

"사용자가 커밋을 명시 요청했나"(의도)를 hook 이 못 읽으므로, UserPromptSubmit 가 실제
발화에서 인가 신호를 추출해 state 에 기록하고, PreToolUse 가 그 state 로 결정론 판정한다.

  - is_authorizing_prompt : 발화가 커밋/푸시 인가인가 (부정 표현 제외)
  - is_commit_command     : Bash 명령이 git commit/push 인가 (status/diff/add 등 제외)
  - write_state/read_state: 인가 상태 transient 파일 (.claude/.session-state/commit-intent.json)
"""
from __future__ import annotations

import json
import os
import shlex
from pathlib import Path
from typing import Optional

_STATE_REL = Path(".claude") / ".session-state" / "commit-intent.json"

# 커밋/푸시 인가 신호 (broad — 미매칭 시 OVERRIDE 로 보완)
_AUTH_KEYWORDS = (
    "커밋", "commit", "푸시", "푸쉬", "push", "머지", "merge",
    "올려", "반영해", "반영 해", "pr 올려",
)
# 부정 표현 — 인가 키워드 있어도 미인가로
_NEGATION = ("하지마", "하지 마", "말고", "말아", "no commit", "don't", "do not", "안 해", "안해")


def is_authorizing_prompt(prompt: str) -> bool:
    if not prompt:
        return False
    lower = prompt.lower()
    if any(n in lower for n in _NEGATION):
        return False
    return any(k in lower for k in _AUTH_KEYWORDS)


def _split_segments(command: str):
    """복합 명령을 connector(&&, ||, ;, |) 로 분리. (`||` 를 `|` 보다 먼저 치환)"""
    tokens = command.replace("&&", "\x00").replace("||", "\x00") \
                    .replace(";", "\x00").replace("|", "\x00").split("\x00")
    return [t.strip() for t in tokens if t.strip()]


_GIT_GLOBAL_FLAG_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def is_commit_command(command: str) -> bool:
    """Bash 명령이 git commit / git push 를 실행하는가.

    복합 명령의 각 세그먼트를 검사. git global flag(-C path 등) 건너뛰고 subcommand 판정.
    shlex 실패(따옴표 깨짐 등) 시 보수적으로 False.
    """
    if not command or "git" not in command:
        return False
    for seg in _split_segments(command):
        try:
            tokens = shlex.split(seg)
        except ValueError:
            continue  # 보수적 — 파싱 불가 세그먼트는 skip
        if not tokens or tokens[0] != "git":
            continue
        i = 1
        while i < len(tokens):
            tok = tokens[i]
            if tok in _GIT_GLOBAL_FLAG_WITH_ARG:
                i += 2
                continue
            if tok.startswith("-"):
                i += 1
                continue
            # 첫 비-플래그 토큰 = subcommand. commit/push 면 매칭, 아니면 다음 세그먼트로.
            if tok in ("commit", "push"):
                return True
            break
    return False


def _state_path(root: Optional[str]) -> Path:
    """state 파일 경로. root → CLAUDE_PROJECT_DIR → cwd 순.

    주의: 기록(UserPromptSubmit)·판정(PreToolUse) 양 hook 가 동일 base 를 봐야 한다.
    settings.json 이 CLAUDE_PROJECT_DIR 을 주입하므로 운용 환경에선 일치. 미설정 시
    cwd fallback 으로 경로가 어긋나면 read_state→None→게이트 fail-open(통과)이 된다.
    """
    base = root or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return Path(base) / _STATE_REL


def write_state(authorized: bool, snippet: str = "", root: Optional[str] = None) -> None:
    p = _state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "authorized": bool(authorized),
        "snippet": (snippet or "")[:120],
    }, ensure_ascii=False), encoding="utf-8")


def read_state(root: Optional[str] = None) -> Optional[dict]:
    p = _state_path(root)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
