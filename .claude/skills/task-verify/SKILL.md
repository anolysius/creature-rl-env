---
name: task-verify
description: |
  rules/80 §G2 DoD 기준으로 1회 검증 (L2 inner check + G2 게이트).
  TDD + 런타임 체크 + hook + 자동수정 통합. /task-loop 의 inner step 또는 사용자 명시 호출.
argument-hint: "[plan-path] (optional, 기본=최신 plan + 매칭 qa-checklist)"
allowed-tools: Bash, Read, Edit, Glob, Grep, Agent
domain: lifecycle
---

# Task Verify (L2-inner — 🧪 단일 검증 + G2 — ✅ 완료 판정, DoD)

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의 **L2 inner check** + **G2 DoD 게이트** 동시 담당. `/task-loop` 가 매 iteration 내부에서 호출하거나 사용자가 명시 호출.

---

## 입력

```
/task-verify                                              # 최신 plan + qa-checklist 자동 탐지
/task-verify docs/_active/<slug>/plan.md     # 명시 경로
```

---

## Mode 분기 (rules/80 §F mode tiering)

| Mode | task-verify 동작 |
|---|---|
| 🟢 quick-fix | **skip 가능** — acceptance 가 산출물 존재로 자동 충족 시. 사용자 컷오프로 task-review 직행 가능 |
| 🟡 standard | 현재 정책 그대로 (4 단계 모두) |
| 🔴 heavy | standard + L2-outer cap=8 (task-loop) |

mode 부재 = standard. quick-fix mode skip 시 task-review 직행 — 단 plan/qa-checklist 의 acceptance 가 read-only 검증 가능 (e.g. JSDoc 추가, 1줄 수정) 한정.

## 동작 (4 단계)

### Step 1: 입력 수집

- `plan.md` + 매칭 `qa-checklist.md` 읽기 (G1 통과 시 freeze 된 acceptance)
- G2 DoD 판정 기준 = rules/80 §G2 (도메인별 default + 합산 알고리즘은 §G2 에 정의)
- `iteration log` 확인 (.session-log/task-loop-{slug}-iterations.json)
- plan frontmatter `mode:` — quick-fix 인지 확인 (skip eligibility)

### Step 2: 검증 분류 + 실행

acceptance 항목을 분류하여 적절한 도구로 병렬 실행:

| 분류 | 도구 | 처리 |
|---|---|---|
| **TDD** (`type_check`, `lint`, `unit_tests`, `build`) | `scripts/run-tdd.py` | pytest/build wrapper |
| **Hook** (프로젝트 가드 hook 의 pass 항목) | 직접 호출 (Python) | hook 별로 dry-run (있을 때만) |
| **Runtime** (`smoke_run`, 동작 체크) | `scripts/run-browser-check.py` | optional — 런타임/동작 체크 (env 실행, 필요 시 MCP browser). 순수 라이브러리 task 는 skip |
| **Manual** (plan-specific 한 줄) | 사용자 마킹 | qa-checklist 의 체크박스 |

**병렬 실행** (단일 메시지 multiple Bash tool):
- TDD 그룹 → run-tdd.py (background 가능)
- Hook 그룹 → 각 hook 직접 호출 (있을 때만)
- Runtime 그룹 → run-browser-check.py (런타임/동작 검증이 필요할 때만)

### Step 3: 자동수정 (whitelist)

`scripts/auto-fix.py` 호출. **안전한 whitelist 변환만** (프로젝트 lint/format 도구):
- lint autofix (예: `ruff --fix` — unused import, 사소한 위반)
- format (예: `ruff format` / `black` — 들여쓰기, 공백, quote style)

화이트리스트 외 자동수정 시도 시 BLOCK + 사용자 승인 요청.

> 주의: `auto-fix.py` 는 copied harness 의 공용 스크립트라 web 전용 변환 규칙도 내장하나, 이 프로젝트 소스(.py)엔 매칭되지 않아 사실상 lint/format autofix 만 발동한다.

### Step 4: G2 판정 + 리포트 갱신

rules/80 §G2 DoD 의 G2 판정 로직 적용:

