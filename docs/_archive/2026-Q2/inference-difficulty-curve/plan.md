---
slug: inference-difficulty-curve
initiative: null
status: active
started: 2026-07-08
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/inference_curve.py
  - scripts/inference_difficulty_curve.py
  - tests/test_inference_curve.py
extracted_to: []
supersedes: []
---

# inference-difficulty-curve — 추론 난이도 곡선 (de-risked scout)

> 작성일: 2026-07-08 | 공개 후 R&D. 미포화 추론 eval 을 "점 하나"→"눈금 있는 계측기"로.

## 목표

현 추론 eval 은 **단일 config**(num_types 고정)에서 "프런티어 모델 바닥 근처,
inconclusive" 라는 점 하나다. **숨은 타입표 크기(num_types)를 다이얼처럼 돌려가며 추론
난이도를 곡선으로** 측정하면 eval 이 계측기가 된다.

**de-risked scout (이 task)**: scripted-only, 결정론, 무료. num_types 를 sweep 하며 4-arm
`inference_baseline` 을 돌려, **`infer` arm**(첫 만남에 규칙 학습·재사용 = 이상적 in-context
추론 프록시)의 SE-rate 와 정규화 `se_inference_score` 가 어떻게 떨어지는지 곡선을 뜬다.
oracle(천장)·type_blind(바닥) 앵커도 함께 기록해 밴드가 유효한지(oracle 높음·blind 낮음)
확인. 학습·LLM·돈 불필요.

## 왜 scout 인가 / 사전선언 해석

- **양성(단조 하락)**: num_types↑ → infer-arm inference_score↓ → num_types 가 **calibrated
  추론-난이도 다이얼** = 강한 결과(계측기·마케팅 헤드라인·판매 티어 축).
- **음성(평평/비단조)**: 이 knob 으론 추론 난이도 조절 안 됨 → **정직 falsify**, 그대로 보고.
- scout 라 헤드라인 금지: 1 seed set·scripted proxy(infer≠학습/LLM 곡선)·결정론 단일 pass.
  학습/LLM 앵커 곡선은 후속(필요 시 돈 게이트).

## 작업 범위

| 파일 | 변경 | 영향 |
|---|---|---|
| `src/critter_gym/inference_curve.py` (신규) | `inference_difficulty_curve(num_types_grid, *, sealed_kwargs)` — N 별 `inference_baseline` 실행, arm별 se_rate + infer-arm 정규화 score + winnable 플래그를 담은 결과 반환 | additive, numpy-only(eval_harness 재사용) |
| `scripts/inference_difficulty_curve.py` (신규) | 곡선 실측 출력(N × oracle/infer/type_blind se_rate + infer score + winnable), 사전선언 규칙·정직 라벨 print | 도구 |
| `tests/test_inference_curve.py` (신규) | 결정론·구조(각 N 결과 키)·밴드 sanity(oracle≥type_blind)·정규화 [0,1] | +테스트 |

## Step별 계획

1. **Red**: test — `inference_difficulty_curve` 결정론(같은 grid→같은 결과)·N별 4-arm 존재·
   oracle se_rate ≥ type_blind·infer score ∈ [0,1]·grid 길이 = 결과 길이.
2. **Green**: `inference_curve.py` — `inference_baseline(SealedEvalSet(num_types=N, **kw))`
   래핑, `se_inference_score(infer_se, oracle_se, blind_se)` 로 infer score 계산.
3. **Scout 실행**: `scripts/inference_difficulty_curve.py` — num_types ∈ {3,4,6,8,10,12}
   (기본, `--quick` 은 축소) 곡선 출력 + 사전선언 해석 규칙 print. 결과를 report 에 기록
   (수치 방향은 결과보고이지 AC 아님 — falsify 도 그대로).
4. 문서/CHANGELOG (task-end) — evergreen `docs/reference/` 는 결과가 유의미하면 task-end 에서.

커밋 단위: 단일 커밋 (단독 PR).

## 검증 방법

- `.venv/bin/python -m pytest -q` (전체, baseline 708 + 신규, 회귀 0)
- `mypy src` · `ruff check .`
- scout 실행 출력을 report 에 기록

## 리스크

| 리스크 | 대응 |
|---|---|
| num_types 상한(ElementType 개수) 초과 | grid 를 `min(len(ElementType), N)` 로 클램프 or 검증가드; 상한 내 sweep |
| 작은 config 라 곡선 노이즈 | scout=신호(단일 seed set), 헤드라인 금지 라벨; 유의미하면 후속 multi-run |
| infer arm 이 예상 밖 동작(추론 프록시 한계) | oracle/type_blind 앵커로 밴드 유효성 동반 검증(oracle 천장 유지 확인) |
| 결정론 깨짐 | 고정 master_seed, 랜덤 없음 |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (곡선 API)**: `inference_difficulty_curve(num_types_grid)` 가 N 별로 oracle/infer/
  type_blind/probe se_rate + infer-arm 정규화 inference_score + winnable(oracle 천장) 을
  담은 결정론적 결과 반환. 단위 테스트(결정론·구조·밴드 sanity oracle≥type_blind·score∈[0,1]).
- **AC2 (scout 스크립트 + 정직 라벨)**: `scripts/inference_difficulty_curve.py` 가 num_types
  곡선을 출력하고, 사전선언 해석 규칙(단조↓=다이얼 / 평평=falsify)·1-seed·scripted-proxy·
  헤드라인-금지·학습/LLM 앵커=후속 라벨 포함. 수치 방향은 AC 아님.
- **AC3 (무회귀·결정론)**: 전체 테스트 green(708+신규, 회귀 0), `mypy`/`ruff` clean,
  기존 eval_harness/inference 경로 무변경(additive).
