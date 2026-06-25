---
slug: jax-duel-integration
initiative: jax-throughput
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md   # duel Update 문단 (4/4 family)
  - DESIGN.md                            # §4 — all four families vectorize
  - docs/explanation/competitive-analysis.md  # gap register "competitively fast" 행 갱신
changelog_entry: docs/CHANGELOG.md
---

# duel(C) JAX 통합 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| parity (numpy `DuelEnv(commit_battles=False)` ↔ JAX duel) | **0 mismatch** |
| 신규 테스트 | 19 (`tests/test_jax_duel_parity.py`) |
| 테스트 총계 | 396 → **415 passed** (+19), 2 skipped, 회귀 0 |
| pre-freeze pilot | 19,200 compared steps 0 mismatch + scripted-optimal win 60·evolve 24 |
| 처리량 (CPU, single, vmap-only) | numpy ~123k/s · jax vmap **4.96M(b=1024)=40× / 10.15M(b=16384)=83×** |
| family 커버리지 | **4/4 (A critter / B forage / C duel / D muster) 전부 벡터화** |
| mypy / ruff / build | clean (28 files) |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 parity 0 mismatch (13 obs+reward+term+trunc, fixed+vary, ≥4 정책) | ✅ | `test_duel_parity_scripted`(4 정책×6 seed×2 vary) + `test_duel_parity_random`(5 seed) green |
| AC2 non-vacuity (ATTACK/CHARGE/GUARD·교착cap·evolve 자극) | ✅ | `test_duel_battery_is_non_vacuous` — 6 신호(attack/charge/guard/stalemate_loss/win/evolve) 전부 assert |
| AC3 family A/B/D 무회귀 + module-level byte-identical | ✅ | 415 passed(기존 396 전부 green), charge 필드·encode_obs·dispatch 전부 compile-time `family` 분기 |
| AC4 jit + vmap smoke | ✅ | `test_duel_jit_and_vmap` (단일 jit obs shape + 8-batch vmap) green |
| AC5 G2 (mypy·ruff·pytest·build) | ✅ | 전부 clean |
| AC6 정직 보고 (4/4 family, CPU·vmap-only·GPU 후속 한계) | ✅ | jax-throughput.md duel Update + DESIGN §4 + competitive-analysis 갱신; CPU·single·vmap-only·GPU(M4-EC3) 후속 명시 |

## 변경 파일 상세

**수정**
- `src/critter_gym/jax_env.py` (+156/-16): `_FAM_DUEL=3` enum + duel 배틀 상수 / `JaxEnvState`에
  `player_charge`/`enemy_charge` 필드 / `reset()` 초기화 / `overworld_branch` 진입 charge 리셋 /
  신규 `duel_battle_branch` / `encode_obs` family-aware charge / `step()` dispatch에 duel 분기 / 모듈
  docstring 갱신(4 family).

**신규**
- `tests/test_jax_duel_parity.py` (+200): parity 배터리(5 정책) + non-vacuity 가드 + jit/vmap smoke.

**문서**
- `docs/explanation/jax-throughput.md`: duel Update 문단(4/4 family, 동시 데미지·raw 데미지·charge obs 3요소,
  pilot 발견[always-attack 0승], 실측).
- `DESIGN.md` §4: all four families vectorize.
- `docs/explanation/competitive-analysis.md`: gap register "competitively fast" 행 = GPU만 남음.
- `docs/_active/jax-throughput/INITIATIVE.md`: task 10 행 + 다음 task 갱신.

## 발견된 이슈 (심각도)

- **(정보) always-attack는 0승** — pilot이 포착. 보스(hp120/atk12)가 탱키해 charge-0 공격만으론 못 이김(보스가
  out-trade). 승리에는 RPS 최적 플레이(보스 결정론 악용) 필요. → 테스트에 `duel_optimal` 정책 추가로 win/evolve
  경제 경로를 명시적으로 자극(non-vacuity 보장). 이는 env 정확성 이슈가 아니라 *테스트 설계* 발견.
- **(설계 결정) `battle_turn` 재사용** — duel turn 카운터로 기존 `battle_turn` 필드 재사용(신규 `duel_turns`
  필드 대신). duel config에선 noncommit branch 미도달이라 `battle_turn`이 duel 전용 → 안전, 상태 pytree 최소화.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 내용 |
|---|---|
| `docs/explanation/jax-throughput.md` (duel Update) | duel 포트의 *왜/무엇/정직 경계* 살아있는 narrative |
| `DESIGN.md` §4 | "all four families vectorize end-to-end" 사실 갱신 |
| `docs/explanation/competitive-analysis.md` | gap register — "competitively fast" 행이 GPU 측정만 남김 |

ADR 가치 결정 없음(기존 staging·parity-gated 포트 패턴의 4번째 적용 — 새 아키텍처 결정 아님).

## 타입 체크 / 빌드 결과

- `mypy src` — Success: no issues found in 28 source files.
- `ruff check .` — All checks passed.
- `pytest -q` — 415 passed, 2 skipped.
- `python -m build` — Successfully built wheel + sdist.
