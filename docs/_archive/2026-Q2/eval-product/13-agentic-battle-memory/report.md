---
slug: agentic-battle-memory
initiative: eval-product
status: completed
ended: 2026-06-29
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md   # sequence #13 (moved to _archive on task-end)
changelog_entry: docs/CHANGELOG.md (eval-product section, #13)
---

# 전투-결과를 기억하는 agentic 메모리 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 502 → **512** (+10, 회귀 0) |
| mypy / ruff / build | clean (31 src files) |
| 신규 공개 심볼 | `llm_eval.BattleMemoryLLMAgent` |
| 러너 플래그 | `--battle-memory` |
| 변경 파일 | 3 (llm_eval.py / test_llm_eval.py / llm_eval_run.py) |

## 계획 대비 실적 (✅/⚠️/❌)

- ✅ **AC1** Protocol(`act`+`reset`) + 봉인 set `score_agent` stub end-to-end
- ✅ **AC2** (타입,무브)당 최신 단일값 덮어쓰기 + bounded(≤num_types×4) + 프롬프트 surface
- ✅ **AC3** 측정 무결성 — surface에 type名/차트/정답-무브 없음 + docstring 정직경계 단언
- ✅ **AC4** `reset()` 전투 메모리 clear (월드 간 누수 0)
- ✅ **AC5** scripted reference arm byte-identical (어댑터↔채점 분리; 테스트로 대조)
- ✅ **AC6** 전체 스위트 그린 + mypy/ruff clean
- ✅ **AC7** 러너 `--battle-memory` 노출, stub 무회귀
- ✅ **AC8** docstring 정직 경계 + AC3 테스트가 실행 단언

## 변경 파일 상세

- **신규** `src/critter_gym/llm_eval.py::BattleMemoryLLMAgent(StatefulLLMAgent)` — 연속 in-battle obs를
  diff해 직전 공격무브(0-3)의 enemy_hp 낙폭을 적 타입별 `{enemy_type:{move:최신데미지}}`로 귀속, 프롬프트에
  *원시 관찰 사실*로 surface(정답-무브 추천 없음). `reset()`이 표 clear. 부모에 `_remember()` 추출(중복 제거).
- **수정** `tests/test_llm_eval.py` — 10개 테스트(귀속·덮어쓰기·bounded·surface·무결성·docstring·교체-비귀속·
  reset·byte-identical 대조).
- **수정** `scripts/llm_eval_run.py` — `--battle-memory`(stateful 함의) + fresh_agent 분기 + memory 라벨.

## 발견된 이슈 (심각도) — L3 SUGGEST 5건, 전부 반영

- (low, correctness) numpy 배열 별칭 → 스칼라 스냅샷(`_prev_battle` tuple)으로 교체 — 별칭 시 delta=0 잠재버그 제거.
- (info, correctness) 같은-type 적 교체 오귀속 → env 불변식(단일 보스·faint가 전투 종료=in_battle 0)으로 **도달 불가**,
  `_observe_battle_outcome` docstring에 명시.
- (low, maint) act() 윈도우 중복 → 부모 `_remember()` 추출·양쪽 재사용.
- (low, verify) bounded 상한 미단언 → 전용 테스트 추가 + docstring "≤4/타입(무브 0-3)"로 정밀화(과대 표현 제거).

## 흡수처 매핑 (extracted_to)

- INITIATIVE.md sequence에 #13 1행 추가(아래 task-end가 수행). 새 ADR/runbook/reference 없음 — 본 task는
  eval-product의 *측정 공정성* 라인(#5~#12)의 연속이라 기존 narrative에 흡수.

## 타입 체크 / 빌드 결과

- `mypy src` → Success (31 files). `ruff check .` → All checks passed. `python -m build` → OK.
- 런타임 sanity: oracle로 실제 전투까지 몰아넣은 뒤 BattleMemoryLLMAgent에게 전투를 맡겨 실제 env obs에서
  귀속 발화 확인(`{2: {1: 10}}`) — 합성 obs 테스트 외 실 env 경로도 검증.

## 정직 경계 (계승 — reframe 금지)

본 task는 **메커니즘**이지 측정 결과가 아니다. CI는 stub `complete`; 실제 프런티어 LLM 재측정은 사용자 로컬
(구독 CLI/API). 어댑터를 두껍게 한 것은 *후속* 측정을 공정하게 만들 뿐, 그 자체로 "chart-blind floor가
아티팩트였다"를 증명하지 않는다. 또한 전투 attrition(`damage=max(1)`)·작은 표본 confound는 여전히 잔존 —
재측정 결과가 floor로 남더라도 "LLM 능력 verdict"로 reframe 금지.
