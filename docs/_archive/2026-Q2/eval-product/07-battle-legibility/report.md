---
slug: battle-legibility
initiative: eval-product
status: completed
ended: 2026-06-28
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md  # task table #7
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# 전투 obs 가독성 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 480 → **484** (+4, 회귀 0), 2 skip |
| mypy / ruff / build | clean(30) / clean / clean |
| scripted score_agent | oracle frac_of_oracle=1.0 불변 (렌더↔채점 분리) |
| obs 스키마 | 무변경 |
| L1 / L3 | 2/2 APPROVE / 2/2 APPROVE |
| 변경 | src 1 (`llm_eval.py`) · tests 1 |

## 평이한 한 문단 요약 (수식 없이)

LLM이 전투에서 "공격(0)"만 반복하다 지던 문제를 고치려고, 시스템 설명과 화면에 전투하는 법을 알려줬습니다:
"공격 기술 0~3은 서로 다른 숨은 속성이다 — 여러 개 써보고 적 체력이 가장 많이 깎이는 걸 기억해라, 안
되면 다른 동료로 교체해라, 지면 회복되니 다시 도전해라." 단 **어떤 기술이 정답인지는 안 알려줍니다** —
그걸 알아내는 게 바로 우리 환경이 측정하려는 '추론' 능력이라서요. 그리고 체육관을 생물로 착각해 잡기를
반복하던 것도 명확히 했습니다.

## 계획 대비 실적

| AC | 결과 | 근거 |
|---|---|---|
| AC1 DEFAULT_SYSTEM 전투 전략(정답 미노출) | ✅ | `test_default_system_explains_battle_strategy` |
| AC2 render 전투 Tip + 스탯 유지 | ✅ | `test_render_battle_has_tactical_hint_and_keeps_stats`, `test_overworld_render_has_no_battle_tactical_hint` |
| AC3 Catch C 타일만 명확화 | ✅ | `test_default_system_clarifies_catch_is_creature_only` |
| AC4 결정론 + 양 분기 코어필드 | ✅ | `test_render_obs_still_deterministic_and_has_core_fields` 등 |
| AC5 무회귀 + obs 무변경 + 정직 경계 | ✅ | 480→484, scripted frac 1.0 불변, mypy/ruff/build clean |

## 변경 파일 상세

- **`src/critter_gym/llm_eval.py`**: `DEFAULT_SYSTEM`에 전투 전략(무브 0~3=다른 숨은 타입·시도+적 hp 관찰+
  기억·`spamming move 0 usually loses`·action 4 교체·패배 후 재진입 재시도) + catch 명확화(C 타일 정확히·
  gym/빈 타일선 무동작). `render_obs` 전투 분기에 한 줄 Tip(무브 다양화·적 hp 관찰·교체). 어떤 무브가
  super-effective인지는 **미노출**(추론은 LLM 몫 — 벤치마크 정직성).
- **`tests/test_llm_eval.py`**: +4 테스트(전투 전략 가이드·전투 render Tip+스탯·오버월드 누출 없음·catch 명확화).

## 진단 맥락 (왜 이 task)

#6 후에도 0% floor. existence probe(grid5·types3·1gym)로 **탐색 벽 제거 후에도 보스전 전패**(battle-entries
19) 확인. 같은 config 대조: **oracle 클리어(3턴) / type_blind 59턴 전패 / LLM=type_blind처럼 행동**(move 0만
반복·교체/커밋 미사용·2턴 사망·catch 혼동). 즉 LLM이 "숨은 타입표 추론" 루프에 진입조차 못 함 → 본 task가
그 진입 장벽(메커닉 무지)을 제거.

## 정직 경계 (계승)

- **벤치마크 정직성**: 무브 정답을 떠먹이지 않음 — "시도→관찰→기억" 전략만. 추론은 LLM 몫(env가 측정하려는 능력).
- **점수 보장 아님**: 가이드를 줘도 2턴 사망·num_types 등으로 여전히 floor일 수 있음(재측정은 신호이지
  acceptance 아님).
- **obs 한계**: commit_window 상태·개별 무브 타입은 obs 미노출(env 변경=별도 task). 시스템 프롬프트가 메커닉을
  *설명*하되 obs에 없는 실시간 상태를 날조하지 않음.
- 재측정 probe는 사용자/자율 로컬. 나오는 숫자는 그대로 기록, reframe 금지.

## 흡수처 매핑

- `extracted_to`: INITIATIVE.md task table #7. 전투 가독성 규약 SSOT는 `render_obs`/`DEFAULT_SYSTEM`(코드).
  cross-task 의존 없음(archive invariant 충족).

## 타입 체크 / 빌드 결과

mypy clean(30) · ruff clean · build → `critter_gym-1.0.0rc1` · pytest 484 passed / 2 skipped.
