---
slug: render-obs-legibility
initiative: eval-product
status: completed
ended: 2026-06-27
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md  # task table #6
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# render_obs 가독성 수정 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 474 → **480** (+6, 회귀 0), 2 skip |
| mypy / ruff / build | clean(30) / clean / clean |
| scripted score_agent | oracle frac_of_oracle=1.0 불변 (렌더↔채점 분리 입증) |
| L1 / L3 | 2/2 APPROVE / 2/2 APPROVE |
| 변경 | src 1 (`llm_eval.py`) · tests 1 |

## 평이한 한 문단 요약 (수식 없이)

LLM이 "나는 생물이 없다"고 착각하게 만든 화면 표시(전투 밖에선 0으로 가려지는 능력치를 그대로 "hp 0"로
찍던 것)를 고쳤습니다. 이제 전투 밖에선 "너는 스타터 파티를 갖고 있고, 능력치는 전투 중에 보인다"고
정직하게 알려주고, 시야에 체육관(G)이나 야생 생물(C)이 보이면 방향까지 짚어줍니다. 다만 화면에 없는
정보(파티 마릿수 등)는 지어내지 않았고, 이 수정이 점수를 올린다고 약속하지도 않습니다 — 오해만 없앴습니다.

## 계획 대비 실적

| AC | 결과 | 근거 |
|---|---|---|
| AC1 오버월드 오도 제거 | ✅ | `test_render_overworld_does_not_mislead_with_zero_hp` ("hp 0" 부재 + "starter party" 존재) |
| AC2 전투 스탯 표시 | ✅ | `test_render_battle_shows_player_and_enemy_stats` |
| AC3 G/C 살라언스 + gym 플래그 | ✅ | `test_render_gym_salience_and_on_gym_flag`, `test_render_creature_salience` |
| AC4 결정론 + 코어필드 | ✅ | `test_render_obs_still_deterministic_and_has_core_fields` + 기존 테스트 |
| AC5 DEFAULT_SYSTEM 설명 | ✅ | `test_default_system_explains_party_goal_and_catch` |
| AC6 무회귀 + 정직 경계 | ✅ | 474→480, scripted frac 1.0 불변, mypy/ruff/build clean, docstring/plan 경계 명시 |

## 변경 파일 상세

- **`src/critter_gym/llm_eval.py`**: `render_obs` 재작성 — (1) `in_battle` 분기: 전투 중엔 player/enemy
  스탯 표시(정확), 오버월드엔 0-mask 줄 제거 + "starter party 보유, 스탯은 전투 중" 정직 표현.
  (2) 시야 살라언스: 신규 `_nearest_in_view`(center 제외 Manhattan 최근접) + `_dir_phrase`(N/S/E/W
  방향구) → gym(G)/creature(C) 위치 안내 + 중앙 타일 gym/creature 플래그. `DEFAULT_SYSTEM`에 스타터
  파티·gym 목표·catch 흐름 1~2문장 추가.
- **`tests/test_llm_eval.py`**: +6 테스트(합성 obs `_make_obs` 헬퍼 + AC1~5). 기존 render 테스트 유지.

## 발견된 이슈

- 없음 (L3 2/2 APPROVE). 진단된 root cause(0-mask 오도 + gym/creature 혼동)를 정면으로 수정.

## 정직 경계 (계승)

- 본 수정은 **오도 제거**이지 점수 보장이 아니다. 호라이즌(40스텝)·전투 난이도가 남아 재측정해도
  여전히 floor일 수 있다.
- obs에 없는 정보(파티 마릿수)는 날조하지 않음 — 진실 한도("파티 보유, 스탯은 전투 중") 표현만.
- 재측정 probe는 **사용자 로컬**(구독 claude CLI/API). 나오는 frac_of_oracle은 그대로 기록, reframe 금지.

## 흡수처 매핑

- `extracted_to`: INITIATIVE.md task table #6. render 가독성 규약의 SSOT는 `render_obs` docstring(코드 옆).
  cross-task 의존 없음(archive invariant 충족). 별도 ADR/explanation 미생성.

## 타입 체크 / 빌드 결과

mypy clean(30) · ruff clean · `python -m build` → `critter_gym-1.0.0rc1` · pytest 480 passed / 2 skipped.
