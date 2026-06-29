---
slug: render-obs-tile-codes
initiative: eval-product
status: completed
ended: 2026-06-29
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md   # sequence #14
changelog_entry: docs/CHANGELOG.md (eval-product section, #14)
---

# render_obs 타일-코드 버그 수정 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 502 → **504** (+2 신규, 회귀 0; 기존 2개 갱신) |
| mypy / ruff | clean (31 src files) |
| 변경 파일 | 2 (llm_eval.py / test_llm_eval.py) |
| 버그 | `render_obs` 글리프/살라언스가 env patch 코드와 어긋남 (gym 3≠2, creature 2≠1) |

## 무엇이 문제였나

env(`critter_env.py:53`)는 `_PATCH_EMPTY=0, _PATCH_CREATURE=1, _PATCH_GYM=2`를 emit하는데,
`render_obs`(`llm_eval.py`)는 `_TILE_GLYPHS={0:".",1:"#",2:"C",3:"G"}` + 살라언스가 gym=3·
creature=2를 가정. 결과: LLM이 **env 생물(1)→"#"벽**, **env 체육관(2)→"C"생물**로 보고, **"G"는
절대 안 뜸**. scripted arm은 raw obs를 읽어 정상(체육관 클리어) — **LLM만** render_obs를 소비해
뒤섞인 지도를 봄 → 체육관 못 찾고 Catch 루프. task #6·#7이 묘사한 증상과 정확히 일치.
**LLM 측정 floor의 root-cause 후보.**

**왜 안 잡혔나**: 기존 합성 테스트(`_make_obs`)가 env 실제 코드가 아니라 render_obs의 *틀린
가정*(gym=3, creature=2)을 그대로 써서 통과 — env 출력과 대조한 적 없는 사각지대.

## 계획 대비 실적 (✅)

- ✅ **AC1** env `_PATCH_*` 상수를 import해 SSOT 대조하는 회귀 테스트 + 실 env obs 렌더 테스트
  (수정 전 둘 다 실패 확인 = Red).
- ✅ **AC2** `_TILE_GLYPHS`·범례·살라언스·center 분기를 env 상수로 수정(리터럴 2/3 제거).
- ✅ **AC3** 버그 인코딩 합성 테스트를 올바른 코드로 갱신 + (L3 SUGGEST) 리터럴→상수 import.
- ✅ **AC4** scripted `score_agent` byte-identical — `render_obs`가 `eval_harness.py`/
  `learnability.py`에 **미참조**(grep 증명) + `test_eval_harness.py` 통과(scripted 수치 pin).
- ✅ **AC5** 504 passed(회귀 0), mypy/ruff clean.
- ✅ **AC6** 정직 경계 — 렌더러↔env 정합 수정이며 "floor가 풀린다"는 재측정 후속 가설.

## 변경 파일 상세

- `src/critter_gym/llm_eval.py`: `from ...critter_env import _PATCH_CREATURE,_PATCH_EMPTY,_PATCH_GYM`
  → `_TILE_GLYPHS`·범례("#=wall" 제거)·`_nearest_in_view(patch, _PATCH_GYM/_PATCH_CREATURE)`·
  `center == _PATCH_GYM/_PATCH_CREATURE`. 드리프트 재발 방지(SSOT import).
- `tests/test_llm_eval.py`: 신규 2(SSOT 글리프 대조 + 실 env, `"#" not in grid` 음성 단언 포함),
  기존 2 갱신(상수 import).

## 발견된 이슈 / 후속 (L3)

- (follow-up, out-of-scope) `baselines.py` `greedy_policy`가 creature를 리터럴 `== 1`로 비교 —
  현재 값은 맞지만 같은 SSOT 갭(상수 미사용). 별도 hygiene task 후보.
- (follow-up, 사람/비용 게이트) **재측정**: 본 fix merge 후 `--battle-memory`/무상태 demonstrator
  probe를 재실행해 floor가 풀리는지 정직 기록. 본 task acceptance 아님.

## 런타임 확인 (money shot)

수정 전 생물을 `. . . # .`로 보이던 seed 1000000이 수정 후 `. . . C .` + "A wild creature (C)
is visible …"로 정상 렌더 — LLM이 처음으로 맵을 제대로 봄.

## 정직 경계

본 task는 렌더러↔env **정합 수정**이다. 이게 LLM floor의 root-cause인지(=고치면 floor가 풀리는지)는
**재측정으로 확인할 후속 가설**이며 본 task가 증명하지 않는다. 결과 reframe 금지.
