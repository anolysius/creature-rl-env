---
slug: family-d-muster
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - DESIGN.md#3.1.1   # (B) genre generalization: 4 families, family D progression axis + caveats
changelog_entry: docs/CHANGELOG.md (env-core, 2026-06-23)
---

# Family D — collection-gated power — 결과 보고서

## 요약 (수치 표)

(B) 장르 일반화 토대를 **4번째 family**로 확장. family D `MusterEnv`(`CritterGym-muster-v0`) = 세 번째 축
(**진행 의존**): CATCH 성공 시 파티 공격력 +12, 강한 보스(hp300/def24) → **먼저 muster**해야 승리. 수집·배틀을
의존 관계로 결합. (A=action-collect, B=contact-collect 수집축, C=type-agnostic duel 배틀축, **D=collection-gated 진행축**)

| 정책-특정 대조 (within-family, gym-clears) | family D (muster) | family A (critter) |
|---|---|---|
| `muster_policy` (수집-우선) | **1.42** | 1.08 |
| `rush_policy` (직행·수집안함) | **0.00** | 1.58 |
| 차이 (muster − rush) | **+1.42** (load-bearing) | −0.50 (스킬 무용/손해) |

→ muster 스킬이 **family D에선 load-bearing**(없으면 floor), **family A에선 무용**(catch 버프 없어 수집은 step 낭비)
= 깨끗한 skill-structural 신호(family C와 평행). D는 muster로 winnable(1.42)이므로 "그냥 어려움" 아님.

| 검증 | 결과 |
|---|---|
| 테스트 | **181 passed**/2 skipped (174→181, +7, 회귀 0) |
| check_env | **6 gym id** (+`CritterGym-muster-v0`) |
| mypy/ruff/build | clean (22 files) |
| honesty 가드 | pass |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 conforms+등록 | ✅ | `test_muster_env_conforms_and_registered` |
| AC2 구조적 상이(catch 버프) | ✅ | `test_catch_buffs_party_attack` + `test_structurally_distinct_from_family_a` |
| AC3 winnable(muster) | ✅ | `test_muster_policy_winnable_from_observation`(gym-clear>0, 크기 아님) |
| AC4 4-family LOO + API 무회귀 | ✅ | `test_leave_one_out_measures_four_families` + 기존 LOO/2-family 무회귀 |
| AC5 정책-특정 대조 + 정직 보고 | ✅ | `test_muster_skill_is_load_bearing_on_d_and_useless_on_a`(방향 검증); DESIGN 난이도 confound 캐비엣 |
| AC6 무회귀+check_env 6종+DESIGN+honesty | ✅ | 181 passed, mypy/ruff/build clean, A/B/C 무변경 |

전 AC ✅. acceptance를 *4번째 family + 측정 + 정직 보고*로 freeze(증명 아님).

## 변경 파일 상세

**신규**
- `src/critter_gym/envs/muster_env.py` (54) — family D, `_step_overworld` override(CATCH→파티 공격력 +MUSTER_ATK). 버프는 live party 참조로 Battle 데미지에 흐름(엔진 무변경).
- `tests/test_muster_env.py` (113) — 계약/버프/구조적 상이/winnable/대조/check_env.

**수정**
- `src/critter_gym/genre_generalization.py` (+60) — `rush_policy`(직행·catch안함)/`muster_policy`(수집-우선) + nav 헬퍼. LOO는 family 리스트 확장으로 4-family 자동.
- `src/critter_gym/registration.py` (+18) — `CritterGym-muster-v0` + family `"muster"`(강한 보스 calibration `_MUSTER_CFG`, A/B/C `_FAMILY_CFG` 무변경).
- `tests/test_genre_generalization.py` (+13) — 4-family LOO 테스트.
- `DESIGN.md` (§3.1.1 (B)) — 3→4 family, 진행 축, 정책-특정 대조 + 난이도 confound 캐비엣.

## 발견된 이슈 (심각도)

- **(낮음, 설계상 정직 표기)** family D는 강한 보스(다른 boss config) → raw cross-family LOO 평균 gap은 **난이도 confound**. 헤드라인은 **within-family 대조**(muster≫rush on D, muster≤rush on A)로 통제 — 같은 family config에서 정책만 변주하므로 난이도 일정. DESIGN 명시.
- **(낮음, L3 measurement reviewer 반영)** family A에서 muster(1.08)는 rush(1.58)보다 *약간 나쁨*(수집이 step 낭비) — "≈"가 아니라 "≤ rush"로 DESIGN 정정.
- **(낮음)** 측정 N=12 단일 run scripted = 신호.

## 흡수처 매핑 (extracted_to)

- **DESIGN.md §3.1.1 (B)** — 4 family·진행 축·정책-특정 대조·난이도 confound 캐비엣 흡수. 별도 ADR 불요(family B/C 동일 서브클래스 패턴).

## 타입 체크 / 빌드 결과

mypy: Success (22) · ruff: passed · build: OK · pytest: 181 passed/2 skipped.
