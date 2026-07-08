---
slug: inference-difficulty-curve
initiative: null
status: completed
ended: 2026-07-08
extracted_to: []
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# inference-difficulty-curve — 결과 보고서 (de-risked scout)

| 항목 | 값 |
|---|---|
| 도구 | `inference_curve.py`(`inference_difficulty_curve(grid)`→CurvePoint 튜플: N별 oracle/infer/type_blind/probe se_rate + infer 정규화 score + winnable) + scout 스크립트, additive(eval_harness 재사용) |
| 사전선언 규칙(데이터 전) | infer_score 단조↓ = num_types 는 calibrated 추론-난이도 다이얼 / 평평 = falsify |
| **실측 = 정직 FALSIFY** | 곡선 **평평**: infer_score num_types 3→12 에서 **0.91→0.92**(비단조, drop −0.01). oracle 100%·blind ~5-17% 유지(밴드 유효) |
| **메커니즘 검증** | num_types 3/6/12 전부 **월드당 distinct 보스타입 ~2개로 고정**(재발생 pool `min(exploitable, max(2, n_gyms//2))` 가 타입 다양성 캡) → 차트 *크기*가 첫-만남 추론자에게 안 닿음. 평평한 곡선의 정확한 원인 |
| 정직 결론 | **num_types(차트 크기) 는 추론 난이도 다이얼이 아니다.** 진짜 다이얼 후보 = **per-episode 타입 다양성(pool 크기)** — chart 크기가 아니라 "한 에피소드에서 몇 개의 서로 다른 매치업을 기억해야 하나"가 난이도를 만든다 |
| 테스트 | 708 → **713**(+5). ruff clean, mypy 신규 0. 결정론 |
| L1 / L3 | 2/2 APPROVE / 2/2 APPROVE |

## 과학적 가치

부정 결과지만 값어치 있음 — **명백한 knob(차트 크기)을 반증하고 진짜 knob(per-episode 다양성)을
정확히 지목**. scout 의 목적 그대로. 우리 정직 문화(patch_radius·strict_battle falsify 선례) 재현.

## 후속 (분리 task)

**pool/diversity 다이얼 scout**: num_gyms 또는 pool-size 파라미터로 per-episode distinct 타입 수를
늘려가며 infer-arm inference_score 곡선. 이게 단조 하락하면 → 진짜 calibrated 추론-난이도 다이얼
(계측기·마케팅 헤드라인·판매 티어 축). CPU 자율 가능. 그 다음 학습/LLM 앵커는 돈 게이트.
