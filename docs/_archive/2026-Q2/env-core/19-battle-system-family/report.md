---
slug: battle-system-family
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - DESIGN.md#3.1.1   # (B) genre generalization honest-scope SSOT updated (3 families + skill-structural signal + caveats)
changelog_entry: docs/CHANGELOG.md (env-core, 2026-06-23)
---

# Family C — structurally-distinct battle system — 결과 보고서

## 요약 (수치 표)

DESIGN §3.1.1 (B) 장르 일반화의 **정직한 약점**(family B가 thin = 수집 1축, A-튜닝 정책이 gap≈0으로 전이)을
메우는 **세 번째 env family** 추가. family C(`DuelEnv`)는 **배틀 시스템 자체를 교체** = family B가 결여한
*더 강한 구조 축*: 타입-무관 stamina/commit RPS 결투(ATTACK>CHARGE>GUARD>ATTACK, charge가 공격 배율; 타입표·스위칭 없음).

| 측정 (leave-one-out, {critter,forage,duel}, held-out 시드 N=12) | held-out=duel mean | gap |
|---|---|---|
| A-튜닝 (`type_attacker`) | 0.583 | **+3.917** (A 스킬 C로 비전이) |
| C-적합 (`duel_aware`) | 4.333 | **+0.167** (전이됨) |
| random | 0.333 | +1.542 |

→ family C의 env-level gap은 **정책-특정**(A-튜닝 +3.917 ≫ C-적합 +0.167) = **skill-structural**(틀린 스킬),
*난이도 confound 아님*(C는 C-적합 정책으로 winnable 4.333). family B(관대한 수집 축)가 만들지 못한 신호.

| 검증 | 결과 |
|---|---|
| 테스트 | **171 passed** / 2 skipped (160→171, **+11 신규, 회귀 0**) |
| check_env | **5 gym id** (fixed/procgen/commit/forage/**duel**) |
| mypy / ruff / build | clean (21 files) |
| honesty 가드 | `test_source_does_not_overclaim_learned_inference` pass |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 conforms+등록 | ✅ | `test_duel_env_conforms_and_registered`; `CritterGym-duel-v0` + family `"duel"` |
| AC2 구조적 상이 배틀 | ✅ | `test_duel_battle_trajectory_distinct_from_family_a`(배틀상태 시그니처 A≠C) + `test_duel_battle_is_type_agnostic`(차트 무관 stat 데미지) |
| AC3 observable-only winnable | ✅ | `test_duel_exposes_charge_in_obs_but_contract_still_holds` + `test_duel_winnable_from_observable_state`(obs-only duel_aware ≈4.33) |
| AC4 3-family LOO + 2-family 무회귀 | ✅ | `test_leave_one_out_measures_three_families` + `test_two_family_pairwise_api_unregressed` |
| AC5 측정+정직 보고(정책-특정 대조) | ✅ | `test_family_c_gap_is_skill_structural_not_difficulty`; 위 수치표; DESIGN §3.1.1 갱신 |
| AC6 무회귀+toolchain+honesty | ✅ | 171 passed, check_env 5종, mypy/ruff/build clean, `test_family_a_battle_unchanged_by_family_c` |

전 AC ✅ — 편차 없음. acceptance를 *측정+정직 보고*로 freeze했고(성능/주장 freeze 아님), 결과는 신호로 보고.

## 변경 파일 상세

**신규**
- `src/critter_gym/envs/duel_env.py` (147) — family C `DuelEnv(CritterEnv)`. 배틀 경로만 override(`__init__`/`reset`/`_obs`/`_maybe_enter_battle`/`_step_battle`). duel charge를 extra obs 키로 노출(`conforms` ⊇ REQUIRED → 계약 무위반).
- `tests/test_duel_env.py` (175) — AC1–AC3 + 메커닉(GUARD 무효화·charge 배율) + check_env(duel) + family A 무회귀.

**수정**
- `src/critter_gym/genre_generalization.py` (+112) — `LeaveOneOutGap` + `measure_genre_generalization_loo`(다-family) + obs-only 레퍼런스 정책 `nav_toward_gyms`/`type_attacker_policy`/`duel_aware_policy`. 기존 2-family API 무회귀.
- `src/critter_gym/registration.py` (+11) — `CritterGym-duel-v0` + family registry `"duel"`.
- `tests/test_genre_generalization.py` (+64) — AC4(LOO 3-family + 2-family 무회귀) + AC5(skill-structural 대조).
- `DESIGN.md` (§3.1.1 (B)) — 2 family→3 family, skill-structural 신호, 캐비엣 명시.

## 발견된 이슈 (심각도)

- **(낮음, L3 SUGGEST 반영)** family C의 보스는 **고정 결정론 패턴**(charge→공격)이고 duel charge가 obs에 노출 →
  winnability 4.333은 *상대 예측가능성*도 일부 반영(순수 duel 스킬만 아님). **skill-structural 판정은 유효** —
  A-튜닝 정책도 동일 obs 접근에서 ≈0.6으로 floor. 캐비엣을 DESIGN §3.1.1에 명시.
- **(낮음)** 측정은 N=12 단일 run scripted 레퍼런스 = *신호*지 튜닝 수치 아님(직전 3 task 패턴 계승).

## 흡수처 매핑 (extracted_to)

- **DESIGN.md §3.1.1 (B)** — 살아있는 honest-scope SSOT. 3 family·정책-특정 skill-structural 신호·캐비엣 흡수.
  별도 explanation/how-to/reference/ADR 신설 없음(설계 narrative는 DESIGN이 SSOT, family C는 ForageEnv 선례의
  동일 패턴 — 새 ADR 불요).

## 타입 체크 / 빌드 결과

mypy: Success (21 files) · ruff: All checks passed · build: OK · pytest: 171 passed/2 skipped.
