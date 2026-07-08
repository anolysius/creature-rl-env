---
slug: diversity-dial
initiative: null
status: completed
ended: 2026-07-08
extracted_to: []
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# diversity-dial — 결과 보고서 (scout)

| 항목 | 값 |
|---|---|
| opt-in knob | `boss_pool_size`(region.py, 기본 None=byte-identical=현 `max(2,n_gyms//2)`) + CritterEnv/SealedEvalSet 플러밍. boss_secondary/strict_battle 선례. parity·determinism 무회귀 확인 |
| 곡선 API | `diversity_curve(pool_grid)`→DiversityPoint(pool별 infer inference_score + oracle/blind 앵커 + **실측 mean distinct-types/world** + winnable), 결정론 |
| 사전선언 규칙(데이터 전) | 실측 다양성↑에 infer_score 단조↓ = calibrated 다이얼 / 평평 = falsify |
| **실측 = 정직 FALSIFY + 메타 통찰** | 다양성 knob **작동함**(실측 distinct-types **1.0→5.0**/world). 그러나 infer_score **평평**(0.96→0.92, 비단조). oracle 100%·blind 3-13% 유지 |
| 메커니즘 통찰 | scripted `infer` arm 은 **즉석-완벽 학습**(첫 만남에 차트로 favorable 계산·저장)이라 다양성이 올라도 SE-rate saturated(~90%+). **scripted 프록시로는 추론 난이도를 calibrate 할 수 없다** — 밴드는 eval *검증*용(변별하나? yes)이지 *난이도 측정*용이 아니다 |
| 정직 결론 | 두 scout(num_types·diversity) 모두 scripted infer flat — (1) pool 이 다양성 캡(#직전) + (2) 무캡이어도 프록시 saturated. **난이도 다이얼은 *불완전하게 추론하는* 학습/LLM agent 에게만 보인다** → 돈 게이트 학습/LLM 곡선의 동기를 정확히 규정 |
| 테스트 | 713 → **718**(+5). ruff clean, mypy 신규 0. 결정론·byte-id |
| L1 / L3 | qa BLOCK(AC4 측정가능성)→보완→APPROVE / 2/2 APPROVE |

## 과학적 가치

부정 결과지만 **eval 설계에 중요한 메타-발견**: scripted 밴드는 *검증*(discriminate)에 강하나
*calibration*(난이도 곡선)에는 무력 — 즉석-완벽 프록시가 천장을 saturate. 난이도 계측은 실제
(불완전) 추론자(학습/LLM)가 필요. 이는 향후 유료 LLM 측정이 "왜 필요한가"를 정확히 정당화한다.

## 후속

- **학습/LLM 다양성 곡선** (돈 게이트): `boss_pool_size` knob 는 준비됨 — 학습 agent 나 LLM 을
  pool ∈ {1..8} 로 돌려 inference_score 낙하를 보면 진짜 난이도 다이얼 입증. `--llm` 경로 재사용.
- `boss_pool_size` opt-in knob 은 이제 판매 티어의 난이도 레버 후보로도 남음(byte-id 기본).
