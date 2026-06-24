---
slug: transfer-budget-recovery
initiative: env-core
status: completed
ended: 2026-06-24
extracted_to:
  - docs/explanation/genre-generalization.md   # (B) 결론 갱신: real but structurally bounded
changelog_entry: docs/CHANGELOG.md (env-core, transfer-budget-recovery)
---

# transfer-budget-recovery — 예산 RECOVERY + confound-reduced gap — 결과 보고서

## 1. 예산 사다리 (baseline-net, 용량 배제, 5 run, muster anchor fold)

| budget | held-in (±std) | held-out (±std) | gap (±std) |
|---|---|---|---|
| 250k (#31) | 2.442 ±0.352 | 2.487 ±0.783 | −0.046 ±0.492 |
| **400k** | **2.746 ±0.386** | 2.862 ±1.213 | −0.117 ±0.995 |
| 500k | 2.746 ±0.533 | 2.800 ±0.985 | −0.054 ±0.632 |

**사전약정 verdict = RECOVERY** (best held-in 2.75 ≥ 2.5). held-in이 400k≈500k에서 **PLATEAU ≈2.75**
(2.5 통과, #26 2.94 미만). 단일-seed pilot(400k 2.19/500k 1.39)은 또 노이즈 → **multi-run 3번째 교정**.

## 2. full-LOO confound-reduced gap @400k (RECOVERY 상태, 5 run) — 핵심 결과

| held-out | held-in (±std) | held-out (±std) | gap (±std) | 읽기 |
|---|---|---|---|---|
| critter | 2.046 ±0.671 | 3.125 ±1.096 | **−1.079 ±0.726** | 전이 OK (≤0) |
| forage | 2.542 ±0.440 | 4.025 ±0.804 | **−1.483 ±0.507** | 전이 OK (≤0) |
| **duel** | 2.650 ±0.688 | 0.925 ±0.232 | **+1.725 ±0.608** | **전이 실패 (robust 양수)** |
| muster | 2.746 ±0.386 | 2.862 ±1.213 | −0.117 ±0.995 | ≈0 |

## 3. 정직한 결론 — (B) is real but structurally bounded

- held-in이 **회복**된 상태(2.0~2.75, 평범 아님)이므로 이 gap들은 **generalist-mediocrity가 아닌 진짜 전이 신호**.
- **critter/forage/muster (gap ≤ 0)**: 학습 정책이 미학습 family에서 *그만큼/더* 잘함 = **메커닉 이웃 안에선 전이됨**.
- **duel (gap +1.73, std≪gap=robust)**: 회복된 skill(held-in 2.65)에서도 duel(타입무관 RPS/스태미나, 유일하게
  구조적으로 다른 배틀 시스템)로는 **전이 실패** = (B)의 진짜 경계.
- → **(B)는 "전이가 메커닉 이웃 안에선 되고, 진짜 다른 게임 시스템(duel)으론 안 된다"** — open frontier를
  **cross-배틀시스템 전이**로 국소화한 *부분적·정직한 주장*(blanket 주장 아님).

**caveat**: 음수 gap은 held-out family **난이도 비대칭**도 반영(forage held-out ≈4.0 쉬움) — 순수 전이 품질 아님.
깨끗한 신호는 **duel 실패**. held-in 천장 2.75<#26 2.94, 단일 config·N16·결정론 보스.

## 계획 대비 실적 (✅)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 예산 사다리 multi-run + 기준선 표 | ✅ | `budget_ladder_configs`+`--budgets`, #26/#28/#31 천장 병기 |
| AC2 사전약정 결정규칙 판정 | ✅ | **RECOVERY**(2.75≥2.5) 자동 판정 + ±std + caveat |
| AC3 (RECOVERY 시) full-LOO confound-reduced gap 재측정 | ✅ | 400k loo_multirun, #28 동일 축, 4 fold(duel +1.73 등) |
| AC4 [rl] smoke + 결정론 | ✅ | `test_budget_ladder_configs`; held_in_sweep/loo_multirun 결정론(기존 검증) |
| AC5 무회귀 + 툴체인 | ✅ | 196→197 passed, mypy 22/ruff/build clean, core numpy-only |
| AC6 DESIGN + genre-generalization.md + CHANGELOG | ✅ | RECOVERY + confound-reduced gap + duel 국소화 반영 |
| AC7 freeze 전 pilot | ✅ | pilot(400k/500k single-seed) + timing(108/133s) — 단일seed 정체는 multi-run서 교정(예측대로) |

## 변경 파일 상세
**수정**
- `scripts/genre_learned_transfer.py` — `budget_ladder_configs`(baseline-net 사다리) + `--budgets` CLI(사다리 multi-run + RECOVERY/APPROACHING/PLATEAU 사전약정 verdict). 기존 held_in_sweep/loo_multirun 재사용.
- `tests/test_genre_learned_transfer.py` — `test_budget_ladder_configs`(사다리 config 형태/baseline-net/budget 라벨).
- `DESIGN.md` §3.1.1 — RECOVERY + confound-reduced gap + "real but structurally bounded" verdict.
- `docs/explanation/genre-generalization.md` — §5 결론 + §6 "남은 경로"를 duel(cross-battle-system)로 국소화.

## 발견된 이슈 (심각도)
- (방법론, 재확인) **단일-seed 외삽 위험 3번째 사례** — pilot 단일seed가 PLATEAU/하락처럼 보였으나 multi-run mean은 RECOVERY(2.75). 학습 결론은 반드시 multi-run으로(이미 가드).
- (해석) 음수 gap의 난이도-비대칭 교란 — held-out family가 더 쉬우면 음수 gap이 전이로 오인될 수 있음. duel(held-out이 더 *어려운* 경우)의 양수 gap이 깨끗한 신호.

## 정직한 한계 / 다음 task
- held-in 천장 2.75<2.94(완전 회복 아님)·단일 config·N16·결정론 보스·anchor 400k.
- **다음(국소화된 frontier)**: **cross-배틀시스템 전이** — duel로 전이하는 정책. 예산으론 안 됐으니 메커닉-범용
  표현(family/task embedding) 또는 duel-포함 커리큘럼이 다음 후보. 또는 현 "structurally bounded (B)" 결과로
  arXiv 패키징하고 난이도·JAX로 피벗.

## 타입 체크 / 빌드 결과
- pytest 197 passed, 2 skipped · mypy 22 files clean · ruff clean · build OK.
