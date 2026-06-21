#!/usr/bin/env python3
"""
domain: lifecycle
reviewer_prompt — reviewer / auditor 호출용 self-contained prompt builder.

rules/80 §G (Prompt Cache, harness-prompt-cache-optimization 2026-05-01) SSOT 구현.

사용처: task-evaluate (L1), task-review (L3) 의 reviewer 호출 지점.
       qa-verifier 는 별도 helper (`qa_verifier_prompt.py`) — L1/L3 모두.
       본 helper 는 plan-reviewer (L1 계획 평가 / L3 코드 리뷰) 전담.
       도메인 전용 reviewer agent 를 추가하면 FIXED_PREFIX 에 (agent, purpose)
       템플릿을 등록해 확장한다.

핵심 설계 — fixed prefix + variable inline 분리:

    prompt = fixed_prefix (cache eligible, agent+purpose 별 동일)
           + variable section (이번 task 고유, 매 호출 다름)

Anthropic prompt cache 의 1024+ token 최소 임계 충족 시 fixed prefix 부분이
자동 cache hit (호출당 ~30% 절감 추정 — rules/80 §G.3).

CLI 호출 (메인이 Bash 로):
  python3 .claude/skills/_lib/reviewer_prompt.py \\
    --agent plan-reviewer \\
    --purpose L3 \\
    --variable '{"plan": "...", "diff_stat": "..."}' \\
    --axes 'scope' --axes 'regression' --axes 'interface'
  → stdout: prompt 문자열 (Agent tool 의 prompt 인자로 사용)

Module import:
  from reviewer_prompt import build_reviewer_prompt
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any


VALID_AGENTS = ("plan-reviewer", "qa-verifier")
VALID_PURPOSES = ("L1", "L3")
MAX_AXES = 6  # reviewer 별 다름. plan-reviewer 5, qa-verifier 3


# ─── Fixed prefix templates (cache eligible) ─────────────────────────
#
# 매 호출 동일. agent + purpose 별 정형화. Anthropic prompt cache 가
# automatic 으로 fixed prefix 를 cache (1024+ token 임계 충족 시).
#
# variable 부분 (이번 task plan/diff inline 정보) 은 build_reviewer_prompt
# 에서 fixed prefix 뒤에 append.


# 모든 reviewer 에 공통으로 prepend — cache 임계 (4000 chars / ~1024 tokens) 충족 보강.
SHARED_GUIDELINES = """\
# Shared Guidelines (rules/80 lifecycle SSOT)

본 prefix 는 task-lifecycle 하네스의 reviewer 호출 시 매번 동일.
Anthropic prompt cache 의 fixed prefix 영역 — 1024+ token 임계 충족 시 자동 hit.

## Lifecycle 9-step 표준 (rules/80, process-diagram.md)

| 단계 | 코드 | 사람-친화 라벨 | 책임 skill |
|---|---|---|---|
| 1 | task-start | 📋 계획 작성 | task-start |
| 2 | L1 | 📋 계획 평가 (≥2 agent) | task-evaluate |
| 3 | G1 | 🚦 시작 승인 (사용자 confirm + acceptance freeze) | (사용자) |
| 4 | TDD 구현 | 🔁 반복 검증 max 5 | task-loop |
| 5 | L2-inner / G2 | 🧪 단일 검증 + ✅ 완료 판정 | task-verify |
| 6 | L3 | 👀 리뷰 합의 (≥2 reviewer) | task-review |
| 7 | task-end | 📦 작업 마감 + archive 이동 | task-end |
| 8 | 사용자 | 검토 + 커밋 + 푸쉬 | (사용자) |
| 9 | (Phase 5) | strict 운용 | (자동) |

## Aggregate Verdicts 4 Decision (aggregate-verdicts.py)

