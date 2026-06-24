---
slug: transfer-rigor
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to: []          # evergreen 흡수 없음 — DESIGN §3.1.1(살아있는 scope)에 직접 반영
changelog_entry: docs/CHANGELOG.md (env-core, transfer-rigor)
---

# transfer-rigor — multi-run + 예산↑ robust 재측정 — 결과 보고서

## 요약 (실측: 50k·150k × 5 run, N16/16)

| muster fold (앵커) | held-in (±run-std) | held-out (±run-std) | gap (±run-std) | 사전약정 판정 |
|---|---|---|---|---|
| #26 baseline (2-family) | 2.940 | 0.380 | +2.560 | — |
| **50k × 5run** (3-family) | 1.733 ±0.502 | 1.512 ±0.443 | **+0.221 ±0.445** | std>gap → **불확실** |
| **150k × 5run** (3-family) | 2.067 ±0.616 | 1.625 ±0.658 | **+0.442 ±0.725** | std>gap → **불확실** |

전체 fold(150k×5): critter −1.12±0.54 / forage −1.35±0.61 / duel **+1.28±0.67** / muster +0.44±0.72.
(50k×5: critter −0.75±0.33 / forage −0.91±0.69 / duel +1.15±0.11 / muster +0.22±0.45.)

## 정직한 결과 해석 (사전약정 결정규칙 적용 — 사후 편향 차단)

1. **gaps는 #26 +2.56보다 robust하게 훨씬 좁음** — 모든 fold에서. 이 부분(wider train→narrower gap)은 유지.
2. 그러나 대체로 **held-in 하락**: widened held-in 0.9~2.1 ≪ #26 2.94. 예산 50k→150k는 held-in을 **약간만**
   올림(muster 1.73→2.07, 여전히 <2.5의 신호강화 임계 미달). → **generalist-mediocrity confound는 축소되나
   제거되지 않음**. 병목은 compute가 아니라 정책/obs/env.
3. **#27의 음수 muster gap(−0.25)은 robust하지 않음** — 5 run에서 +0.22±0.45 / +0.44±0.72로 **run-std가 gap을
   초과** → 사전약정 규칙상 **불확실**(부호 불안정). #27의 −0.25는 run 노이즈였음.
4. **multi-run이 단일-seed pilot을 교정** — pilot(seed 0)은 "예산↑로 held-in 안 오름(1.96→1.58)"을 보였으나,
   5-run mean은 held-in이 *오르는* 방향(1.73→2.07). 단일 seed 노이즈를 multi-run이 바로잡음 = (b)의 가치 입증.
5. **duel이 robust하게 가장 어려운 held-out**(gap +1.15±0.11, std≪gap) — 가장 전이 안 되는 family.

**verdict**: wider train이 gap을 진짜 좁히지만 *낮은 절대 skill*에 confound되고 음수 부호는 노이즈 →
(B)는 여전히 **신호**, 깨끗한 주장에는 **절대 skill 향상(정책/obs 개선, compute·seed 추가 아님)**이 필요.

## 계획 대비 실적 (✅) + pilot reframe

| AC | 상태 | 근거 |
|---|---|---|
| AC1 multi-run LOO run-간 mean±std + #26/#27 동일 metric | ✅ | `train_and_transfer_loo_multirun`/`--runs N`, `MultiRunFoldReport` |
| AC2 높은 예산 + held-in 상승 보고 + **사전약정 결정규칙** 정직 판정 | ✅ | muster fold = **불확실**(std>gap) 판정, held-in 1.73→2.07 보고, 음수=노이즈 명시 |
| AC3 [rl] smoke(importorskip) multi-run(≥2run) | ✅ | `test_widened_train_loo_multirun_smoke`(256ts, 2run, mean/std finite) |
| AC4 무회귀 + 툴체인 | ✅ | 193→194 passed, mypy 22/ruff/build clean, core numpy-only |
| AC5 DESIGN §3.1.1 정직 갱신 + M5/층2 | ✅ | transfer-rigor robust 결과 + 사전약정 verdict 단락 |
| AC6 CHANGELOG | ✅ | env-core 상단 |
| AC7 freeze 전 pilot 정량 게이트 | ✅ (falsify→reframe) | pilot: timing(150k 40s/fold→전체 ~19min 현실적) + held-in 방향. **단일-seed pilot이 (a)전제 일부 falsify→AC7(ii)/R3 사전등록 분기로 reframe**((a)=수정→발견); multi-run이 그 노이즈 교정 |

## 변경 파일 상세
**수정**
- `scripts/genre_learned_transfer.py` — `MultiRunFoldReport` + `train_and_transfer_loo_multirun`(run-간 mean±std) + `--runs N` main(두 예산 대조, 사전약정 caveat). `import numpy as np` 모듈화.
- `tests/test_genre_learned_transfer.py` — `test_widened_train_loo_multirun_smoke`(집계 형태·std≥0 가드).
- `DESIGN.md` §3.1.1 — robust 재측정 결과 + 사전약정 verdict 반영.

## 발견된 이슈 (심각도)
- (중간, 방법론) **단일-seed pilot이 오도할 수 있음** — pilot의 held-in 단일 seed가 노이즈로 (a) 전제를 잘못
  falsify할 뻔. multi-run mean이 교정. → pilot 결론은 단일 seed라 *방향 가늠*까지만, 확정은 multi-run으로(이미 반영).

## 정직한 한계 / 다음 task
- 단일 config·N16·결정론 보스·held-in<2.5 = 신호지 증명 아님.
- 다음(가장 직접적): **절대 skill 향상** — held-in을 #26 수준(≈2.9)으로 끌어올리는 **정책/obs 표현 개선**(예:
  메커닉-범용 인코딩, 더 큰 net, 보상/커리큘럼). 그 위에서 gap을 재측정해야 generalist-mediocrity confound가
  비로소 제거되고 (B)가 신호→주장으로 이동 가능. (compute·seed로는 한계 확인됨.)

## 타입 체크 / 빌드 결과
- pytest 194 passed, 2 skipped · mypy 22 files clean · ruff clean · build OK.
