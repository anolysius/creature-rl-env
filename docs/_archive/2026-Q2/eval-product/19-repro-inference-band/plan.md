---
slug: repro-inference-band
initiative: eval-product
status: active
started: 2026-06-30
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
scope_paths:
  - scripts/reproduce_results.py
  - tests/test_reproduce_results.py
extracted_to: []
supersedes: []
---

# 논문 §5 inference band 를 one-command 재현에 추가 (M3-EC4)

> 작성일: 2026-06-30 | 상태: 계획 | 마일스톤: M3-EC4 (arXiv 초안 신뢰성)

## 목표

`scripts/reproduce_results.py`(논문 headline 재현 진입점)는 현재 **(1) throughput + (2) oracle
headroom** 만 재생성하고, **논문 §5 의 새 중심 수치 = eval-product inference band**(#16
`inference_baseline`: oracle/infer/type_blind/probe 의 super-effective-move rate)는 빠져 있다.
#17 reframe 으로 §5 가 논문의 주요 섹션이 됐는데 그 band 수치를 **한 명령으로 검증할 수 없다.**
band 는 scripted·무료·결정론 → 완벽히 재현 가능. 이 task 가 repro 에 **§5 band 섹션**을 추가해
리뷰어가 §5 의 band(LLM 을 읽는 자)를 직접 재생성·검증하게 한다(M3-EC4 신뢰성).

**정직 경계**: scripted band 만 재현(무료·결정론·CI-가능); **LLM 실측(SE 50%)은 유료·평가자 로컬**
이라 repro 에 포함하지 않음(명시). 본 task = 재현 진입점 확장, 측정 실행 아님.

## 선행 조건

- #16 `inference_baseline(sealed)` (main 안착) — band 산출.
- #18 `se_inference_score` (main 안착, #88 머지 시) — 정규화 앵커. **주의**: #88 미머지면 se_inference_score
  미존재 → band(SE-rate)만 출력하고 se_inference_score 표시는 #88 의존으로 분기/생략(아래 리스크).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/reproduce_results.py` | 신규 testable 헬퍼 `inference_band(quick) -> InferenceBaseline`(demonstrator config, quick 시 n_worlds 축소) + main() 에 "(3) eval-product inference band" 출력 섹션(4-arm SE-rate + 정직 framing) | **중** |
| `tests/test_reproduce_results.py` | 신규 — 헬퍼 band 단조(oracle≥infer≥type_blind≥probe)·결정론·quick 축소 smoke | 중 |

### 영향 범위

- `inference_band` = `inference_baseline`(read-only, scripted) 호출 → 기존 throughput/headroom 섹션 무변경.
- main() 헤더 문구에 (3) 추가. 기존 (1)/(2) shell-out 무변경(회귀 0).
- LLM·env·채점 무변경.

## Step별 계획 (TDD)

1. **Red** — `tests/test_reproduce_results.py`: `inference_band(quick=True)` 가 InferenceBaseline 반환,
   SE-rate 단조(oracle≥infer≥type_blind≥probe), 결정론, quick 이 full 보다 작은 n_worlds.
2. **Green** — `reproduce_results.py` 에 `_DEMO_CONFIG` + `inference_band(quick)`(quick: n_worlds=4,
   else 8) + main() 출력 섹션(band 4-arm + "scripted·무료·결정론 재현 / LLM 실측=유료·로컬·여기 미포함").
3. **Refactor** — 헤더 문구 (1)(2)→(1)(2)(3) 갱신, docstring 정합.

## 검증 방법

- 신규 테스트(단조·결정론·quick) 통과.
- `python scripts/reproduce_results.py --quick` 가 (3) band 섹션을 결정론 출력(수동 1회).
- 전체 pytest 회귀 0(523 유지 + 신규). mypy/ruff clean.
- band 수치가 #16 band·§5·`inference-baseline.md` 와 일치.

## 리스크

| 리스크 | 완화 |
|---|---|
| #88(se_inference_score) 미머지 → import 실패 | main 에 #88 머지 후 분기 시작(또는 se_inference_score 표시를 옵셔널 import 로 감싸 부재 시 band 만 출력). G1 전 main 상태 확인. |
| repro 실행이 느려짐(band = scripted 8 world × episode) | quick 시 n_worlds=4·기존 throughput/headroom 보다 훨씬 빠름(scripted, LLM 無). |
| 과대(“repro 가 LLM 결과 재현”) | 출력에 "scripted band 만·LLM 실측=로컬·미포함" 명시. |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[hard]** `reproduce_results.inference_band(quick)` 가 demonstrator config 의 `InferenceBaseline`
   결정론 반환, SE-rate 단조(oracle≥infer≥type_blind≥probe), quick 이 full 보다 작은 n_worlds. 신규 테스트.
2. **[tooling]** `reproduce_results.py` main() 이 "(3) eval-product inference band" 섹션을 출력(4-arm
   SE-rate). 헤더 (1)(2)(3) 반영. 기존 (1)(2) 섹션 무변경(회귀 0).
3. **[honesty]** 출력에 "scripted band=무료·결정론·재현 가능 / LLM 실측(§5 SE 50%)=유료·평가자 로컬·
   본 repro 미포함" 명시.
4. **[regression]** 전체 pytest 회귀 0(523 유지 + 신규). mypy/ruff clean. 기존 throughput/headroom 무변경.
