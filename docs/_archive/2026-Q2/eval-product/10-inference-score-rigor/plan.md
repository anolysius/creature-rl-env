---
slug: inference-score-rigor
initiative: eval-product
status: active
started: 2026-06-28
acceptance_freeze: true
domains: [agents]
task_type: env
mode: standard
scope_paths:
  - src/critter_gym/inference_rigor.py
  - scripts/llm_eval_run.py
  - tests/test_inference_rigor.py
extracted_to: []
supersedes: []
---

# inference_score 측정 robust화 — 사전약정 multi-run 분류기

> 작성일: 2026-06-28 | 상태: 계획 | 이니셔티브: eval-product (M5)

## 목표

#8의 첫 inference_score는 **단일 run·2월드·60스텝 = 약한 0.00**. 과거 (B) 스레드가 single-run을 노이즈로
반복 교정한 학습대로, **multi-run + 데이터 보기 전 고정한 결정규칙**으로 "프런티어 LLM이 chart-blind
floor를 robust하게 못 넘는가(또는 넘는가)"를 판정 가능하게 한다. `headroom.py`/`classify_headroom`
(ppo-headroom-rigor)의 rigor 패턴을 그대로 mirror.

> **결정규칙 (데이터 전 freeze, qa-checklist에 기록)**: per-run inference_score들의 mean `m`, std `s`(across runs).
> - `m − k·s ≥ infer_thresh` → **infers** (비관적 하한도 임계 위 → robust하게 추론/floor 초과)
> - `m + k·s ≤ floor_eps` → **at-chart-blind-floor** (낙관적 상한도 floor → robust하게 추론 실패)
> - else → **inconclusive** (run band가 임계를 가로지름 → run 더 필요)
> 고정값: `infer_thresh=0.50`, `floor_eps=0.10`, `k=1.0`.

**M5-EC1 기여**: "첫 고객 숫자"를 단일 run에서 **robust verdict**로 격상 — 고객에게 "노이즈 아닌 측정"으로 제시 가능.

## 선행 조건

- #8 done(main `81accfa`). `Scorecard.inference_score`, `SealedEvalSet` 노브, `scripts/llm_eval_run.py`,
  `src/critter_gym/headroom.py`(mirror 대상) 존재. 489 tests green.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/inference_rigor.py` | **신규** — `classify_inference(inference_runs, *, infer_thresh=0.5, floor_eps=0.1, k=1.0)` + `InferenceVerdict` NamedTuple (numpy-only, CI-cheap, headroom.py mirror). 빈 run/범위밖 가드 | 중 — 신규 순수 모듈 |
| `scripts/llm_eval_run.py` | `--runs N`(기본 1) — submission을 N회 채점, per-run inference_score 수집 → `classify_inference` verdict 출력. N=1이면 기존 출력 유지(무회귀) | 저 |
| `tests/test_inference_rigor.py` | **신규** — classify_inference property(infers/floor/inconclusive/경계/빈 가드/클램프 입력) | 저 |

### 영향 범위

- `inference_rigor`는 순수 함수(numpy) — env/jax 무import, CI에서 LLM 없이 테스트. 기존 모듈 무변경.
- 러너 `--runs` 미지정(기본 1) 시 기존 단일-run 출력 경로 그대로(무회귀). N>1일 때만 집계 분기.

## Step별 계획

1. **`classify_inference`** — `headroom.py` 구조 그대로: `InferenceVerdict(verdict, mean, std, n_runs)`;
   runs 비었으면 ValueError; 각 run score는 [0,1] 가정(score_agent가 이미 클램프). mean±std, 3-branch 판정.
2. **러너 `--runs`** — N회 `score_agent`(scripted arm은 결정론이라 oracle/type_blind 동일; LLM submission만
   변동). per-run `card.inference_score` 리스트 → `classify_inference` → "INFERENCE SCORE: m ± s (n runs) →
   VERDICT" 출력. N=1이면 기존 단일 라인 유지.
3. **테스트** — classify_inference: 전부 1.0→infers / 전부 0.0→floor / 0.5 근처 흩어짐→inconclusive /
   경계값 / 빈 입력 ValueError / mean·std·n_runs 정확.
4. **무회귀** — 전체 pytest green, 러너 N=1 경로 불변, mypy·ruff·build clean.

## 검증 방법

- mypy·ruff·pytest(.venv)·build clean. classify_inference property 테스트(LLM 불요).
- **실측 robust화(probe)는 사용자/자율 후속** — `--runs` 도구만 ship, 실제 N-run LLM 수치는 별도. 결과 숫자는
  acceptance 아님(분류기 메커니즘만 게이트).

## 리스크

- **사전약정 준수**: `infer_thresh/floor_eps/k`는 데이터 보기 전 고정(qa-checklist 기록) — p-hacking 차단.
- **과대 금지**: 분류기는 *도구* — verdict가 "infers"든 "floor"든 그대로 정직 기록. 단일 config·scripted-oracle
  proxy 경계 유지. inference_score 자체의 한계(특정 band 신호)는 #8에서 이미 명시.
- **비용**: `--runs N`은 LLM 호출 N배 — docstring에 경고. scripted/테스트는 무료.

## Acceptance Criteria (G1 통과 시 freeze)

- [ ] AC1: `classify_inference(runs, *, infer_thresh=0.5, floor_eps=0.1, k=1.0)` + `InferenceVerdict`가
  3-branch(infers/at-chart-blind-floor/inconclusive)를 `m−k·s≥infer_thresh` / `m+k·s≤floor_eps` / else로
  판정하고, 빈 run은 ValueError, mean/std/n_runs를 정확히 보고.
- [ ] AC2: 결정규칙 임계(`infer_thresh=0.5`, `floor_eps=0.1`, `k=1.0`)는 데이터 전 고정 — 코드 기본값 + qa-checklist 기록.
- [ ] AC3: `llm_eval_run.py --runs N`이 per-run inference_score를 모아 verdict를 출력하고, N=1은 기존 경로 불변(무회귀).
- [ ] AC4: classify_inference property 테스트(infers/floor/inconclusive/경계/빈 가드)가 LLM 없이 통과.
- [ ] AC5: 무회귀 — 전체 pytest green, mypy·ruff·build clean. 정직 경계(사전약정·도구≠결과·probe 후속) 명시.