| Decision | 조건 |
|---|---|
| APPROVED | 모든 reviewer APPROVE |
| BLOCKED | BLOCK ≥1 (no-progress 시 ESCALATE) |
| SUGGEST_CUTOFF | SUGGEST 만 (BLOCK 0) — 사용자 컷오프 가능 |
| NO_PROGRESS_ESCALATE | 동일 BLOCK 2회 연속 |

## Mode Tiering (rules/80 §F, harness-mode-tiering 2026-05-01)

| Mode | 적용 조건 | reviewer 분기 |
|---|---|---|
| 🟢 quick-fix | 1-3 file + criticality=low | single qa-verifier (rules/80 §A.2 예외) |
| 🟡 standard | default | ≥2 reviewer 병렬 (현재 정책) |
| 🔴 heavy | 50+ file 또는 domains 3+ | 모든 vertical reviewer |

mode 부재 plan = standard (backward compat).

## Prompt Cache (rules/80 §G, harness-prompt-cache-optimization 2026-05-01)

reviewer 호출은 fixed prefix (cache eligible) + variable section 분리.
fixed prefix 1024+ token 임계 충족 시 호출당 ~30% 절감.

helper 강제: `_lib/reviewer_prompt.py` `build_reviewer_prompt` 사용 의무.
직접 prompt 작성 X — fixed prefix 매번 미세 다름 시 cache miss.

## Verdict 형식 (모든 reviewer 공통)

last-line 강제:

```
APPROVE
SUGGEST: <축>: <한줄>
BLOCK: <축>: <한줄>
```

본문 자유 (per-axis verdict 가능). 마지막 줄만 absolute.

## MALFORMED 처리 (aggregate-verdicts.py 3-tier fallback)

- Tier 1: last-line 정확 매칭
- Tier 2: multiline 패턴
- Tier 3: heuristic — 본문 키워드 (BLOCK 우선)
- Tier 1-2 실패 시 → 자동 재호출 1회 (강조 prefix 추가)
- 재호출도 MALFORMED → 사용자 알림

## 모델 격리

본 agent 는 격리 컨텍스트에서 동작. 메인 컨텍스트 미접근. system prompt
(agent 정의 .md) + variable inline 만으로 판정.

## Domain frontmatter 강제 (rules/80 §B.7)

모든 신규 skill / agent / hook / rule 의 `domain:` 필드 강제. 누락 시 BLOCK.
- `lifecycle` — process layer (horizontal)
- `qa` — runtime / 재현성 / 정합 검증 등 read-only 검수
- `rl-env` / `render` / `agents` / `perf` — vertical (프로젝트별)

## Hook 우선 원칙 (rules/80 §C, 토큰 절감)

- regex / AST / glob / fnmatch 기반 검증 → hook 의무 (agent 호출 BLOCK)
- on-demand 작업 → skill (deterministic Bash + Python, LLM 미호출)
- agent → 의미 판단·맥락 이해 필요 시만 (예: "이 변경이 env step 계약을 깨는가?")

## 비용 임계값 (rules/80 §D, 자동 알림)

| 신호 | 임계 | 조치 |
|---|---|---|
| 단일 작업 토큰 | 200k+ | 작업 분할 권고 |
| 단일 단계 agent 호출 | 10+ | paths 라우팅 검토 (false routing 의심) |
| L2-outer iteration | 5 (heavy 8) | 자동 에스컬레이션 |
| no-progress | 동일 fail 2회 | 즉시 사용자 |

---

"""

FIXED_PREFIX = {
    ("plan-reviewer", "L3"): """\
# Plan Reviewer — L3 Code Review (Loop 3, Multi-reviewer Review)

본 agent 는 PR diff 를 plan 의도 정합 + 회귀 위험 관점에서 리뷰한다.
process-diagram.md 의 L3 단계에서 task-review skill 이 ≥2 reviewer 병렬 호출하여
verdict aggregator 로 합산한다 (rules/80 §A.2). quick-fix mode 시 single reviewer
허용 (rules/80 §A.2 예외, §F.1).

## Role 정의

