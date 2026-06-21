---
slug: battle-system
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
milestone: M1
exit_criteria: [M1-EC1]
---

# Report — battle-system (턴제 배틀 sub-MDP 엔진) · M1-EC1 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약
활성 마일스톤 **M1**의 첫 벽돌. DESIGN §3.4 턴제 배틀 sub-MDP를 독립 테스트 가능한 **결정론 엔진**으로
구현 — 고정 타입표(rock-paper-scissors) · 타입 상성 데미지 · 스위치 · 아이템(potion) · scripted 상대.
Acceptance 9/9, 35 tests green. **M1-EC1 충족.**

## 산출물
| 파일 | 내용 |
|---|---|
| `src/critter_gym/types.py` | `ElementType`(FIRE/WATER/GRASS 3-cycle) + `TypeChart`(고정 효과 행렬, 다중타입 곱연산) |
| `src/critter_gym/creatures.py` | `Move`, `Creature`(types·stats·moves·hp) + take_damage/heal(클램프)/is_fainted |
| `src/critter_gym/battle.py` | `BattleState`·`BattleAction`·`Battle` 엔진 + `scripted_opponent` + `play_scripted` |
| `src/critter_gym/__init__.py` | 배틀 심볼 export |
| `tests/test_types.py`·`test_creatures.py`·`test_battle.py` | 17 케이스 |

## Acceptance 결과 (G1 freeze ↔ 실측, 1:1)
- ✅ AC1 타입표 — rps 사이클 2.0/0.5/1.0, 다중타입 곱연산
- ✅ AC2 creature 모델 — stats·moves + take_damage/heal/is_fainted
- ✅ AC3 데미지 — 결정론 floor(power·atk/def·eff) 최소1; known-value (FIRE→GRASS=96 > FIRE→WATER=24)
- ✅ AC4 턴 순서 — speed 높은 쪽 선공(타이 결정론); 빠른 쪽이 one-shot 시 느린 쪽 move skip
- ✅ AC5 스위치+아이템 — Switch 교체·턴소모; UseItem(potion) 힐+소비; `ItemKind` enum 추상화
- ✅ AC6 종료 — 전멸 시 terminated+winner; 기절 시 강제 스위치, 없으면 패배
- ✅ AC7 scripted 상대 — 타입인지 최대데미지 무브; scripted vs scripted max_turns 내 종료
- ✅ AC8 결정론 — 동일 초기 state + 동일 행동 → 동일 trace (deepcopy 2회 동일); 숨은 랜덤 0
- ✅ AC9 툴체인 — ruff ∧ mypy(8 files) ∧ pytest(35) ∧ build(sdist+wheel)

## 설계 메모 (후속 인계)
- **결정론**: 데미지 랜덤 롤 없음, dict insertion-order만 사용 → RLVR/재현성. 랜덤(변동·급소)은 의도적 제외.
- **턴 해소**: switch/item 선행 → move는 speed 내림차순(타이 A 먼저). 기절 active는 phase3에서 다음 생존으로 강제 스위치.
- **BattleAction(kind, index)**: 향후 `CritterEnv.step` 통합 시 Discrete 인코딩 가능(MOVE 0..N / SWITCH / ITEM). `StepResult`는 Gymnasium 5-tuple에 직접 매핑.
- **경계**: 엔진만. env 통합·월드 gated checkpoint는 **M1-EC3** `gym-boss-progression`.

## L3 리뷰 반영
- @plan-reviewer SUGGEST(verification): 양측 동시 전멸 tie-break(주석 의도)을 실행 테스트로 → `test_simultaneous_wipe_resolves_to_side_b` 추가(현재 무방어 분기 회귀 가드).
- @qa-verifier: APPROVE (AC 9/9 정합).

## 마일스톤 진행 (M1)
- [x] **M1-EC1** 턴제 배틀 sub-MDP ← 본 task
- [ ] M1-EC2 진화 (`creature-evolution`)
- [ ] M1-EC3 gym boss 체인 + env 통합 (`gym-boss-progression`) — 본 엔진 소비
- [ ] M1-EC4 subgoal boolean 리워드 · M1-EC5 ≥1 boss 격파

## 후속
- 다음 권장: `creature-evolution`(M1-EC2) 또는 `gym-boss-progression`(M1-EC3, 배틀을 월드에 연결).
- (소규모) 데미지 1턴 격파가 흔함 — 보스 밸런싱은 `typechart-fixed`/boss 설계에서.
