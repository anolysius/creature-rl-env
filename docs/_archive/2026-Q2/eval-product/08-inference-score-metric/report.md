---
slug: inference-score-metric
initiative: eval-product
status: completed
ended: 2026-06-28
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md  # task table #8
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# inference score (고객용 moat 지표) — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 484 → **489** (+5, 회귀 0), 2 skip |
| mypy / ruff / build | clean(30) / clean / clean |
| 기본 SealedEvalSet | oracle mean=1.125 (byte-identical 무회귀) |
| L1 / L3 | plan-reviewer APPROVE + qa-verifier SUGGEST(반영) / 2/2 APPROVE |
| 변경 | eval_harness.py · llm_eval_run.py · test_eval_harness.py |

## 평이한 한 문단 요약 (수식 없이)

고객(프런티어 랩)에게 "우리 시험이 외울 수도 없고 베낄 수도 없다"를 한 숫자로 보여주는 지표를 만들었습니다:
**inference score** — 규칙을 *모르고* 치는 baseline을 0, 규칙을 *아는* 전문가를 1로 놓고, 시험 보는 AI가 그
사이 어디에 있는지를 0~1로 매깁니다. 0이면 "그냥 찍는 수준", 1이면 "전문가급". 처음 보는 봉인 세계에서
숨은 규칙을 *그 자리에서 추론*해야만 점수가 오르므로, 답을 외워 오거나 데이터 오염으로 부풀릴 수 없습니다.
또 시험 난이도(맵 크기·보스 강함)를 조절하는 손잡이를 열어, AI가 길을 찾을 수 있으면서도 추론이 꼭 필요한
"딱 좋은" 시험을 만들 수 있게 했습니다.

## 계획 대비 실적

| AC | 결과 | 근거 |
|---|---|---|
| AC1 SealedEvalSet 노브 + 기본 byte-identical | ✅ | `test_sealed_world_battle_knobs_reach_env`, `test_sealed_default_knobs_are_env_defaults` |
| AC2 Scorecard.inference_score + 계산 | ✅ | `score_agent` span>0 가드 + [0,1] 클램프 |
| AC3 경계 테스트 | ✅ | oracle→1.0 / type_blind→0.0 / random∈[0,1] / 분모 가드→0.0 |
| AC4 러너 노브 CLI + 고객 출력 | ✅ | `--grid-size/--boss-*` + `INFERENCE SCORE` headline + demonstrator preset |
| AC5 무회귀 + 정직 경계 | ✅ | 484→489, 기본 byte-identical, mypy/ruff/build clean |

## 변경 파일 상세

- **`src/critter_gym/eval_harness.py`**: `SealedEvalSet`에 `grid_size`·`boss_hp`·`boss_atk`·`boss_def` 노브
  (기본=CritterEnv 기본 → byte-identical), `env_factory`가 전달. `Scorecard`에 `inference_score: float`
  (끝에 추가), `score_agent`가 `(mean−type_blind)/(oracle−type_blind)` 계산([0,1] 클램프, oracle≤type_blind면 0.0).
- **`scripts/llm_eval_run.py`**: `--grid-size/--boss-hp/--boss-atk/--boss-def` CLI + 고객용 3-arm 출력
  (oracle=expert ceiling / type_blind=blind floor / LLM) + `INFERENCE SCORE` headline + demonstrator preset 안내.
- **`tests/test_eval_harness.py`**: +5 테스트(노브 전달·기본 무회귀·oracle 1.0·blind 0.0·unit-interval·분모 가드).

## moat 맥락 (왜 이 지표)

probe 여정(#5~#7)으로 LLM이 floor→클리어까지 왔고, scout로 **oracle 100% vs type_blind 50%** 추론 gap을
확인. inference score는 그 gap 위 LLM 위치를 [0,1]로 정규화 — **"오염·암기 불가능한 in-context 규칙 추론"
능력의 단일 KPI**. 이것이 고정 벤치마크(언젠가 유출)가 못 주는, 우리가 파는 희소재의 정량 증거.

## 정직 경계 (계승)

- 지표는 **특정 난이도 band의 신호**이지 절대 능력치 아님 — config(밴드·oracle proxy·seed-set) 동반 보고.
- type_blind를 floor로 쓰는 정당성=규칙을 모르고 침. 그 사이 정규화가 "추론 정도"를 잰다.
- **점수 보장 아님**: 지표는 도구 — 낮게 나오면 낮은 대로 정직 기록. demonstrator config는 *시연용*이지
  제품 난이도 표준 아님(별도 사람/전략 게이트).

## 흡수처 매핑

- `extracted_to`: INITIATIVE.md task table #8. inference_score 정의 SSOT는 `Scorecard` docstring(코드).

## 타입 체크 / 빌드 결과

mypy clean(30) · ruff clean · build → `critter_gym-1.0.0rc1` · pytest 489 passed / 2 skipped.