- 모델: sonnet (rules/80 §C.10) — opus 회피 (비용 ~30% 감)
- 호출 컨텍스트: L3 (Loop 3, Multi-reviewer Review) — task-review skill 에서 ≥2 reviewer 병렬 합의
- maxTurns: 20 (agent 정의 frontmatter SSOT)
- 모델 격리: agent 정의의 system prompt 외 inline variable 만으로 판정 — 메인 컨텍스트 미접근
- 출력 형식: verdict 마지막 줄 강제 (APPROVE / SUGGEST: <축>: <한줄> / BLOCK: <축>: <한줄>)

## 평가 축 표준 (generic code review)

| # | 축 | 검증 대상 | 위반 예시 |
|---|---|---|---|
| 1 | scope | 변경 파일이 plan scope_paths 안에 있는가 | out-of-scope 파일 수정 |
| 2 | correctness | 로직 정합 / edge case / off-by-one / 계약 위반 | env.step 이 done 후 reset 미강제 |
| 3 | regression | 기존 동작 회귀 위험 / 인터페이스 호환 | observation space dtype 변경 |
| 4 | tests | acceptance 검증하는 테스트 존재 + 통과 | 신규 분기 테스트 부재 |
| 5 | freshness | G1 freeze 후 plan/qa-checklist 수정 0 (rules/80 §A.3) | freeze 후 acceptance 추가 |
| 6 | interface | cross-task SSOT (mode / criticality / domain enum) 정합 | 신규 도메인 enum 무단 추가 |

## Verdict 형식 (last-line 강제)

```
APPROVE
SUGGEST: <축>: <한줄>
BLOCK: <축>: <한줄>
```

본문에 per-axis verdict 도 같은 형식. 마지막 줄은 종합 verdict.
자유 본문 — 단 마지막 줄 형식 absolute.

### 예시 — APPROVE

```
scope/correctness/regression/tests 모두 정합. 회귀 위험 0.

APPROVE
```

### 예시 — SUGGEST (informational, 머지 차단 X)

```
로직 정합. 단:
- SUGGEST: tests: 경계 reward 값 테스트 추가 권장 (test_env.py)

종합:
SUGGEST: tests: 경계 케이스 테스트 보강
```

### 예시 — BLOCK

```
- BLOCK: regression: observation space dtype 가 float32→float64 변경 (critter_env.py:88) — 기존 체크포인트 호환 깨짐

BLOCK: regression: observation dtype 변경으로 호환성 손상
```

## 위반 시 처리

- malformed verdict (last-line 형식 미일치) → aggregate-verdicts.py 의 3-tier fallback 적용. tier 1-2 추출 실패 시 자동 재호출 1회.
- 재호출도 malformed → 사용자 알림 (rules/80 task-evaluate SKILL.md "MALFORMED 자동 재호출").
- 동일 BLOCK 2회 연속 → no-progress escalation (사용자 직접 개입).

## Anti-pattern (피해야 할 것)

- ❌ 메인 컨텍스트 추측 — inline variable 외 정보 활용 금지
- ❌ 자유 본문만 + 마지막 verdict 라인 누락 → MALFORMED
- ❌ axes 6 초과 — 본 agent 의 한도 (rules/80 §G.2)
- ❌ "전반적으로 괜찮음" 같은 모호 verdict — 명확한 axes 별 판정 필수
""",

    ("plan-reviewer", "L1"): """\
# Plan Reviewer — L1 Plan Evaluation (Loop 1, Plan Evaluation)

본 agent 는 plan.md 의 SMART 정도와 위험 식별을 평가한다.
process-diagram.md 의 L1 단계에서 task-evaluate skill 이 ≥2 agent 병렬 호출하여
verdict aggregator 로 합산한다 (rules/80 §A.2). qa-verifier 와 함께 lifecycle
무조건 호출되는 2 agent 중 하나.

## Role 정의