| Decision | 조건 | 다음 |
|---|---|---|
| `G2_PASSED` | 모든 acceptance pass | L3 진입 권유 (`/task-review`) |
| `PARTIAL` | 일부 fail | task-loop 재시도 |
| `CRITICAL_BLOCKER` | type_check/build 실패 | **즉시** 사용자 (재시도 무의미) |

iteration log 갱신:
```json
.claude/.session-log/task-loop-{slug}-iterations.json
{
  "iter": N,
  "verify_result": "pass|partial|fail|critical",
  "results": {"type_check": "pass", "unit_tests": "fail", ...},
  "fixed": ["format: 3건"],
  "remaining_blockers": [...],
  "ts": "..."
}
```

---

## 사용자 응답 형식

### G2_PASSED

```
✅ G2 통과 — 모든 acceptance pass

lifecycle:
  ✅ type_check / lint / unit_tests / build

runtime:
  ✅ smoke_run (env reset/step 정상)

다음 단계: L3 (Multi-reviewer) — /task-review 호출
```

### PARTIAL

```
⚠️ PARTIAL — task-loop 재시도 권장

통과: type_check, lint
실패:
  - unit_tests: tests/test_env.py:42 reward 경계 assert 실패
  - smoke_run: env.step() 중 KeyError (critter_env.py:18)

자동수정 시도:
  - format: 3건 적용 (ruff format)

남은 blocker (사용자 개입 필요):
  - tests/test_env.py:42 reward 클리핑 로직 수동 점검
  - critter_env.py:18 의 observation dict 누락 키 — 코드 수정 필요

→ /task-loop 재호출 또는 수동 수정 후 /task-verify
```

### CRITICAL_BLOCKER

```
🚨 CRITICAL — 즉시 중단 (재시도 무의미)

type_check FAIL:
  src/critter_gym/envs/critter_env.py:23
  Argument of type "str" is not assignable to parameter of type "int"

빌드/타입 오류는 자동수정 불가. 코드 수정 후 /task-verify 재호출.
```

### MAX_ITERATIONS_REACHED (task-loop 가 호출 시)

```
🚫 MAX 5 iteration 도달 — 자동 에스컬레이션

iteration log:
  1: PARTIAL (3 blockers)
  2: PARTIAL (2 blockers, 1 자동수정)
  ...
  5: PARTIAL (1 blocker — 동일)

남은 blocker: <한 줄>
→ 사용자 직접 수정 후 /task-verify, 또는 plan 재검토
```

---

## 비용 모델 (cross-vertical-scenarios.md)

| 항목 | 추정 |
|---|---|
| run-tdd 1회 (pytest unit) | 0 (LLM 미호출) |
| Hook 직접 호출 | 0 (deterministic) |
| Runtime/MCP 1 round (있을 시) | ~3k tokens (런타임 관찰) |
| auto-fix dry-run | 0 (script) |
| qa-verifier 격리 호출 (선택) | ~3k Haiku — `_lib/qa_verifier_prompt.py` helper 사용 ([task-evaluate SKILL.md](../task-evaluate/SKILL.md#agent-별-prompt-가이드-malformed-방지) 참조) |

**1 verify**: 평균 ~3-5k tokens (런타임 체크 동반), 0 (순수 라이브러리/문서 작업)

---

## TDD 가드 협업 (optional — 가드 hook 이 있을 때만)

TDD 가드 hook 이 도입되어 있으면 매 PostToolUse 시 발화:
1. 편집된 소스 파일 (`.py` 등) 에 대응하는 test 가 먼저 작성됐는지 조회
2. test 부재 → "BLOCK: TDD violation: test 우선 작성"
3. task-verify 가 verdict 수집 시 가드 verdict 포함
4. BLOCK 감지 시 PARTIAL → task-loop 가 Red 단계 회귀 (test 작성 우선)

> 이 프로젝트엔 전용 TDD 가드 hook 이 없다. 위는 가드 도입 시 발동하는 협업 명세이며, 부재 시 메인이 대응 test 존재 여부를 휴리스틱으로 점검한다. 강제 정책은 rules/80.

---

## 다이어그램 매핑

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의:
- **L2-inner check** (각 iteration 의 검증)
- **G2 DoD 게이트** (자동 판정)

`/task-loop` 가 본 Skill 을 매 iteration 호출. 직접 호출도 가능 (구현 후 1회 검증).
