---
slug: render-obs-tile-codes-2
initiative: eval-product
status: active
started: 2026-06-30
acceptance_freeze: true
mode: standard
domains: [agents, rl-env]
scope_paths:
  - src/critter_gym/llm_eval.py
  - tests/test_llm_eval.py
extracted_to: []
supersedes: [render-obs-tile-codes]
---

# render_obs 타일-코드 버그 수정 — #14 재적용 (PR #81 머지충돌 회피)

> 작성일: 2026-06-30 | 상태: 계획(재적용)

## 배경 (왜 새 task인가)

이 변경은 **이미 L1/L3 APPROVED 된 #14(`render-obs-tile-codes`, PR #81)** 와 **동일한 코드 변경**이다.
#79·#80을 main에 머지한 뒤 #81이 main과 충돌(같은 파일 편집)했고, #81 브랜치는 #79보다 먼저
갈라져 `BattleMemoryLLMAgent`가 없으므로 GitHub 웹 충돌 해소가 #79 코드를 날릴 위험이 있다.
따라서 **#79가 들어간 새 main 위에 동일 수정을 깨끗이 재적용**해 충돌 없는 PR을 만든다.
신규 리뷰가 아니라 *승인된 #14의 재적용* — L1/L3는 #14에서 이미 완료.

## 목표

`render_obs`(LLM 텍스트 맵)의 글리프/살라언스 코드를 env 실제 `local_patch` 코드와 일치시킨다.
- env(`critter_env.py:53`): `_PATCH_EMPTY=0, _PATCH_CREATURE=1, _PATCH_GYM=2`.
- 버그: `_TILE_GLYPHS={0:".",1:"#",2:"C",3:"G"}` + 살라언스가 gym=3·creature=2 가정 → LLM이 생물을
  "#"벽으로, 체육관을 "C"생물로 봄, "G" 안 뜸.

## 작업 범위

| 파일 | 변경 |
|---|---|
| `src/critter_gym/llm_eval.py` | env `_PATCH_*` import + `_TILE_GLYPHS`·범례·살라언스·center 분기를 상수로 |
| `tests/test_llm_eval.py` | 신규 2(SSOT 글리프 대조 + 실 env, `"#" not in grid`) + 기존 2 합성 갱신(상수 import) |

## 검증 방법

- `python -m pytest tests/test_llm_eval.py -q` + 전체 스위트 그린(회귀 0), `mypy src`/`ruff check .` clean.
- 무회귀: `render_obs`는 scripted 채점 경로 미참조 → scripted byte-identical, #79 BattleMemoryLLMAgent 무영향.

## Acceptance Criteria (#14에서 freeze, 재적용)

- [ ] AC1: env `_PATCH_*` 상수 import해 글리프/살라언스 SSOT 대조 회귀 테스트 + 실 env 렌더 테스트.
- [ ] AC2: `_TILE_GLYPHS`·범례·살라언스·center 분기가 env 상수로 수정(리터럴 2/3 제거).
- [ ] AC3: 기존 합성 테스트 상수 import로 갱신.
- [ ] AC4: scripted `score_agent` byte-identical + #79 BattleMemoryLLMAgent 무영향(전체 스위트 그린).
- [ ] AC5: 전체 스위트 그린(회귀 0) + mypy/ruff clean.
- [ ] AC6: 정직 경계 — 렌더러↔env 정합 수정(이미 #14에서 floor 재측정 follow-up 기록 완료).