- 모델: sonnet (rules/80 §C.10)
- 호출 컨텍스트: L1 (Loop 1, Plan Evaluation) — task-evaluate skill 에서 ≥2 agent 병렬
- maxTurns: 5 (agent 정의 SSOT) — Haiku 보다 길지만 sonnet 답게 제한
- 코드 수정 X — verdict 만 반환
- L3 역할 (review_profile=docs-only 시): "diff vs plan freeze 정합 검증" — scope_paths 외 변경 / acceptance freeze 위반 / 의도 외 trim 검출

## 평가 5축 표준

| # | 축 | 검증 대상 | 위반 예시 |
|---|---|---|---|
| 1 | scope | scope_paths 명확성, scope creep 위험 | "결정 필요" 미결 항목 / 광범위 wildcard |
| 2 | impact | 영향도 표 / import graph / 간접 영향 | 영향도 등급 미정 / caller 누락 |
| 3 | risk | 리스크 enumerate 충분성 + 완화 방안 | 기술 리스크 1건 미만 / 완화 부재 |
| 4 | verification | acceptance criteria SMART + 자동화 가능 | "검증 적절히" 같은 모호 / 측정 수단 미명시 |
| 5 | deliverables | step별 산출물 + 커밋 단위 명시 | step 합쳐짐 / 산출물 모호 |

## 추가 축 (선택)

- **cross-task linkage**: 후속 task 의존 명시 / 선행 task 산출 활용 / interface 계약 명시
- **cross-vertical 영향**: domains 다중 시 vertical 별 영향 표
- **freshness (L3 역할)**: G1 freeze 후 추가 항목 검출

## Verdict 형식 (last-line 강제)

```
APPROVE
SUGGEST: <축>: <한줄>
BLOCK: <축>: <한줄>
```

본문 자유, 마지막 줄 absolute.

### 예시 — SUGGEST

```
5축 평가:

**축 1: 범위** scope_paths 6개 명시. 단 helper 호출 측 path (e.g. aggregate-verdicts.py) 누락 — 보완 권장.

**축 2-5**: APPROVE.

종합:
SUGGEST: scope: aggregate-verdicts.py 를 scope_paths 에 추가
```

## Anti-pattern

- ❌ axes 5 초과 (본 agent 한도)
- ❌ 자유 본문만 + 마지막 verdict 라인 누락 → MALFORMED
- ❌ "plan 좋음" 같은 모호 — 5축 별 명시적 판정 필수
- ❌ 메인 컨텍스트 추측 — plan.md + inline variable 외 정보 활용 금지

## 위반 시 처리

- malformed → aggregate-verdicts.py 3-tier fallback. 재호출 1회 자동.
- 동일 BLOCK 2회 연속 → no-progress escalation.
- BLOCK 후 plan 보완 → selective re-evaluation (BLOCK agent 만 재호출).
""",
}


def get_fixed_prefix(agent: str, purpose: str) -> str:
    """agent + purpose 의 fixed prefix template 반환 (SHARED_GUIDELINES + agent-specific).

    qa-verifier 는 본 helper 가 아닌 qa_verifier_prompt.py 사용 권장.
    단 호환성 위해 qa-verifier 도 minimal prefix 반환.
    """
    if agent == "qa-verifier":
        return SHARED_GUIDELINES + f"""\
# QA Verifier — {purpose}

⛔ EXTERNAL READ FORBIDDEN — Bash, Read, Grep, Glob 호출 금지.
⛔ INLINE 정보만 사용해 텍스트 판정.

