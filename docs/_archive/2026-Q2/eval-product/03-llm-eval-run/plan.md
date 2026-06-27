---
slug: llm-eval-run
initiative: eval-product
status: active
started: 2026-06-27
acceptance_freeze: true
domains: [rl-env]
mode: standard
task_type: general
scope_paths:
  - src/critter_gym/eval_harness.py
  - scripts/llm_eval_run.py
  - tests/test_eval_harness.py
extracted_to: []
supersedes: []
---

# Real-LLM sealed-eval 러너 (비용-제한) — 프런티어 LLM이 우리 환경서 몇 %? (eval-product #3)

> 작성일: 2026-06-27 | 상태: 계획

## 목표

"우리 시뮬 난이도가 *프런티어 LLM* 기준 어느 정도?"를 **실측**하기 위한 러너. #2 `LLMAgent` +
`anthropic_complete`로 실제 모델(예: `claude-opus-4-8`)을 #1 봉인 set서 `score_agent` 채점 →
**frac_of_oracle**(전문가 대비 %)를 낸다. 단 매 스텝 LLM 호출이라 **비용/시간 폭증** → 러너에 **월드 수 +
스텝 상한**을 넣어 *작은 첫 측정*(예: 3월드×40스텝≈120콜)부터 안전하게.

**실행은 사용자 로컬**(API 키는 사용자 것·채팅 금지). 러너 자체(스크립트+상한 메커니즘)는 **stub로 CI 검증**
(무-API). 사용자가 키 set 후 `python scripts/llm_eval_run.py --model … --worlds 3 --max-steps 40` 실행 →
출력 숫자 회수.

## 선행 조건

- #1 `eval_harness`: `SealedEvalSet`/`score_agent`/`Scorecard`. #2 `llm_eval`: `LLMAgent`/`anthropic_complete`.
- `SealedEvalSet`가 현재 `max_steps` 노브 없음(env_factory가 CritterEnv 기본 max_steps=200) → 비용 상한 위해
  **추가 필요**(additive·기본 200 = byte-identical).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/eval_harness.py` | `SealedEvalSet`에 **`max_steps: int = 200`** 추가(env_factory의 CritterEnv에 전달; 기본 200=무회귀) | 저 | 비용 상한용. 기존 호출 byte-identical(기본값) |
| `scripts/llm_eval_run.py` | 신규 | 저 | CLI 러너(`--model`/`--worlds`/`--max-steps`/`--num-types`); **비용 경고** 출력 + `LLMAgent(anthropic_complete(model))` 채점 + frac_of_oracle/oracle/blind 출력 |
| `tests/test_eval_harness.py` | `max_steps` 테스트 추가 | 저(test) | max_steps가 에피소드 길이를 캡하는지(작은 값서 빠름)·기본 200 무회귀 |

### 영향 범위

- `SealedEvalSet(max_steps=200)` 기본 = 기존 동작 byte-identical → #1/#2 테스트 회귀 0. 러너는 신규 독립 스크립트.

## Step별 계획
> 커밋 경계: lifecycle 끝 1 커밋(관례).
1. **(red)** `tests/test_eval_harness.py`에 추가: (a) `SealedEvalSet(max_steps=8)`로 score_agent 시 에피소드가
   ≤8스텝서 종료(stub agent로 빠르게 — 호출 수/시간으로 캡 확인) (b) 기본 max_steps=200 무변경(기존 테스트 유지).
2. **(green)** `eval_harness.py`: `SealedEvalSet.__init__(max_steps=200)` + `env_factory`가 CritterEnv에
   `max_steps=` 전달. 기존 필드/로직 무변경.
3. **(green)** `scripts/llm_eval_run.py`: argparse(`--model claude-opus-4-8`/`--worlds 3`/`--max-steps 40`/
   `--num-types 8`). 시작 시 **예상 콜 수(worlds×max_steps×arm)+비용 경고** 출력. `LLMAgent(anthropic_complete(
   model))`를 `SealedEvalSet(max_steps=…)`서 `score_agent` → frac_of_oracle·oracle·blind·subgoal rate 출력 +
   정직 caveat(작은 표본·step 상한·proxy oracle). 키 없으면 `anthropic_complete`의 명확 에러 전파.
4. **(verify)** mypy·ruff·pytest(stub만·무-API·무회귀)·build clean.

## 검증 방법
- pytest: max_steps 캡 테스트 + 기존 461 무회귀. mypy/ruff/build clean. (실제 LLM run은 사용자 로컬·키 필요·CI 아님.)
- 러너의 비용 상한(worlds×max_steps)·비용 경고·정직 출력이 코드로 확인. stub로 score_agent 경로 검증.

## 리스크
- **R1 비용/시간 폭증**: 매 스텝 LLM 호출. **완화**: max_steps+worlds 상한 + 시작 시 예상 콜/비용 경고.
  기본을 작게(3월드·40스텝).
- **R2 키 노출**: API 키가 채팅/로그에 남으면 위험. **완화**: 실행은 사용자 로컬, 키는 사용자 env. 러너는
  키를 인자로 받지 않고 SDK가 env(`ANTHROPIC_API_KEY`)서 읽음. 채팅에 키 붙이지 말 것 명시.
- **R3 측정 해석 과대**: 작은 표본·step 상한·proxy oracle인데 "프런티어 LLM 난이도 확정"으로 과대.
  **완화**: 출력·문서에 "작은 첫 probe·step 상한·우리 oracle proxy·단일 run·noise" 경계 명시.

## Acceptance Criteria (G1 통과 시 freeze)
- **AC1 (step 상한)**: `SealedEvalSet(max_steps=N)`가 에피소드를 N스텝서 캡(테스트: 작은 N서 run_episode가
  ≤N스텝). 기본 `max_steps=200`은 기존 동작 byte-identical(기존 #1/#2 테스트 무회귀).
- **AC2 (러너)**: `scripts/llm_eval_run.py` 존재 — argparse(model/worlds/max-steps/num-types), 시작 시
  **예상 콜 수 + 비용 경고**, `LLMAgent(anthropic_complete(model))`를 봉인 set서 `score_agent` 채점 →
  frac_of_oracle·oracle·blind·subgoal rate 출력. ruff clean. (실행=사용자 로컬·키 필요.)
- **AC3 (회귀 0 + 보안/정직)**: 기존 src(SealedEvalSet 기존 동작) byte-identical·전체 테스트 무회귀·
  mypy/ruff/build clean. 러너는 키를 인자로 안 받음(SDK env서 읽음)·"키 채팅 금지" 명시. 출력/docstring에
  "작은 첫 probe·step 상한·proxy oracle·단일 run" 정직 경계. claude-api 준수(claude-opus-4-8 기본).
- **AC4 (task-end 산출)**: INITIATIVE #3 행 + CHANGELOG 1줄(rules/80 §F.5). G1 freeze 시점 미작성.
