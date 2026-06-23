---
slug: obs-harmonization
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to: []          # evergreen 흡수 없음 — DESIGN §3.1.1(살아있는 scope)에 직접 반영
changelog_entry: docs/CHANGELOG.md (env-core, obs-harmonization)
---

# obs 조화 (Observation Harmonization) — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | **185 → 192 passed**(+7), 2 skipped, 0 fail |
| mypy | 22 files clean |
| ruff | clean |
| build | OK (wheel+sdist) |
| env id | 6종 무회귀 |
| env family | 4종(A/B/C/D) 동일 obs 공간 공유 |
| core | numpy-only 유지(PPO는 `[rl]` 뒤 importorskip) |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 HARMONIZED_OBS_KEYS SSOT + 4 family 동일 키 | ✅ | `env_family.HARMONIZED_OBS_KEYS = REQUIRED_OBS_KEYS ∪ {player_charge,enemy_charge}`; `test_all_four_families_share_one_obs_space` |
| AC2 비-duel 0마스킹 / duel 보존 | ✅ | `test_nonduel_families_mask_charge_to_zero` + `test_duel_preserves_real_charge_values` + dtype int64 |
| AC3 scripted 정책 점수 조화 전후 동일 | ✅ | `test_scripted_policies_ignore_padded_charge_keys` — 5정책×3 family, charge 키 제거 시 액션 동일(=패딩 행동 불변, 점수동일보다 강한 보증) |
| AC4 무회귀 + 툴체인 | ✅ | 185→192 passed, mypy/ruff/build clean, `check_env`(test_compliance) green |
| AC5 assert_obs_compatible 4 family 통과 + _MultiFamilyEnv 구성 | ✅ | `test_all_families_obs_compatible_after_harmonization` + `test_multifamily_env_constructs_with_duel`(smoke) — **실험 실행은 다음 task** |
| AC6 DESIGN/독스트링 정직 갱신 + override 기록 | ✅ | DESIGN §3.1.1 "duel excluded" 제거 + "duel now includable, 실험은 다음 task, gap 미축소" + M5/override 명시; genre_learned_transfer docstring 갱신 |
| AC7 CHANGELOG 1줄 | ✅ | `docs/CHANGELOG.md` env-core 상단 |

## 변경 파일 상세

**신규**
- `tests/test_obs_harmonization.py`(99줄) — AC1·2·3 가드(4 family obs 동일 / charge 마스킹·보존 / 패딩 행동 불변).

**수정**
- `src/critter_gym/env_family.py` — `CHARGE_OBS_KEYS`/`MAX_CHARGE_OBS`/`HARMONIZED_OBS_KEYS` SSOT 추가.
- `src/critter_gym/envs/critter_env.py` — base obs space+_obs에 charge 키(0) 추가, `MAX_CHARGE_OBS` import.
- `src/critter_gym/envs/duel_env.py` — base가 charge 키를 제공하므로 중복 space 확장 제거, `assert MAX_CHARGE <= MAX_CHARGE_OBS` 가드, `spaces` import 제거.
- `scripts/genre_learned_transfer.py` — docstring + `assert_obs_compatible` docstring 갱신(로직 무변경 — 키가 동일해져 자연 통과). 4 family 포함 가능.
- `tests/test_genre_learned_transfer.py` — "duel 거부" 테스트를 "4 family 수용 + _MultiFamilyEnv smoke"로 교체.
- `DESIGN.md` §3.1.1 — obs 조화 완료 + 마일스톤 override 정직 기록.

## 설계 결정 — A안(코어 최소 침습 superset/마스킹)을 pilot로 확정

freeze 전 pilot로 base `CritterEnv`에 charge 키를 추가하고 전체 스위트를 돌린 결과 **회귀 단 1건**(`test_obs_incompatible_family_rejected` — AC5가 의도적으로 뒤집는 "duel 거부" 테스트)만 발생. 나머지 184개 전부 green(`check_env` 6종, duel charge 역학, chart-leak 포함). 모든 family가 `CritterEnv`를 상속하므로 base 한 곳 수정으로 4 family 통일 달성 → **A안 확정, B안(계약 1급화·코어 전면 변경) reframe 불필요**.

## 발견된 이슈 (심각도)

- (낮음) `MAX_CHARGE`(duel 로컬)와 `MAX_CHARGE_OBS`(env_family)가 별도 상수 — 드리프트 방지로 `duel_env`에 `assert MAX_CHARGE <= MAX_CHARGE_OBS` 런타임 가드 추가. SSOT 1급 통합은 과한 변경이라 보류.

## 정직한 한계 / 다음 task

- 이 task는 **enabler**다. 4 family가 한 obs 공간을 공유하게 됐을 뿐, **전이 gap(#26 +2.56)을 줄이지 않았다**. duel 포함 widened-train-distribution + 메커닉-범용 정책으로 전이 gap을 *줄이는* 실험이 다음 task(이니셔티브 층2의 핵심).
- 마일스톤 override: 본 작업은 M3(공개)가 아니라 M5/moat 층2 enabler이며 "기능 준비가 공개보다 먼저" 방침에 따라 진행. G1에서 사람이 override 승인.

## 타입 체크 / 빌드 결과
- mypy: Success, 22 source files.
- ruff: All checks passed.
- build: critter_gym-0.0.1 wheel+sdist OK.
- pytest: 192 passed, 2 skipped.
