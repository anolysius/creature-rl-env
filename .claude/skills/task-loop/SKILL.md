---
name: task-loop
description: |
  /task-verify 자율 N회 반복 (L2-outer macro loop). G1 통과 후 자동 또는 사용자 명시 호출.
  4 종료 조건 (all_passed/max_iterations/no_progress/critical_blocker) 자동 판정.
argument-hint: "[plan-path] (optional, 기본=최신 plan)"
allowed-tools: Bash, Read, Edit, Glob, Grep, Agent
domain: lifecycle
---

# Task Loop (L2-outer — 🔁 반복 검증, Loop 2 outer macro)

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의 **L2-outer macro loop** — `/task-verify` 를 자율 N회 반복하며 G2 통과까지 진행.

---

## 입력

```
/task-loop                                          # 최신 plan 자동 탐지
/task-loop docs/_active/<slug>/plan.md          # 명시 경로
/task-loop --max-iter 5                             # 최대 반복 수 override (default 2, heavy mode 8)
```

---

## 동작 (loop)

```python
iter = 0
log = load_iteration_log()  # 이전 round 기록

while iter < max_iter:
    iter += 1

    # 1) TDD 가드 협업 (optional, 가드 hook 이 있을 때만)
    if has_uncovered_changes():            # test 없는 소스 편집 (.py 등)
        log.append({"iter": iter, "result": "tdd_violation", "action": "Red 회귀 권유"})
        return Decision.TDD_VIOLATION

    # 2) /task-verify 호출 (L2 inner check)
    verify_result = invoke_task_verify(plan_path)
    log.append({"iter": iter, "verify_result": verify_result, "ts": now()})
    save_iteration_log(log)

    # 3) 4 종료 조건 판정
    if verify_result.decision == "G2_PASSED":
        return Decision.ALL_PASSED         # → L3 진입 권유

    if verify_result.decision == "CRITICAL_BLOCKER":
        return Decision.CRITICAL_BLOCKER   # 즉시 중단 (재시도 무의미)

    if is_no_progress(log):                 # 동일 fail 2회 연속
        return Decision.NO_PROGRESS_ESCALATE

    # 4) PARTIAL → 다음 iteration
    # task-verify 가 자동수정 적용했으면 효과 누적, 사용자 개입 필요한 blocker 는 사용자 알림
    if verify_result.requires_user_action:
        return Decision.USER_ACTION_REQUIRED

# loop exit (max_iter 도달)
return Decision.MAX_ITERATIONS_REACHED
```

---

## 4 종료 조건

| Decision | 조건 | 다음 단계 |
|---|---|---|
| `ALL_PASSED` | task-verify 결과 `G2_PASSED` (모든 acceptance pass) | L3 진입 권유 (`/task-review`) |
| `MAX_ITERATIONS_REACHED` | iteration 수 ≥ max_iter (default 2, heavy 8, --max-iter override) | 사용자 에스컬레이션 |
| `NO_PROGRESS_ESCALATE` | 동일 verify_result 2회 연속 (results dict 매칭) | 즉시 사용자 |
| `CRITICAL_BLOCKER` | type_check / build 실패 (task-verify 가 표시) | **즉시** 중단 (코드 수정 후 재호출) |
| `TDD_VIOLATION` | TDD 가드 (있을 시) 가 test 부재 BLOCK | Red 단계 회귀 (test 우선 작성) |
| `USER_ACTION_REQUIRED` | 자동수정 whitelist 외 위반 | 사용자 승인 후 재호출 |

---

## iteration log

`.claude/.session-log/task-loop-{plan-slug}-iterations.json`:

```json
[
  {
    "iter": 1,
    "verify_result": {
      "decision": "PARTIAL",
      "results": {
        "type_check": "pass",
        "lint": "pass",
        "unit_tests": "fail",
        "smoke_run": "fail"
      },
      "fixed": ["format: ruff --fix 3건"],
      "remaining_blockers": [
        "tests/test_env.py:42 assert reward >= 0 실패",
        "critter_env.py:18 KeyError in step()"
      ]
    },
    "ts": "2026-04-26T10:30:00"
  },
  {
    "iter": 2,
    "verify_result": {
      "decision": "PARTIAL",
      "results": {"unit_tests": "fail", "smoke_run": "fail"},
      "remaining_blockers": [
        "tests/test_env.py:42 assert reward >= 0 실패",       // 동일!
        "critter_env.py:18 KeyError in step()"                // 동일!
      ]
    }
  }
  // → no-progress 감지 (동일 blocker 2회) → ESCALATE
]
```

---

## no-progress 감지 알고리즘

```python
def is_no_progress(log: list, window: int = 2) -> bool:
    """동일 verify_result 가 window 회 연속 등장하면 no-progress."""
    if len(log) < window:
        return False
    recent = log[-window:]
    # 모든 회차의 remaining_blockers (axis+message 매칭) 가 동일한가
    blocker_sets = []
    for round in recent:
        blockers = round["verify_result"].get("remaining_blockers", [])
        # blocker 를 set 으로 (순서 무관)
        blocker_sets.append(frozenset(blockers))
    return len(set(blocker_sets)) == 1 and len(blocker_sets[0]) > 0
```

---

