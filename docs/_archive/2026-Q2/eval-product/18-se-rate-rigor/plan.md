---
slug: se-rate-rigor
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
extracted_to: []
supersedes: []
---

# SE-rate robustness — 다회 super-effective-move-rate 의 사전약정 robust verdict

> 작성일: 2026-06-30 | 상태: 계획 | 마일스톤: eval 측정 validity (헤드라인 신호 robust화)

## 목표

#17 의 헤드라인(보정 분포 위 claude-opus-4-8 **SE-rate ≈50%** = 부분 추론)은 **단일 telemetry
패스**라 robust 하지 못하다. #10 `inference-score-rigor` 가 gym 기반 `inference_score` 에 한 것을
**SE-rate 에도** 적용한다: SE-rate 를 band(type_blind=0, oracle=1)로 **정규화**해 inference_score 와
*같은 [0,1] frame* 으로 만들고, 다회 run 의 정규화 점수를 **사전약정 분류기 `classify_inference`
(임계 frozen)**로 묶어 robust verdict(`infers`/`at-chart-blind-floor`/`inconclusive`)를 낸다.

핵심: 현재 `--runs N` 은 gym `inference_score`(saturate·협소)만 집계하고 **SE-rate(진짜 변별자)는
단일 패스**다(러너 `agent_tel = score_inference_telemetry(...)` 1회). 이 task 가 SE-rate 를 N-run
robust 하게 만들어 50% 발견을 verdict 로 격상 가능케 한다. **유료 N-run LLM 실행은 사용자 로컬**
— 본 task 는 도구(정규화 + N-run 집계 + 분류기 재사용)와 테스트만.

## 선행 조건

- #16 `inference_baseline` (band: oracle/type_blind SE 앵커) — main 안착(#87).
- #10 `inference_rigor.classify_inference` (사전약정 분류기, 임계 0.50/0.10/1.0 frozen) — 재사용.
- #17 단일-run 실측: SE 50% → 정규화 (50−27)/(100−27) ≈ **0.32** (floor 0.10 위·infer_thresh 0.50
  아래 → 단일 run 은 "inconclusive" 근처; 다회로 robust 판정 필요).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/eval_harness.py` | 신규 `se_inference_score(submission_se, oracle_se, blind_se) -> float` — SE-rate 를 [0,1] 정규화(blind=0/oracle=1, clamp, span≤0→0). `Scorecard.inference_score` 공식 mirror | **중** (추가 함수, read-only) |
| `scripts/llm_eval_run.py` | `--telemetry` + `--runs N>1` 시 submission telemetry 를 N회 실행 → N SE-rate 정규화 → `classify_inference` robust SE verdict 출력. runs=1 은 단일 se_inference_score(무회귀) | 중 (집계+print) |
| `tests/test_eval_harness.py` | se_inference_score 앵커(oracle→1·blind→0·mid→between·span≤0→0)·결정론 + 분류기 재사용(scripted arm: oracle→infers·type_blind→at-floor) | 중 |

### 영향 범위

- `se_inference_score` = `inference_baseline` 의 oracle/blind SE 앵커 + submission SE → 정규화. read-only.
- 러너 변경: runs=1 경로 무회귀(단일 패스 유지). runs>1 telemetry 만 N회(비용은 사용자 N-run 시).
- `classify_inference` 재사용(임계 frozen, 같은 [0,1] frame) — 새 분류기 없음(중복 0).

## Step별 계획 (TDD)

1. **Red** — `tests/test_eval_harness.py`:
   - `test_se_inference_score_anchors`: oracle_se 입력→1.0, blind_se→0.0, 중간→(0,1), span≤0→0.0.
   - `test_se_inference_score_on_band`: 보정 분포 band 에서 infer arm 의 se_inference_score ∈ (0,1)
     (proxy 가 blind 위·oracle 아래) — 결정론.
   - `test_classify_reuse_on_se_scores`: oracle SE×3 정규화→`infers`, type_blind×3→`at-chart-blind-floor`.
2. **Green** — `se_inference_score` 구현(inference_score span 공식 mirror) + 러너 N-run telemetry 집계
   (`classify_inference([se_inference_score(...) for each run])`) + verdict 출력.
3. **Refactor** — 러너 telemetry 블록 정리(band 1회 계산 재사용), docstring 에 "정규화 SE 는
   inference_score 와 같은 frame → frozen 임계 transfer; 유료 N-run 은 사용자 로컬·신호이지 verdict
   아님" 명시.

## 검증 방법

- 신규 테스트(앵커·band·분류기 재사용) 통과.
- 러너 `--telemetry --runs 1` 단일 se_inference_score, `--runs 3`(scripted-free 부분 확인) robust SE
  verdict 경로 — score_agent 채점 byte-identical.
- 전체 pytest 회귀 0(520 유지 + 신규). mypy/ruff/build clean.

## 리스크

| 리스크 | 완화 |
|---|---|
| frozen 임계(0.50/0.10) 를 SE frame 에 재사용 정당성 | 정규화 SE 는 inference_score 와 **동일 [0,1] frame**(0=blind/1=expert) → 임계 transfer by construction. docstring 명시. 별도 임계 도입 안 함(p-hacking 회피). |
| N-run telemetry = N× LLM 비용 | 도구만 제공, 유료 N-run 실행은 사용자 로컬(기존 규율). runs=1 무회귀. |
| SE-rate 가 max_steps 의존(type_blind floor) | band 와 submission 을 *같은* sealed(같은 max_steps)서 계산(러너가 자동) — #16 경고 계승. |
| 과대 해석(robust verdict=능력 verdict) | "신호이지 verdict 아님·proxy band·1 모델" docstring/출력 명시. |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[hard]** `se_inference_score(submission_se, oracle_se, blind_se)` 결정론: oracle_se→1.0,
   blind_se→0.0, 중간→(0,1) clamp, span≤0→0.0. 신규 테스트.
2. **[tooling]** 러너 `--telemetry --runs N>1` 가 submission SE-rate 를 N회 수집→정규화→
   `classify_inference` robust SE verdict(mean±std + infers/at-floor/inconclusive) 출력. runs=1 무회귀.
3. **[rigor]** 정규화 SE 는 inference_score 와 같은 [0,1] frame → frozen 임계(0.50/0.10/1.0) 재사용,
   새 임계 도입 0. 분류기 재사용 테스트(oracle→infers·type_blind→at-floor) 통과.
4. **[regression]** 전체 pytest 회귀 0(520 유지 + 신규). score_agent 채점 byte-identical. mypy/ruff/build clean.
5. **[honesty]** docstring/출력에 "정규화 SE·proxy band·유료 N-run=사용자 로컬·신호이지 verdict 아님" 명시.
