#!/usr/bin/env python3
"""
domain: lifecycle
harness-task-intent-nudge — UserPromptSubmit hook (rules/80 §A.6.1 넛지 계층).

사용자 발화가 기능 요청 의도((a)신설/(b)다파일 리팩터·마이그/(c)도메인·API·라우팅)로
보이고 **진행 중인 frozen task 가 없을 때** → "구현 전 /task-start 권장" reminder 를
additionalContext 로 주입. 긴 컨텍스트에서 §A.6.1 가 묻히는 lost-in-the-middle 을
recency 로 보완. 차단 X (비차단 — 오탐 비용 낮음).

stdin:  {"prompt": "...", ...}
stdout: {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
        "additionalContext": "..."}} | 빈 출력

미주입 조건: 명시 skip 발화 / 질문성 발화 / intent 미매칭 / 이미 frozen task 진행 중.
"""
import io
import json
import os
import sys

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

# 기능 요청 의도 신호 (보수적 — 강한 동사/명사만)
# 주의: "add "/"new " 의 후행 공백은 word-boundary proxy — 부분단어 오탐 회피용 (trim 금지)
_INTENT_KEYWORDS = (
    "추가", "만들", "구현", "신설", "새 ", "새로운", "페이지", "컴포넌트",
    "리팩터", "리팩토링", "마이그", "일괄", "치환", "바꿔", "교체", "도입",
    "feature", "implement", "add ", "create", "build", "refactor", "migrate",
)
# 명시 skip / 사소함 신호 → 미주입
_SKIP_KEYWORDS = (
    "작은", "그냥 해", "그냥해", "skip", "오타", "한 줄", "한줄", "사소",
    "확인만", "알려줘", "알려 줘", "설명", "뭐야", "뭔지", "왜", "어디", "어떻게",
    "?", "？",
)


def looks_like_feature_request(prompt: str) -> bool:
    lower = prompt.lower()
    if any(k.lower() in lower for k in _SKIP_KEYWORDS):
        return False
    return any(k.lower() in lower for k in _INTENT_KEYWORDS)


def has_active_frozen_task() -> bool:
    """docs/_active 에 acceptance_freeze:true plan 이 하나라도 있나 (진행 중 task)."""
    try:
        import active_plan_scope as aps
        from pathlib import Path
        root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        active = Path(root) / "docs" / "_active"
        if not active.exists():
            return False
        for plan in active.rglob("plan.md"):
            fm = aps.parse_plan_frontmatter(plan.read_text(encoding="utf-8"))
            if (fm.get("acceptance_freeze") or "").lower() == "true":
                return True
    except Exception:
        pass
    return False


def build_reminder() -> str:
    return (
        "## 🚦 하네스 안내 (rules/80 §A.6.1)\n"
        "이 발화는 **기능 요청**으로 보입니다. 바로 구현하지 말고 **`/task-start` 부터** 진행하세요 "
        "(plan → L1 평가 → G1 승인 → 구현). 제품 소스(src/**) 변경은 "
        "`harness-task-start-guard` 가 frozen plan 없이는 차단합니다.\n"
        "- 작은 수정·오타·탐색이면 이 안내를 무시하세요.\n"
        "- 긴급/의도적 우회는 `HARNESS_SKIP_HARNESS=1`."
    )


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
        prompt = data.get("prompt", "")
        if not prompt:
            return
        if not looks_like_feature_request(prompt):
            return
        if has_active_frozen_task():
            return  # 이미 진행 중 — 잔소리 안 함
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": build_reminder(),
            }
        }
        sys.stdout.write(json.dumps(output, ensure_ascii=False))
    except (json.JSONDecodeError, KeyError):
        pass


if __name__ == "__main__":
    main()
