---
slug: battle-system
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
milestone: M1
exit_criteria: [M1-EC1]
scope_paths:
  - src/critter_gym/types.py
  - src/critter_gym/creatures.py
  - src/critter_gym/battle.py
  - src/critter_gym/__init__.py
  - tests/**
extracted_to: []
supersedes: []
---

# battle-system — 턴제 배틀 sub-MDP 엔진 (M1-EC1)

> 작성일: 2026-06-21 | 상태: 계획 | **마일스톤 M1 · exit criterion M1-EC1**

## 목표
활성 마일스톤 **M1**(고정월드 full subgoal chain)의 첫 벽돌. DESIGN §3.4 의 **턴제 배틀 sub-MDP**를
독립 테스트 가능한 결정론 엔진으로 구현한다: 타입 상성 데미지 · 스위치 · 아이템. 이후 진화(M1-EC2)·
gym 보스(M1-EC3)·최종보스의 토대이자, 궁극적으로 킬러 데모(보스 격파)의 코어.

**M1-EC1 충족 정의**: "턴제 배틀 sub-MDP 동작 (타입 상성 데미지·스위치·아이템) — 고정 타입표."

## 선행 조건
- M0 완료 (`CritterEnv` 존재). 본 task 는 배틀 *엔진* 만 — `CritterEnv.step` 통합은 **본 task 아님**
  (후속 `gym-boss-progression`=M1-EC3 가 배틀을 월드의 gated checkpoint 로 연결).
- 결정론 우선: 데미지 변동(랜덤 롤) 없음 — RLVR/재현성. 랜덤 요소 도입은 별도 task.
- 최소 고정 타입표를 본 task 에 포함(배틀이 데미지 계산에 필요); 확장(K 타입·밸런싱)은 `typechart-fixed`.

## 작업 범위
### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | criticality | 비고 |
|---|---|---|---|
| `src/critter_gym/types.py` | 신규 | critical | `ElementType` enum + `TypeChart`(고정 효과 행렬, rock-paper-scissors) |
| `src/critter_gym/creatures.py` | 신규 | critical | `Move`, `Creature`(types·stats·moves·hp), take_damage/heal/is_fainted |
| `src/critter_gym/battle.py` | 신규 | critical | `BattleState`·`BattleAction`·`Battle` 엔진(턴 해소·데미지·스위치·아이템) + scripted 상대 |
| `src/critter_gym/__init__.py` | 갱신 | critical | 배틀 심볼 export |
| `tests/test_types.py` | 신규 | low | 효과 행렬·상성 사이클 |
| `tests/test_creatures.py` | 신규 | low | 데미지 적용·기절·힐 |
| `tests/test_battle.py` | 신규 | low | 턴 순서·스위치·아이템·종료·scripted·결정론 |

### 영향 범위 (import 그래프)
- `creatures.py` → `types.py`; `battle.py` → `creatures.py`+`types.py`. 신규, 기존 env 영향 0.
- `CritterEnv`(envs/critter_env.py) 변경 없음 — 통합은 후속 task. core deps 불변(numpy).

## Step별 계획
1. **types.py** — `ElementType`(예: FIRE/WATER/GRASS, 최소 3, rock-paper-scissors). `TypeChart`:
   `effectiveness(attacker: ElementType, defender: ElementType) -> float` (2.0 super / 0.5 not-very /
   1.0 neutral). 고정·결정론. 다중 타입 방어 시 곱연산.
2. **creatures.py** — `Move(name, type, power)`. `Creature(name, types, max_hp, attack, defense, speed,
   moves, hp)`. 메서드: `take_damage(n)`, `heal(n)`(max_hp 클램프), `is_fainted`.
3. **battle.py** —
   - `BattleAction`: `UseMove(move_idx)` / `Switch(creature_idx)` / `UseItem(item_idx)` (정수 인코딩 가능).
   - `BattleState`: party_a/party_b(list[Creature]), active_a/active_b idx, items_a/items_b(예: potion 수), turn.
   - 데미지(결정론): `dmg = floor(move.power * (attacker.attack/defender.defense) * type_eff)`, 최소 1.
   - 턴 해소: 양측 행동 수집 → MOVE 끼리는 speed 순(타이 결정론), SWITCH/ITEM 은 선행. 적용 후 기절 판정.
   - 기절 시: 다음 생존 creature 로 강제 스위치(없으면 패배). 종료: 한쪽 전멸 → `terminated`, `info["winner"]`.
   - scripted 상대 `scripted_opponent(state, side) -> BattleAction`: 최대 (효과×power) 무브 선택(타입 인지).
4. **__init__.py** — 주요 심볼 export.
5. **tests** — 아래 검증 방법.

## 검증 방법
- 결정론 엔진이라 전부 pytest 단위 검증(랜덤 없음). 동일 행동 시퀀스 → 동일 결과.
- `run-tdd.py`(mypy/ruff/pytest/build). 새 모듈은 src/ 라 mypy strict 대상.
- 전체 배틀 플레이스루(scripted vs scripted) 가 유한 턴 내 종료(무한루프 가드 — max_turns).

## 리스크
- **스코프 팽창**: 배틀에 상태이상/급소/랜덤/멀티히트 등 포켓몬 기능을 다 넣으면 폭발 → M1 은 **결정론
  최소 코어**(타입·스위치·potion)만. 확장은 후속.
- **타입표 중복(typechart-fixed)**: 최소표를 여기 포함하되 `TypeChart`를 데이터-주도로 설계해 후속 확장이
  교체만으로 되게. milestones.md 수정은 본 task scope 아님(필요 시 소규모 후속).
- **env 통합 경계 혼동**: 본 task 는 엔진만. step() 연결 누락은 *의도된 경계*(M1-EC3).
- **무한 배틀**: 양측이 서로 못 죽이는 교착 → `max_turns` 로 truncate + info 표기.

## Acceptance Criteria (G1 통과 시 freeze)
- [ ] **AC1 (타입표)**: `TypeChart.effectiveness` 가 ≥3 타입의 rock-paper-scissors 사이클에서 super(2.0)/
  not-very(0.5)/neutral(1.0) 를 반환; 결정론. 다중 타입 방어는 곱연산. (test)
- [ ] **AC2 (creature 모델)**: `Creature`/`Move` 가 types·stats(max_hp/attack/defense/speed)·moves 보유;
  `take_damage`/`heal`(max_hp 클램프)/`is_fainted` 동작. (test)
- [ ] **AC3 (데미지 계산)**: 결정론 데미지 = floor(power·atk/def·type_eff), 최소 1; 타입 우위 시 데미지 증가
  (known-value test). 랜덤 없음.
- [ ] **AC4 (턴 순서)**: 한 턴 내 두 MOVE 는 speed 높은 쪽이 먼저 해소; 타이는 결정론 규칙. (test)
- [ ] **AC5 (스위치+아이템)**: `Switch` 가 active 교체; `UseItem` 이 active 를 힐+소비; 둘 다 턴 소모. (test)
  아이템 종류는 enum/dict 로 추상화(후속 확장 대비); M1 단일 구현은 `POTION`(고정 회복량). (test)
- [ ] **AC6 (종료)**: 한쪽 전멸 시 `terminated=True` ∧ `info["winner"]` 정확; active 기절 시 다음 생존으로
  강제 스위치, 없으면 패배. (test)
- [ ] **AC7 (scripted 상대)**: `scripted_opponent` 가 매 턴 합법·타입인지 행동 반환; scripted vs scripted
  배틀이 `max_turns` 내 결정론적으로 종료. (test)
- [ ] **AC8 (결정론)**: 동일 초기 `BattleState` + 동일 행동 시퀀스 → 동일 최종 상태/turn-by-turn(숨은 랜덤 0). (test)
- [ ] **AC9 (툴체인 green)**: `ruff check .` ∧ `mypy src` ∧ `pytest -q` ∧ `python -m build` 통과.
