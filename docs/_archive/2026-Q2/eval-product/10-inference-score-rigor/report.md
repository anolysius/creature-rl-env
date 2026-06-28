---
slug: inference-score-rigor
initiative: eval-product
status: completed
ended: 2026-06-28
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md  # task table #10
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# inference_score 측정 robust화 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 489 → **498** (+9, 회귀 0), 2 skip |
| mypy / ruff / build | clean(31) / clean / clean |
| 집계 검증 | oracle×3 → `infers`(mean 1.00) / type_blind×3 → `at-chart-blind-floor`(mean 0.00) |
| L1 / L3 | 2/2 APPROVE / 2/2 APPROVE |
| 변경 | inference_rigor.py(신규) · llm_eval_run.py · test_inference_rigor.py(신규) |

## 평이한 한 문단 요약 (수식 없이)

#8에서 얻은 첫 KPI(0.00)는 딱 한 번 잰 값이라 "운/노이즈"일 수 있었습니다. 그래서 같은 측정을 여러 번
돌려 **평균±편차로 판정**하는 채점 규칙을 만들었습니다 — 판정 기준은 데이터를 보기 *전에* 고정해(p-hacking
방지) "확실히 추론한다 / 확실히 무지식 바닥이다 / 더 돌려봐야 안다" 셋 중 하나로 정직하게 분류합니다.
규칙 자체는 LLM 없이 테스트했고(공짜·결정론), 실제 여러 번 측정은 `--runs N` 도구로 나중에 돌립니다.

## 계획 대비 실적

| AC | 결과 | 근거 |
|---|---|---|
| AC1 classify_inference 3-branch + 가드 | ✅ | property 9개 (infers/floor/inconclusive/경계/빈/single) |
| AC2 임계 데이터 전 고정 | ✅ | 코드 기본값 0.50/0.10/1.0 + `test_frozen_thresholds_are_defaults` + qa-checklist |
| AC3 러너 --runs N + N=1 무회귀 | ✅ | N회 집계→verdict, N=1 기존 경로 불변 |
| AC4 property 테스트 LLM 없이 | ✅ | 순수 numpy, CI |
| AC5 무회귀 + 정직 경계 | ✅ | 489→498, mypy/ruff/build clean, "분류기=도구" docstring |

## 변경 파일 상세

- **`src/critter_gym/inference_rigor.py`** (신규): `classify_inference(runs, *, infer_thresh=0.5,
  floor_eps=0.1, k=1.0)` + `InferenceVerdict(verdict, mean, std, n_runs)`. `headroom.py` 패턴 mirror,
  numpy-only(CI-cheap). 3-branch: `m−k·s≥infer_thresh`→infers / `m+k·s≤floor_eps`→at-chart-blind-floor / else inconclusive.
- **`scripts/llm_eval_run.py`**: `--runs N`(기본 1) — N회 `score_agent`, per-run inference_score →
  `classify_inference` verdict 출력. N=1이면 기존 단일-run 출력(무회귀).
- **`tests/test_inference_rigor.py`** (신규): +9 property.

## 정직 경계 (계승)

- **사전약정**: 임계(0.5/0.1/1.0)는 데이터 보기 전 고정(코드 기본값 + qa-checklist) — p-hacking 차단.
- **도구≠결과**: 분류기는 verdict를 그대로 기록할 뿐 결과를 단정하지 않음. 실측 N-run LLM 수치는 후속
  (acceptance 아님). inference_score 자체의 한계(특정 band·scripted proxy)는 #8에서 명시.

## 흡수처 매핑

- `extracted_to`: INITIATIVE.md task table #10. classify_inference SSOT는 모듈 docstring(코드).

## 타입 체크 / 빌드 결과

mypy clean(31) · ruff clean · build → `critter_gym-1.0.0rc1` · pytest 498 passed / 2 skipped.
