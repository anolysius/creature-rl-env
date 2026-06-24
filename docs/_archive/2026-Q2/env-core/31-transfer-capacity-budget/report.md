---
slug: transfer-capacity-budget
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - docs/explanation/genre-generalization.md   # (B) narrative 갱신(budget ladder + verdict)
changelog_entry: docs/CHANGELOG.md (env-core, transfer-capacity-budget)
---

# transfer-capacity-budget — 용량×예산 동시 스케일 — 결과 보고서 (PARTIAL)

## 요약 — capacity×budget sweep, muster anchor fold, 5 run

| config | held-in (±run-std) | held-out (±run-std) | gap (±run-std) |
|---|---|---|---|
| baseline-net @150k (budget-only, #28) | 2.067 ±0.616 | 1.625 ±0.658 | +0.442 ±0.725 |
| **baseline-net @250k (more budget)** | **2.442 ±0.352** | 2.487 ±0.783 | **−0.046 ±0.492** |
| big-net[256,256] @250k (capacity+budget) | 1.871 ±0.385 | 1.175 ±0.108 | +0.696 ±0.387 |

천장: #26 2.94 · #28 budget-only@150k 2.07 · #30 net-only@50k 1.15 · 사전약정 회복임계 2.5.
**사전약정 verdict = PARTIAL** (best held-in 2.44 > 2.07 천장, < 2.5 회복).

## 정직한 결과

1. **예산이 held-in을 robust하게 올린다 — 아직 포화 안 됨**: 150k 2.07 → 250k **2.44**, run-std도 0.62→0.35로
   조임. 2.5 회복임계에 근접. → **#28의 "compute는 병목 아님"을 부분 정정**(그건 50k→150k 저예산의 조기 결론;
   250k까지 주면 예산은 *계속* 효과 있음 — #28 단일-seed pilot 교정과 같은 교훈의 budget 버전).
2. **용량(큰 net)은 robust하게 해롭다**: big-net@250k 1.87 < baseline@250k 2.44(5 run). underfit/수렴 지연.
   → **lever는 예산이지 용량이 아니다**(이 task의 핵심 발견).
3. **가장 긍정적 점**: baseline@250k에서 held-in 2.44(평범 아님, #26 2.94 근접)·held-out 2.49·**gap −0.05≈0**.
   held-in이 *평범하지 않으면서* gap이 ~0인 **첫 데이터 점** — generalist-mediocrity가 실질적으로 줄어든 ~0 gap.
   ⚠ 단, **단일 fold·단일 config·큰 held-out std(0.78)·held-in<2.5** = 주장 아님, 신호.

## verdict & 경계 상태
- **PARTIAL** — 예산(cheap-ish 레버)이 *아직 오르는 중*, 회복임계 직전. **cheap/expensive 경계 미종결.**
- AC3 조건부: held-in이 2.5(RECOVERY) 미달 → full-LOO confound-reduced gap 재측정 **보류**(정직 skip).
  다음 정직한 probe = **더 큰 예산**(수확체감 감시), 용량은 배제됨.

## 계획 대비 실적 (✅) + pilot 정련

| AC | 상태 | 근거 |
|---|---|---|
| AC1 용량×예산 sweep multi-run + 천장 기준선 표 | ✅ | `held_in_sweep`/`SweepRow`/`--sweep`, #26/#28/#30 천장 병기 |
| AC2 사전약정 결정규칙 판정(회복/부분/종결) | ✅ | **PARTIAL**(2.44) 자동 판정 + ±run-std + caveat |
| AC3 (조건부) held-in 회복 시 gap 재측정 | ✅ | held-in<2.5 → **재측정 불요/보류** 정직 기록(조건 미충족, 실제 skip) |
| AC4 [rl] smoke + 결정론 | ✅ | `test_held_in_sweep_smoke`(집계 형태·std≥0); 노브 결정론 #30 검증 |
| AC5 무회귀 + 툴체인 | ✅ | 195→196 passed, mypy 22/ruff/build clean, core numpy-only |
| AC6 DESIGN §3.1.1 + genre-generalization.md + CHANGELOG | ✅ | budget ladder 결과 + #28 정정 + verdict 반영 |
| AC7 freeze 전 pilot(held-in 방향/timing/결정론) | ✅ (정련) | pilot: 예산이 천장 상회(2.07→2.39 단일seed)·용량 무효 발견→sweep을 예산 사다리로 refocus; timing 70-85s/fold |

## 변경 파일 상세
**수정**
- `scripts/genre_learned_transfer.py` — `HELD_IN_CEILINGS`/`RECOVERY_THRESHOLD` + `SweepRow` + `held_in_sweep`(anchor fold multi-run) + `--sweep`/`--runs-n` main(천장 표 + 사전약정 verdict). 노브는 #30 재사용.
- `tests/test_genre_learned_transfer.py` — `test_held_in_sweep_smoke`(sweep 집계 형태 가드).
- `DESIGN.md` §3.1.1 — budget ladder 결과 + #28 정정 + PARTIAL verdict.
- `docs/explanation/genre-generalization.md` — budget ladder 방법론 + "남은 경로" status update.

## 발견된 이슈 (심각도)
- (방법론, 중간) **저예산 외삽 위험** — #28의 "compute 병목 아님"은 50k→150k에서 조기 결론이었음. 더 큰 예산에서
  정정됨. 학습-효과 결론은 예산 사다리로 확인해야(단일 예산점 외삽 금지). genre-generalization.md에 반영.

## 정직한 한계 / 다음 task
- 단일 fold·단일 config·N16·결정론 보스·held-in<2.5 = 신호. held-out std 큼.
- **다음(가장 직접적)**: 더 큰 예산(예: 400~500k)로 baseline-net held-in이 2.5를 robust하게 넘는지 + 넘으면
  full-LOO confound-reduced gap 재측정. 수확체감이면 (B)를 "예산으로 부분 회복, 완전 회복엔 표현/메타-RL 필요"로
  패키징. (용량 스케일은 배제됨.)

## 타입 체크 / 빌드 결과
- pytest 196 passed, 2 skipped · mypy 22 files clean · ruff clean · build OK.