## TDD 가드 협업 (optional — 가드 hook 이 있을 때만)

### 매 iteration 시작 시
1. `git diff --name-only HEAD` 로 변경된 소스 파일 (`.py` 등) 추출
2. 각 파일에 대응하는 test 파일이 존재하는지 확인 (예: `src/critter_gym/envs/critter_env.py` ↔ `tests/test_env.py`)
3. 부재 시 `Decision.TDD_VIOLATION` 반환 + Red 단계 회귀 권유

### 적용 예외
- `.md` / `.json` / 설정 파일 편집은 TDD 무관
- `.claude/` 내부 자산 (skill/agent/hook 자체) 도 TDD 무관 (하네스 메타 변경)

> 이 프로젝트에 전용 TDD 가드 hook 은 없다. 위 협업은 가드가 도입되면 자동 발동하는 명세이며, 부재 시 메인이 휴리스틱(대응 test 존재 여부)으로 판단한다.

---

## 사용자 응답 형식

### ALL_PASSED

```
✅ G2 통과 — task-loop 종료 (3 iterations)

iteration log:
  1: PARTIAL (4 blockers, 자동수정 3건)
  2: PARTIAL (1 blocker, 사용자 1건 수정)
  3: G2_PASSED (모든 acceptance ✅)

다음 단계: L3 멀티 리뷰어 (`/task-review`)
```

### MAX_ITERATIONS_REACHED

```
🚫 MAX 5 iteration 도달 — 사용자 에스컬레이션

iteration log:
  1: PARTIAL (3 blockers)
  2: PARTIAL (2 blockers)
  3: PARTIAL (2 blockers)
  4: PARTIAL (1 blocker — scope creep 의심)
  5: PARTIAL (1 blocker — 동일)

남은 blocker:
  src/critter_gym/envs/critter_env.py:18 step() 의 비정상 종료 처리 (자동수정 불가)

→ 사용자 직접 수정 후 /task-verify 재호출, 또는 plan 재검토
```

### NO_PROGRESS_ESCALATE

```
🚨 NO-PROGRESS — 동일 fail 2회 연속

iteration 1, 2 모두:
  - tests/test_env.py:42 reward 경계 assert 실패 (자동수정 시도했으나 효과 X)
  - critter_env.py:18 KeyError (코드 분석 필요)

자동 수정으로 해결 불가. 사용자 직접 개입 필요.
```

### CRITICAL_BLOCKER

```
🚨 CRITICAL — 즉시 중단 (재시도 무의미)

type_check FAIL (iter 1):
  src/critter_gym/envs/critter_env.py:23
  Argument of type "str" is not assignable to parameter of type "int"

빌드/타입 오류 자동수정 불가. 코드 수정 후 /task-loop 재호출.
```

### TDD_VIOLATION

```
⚠️ TDD 위반 — Red 단계 우선

변경 감지:
  src/critter_gym/envs/critter_env.py (test 부재)

대응:
  tests/test_env.py 먼저 작성 → /task-loop 재호출

(rules/80 가 강제. 현재는 권유)
```

---

## 비용 통제 (cross-vertical-scenarios.md)

| 항목 | 한도 |
|---|---|
| max_iter | **2 (default)** — heavy mode 8 / `--max-iter` override (2026-05-04 harness-token-efficiency) |
| 1 iteration 평균 토큰 | ~5k (런타임 체크 동반 작업) / ~1k (순수 라이브러리/문서) |
| 2 iteration 합계 | ~10k (런타임 체크) / ~2k (other) — default 2 적용 후 worst case |
| no-progress 감지 시 | 즉시 종료 (낭비 방지) |
| critical blocker 시 | 즉시 종료 (재시도 무의미) |

### Iter 간 plan.md hand-off (2026-05-04, harness-token-efficiency)

iter 1 시점에 plan.md 의 핵심 (목표 + acceptance + 현 step + 직전 verify_result)
을 in-memory summary 로 잡고, iter 2 부터 plan.md re-read 회피. 매 iter ~3-5k 절감.

```python
# iter 1
plan_summary = read_plan_summary(plan_path)  # 1회 read, frontmatter + acceptance
prev_result = None

# iter 2..N
verify_result = invoke_task_verify(plan_summary, prev_result=prev_result)
prev_result = verify_result.summary  # next iter 의 hand-off
```

plan.md 자체가 iter 도중 수정되면 (G1 freeze 위반 — rules/80 §A.3) 새 task slug 강제.
즉 plan.md 는 frozen 가정 가능 → 1회 read 정합.

---

## 사용 시나리오

### 시나리오 1: G1 통과 직후 자동 호출

`/task-evaluate APPROVED → G1 통과 → qa-checklist 자동 생성 → /task-loop` 자동 권유.

### 시나리오 2: 수동 호출

사용자가 구현 중 검증 + 자동수정 사이클 원할 때.

### 시나리오 3: 디버깅

`--max-iter 1` 로 1회 verify 만 (실제 1회는 `/task-verify` 직접 호출이 더 명확).

---

## 다이어그램 매핑

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의:
- **L2-outer macro loop** (자율 반복)
- **G2 DoD 게이트 도달**

종료 조건 5종이 자율성과 비용 통제의 균형.
