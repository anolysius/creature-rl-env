---
slug: inference-robust-correction
initiative: eval-product
status: completed
ended: 2026-07-01
extracted_to:
  - docs/paper/critter-gym.md
  - docs/explanation/competitive-analysis.md
changelog_entry: docs/CHANGELOG.md (eval-product 섹션)
---

# §5 정정 — 단일-run "부분 추론(50%)" 정직 하향 — 결과 보고서

## 요약

#18(SE-rate robustness 도구)로 돌린 **3-run(n=4) robust 측정**이 #17 의 헤드라인(단일-run SE 50% =
부분 추론)을 **확인해주지 못함**: 정규화 SE-rate inference score **0.10 ± 0.08 → INCONCLUSIVE**
(gym 0.04 ± 0.06), LLM SE ≈14%, near chart-blind floor. 논문 §5·Abstract·competitive-analysis 의
"partial, real in-context inference" 단언을 "**inconclusive, near-floor — 단일 50% 재현 안 됨**"으로
정직 하향. 동시에 **설계 건강 명시**: scripted infer 앵커가 robust 하게 ≈89% → eval 은 추론을
registered → LLM near-floor 는 **eval 아티팩트 아닌 진짜 신호**(engagement confound 잔존).

## 계획 대비 실적

- ✅ **AC1** — Abstract + §5 결론 + Honest scope 가 robust 하향 반영, "partial, real inference" 제거.
- ✅ **AC2** — 신규 §5 bullet "design validated even though the prediction failed"(infer 89% → 진짜 신호) + competitive-analysis 동일 + Abstract "eval nonetheless validated".
- ✅ **AC3** — 수치(0.10±0.08 inconclusive·gym 0.04±0.06·infer 89%·LLM 14%·단일 50%·floors 27% vs 6%) 실측 일치(L3 지적한 gym std 0.08→0.06 정정) + n4-vs-n8 caveat + n=8 3-run 후속.
- ✅ **AC4** — docs-only(코드 0), broken-link 0. L3 plan-reviewer+qa-verifier 2/2 APPROVE.

## 변경 파일

- `docs/paper/critter-gym.md`: Abstract(28-33) + §5(single-run bullet + 신규 design-validated bullet + Honest scope).
- `docs/explanation/competitive-analysis.md`: "monetizable eval" 행 robust 하향 + design-validated.

## 발견된 이슈

- L3 plan-reviewer: docs 의 gym std `0.04 ± 0.08` 이 실측 `0.04 ± 0.06` 과 불일치 → 두 문서 정정(AC3).

## 흡수처 (extracted_to)

- `docs/paper/critter-gym.md`, `docs/explanation/competitive-analysis.md` — evergreen. cross-task 의존 없음.

## 정직 경계 / 교훈

- **이 정정 자체가 moat 논리의 실증**: robustness 도구(#18)가 우리 자신의 non-robust reframe(#17)을
  잡음. 앵커(infer 89%)로 설계를 검증한 뒤에도 예측이 깨지는 것 = eval 이 정직·un-gameable 하게
  작동한다는 증거.
- 현재 상태: **inconclusive, near-floor** (과대 X). 단 설계 건강(infer 앵커) → LLM near-floor 는 진짜
  신호(과소 X). engagement/survival confound 잔존 → 강한 신호지 verdict 아님.
- 후속: apples-to-apples n=8 3-run(구독 quota ~2.5h) → 50% outlier 확정 / engagement confound 규명 /
  전투 모델·공개=사람 게이트.
