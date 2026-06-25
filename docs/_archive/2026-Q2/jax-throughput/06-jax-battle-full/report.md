---
slug: jax-battle-full
initiative: jax-throughput
status: completed
ended: 2026-06-24
extracted_to:
  - docs/explanation/jax-throughput.md   # §5 #1 (jax-battle-full ✅) + 코드 포인터
  - DESIGN.md                            # §4 M4 follow-on 문장
changelog_entry: docs/CHANGELOG.md (jax-throughput 섹션)
---

# jax-battle-full — non-commit full battle JAX 포트 — 결과 보고서

## 한 문단 요약 (수식 없이)

지금까지 JAX로 옮긴 배틀은 보스전용 "챔피언 1마리" 버전뿐이었습니다. 이번에 **일반 배틀**(파티 3마리, 교체·회복아이템·기절 시 자동 교체·전멸 패배)까지 JAX로 옮겼고, **원본과 한 글자도 안 틀림(0 mismatch)**을 확인했습니다 — 공격/교체/회복/기절교체/전멸/시간초과 모든 시나리오 + 무작위 40판. 속도는 한 번에 수천 판 돌리면 옛 방식보다 **약 452배** 빨랐습니다. 기존 코드는 안 건드린 새 파일이라 안전합니다. 다만 정직하게: 실제 도장 보스전은 "챔피언" 버전을 쓰므로 이건 *기본(일반) 배틀 경로를 마저 커버*하는 완성도 작업이지, 핵심 경로 교체는 아닙니다.

## 요약 (수치)

| 측정 | 결과 |
|---|---|
| parity (jax vs numpy `Battle(commit_mode=False)`) | **0 mismatch** (party_a_hp·active_a·boss_hp·winner·turn·done) |
| parity 커버 | 배터리 6종(attack/switch/item-heal/force-switch/party-wipe/truncation) + random 40 seed(fixed+vary chart) |
| throughput | numpy 96k/s · **jax vmap 43.5M/s(b=1024) = 452×** |
| 테스트 | 310 → **328** (+18 importorskip parity, 회귀 0) |
| canonical | mypy(27)/ruff/build clean |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 jax_battle_full.py | ✅ | `FullBattleState`/`FullBattleParams` + `full_battle_step`(branch-free Phase1/2/3+terminal) + bridge. `__init__` 미import. |
| AC2 parity 테스트 | ✅ | 18 테스트(배터리 6 + random 12 param + jit/vmap), 0 mismatch. |
| AC3 bench | ✅ | full-battle vmap 행(numpy 96k vs jax 43.5M=452×), 정직 framing. |
| AC4 CI 불변 | ✅ | 328 passed/2 skipped(회귀 0), jax not in core, canonical clean. |
| AC5 pilot | ✅ | freeze 전 R1(parity 0)·R2(jit/vmap)·R3(speed-order) 측정. parity 비협상 충족. |
| AC6 정직 보고 | ✅ | parity 0 박제 + 속도 vmap·CPU·single-run + 한계효용(commit load-bearing·full-env 통합 별도) 명시. |
| AC7 문서 | ✅ | jax-throughput.md §5 #1 ✅ + 코드 포인터 + DESIGN §4 + CHANGELOG + INITIATIVE. broken-link 0. |

## 변경 파일 상세

**신규**
- `src/critter_gym/jax_battle_full.py` — `FullBattleState`(party_a_hp (P,)·active_a·items_a·boss_hp·turn·done·winner) + `FullBattleParams`(party 배열 + boss 스칼라 + eff + max_turns + potion_heal) + `full_battle_step`(non-commit 1턴, branch-free: Phase1 switch[alive체크]/item[potion, min(max_hp) 클램프], Phase2 speed-order moves[빠른쪽 먼저·tie A·기절 attacker skip·damage max(1,floor)·max(0) 클램프], Phase3 force-switch[argmax next-alive], terminal[party-wipe·동시기절 A-wiped→B승·truncate]) + `params_from_parties`/`initial_state` bridge.
- `tests/test_jax_battle_full_parity.py` (18, importorskip).

**수정**
- `scripts/bench_throughput.py` — non-commit full battle 섹션(numpy + jax vmap 행).
- 문서: jax-throughput.md(§5 #1 + 코드 포인터)·DESIGN §4·INITIATIVE·CHANGELOG.

## 발견된 이슈 / 정직한 한계

- **L3가 switch+item 동일턴 edge를 점검** → 한 턴 = 한 액션이라 발생 불가 확인(parity 영향 없음). force-switch argmax·동시기절 동점도 numpy와 일치 확인.
- **한계효용 정직**: gym-boss 실경로는 commit-mode(이미 포트). 본 포트=env 기본(non-commit) 경로 커버 + M4 배틀 완전성. **non-commit full-env 통합(jax_env 분기)은 별도 후속**(standalone, jax_env 무변경).
- 속도=vmap 한정·CPU·single-run. boss=단일 creature 가정(env 사용 형태; numpy Battle은 일반 party_b지만 env는 boss 1마리).

## 흡수처 (extracted_to)

| 정보 | 흡수처 |
|---|---|
| non-commit full battle 포트 + parity + 452× narrative | jax-throughput.md §5 #1 |
| M4 follow-on(배틀 두 경로 완성) | DESIGN §4 |
| jax_battle_full 코드 포인터 | jax-throughput.md references |

ADR 가치: 없음.

## 검증 결과
mypy clean(27)·ruff clean·pytest 328 passed/2 skipped(310→328, 회귀 0)·build OK·jax not in core. L3 2/2 APPROVED(plan-reviewer 라인별 parity 검증 + qa-verifier AC 7/7).
