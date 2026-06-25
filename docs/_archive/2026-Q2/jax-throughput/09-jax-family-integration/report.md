---
slug: jax-family-integration
initiative: jax-throughput
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md   # family 통합 Update
  - DESIGN.md                            # §4 — 3/4 family 벡터화
changelog_entry: docs/CHANGELOG.md
---

# forage + muster family를 jax_env에 통합 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| parity | **0 mismatch** (numpy `ForageEnv`/`MusterEnv`, non-commit) |
| 신규 테스트 | **24 passed** (`test_jax_family_parity.py`) |
| 전체 테스트 | 372 → **396** (+24, 회귀 0), 2 skipped |
| family 벡터화 | A(critter)/B(forage)/D(muster) = 3/4. duel(C)=별도 후속 |
| canonical | mypy(28)/ruff/build clean |
| family A | byte-identical (party_atk_boost critter 미관여) |

## 계획 대비 실적

AC1–AC8 전부 ✅(qa-checklist 1:1). muster 미러 성공 → descope 미발동.

## 변경 파일 상세

**수정**: `src/critter_gym/jax_env.py` (+63): `JaxEnvConfig.family`(0/1/2) + `JaxEnvState.party_atk_boost`
+ overworld_branch family 분기(forage contact-collect/CATCH inert/gym-enter 상호배제, muster catch 부스트)
+ `attack_of`(muster 부스트 반영)/`reset_boost_on_evolve`(evolve 리셋) + 양 battle branch 적용.
**신규**: `tests/test_jax_family_parity.py` (+188): forage/muster parity 24 + non-vacuity 가드.

## 발견된 이슈 (심각도)

- **[중] muster 부스트×evolve 상호작용** — `evolve()`가 `attack=form.attack`(creatures.py:97)로 부스트를
  덮음 → 단순 `base+12×caught` 모델은 발산. `party_atk_boost` 누적기(catch +12 전멤버/evolve시 해당 멤버 0)로
  정확 미러. pilot의 catch-then-gym parity(enemy_hp) + non-vacuity 가드(catch·evolve 자극)로 검증. → 해소.
- **[정보] duel(C) 범위 밖** — type-agnostic RPS/stamina 배틀은 별도 엔진(jax_battle처럼) → 후속 task.

## 흡수처 매핑 (extracted_to)

- `jax-throughput.md` — family 통합 Update(forage·muster·muster 부스트 미러·duel 후속).
- `DESIGN.md` §4 — 3/4 family 벡터화.
- ADR 가치 없음(config 확장). INITIATIVE task 9 행으로 충분.

## 타입 체크 / 빌드 결과

`mypy src` Success(28). `ruff` passed. `pytest` 396 passed/2 skipped. `build` 성공.
