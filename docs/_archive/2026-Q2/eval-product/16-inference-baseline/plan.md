---
slug: inference-baseline
initiative: eval-product
status: active
started: 2026-06-30
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
scope_paths:
  - src/critter_gym/eval_harness.py
  - scripts/llm_eval_run.py
  - tests/test_eval_harness.py
  - docs/reference/inference-baseline.md
extracted_to: []
supersedes: []
depends_on: [matchup-validity (#15, PR #84)]
---

# 보정된 분포 위 inference baseline 확정 + 재측정 프로토콜

> 작성일: 2026-06-30 | 상태: 계획 | 마일스톤: eval 측정 validity (재측정 토대)

## 목표

매치업 fix(#15)로 held-out 세계 분포가 바뀌어(이제 SE-exploitable boss 만 배치) **이전 LLM
inference 수치(#11/#13/#14)와 직접 비교 불가**가 되었다. 이 task 는 *타당한 baseline 위에서* 다음
재측정을 가능하게 한다:

1. **4-arm scripted band 를 한 묶음으로 산출하는 순수 헬퍼** — oracle/infer/type_blind/probe 의
   gym-clears + super-effective-rate(telemetry) + inference_score 정규화 앵커를 결정론으로 계산
   (LLM 불요, CI-cheap). 이게 LLM 을 끼워 넣을 *변별 band* 의 SSOT.
2. **러너 telemetry 를 full 4-arm band 로 확장** — 현재 oracle/type_blind 만 표시 → infer(추론
   에이전트 reference)·probe(blind guess floor)를 추가해 LLM SE-rate 를 *해석 가능*하게.
3. **재측정 프로토콜 + 정직 reference 문서** — 보정 분포 위 band 수치 + 사용자가 LLM 으로 돌릴
   고정 명령/config + "이전 수치는 옛(매치업-broken) 분포라 비교 불가" 경고.

**실측 유료 LLM probe 는 사용자 로컬**(기존 규율) — 이 task 는 무료 scripted band + 도구 + 문서만.
어떤 LLM 능력 verdict 도 단정하지 않는다.

## 선행 조건 (측정된 보정-분포 band)

매치업 fix 적용 상태에서 측정(이 task 의 근거):

| config | arm | gym-clears | SE-rate | n_moves |
|---|---|---|---|---|
| demo types3 n8 | oracle | 2.12 | **100%** | 62 |
| | infer | 1.88 | **39%** | 134 |
| | type_blind | 1.25 | **7%** | 391 |
| | probe | 0.00 | **0%** | 739 |
| runner-default types8 n8 | oracle | 2.12 | 100% | 34 |
| | infer | 1.62 | 24% | 107 |
| | type_blind | 1.00 | 4% | 312 |
| | probe | 0.38 | 1% | 544 |

→ 보정 후 band 가 **단조 정렬**(oracle ≥ infer ≥ type_blind ≥ probe), SE-rate 분리가 깨끗
(특히 attrition-proof). infer(cross-gym 학습자 proxy)가 type_blind 위에 명확히 떠 — eval 이
"추론하는 에이전트"를 "blind"와 변별. 단 gym-clears 의 span(oracle−type_blind≈0.87)은 attrition
으로 좁음 → **SE-rate band 가 더 깨끗한 변별자**(#12 교훈 재확인).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/eval_harness.py` | 신규 순수 헬퍼 `inference_baseline(sealed) -> InferenceBaseline` (4-arm gym-clears + SE-rate + inference_score 앵커) | **중** | 기존 score_agent/telemetry 재사용, read-only. 기존 API 무변경(추가만). |
| `scripts/llm_eval_run.py` | telemetry 출력에 infer·probe arm 추가(full 4-arm band) | 중 | print-only. 기존 oracle/type_blind 라인 유지. |
| `tests/test_eval_harness.py` | 헬퍼 band 정렬/결정론/inference_score 앵커 테스트 | 중 | scripted-only, 결정론. |
| `docs/reference/inference-baseline.md` | 신규 — 보정 band 수치 + 고정 재측정 프로토콜 + 정직 "비교 불가" 경고 | 저 | evergreen reference. |

### 영향 범위 (import 그래프)

- `inference_baseline` = `score_agent`(gym-clears) + `score_inference_telemetry`(SE-rate) 조합 →
  scripted reference arm 결과만 읽음. env read-only. 기존 채점 경로 byte-identical(추가 함수).
- 러너 변경은 print-only(채점 로직 무변경).
- 문서는 evergreen reference (cross-task 의존 없음).

## Step별 계획 (TDD)

1. **Red** — `tests/test_eval_harness.py` 에 헬퍼 테스트 추가(현재 실패):
   - `test_inference_baseline_band_is_monotone`: 보정 분포(demo types3 n8)에서 SE-rate 가
     oracle ≥ infer ≥ type_blind ≥ probe, oracle SE-rate == 1.0, probe ≈ floor.
   - `test_inference_baseline_is_deterministic`: 같은 sealed → 같은 band.
   - `test_inference_baseline_inference_score_anchors`: oracle inference_score==1.0,
     type_blind==0.0 (정규화 앵커 정합).
2. **Green** — `eval_harness.inference_baseline(sealed)` 구현:
   - 4-arm 루프(oracle/infer/type_blind/probe)로 gym-clears(`score_agent` 또는 `_play_once`) +
     SE-rate(`score_inference_telemetry`) 수집 → `InferenceBaseline` NamedTuple(arm별 dict).
   - inference_score 앵커는 기존 `score_agent` span 공식 재사용(중복 금지).
3. **Refactor** — 러너 telemetry 블록이 헬퍼를 호출하도록 정리(중복 측정 제거), 문서 작성.

## 검증 방법

- 신규 헬퍼 테스트 통과(band 정렬·결정론·앵커).
- 러너 `--telemetry` 출력에 infer·probe 라인 추가 확인(수동 1회 실행, scripted-free).
- 전체 pytest 회귀 0(현재 517 + 신규). mypy/ruff/build clean.
- 문서: 보정 band 수치 + 고정 명령 + 정직 경고가 코드 산출과 일치.

## 리스크

| 리스크 | 완화 |
|---|---|
| #84(매치업 fix) 미머지 → 이 branch 가 stacked | fix/matchup-validity 위에 분기(서로 다른 파일=충돌 0). PR base=fix/matchup-validity → #84 머지 시 자동 main 리타깃. |
| band 수치를 "LLM 능력 verdict"로 과대 해석 | 문서·docstring 에 "scripted proxy band·LLM 실측은 사용자 로컬·옛 수치 비교 불가" 명시. infer arm 은 *추론 에이전트 proxy*이지 LLM 아님. |
| gym-clears span 협소(attrition) | SE-rate band 를 1차 변별자로 제시, gym-clears 는 보조. #12 교훈 계승(reframe 금지). |
| 헬퍼가 기존 채점 경로 변경 | 추가 함수만, score_agent/telemetry 본문 무변경 → byte-identical 회귀 테스트. |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[hard]** `inference_baseline(sealed)` 가 4-arm(oracle/infer/type_blind/probe) gym-clears +
   SE-rate + inference_score 앵커를 결정론으로 반환. 보정 분포에서 SE-rate 단조 정렬
   (oracle ≥ infer ≥ type_blind ≥ probe) + oracle SE-rate==1.0 + oracle inference_score==1.0 ∧
   type_blind inference_score==0.0. 신규 테스트로 검증.
2. **[tooling]** 러너 `--telemetry` 가 full 4-arm band(infer·probe 포함) 출력. 기존 채점 경로
   byte-identical(추가 함수·print-only).
3. **[regression]** 전체 pytest 회귀 0(517 유지 + 신규 통과). mypy/ruff/build clean.
4. **[doc/honesty]** `docs/reference/inference-baseline.md` 에 (a) 보정 분포 band 수치 (b) 고정
   재측정 명령+config (c) "이전 LLM 수치(#11/#13/#14)는 옛 매치업-broken 분포 측정이라 비교 불가,
   유료 실측은 사용자 로컬" 정직 경고. infer=추론 proxy(LLM 아님) 명시.
