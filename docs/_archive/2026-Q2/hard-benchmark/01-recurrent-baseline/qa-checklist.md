# QA 체크리스트 — recurrent-baseline

## Acceptance (G1 freeze 대조)
- [x] AC1 — 사전약정 판정(rec−ff > max std): +0.79 > 0.33 → LOAD-BEARING ✅
- [x] AC2 — non-vacuity/correctness: recurrent curve 상승 + matched eval 경로 ✅
- [x] AC3 — 무회귀 + feedforward byte-identical (419→423) ✅
- [x] AC4 — G2 (mypy·ruff·pytest·build) ✅
- [x] AC5 — 정직 보고 + Q1 보정 ✅

## 사전약정 무결성
- [x] 규칙(rec−ff > max(std)) 데이터 전 고정(plan freeze)
- [x] freeze 대상 = 결정규칙(결과 아님)
- [x] matched eval(동일 protocol)로 ff/rec 비교 — eval 경로 차이로 인한 가짜 effect 차단
- [x] FF가 더 넓은데도(h256 > GRU h128) floor → 이득=memory(capacity 아님) 보강

## 회귀 가드
- [x] feedforward `init_params`/`apply_policy`/`train`/`train_ppo`/`evaluate_gym_clears` 무변경
- [x] 기존 419 tests green (423 = 419 + 4)
- [x] recurrent=추가 API만 — `test_jax_{train,ppo}`·ppo_baseline·reproduce_results 무회귀

## 정직성 가드 (과대 금지)
- [x] "메모리 load-bearing"을 robust(std-separated)로만 주장
- [x] **Q1 보정**: robust headroom=feedforward 한정, recurrence가 18%→46% 회복 — 숨기지 않고 명시
- [x] recurrent도 46%서 잔존 → "풀림/이미 hard" 금지
- [x] A2C 한정·recurrent PPO 후속·3 seed·CPU·param-match 아님·oracle proxy 명시
- [x] grid16 inconclusive(A2C 학습 불가) 정직 기록
