---
slug: jax-noncommit-env-integration
initiative: jax-throughput
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md   # §4 Update(non-commit 통합) + §5 #1
  - DESIGN.md                            # §4 — 두 배틀 경제 end-to-end 벡터화
changelog_entry: docs/CHANGELOG.md  # jax-throughput 섹션 상단
---

# non-commit full battle를 jax_env에 통합 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| parity | **0 mismatch** (numpy `CritterEnv(commit_battles=False)` 대비) |
| 신규 parity 테스트 | **32 passed** (`test_jax_noncommit_env_parity.py`) |
| 전체 테스트 | 328 → **360** (+32, 회귀 0), 2 skipped |
| throughput (CPU·single·vmap-only) | numpy 139k/s · jax vmap **5.08M(b=1024)=36× / 5.65M(b=4096)=41× / 8.35M(b=16384)=60×** |
| canonical | mypy(27)/ruff/build clean |
| default-config(commit=True) | byte-identical (commit 경로 무변경) |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 env step + jit | ✅ | `make_jax_env(JaxEnvConfig(commit=False))` + `test_jit_compiles` |
| AC2 parity 0 (비협상) | ✅ | 32 passed, 13 obs+reward+term+trunc, fixed+vary, 4 정책 |
| AC3 무회귀 | ✅ | 360 passed; commit parity(18)/difficulty/standalone 무회귀; commit byte-identical |
| AC4 vmap throughput | ✅ | 36–60× (정직 framing: vmap-only·CPU) |
| AC5 jit 컴파일 | ✅ | `test_jit_compiles`/`test_vmap_batches` |
| AC6 정직 범위 | ✅ | docs 라벨(CPU·single·family A·vmap-only·potion inert·trunc edge) |
| AC7 사전약정 pilot | ✅ | 가정 검증(코드기반·falsify 0) + 0 mismatch + non-vacuity 가드 |
| AC8 canonical + 문서 | ✅ | mypy/ruff/pytest/build clean; jax-throughput.md·INITIATIVE·DESIGN §4; CHANGELOG |

## 변경 파일 상세

**수정**:
- `src/critter_gym/jax_env.py` (+115/-2): `JaxEnvConfig`에 `commit`/`potions`/`battle_max_turns`
  필드 + `DEFAULT_NONCOMMIT_CONFIG`; `JaxEnvState`에 `items`/`battle_turn`; `overworld_branch`가
  진입 시 commit 여부로 `commit_window=on_gym & commit`·`items`·`battle_turn` 설정; 신규
  `noncommit_battle_branch`(action 매핑 + Phase1 cyclic-SWITCH + Phase2 speed-order + Phase3
  first-in-order force-switch + party-wipe/boss-dead/battle-trunc + 승리시 gym_defeated·레벨·evolve);
  `step`이 `config.commit`(compile-time)으로 분기. 모듈/클래스 docstring 갱신.
- `scripts/bench_throughput.py` (+59): non-commit full-env 벤치 섹션(`bench_numpy_noncommit_full_env`
  + `_bench_jax_noncommit_full_env`).

**신규**:
- `tests/test_jax_noncommit_env_parity.py` (+220): parity 32 tests — random·gym-clearing·switch-heavy·
  never-attack(패배) 정책, fixed+vary, jit/vmap smoke, **non-vacuity 가드**(force-switch·party-wipe 실자극).

## 발견된 이슈 (심각도)

- **[중] Phase1 SWITCH vs Phase3 force-switch 순서 차이** — numpy `_next_alive_player`(cyclic-from-active)
  와 `_next_alive`(first-in-party-order)가 *다른* 순서. freeze 전 pilot이 코드 정독으로 포착, JAX에서
  각각 cyclic loop / `argmax`로 구분 미러. 놓쳤으면 parity 깨졌을 off-by-one. → 해소(parity 0).
- **[정보] potion inert** — env action space가 유효 ITEM 인덱스(0)를 방출하지 않음(action 5→ITEM(99)).
  따라서 potion은 실질 미사용. numpy와 동일하므로 정확 미러(items 필드는 미러용으로만 보존). → 정직 라벨.
- **[정보] battle-truncation** — 실전 도달 불가(보스 hp120·min dmg≥1)이나 procgen(max_steps 400>200)서
  이론적 발산 막기 위해 `battle_turn` 카운터로 정확 미러. → 해소.

## 흡수처 매핑 (extracted_to)

- `docs/explanation/jax-throughput.md` — §4에 non-commit 통합 Update 문단(가정·pilot 발견·parity·실측·
  정직 경계) + §5 #1을 ✅ done으로 갱신.
- `DESIGN.md` §4 — 두 배틀 경제(commit/non-commit)가 full-episode env까지 end-to-end 벡터화 명시.
- ADR 가치: 없음(기존 config-driven 포트 패턴의 연장, 신규 결정 아님). INITIATIVE.md task 7 행으로 충분.

## 타입 체크 / 빌드 결과

- `mypy src`: Success, 27 files. `ruff check .`: All checks passed. `pytest`: 360 passed, 2 skipped.
  `python -m build`: wheel + sdist 빌드 성공.
