#!/usr/bin/env python3
"""
domain: lifecycle
harness-commit-intent-record — UserPromptSubmit hook (commit-authorization gate 기록 계층).

매 사용자 발화에서 커밋/푸시 **인가 신호**를 추출해 transient state 에 기록한다.
PreToolUse 의 harness-commit-guard 가 이 state 로 "사용자가 커밋을 시켰나" 를 결정론 판정.
최신 발화가 최종 — 비인가 발화 시 authorized=false 로 갱신(stale 방지).

stdin:  {"prompt": "...", ...}
stdout: 없음 (state 기록만, 비차단)
"""
import io
import json
import os
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        prompt = json.loads(raw).get("prompt", "")
        import commit_intent as ci
        ci.write_state(ci.is_authorizing_prompt(prompt), snippet=prompt)
    except (json.JSONDecodeError, KeyError, ImportError, OSError):
        pass  # 기록 실패가 작업을 막지 않음


if __name__ == "__main__":
    main()
