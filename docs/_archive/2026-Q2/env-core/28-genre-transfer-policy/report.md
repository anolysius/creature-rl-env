---
slug: genre-transfer-policy
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to: []          # evergreen 흡수 없음 — DESIGN §3.1.1(살아있는 scope)에 직접 반영
changelog_entry: docs/CHANGELOG.md (env-core, genre-transfer-policy)
---

# 전이하는 학습 정책 — widened-train LOO 전이 측정 — 결과 보고서

## 요약 (수치 표) — 실측 PPO 50k, N16/16, 단일run

| train → held-out family | held-in (±std) | held-out (±std) | 전이 gap |
|---|---|---|---|
| **#26 baseline** train{critter,forage} → muster (2-family) | 2.940 | 0.380 | **+2.560** |
| widened train{forage,duel,muster} → critter (3-family) | 1.458 ±1.837 | 2.375 ±1.728 | −0.917 |
| widened train{critter,duel,muster} → forage (3-family) | 1.146 ±1.554 | 2.625 ±1.833 | −1.479 |
| widened train{critter,forage,muster} → duel (3-family) | 1.646 ±1.561 | 0.562 ±0.704 | +1.083 |
| widened train{critter,forage,duel} → muster (3-family) | 2.000 ±1.683 | 2.250 ±3.010 | −0.250 |

**같은 metric**(전이 gap = held_in − held_out family, 리턴 단위).

## 정직한 결과 해석

- **양성 신호**: train 분포를 넓히면(duel 포함) unseen-family 전이 gap이 #26의 **+2.56(2-family)**
  에서 **0 근처/음수**로 크게 좁아진다. 같은 held-out(muster)이 +2.56 → **−0.25**. 즉 *wider train
  distribution이 unseen-family 전이를 돕는다*는 신호. (B)가 "측정상 미해결(#26)" → "wider train이
  gap을 좁힌다(이 task)"로 이동.
- **⚠ 결정적 caveat (gap만 보지 말고 절대 컬럼과 함께 읽을 것)**: widened-train의 **held-in 절대성능도
  하락**(2.94 → 1.1~2.0). 한 net이 동일 예산으로 3 family를 배우면 *generalist 평범화*가 일어난다.
  따라서 좁아진(혹은 음수) gap은 *families 전반에 균일하게 평범*한 것을 일부 반영하지, **강한 전이의
  증명이 아니다**. 음수 gap(held-out > held-in)은 *낮은 절대 skill + held-out family가 더 쉬움*이 유력.
- **결론**: 신호지 증명 아님. 깨끗한 (B) 주장에는 **절대 skill 향상 + multi-run**이 필요(여기선 단일run·
  저예산·결정론 보스).

## 계획 대비 실적 (✅)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 widened LOO + #26 동일 metric 대조 | ✅ | `train_and_transfer_loo`/`--loo`, gap=held_in−held_out, baseline row 병렬 |
| AC2 ±std + caveat 정직보고(양성=신호/음성=미해결) | ✅ | 위 표·caveat, 스크립트 print에 generalist-mediocrity/음수 gap 해석 명시 |
| AC3 [rl] smoke(importorskip) 4family fold | ✅ | `test_widened_train_loo_smoke`(256 ts, 4 fold, duel in/out) |
| AC4 무회귀 + 툴체인 | ✅ | 192→193 passed, mypy 22/ruff/build clean, core numpy-only |
| AC5 DESIGN §3.1.1 정직 갱신 + M5/층2 | ✅ | widened-train LOO 결과 + caveat 단락 추가 |
| AC6 CHANGELOG | ✅ | env-core 상단 |
| AC7 freeze 전 pilot + framing 확인 | ✅ | tiny-budget 2 fold pilot(duel in train+held-out) — 배관·동일축·framing 확인, falsify 없음 |

## 변경 파일 상세

**수정**
- `scripts/genre_learned_transfer.py` — `train_and_transfer_loo`(4 family LOO) + `--loo` main(#26 baseline 동일-축 대조 표 + generalist-mediocrity/음수 gap 정직 caveat). 모듈/`assert_obs_compatible` docstring 갱신.
- `tests/test_genre_learned_transfer.py` — `test_widened_train_loo_smoke`(LOO fold 구성·duel in/out·family-level split 가드).
- `DESIGN.md` §3.1.1 — widened-train LOO 실측 + 정직 caveat 반영.

## 발견된 이슈 (심각도)
- (중간, 정직성) 음수 gap의 의미가 직관과 반대일 수 있음(전이 잘됨이 아니라 절대성능 낮음+held-out 쉬움).
  → 스크립트 print·DESIGN·CHANGELOG·report 전부에 "절대 컬럼과 함께 읽을 것" caveat 명시로 처리.

## 정직한 한계 / 다음 task
- 단일run·저예산·N16·결정론 보스 = **신호**지 헤드라인 아님.
- 다음 후보: (a) **절대 skill 향상**(예산↑/정책 개선)으로 held-in을 끌어올린 뒤 gap 재측정(generalist-mediocrity
  교란 제거), (b) **multi-run**으로 robust화, (c) 5~6번째 family로 분포 확대, (d) obs 표현/메커닉-범용 정책 개선.

## 타입 체크 / 빌드 결과
- pytest 193 passed, 2 skipped · mypy 22 files clean · ruff clean · build OK.
