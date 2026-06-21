#!/usr/bin/env python3
"""
domain: lifecycle
harness-task-start-guard — PreToolUse Write|Edit hook (rules/80 §A.6.1 결정론 격상).

제품 소스(src/**)에 **frozen plan 없이** 변경을 시도하면 BLOCK 해서
하네스(/task-start→L1→G1) 우회를 막는다. 판정 로직은 _lib/active_plan_scope.decide.

stdin:  {"tool_name": "Write"|"Edit", "tool_input": {"file_path": "...", ...}}
stdout: {"decision": "block", "reason": "..."} | 빈 출력(통과)

PASS (우회 아님): 비대상 경로(.claude/**·docs/** 등) / trivial edit(단일라인 ≤120자) /
                  frozen plan 이 scope 로 커버 / OVERRIDE.
OVERRIDE: HARNESS_SKIP_HARNESS=1 (.env.local hot-toggle 또는 shell env) → 통과 + stderr 경고.
실패 시 fail-open (hook 이 도구 실행을 막지 않음).
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
    """프로젝트 루트 .env.local 매 호출 파싱 → hot-toggle (세션 재시작 불필요)."""
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
        tool_name = data.get("tool_name", "")
        if tool_name not in ("Write", "Edit"):
            return

        _load_env_local()
        if os.environ.get("HARNESS_SKIP_HARNESS") == "1":
            sys.stderr.write(
                "⚠️  HARNESS_SKIP_HARNESS=1 활성 — 하네스 task-start 게이트 우회 중. "
                "작은 수정/긴급용. 작업 종료 후 라인 제거 권장.\n"
            )
            return

        tool_input = data.get("tool_input", {}) or {}

        import active_plan_scope as aps
        gated, reason = aps.decide(tool_name, tool_input)
        if not gated:
            return

        file_path = tool_input.get("file_path", "")
        result = {
            "decision": "block",
            "reason": (
                "⛔ 하네스 우회 감지 — 제품 소스에 승인된(frozen) plan 없이 변경하려 합니다.\n"
                f"  대상: {file_path}\n"
                f"  사유: {reason}\n\n"
                "  해결:\n"
                "  1) 하네스대로 진행 — /task-start 부터 (plan → L1 평가 → G1 승인 후 구현)\n"
                "  2) 진행 중 task 라면 — 해당 plan 의 acceptance_freeze:true + scope_paths 가 이 경로를 포함하는지 확인\n"
                "  3) 작은 수정/오타 — 단일 라인 ≤120자면 자동 통과 (분할 편집)\n"
                "  4) 긴급/의도적 우회 — HARNESS_SKIP_HARNESS=1 (.env.local 또는 shell env)"
            ),
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False))

    except (json.JSONDecodeError, KeyError, ImportError):
        # fail-open — 게이트 결함이 도구 실행을 막지 않음 (보수적)
        pass


if __name__ == "__main__":
    main()
