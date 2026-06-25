---
slug: recurrent-baseline
initiative: hard-benchmark
status: active
started: 2026-06-25
mode: standard
task_type: general
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/jax_train.py
  - scripts/recurrent_baseline.py
  - tests/test_jax_recurrent.py
  - docs/explanation/jax-throughput.md
  - docs/explanation/competitive-analysis.md
  - docs/_active/difficulty-scaling/INITIATIVE.md
extracted_to: []
supersedes: []
---

# 메모리는 load-bearing인가 — 부분관측 하 recurrent vs feedforward (hard-benchmark #1)

> 작성일: 2026-06-25 | gap register: "a hard benchmark" + Q1 헤드라인 정직 보정

## 목표 (연구 질문 + 검증된 답)

**질문**: CritterGym의 난이도가 *메모리를 요구하는 부분관측 과제*인가? — 즉 부분관측(작은 시야) 하에서
**메모리 있는(recurrent) agent가 메모리 없는(feedforward) agent보다 본질적으로 잘하는가**(메모리 load-bearing)?

**왜**: `headroom-baseline-strength`(Q1)가 "headroom이 cheap *feedforward* 스케일링에 robust"를 입증하며
**"recurrent 미배제"**를 명시 caveat로 남김. 부분관측 scout가 "시야 줄이기"를 falsify하고 지도-스케일을
가리켰으나 grid16은 A2C가 학습 불가(inconclusive). → **정확한 질문 = 부분관측 하 메모리 load-bearing 여부**.

**freeze 전 pilot(검증됨, 3 seed matched eval)**: grid10/patch2(5×5 view) commit world, oracle 2.81:
- feedforward A2C **0.25±0.10 (9% of oracle)** vs recurrent(GRU) A2C **1.42±0.28 (50% of oracle)**.
- **memory effect +1.17, std-separated → 메모리 load-bearing = True.** feedforward가 *더 넓은데도*(h256 vs
  GRU h128) floor → 이득은 **recurrence(메모리)이지 capacity 아님**.

**산출물**: (1) 검증된 recurrent A2C를 `jax_train`에 정식 추가(feedforward 무변경), (2) 재현 가능 측정
스크립트 + 사전약정 규칙, (3) "메모리 load-bearing" 결과 도큐멘트 + **Q1 헤드라인 정직 보정**.

## 선행 조건

- main HEAD `4af4f87`, 419 tests green. `jax_train`: feedforward `init_params`/`apply_policy`/`train`(A2C)/
  `evaluate_gym_clears`/`make_rollout`/`a2c_loss`/`_returns`/`_reset_where`/Adam. env config-driven
  (`JaxEnvConfig` grid/patch_radius). numpy `CritterEnv`(oracle factory via `learnability.reference_arm`).
- pilot 코드(scratchpad `pilot_recurrent.py`/`verify_recurrent.py`)가 GRU rollout+loss+eval를 검증.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/jax_train.py` | 신규 recurrent API: `gru_init_params`/`gru_step`/`recurrent_policy_value`/`make_recurrent_rollout`/`recurrent_a2c_loss`/`train_recurrent`/`evaluate_gym_clears_recurrent`(jitted vmapped). **feedforward 경로 전부 무변경** | 중 (추가만; 기존 API byte-identical) |
| `scripts/recurrent_baseline.py` (신규) | 부분관측 config서 recurrent vs feedforward A2C 측정 + 사전약정 memory-load-bearing 판정 + oracle 대비 % | 중 |
| `tests/test_jax_recurrent.py` (신규) | GRU shape/forward + recurrent train smoke(curve 상승) + recurrent eval smoke + memory-effect 방향 smoke | 소 |

### 영향 범위

- 추가 API만 — `train`/`train_ppo`/`apply_policy`/`evaluate_gym_clears`(feedforward) 전부 무변경 →
  `test_jax_{train,ppo}` + ppo_baseline + reproduce_results 무회귀.

## Step별 계획

1. **(pre-freeze pilot)** = 이미 완료·검증(3 seed matched, +1.17 std-separated). plan에 박제.
2. `jax_train`: GRU recurrent API 추가(pilot 코드 정제·타입·docstring). feedforward 무변경.
3. `evaluate_gym_clears_recurrent`: jitted vmapped greedy(state+h carry, done시 h reset) — feedforward
   `evaluate_gym_clears`와 동일 카운팅(gym_defeated, argmax greedy)으로 **matched 비교** 보장.
4. `scripts/recurrent_baseline.py`: grid10/patch2(min_gyms=3) commit config서 ff vs rec A2C(≥3 seed) +
   oracle. 사전약정 판정 출력.
5. `tests/test_jax_recurrent.py`: shape/train smoke/eval smoke/memory-effect 방향.
6. 도큐멘트: jax-throughput.md(메모리 load-bearing Update) + **Q1 헤드라인 정직 보정**(difficulty-scaling
   INITIATIVE + competitive-analysis: "robust=feedforward 한정, recurrence가 부분관측 headroom 크게 회복").
7. G2 + 측정 실행.

## 검증 방법

- `pytest tests/test_jax_recurrent.py -q` green + 기존 419 무회귀.
- `scripts/recurrent_baseline.py --runs 3` 가 ff vs rec + 사전약정 판정 출력(재현).
- G2: mypy·ruff·pytest·build.

## 리스크

- **recurrent 망가지면 misleading "메모리 무용"** → non-vacuity: recurrent curve 상승 + recurrent eval가
  feedforward와 동일 경로(matched)임을 테스트로 보장. (pilot이 이미 검증.)
- **A2C 한정**(recurrent PPO 아님) → Q1(PPO) 깨끗한 연결은 후속. 정직 명시("A2C 내 memory effect; recurrent
  PPO=후속").
- **capacity 혼동** → feedforward가 더 넓은데도(h256) floor → recurrence 효과임을 명시(param-match 아님 caveat).
- **과대 "이미 hard/풀림" 금지** → recurrent도 50%에서 멈춤(headroom 잔존). "메모리 요구 부분관측 과제, 메모리
  agent가 절반 회복하나 미해결"로 정직.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (사전약정 판정, 데이터 전 고정)**: 부분관측 config(grid10/patch2/min_gyms=3, commit)서 ≥3 seed,
  matched greedy eval. **memory load-bearing iff `rec_mean − ff_mean > max(rec_std, ff_std)`**(robust 분리).
  결과를 oracle 대비 %로 보고.
- **AC2 (non-vacuity / correctness)**: recurrent가 (i) 학습 curve 상승(R1 류), (ii) feedforward와 **동일 eval
  경로**로 비교(matched) — 망가진 recurrent의 공허한 결과 차단.
- **AC3 (무회귀 + feedforward byte-identical)**: feedforward `init_params`/`apply_policy`/`train`/`train_ppo`/
  `evaluate_gym_clears` 무변경, 419 tests green.
- **AC4 (G2)**: mypy·ruff·pytest·build clean.
- **AC5 (정직 보고 + Q1 보정)**: 결과를 jax-throughput.md에 기록 + **Q1 "robust headroom"을 정직 보정**
  (robust=feedforward 한정, recurrence가 부분관측 headroom 크게 회복[9%→50%], 단 50%에서 잔존). 한계
  명시(A2C·3 seed·CPU·param-match 아님·oracle proxy·recurrent PPO 후속). 과대("풀림"/"이미 hard") 금지.