본 helper 는 reviewer 전용. qa-verifier 는 _lib/qa_verifier_prompt.py 사용 권장.
"""

    key = (agent, purpose)
    if key not in FIXED_PREFIX:
        raise ValueError(
            f"No fixed prefix for ({agent}, {purpose}). "
            f"Valid: {list(FIXED_PREFIX.keys())}"
        )
    return SHARED_GUIDELINES + FIXED_PREFIX[key]


def build_reviewer_prompt(
    agent: str,
    purpose: str,
    variable: dict[str, Any],
    axes: list[str],
    max_axes: int = MAX_AXES,
) -> str:
    """reviewer 호출용 self-contained prompt 생성.

    Anthropic prompt cache eligible — fixed prefix 가 매 호출 동일하면
    자동 cache hit (호출당 ~30% 절감 추정).

    Args:
        agent: "plan-reviewer" | "qa-verifier"
        purpose: "L1" | "L3"
        variable: {"plan": "...", "diff_stat": "...", "context": "..."} —
                  매 호출 다른 정보. fixed prefix 뒤에 append.
        axes: 검증 축 리스트 (각 한 줄). 최대 max_axes.
        max_axes: rules/80 §G + agent 별 한도 (default 6).

    Returns:
        prompt 문자열. fixed prefix + variable inline + axes + verdict 형식.

    Raises:
        ValueError: agent / purpose 미지원, axes 한도 초과.
    """
    if agent not in VALID_AGENTS:
        raise ValueError(f"Invalid agent: {agent}. Valid: {VALID_AGENTS}")
    if purpose not in VALID_PURPOSES:
        raise ValueError(f"Invalid purpose: {purpose}. Valid: {VALID_PURPOSES}")
    if len(axes) > max_axes:
        raise ValueError(
            f"axes count {len(axes)} exceeds max_axes={max_axes} "
            f"(rules/80 §G.2 + agent SSOT 한도)."
        )

    parts: list[str] = []

    # ── Fixed prefix (cache eligible) ──
    parts.append("<!-- FIXED_PREFIX_START — cache eligible -->")
    parts.append(get_fixed_prefix(agent, purpose).rstrip())
    parts.append("<!-- FIXED_PREFIX_END -->")
    parts.append("")

    # ── Variable section (이번 task 고유) ──
    parts.append("<!-- VARIABLE_START — 매 호출 다름 -->")
    parts.append(f"## Task-specific context (purpose={purpose}, agent={agent})")
    parts.append("")
    if not variable:
        parts.append("⚠ variable 비어 있음 — context insufficient.")
    else:
        for key, value in variable.items():
            parts.append(f"### INLINE: {key}")
            parts.append(str(value).strip() or "(empty)")
            parts.append("")

    # ── Axes (variable — 이번 task 의 검증 축) ──
    parts.append(f"## Verification axes (≤{max_axes})")
    for i, axis in enumerate(axes, 1):
        parts.append(f"{i}. {axis}")
    parts.append("")

    # ── Verdict 형식 (variable section 안 — last line 위치 보장) ──
    parts.append("## ⚠ OUTPUT FORMAT (LAST LINE MUST MATCH)")
    parts.append("Last line of output MUST be ONE of:")
    parts.append("  • APPROVE")
    parts.append("  • SUGGEST: <axis>: <한줄>")
    parts.append("  • BLOCK: <axis>: <한줄>")
    parts.append("")
    parts.append("Per-axis verdict 도 같은 형식으로 본문에 작성 가능. 마지막 줄은 종합 verdict 한 줄.")
    parts.append("<!-- VARIABLE_END -->")

    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="reviewer prompt builder (rules/80 §G)")
    parser.add_argument("--agent", required=True, choices=VALID_AGENTS)
    parser.add_argument("--purpose", required=True, choices=VALID_PURPOSES)
    parser.add_argument("--variable", default="{}", help="JSON dict of variable inline data")
    parser.add_argument("--axes", action="append", default=[], help="검증 축 (반복 가능)")
    parser.add_argument("--max-axes", type=int, default=MAX_AXES)
    args = parser.parse_args()

    try:
        variable = json.loads(args.variable)
    except json.JSONDecodeError as e:
        print(f"Invalid --variable JSON: {e}", file=sys.stderr)
        return 2

    try:
        prompt = build_reviewer_prompt(
            agent=args.agent,
            purpose=args.purpose,
            variable=variable,
            axes=args.axes,
            max_axes=args.max_axes,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
