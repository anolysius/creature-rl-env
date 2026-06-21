#!/usr/bin/env python3
"""
domain: lifecycle
harness-commit-guard — PreToolUse Bash hook (commit-authorization gate 게이트 계층).

`git commit`/`git push` 가 **사용자 인가 없이** 실행되려 하면 BLOCK 한다 (글로벌 지침
"Commit or push only when the user asks" 의 결정론 강제). 인가 여부는 harness-commit-
intent-record 가 직전 발화에서 기록한 state 로 판정.

stdin:  {"tool_name": "Bash", "tool_input": {"command": "..."}}
stdout: {"decision": "block", "reason": "..."} | 빈 출력(통과)

PASS: non-commit 명령 / state authorized=true / state 없음(fail-open) / OVERRIDE.
OVERRIDE: HARNESS_ALLOW_COMMIT=1 (.env.local hot-toggle 또는 shell env) → 통과 + stderr 경고.
hook 자체 오류 → fail-open.
"""
import io
import json
import os
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)


def _load_env_local():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project_dir:
        return
    path = os.path.join(project_dir, ".env.local")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except (FileNotFoundError, OSError):
        pass


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
        if data.get("tool_name", "") != "Bash":
            return
        command = (data.get("tool_input", {}) or {}).get("command", "")
        if not command:
            return

        import commit_intent as ci
        if not ci.is_commit_command(command):
            return  # git commit/push 아님 → 관여 안 함

        _load_env_local()
        if os.environ.get("HARNESS_ALLOW_COMMIT") == "1":
            sys.stderr.write(
                "⚠️  HARNESS_ALLOW_COMMIT=1 활성 — commit-authorization 게이트 우회 중. "
                "작업 종료 후 라인 제거 권장.\n"
            )
            return

        state = ci.read_state()
        if state is None:
            return  # 판정 불가 → fail-open (hook tax 회피)
        if state.get("authorized") is True:
            return  # 직전 발화가 커밋 인가

        result = {
            "decision": "block",
            "reason": (
                "⛔ 자동 커밋/푸시 차단 — 사용자가 직전 발화에서 커밋·푸시를 명시 요청하지 않았습니다.\n"
                "  (글로벌 지침: Commit or push only when the user asks)\n\n"
                "  해결:\n"
                "  1) 사용자에게 커밋·푸시 여부를 먼저 확인 — 요청 시에만 실행\n"
                "  2) 사용자가 방금 요청했다면 그 발화에 '커밋'/'푸시'/'commit'/'push' 가 포함됐는지 확인\n"
                "  3) 의도적 우회 — HARNESS_ALLOW_COMMIT=1 (.env.local 또는 shell env)"
            ),
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False))

    except (json.JSONDecodeError, KeyError, ImportError):
        pass  # fail-open


if __name__ == "__main__":
    main()
