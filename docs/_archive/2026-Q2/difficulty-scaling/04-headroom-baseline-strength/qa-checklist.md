# QA 체크리스트 — headroom-baseline-strength

## Acceptance (G1 freeze 대조)
- [x] AC1 — 사전약정 3-branch (a/b/c) 적용, 결과 (a) headroom-ROBUST ✅
- [x] AC2 — non-vacuity (best-strong > tiny) ✅ (vacuous deep config 가드가 포착)
- [x] AC3 — 무회귀 + depth=1 byte-identical ✅ (415→419)
- [x] AC4 — G2 (mypy·ruff·pytest·build) ✅
- [x] AC5 — 정직 보고 (robust=cheap-scaling 한정, SOTA 미배제, oracle proxy) ✅

## 사전약정 무결성 (p-hacking 가드)
- [x] frac=0.75·k=1.0 데이터 전 고정 (plan freeze)
- [x] freeze 대상은 결과 아닌 *결정규칙* — 결과가 (a)/(b)/(c) 어디든 보고
- [x] non-vacuity 가드가 "망가진 깊은 net의 공허한 robust"를 실제로 차단(d2 0.33 < tiny 0.56 → vacuous 판정)
- [x] budget-plateau 검증(i600–4000)으로 "budget만 더 주면 닫힌다" 반론 선제 차단

## 회귀 가드
- [x] depth=1·hidden64 default byte-identical (A2C `train`·기존 PPO 무변경)
- [x] 415 기존 테스트 전부 green (419 = 415+4)
- [x] `init_params`/`apply_policy` depth≥2 shape·forward·train smoke

## 정직성 가드
- [x] (a) "robust"를 *cheap feedforward 스케일링 한정*으로 명시, SOTA/recurrent/대형/HP-튜닝 미배제
- [x] oracle=scripted proxy, 3 seed·CPU 한계 명시
- [x] capacity(depth 하락)·budget(plateau) 비단조성을 숨기지 않고 표로 노출
- [x] Q2(부분관측)가 *더 강한 agent 대비* 절대 난이도엔 여전히 동기임을 정직 기록(과대 "이미 hard" 금지)
