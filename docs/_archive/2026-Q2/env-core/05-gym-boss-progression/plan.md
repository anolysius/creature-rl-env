---
slug: gym-boss-progression
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
milestone: M1
exit_criteria: [M1-EC3, M1-EC4, M1-EC5]
scope_paths:
  - src/critter_gym/envs/**
  - src/critter_gym/party.py
  - tests/**
extracted_to: []
supersedes: []
---

# gym-boss-progression — 배틀을 월드에 연결 (M1-EC3)

> 작성일: 2026-06-21 | 상태: 계획 | **마일스톤 M1 · EC3 (주축) + EC4·EC5 (부분)**

## 목표
`battle-system`(M1-EC1)이 만든 배틀 엔진을 **실제 env 루프에 연결**한다. 처음으로 "탐험 → gym 진입 →
턴제 배틀 → 보스 격파"가 한 에피소드에서 돈다. 보스 격파는 **boolean subgoal 리워드**(RLVR)로 노출.
M1 의 핵심 가치("게임이 실제로 돌아간다") 실현.

**충족 EC**: M1-EC3(배틀 sub-MDP가 월드의 gated checkpoint), M1-EC4(subgoal boolean 리워드),
M1-EC5(scripted 가 ≥1 boss 격파 — 부분; 풀 베이스라인은 후속).

## 선행 조건
- M1-EC1 완료(`battle.py` 엔진: `Battle`/`BattleState`/`scripted_opponent` 등).
- 고정월드(procgen 없음 — M2). gym 배치는 시드 결정론(기존 creature 배치와 동일 방식).
- 플레이어 party 는 M1 **고정 스타터**(party 빌딩=catch→팀 구성은 후속 task).

## 작업 범위
### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | criticality | 비고 |
|---|---|---|---|
| `src/critter_gym/envs/critter_env.py` | 갱신 | critical | 모드 머신(OVERWORLD/BATTLE), obs 확장, step 분기, 리워드, 종료 |
| `src/critter_gym/party.py` | 신규 | critical | 시드 결정론 스타터 party + gym 보스 factory |
| `tests/test_env.py` | 갱신 | low | 종료 의미 변경(catch→비종료 subgoal) 반영 |
| `tests/test_gym_battle.py` | 신규 | low | 모드 전환·env 내 배틀·subgoal 리워드·승패·결정론·scripted 격파 |

### 영향 범위 (import 그래프)
- `critter_env.py` → 신규로 `battle.py`·`party.py`·`creatures.py`·`types.py` import.
- `observation_space` 확장(battle 필드 추가) → `tests/test_compliance.py`(check_env), `env-validation`
  determinism/baseline 테스트가 새 obs 로 재검증됨 — **계속 통과 필수**.
- **종료 의미 변경**: 기존 `scaffolding` AC6(caught≥C → terminated)을 "전 gym 격파 → terminated, catch 는
  비종료 subgoal" 로 evolve. `tests/test_env.py` 의 해당 테스트를 업데이트(의도된 진화, 본 plan 에 명시).

## Step별 계획
1. **party.py** — `starter_party(rng) -> list[Creature]`(3 타입 1마리씩, 결정론), `gym_boss(index, rng)
   -> list[Creature]`(시드 결정론 단일 보스). `battle.py`/`types.py` 재사용.
2. **월드에 gym 배치** — `reset(seed)` 가 N(예 2)개 gym 타일을 시드 결정론 배치(creature 와 겹치지 않게).
   `_gyms_defeated: int`, `_mode: OVERWORLD|BATTLE`, `_battle: Battle|None` 상태 추가.
3. **obs 확장** — 기존(agent_pos/local_patch/caught)에 추가: `in_battle`(0/1), `player_hp`, `player_type`,
   `enemy_hp`, `enemy_type`, `gyms_defeated`. BATTLE 아닐 때 battle 필드는 0. observation_space 갱신.
4. **step 분기** —
   - OVERWORLD: 0-3 MOVE / 4 CATCH / 5 NOOP(기존). 미격파 gym 타일 진입 시 → BATTLE 진입(party full heal,
     `Battle(player, gym_boss)` 생성), `in_battle=1`.
   - BATTLE: 0-3 = 배틀 무브 j(가용 무브로 클램프) / 4 = 다음 생존으로 SWITCH / 5 = NOOP. 매 env step = 배틀 1턴.
     변환: env 의 단방향 에이전트 action → `BattleAction`(플레이어=A측), 상대(B측)= `scripted_opponent(state,
     Side.B)`; 둘을 `Battle.step(action_a, action_b)` 로 1턴 해소. 승 → gym 격파 표시, `gyms_defeated+=1`,
     **reward=+1**, OVERWORLD 복귀.
     패(플레이어 전멸) → OVERWORLD 복귀, party 복원, gym 미격파(재도전 가능), reward 0.
5. **리워드(RLVR)** — gym 격파 +1, catch +1(기존). 그 외(이동/배틀 무브/턴) 0. dense shaping 없음.
6. **종료** — 전 gym 격파 → `terminated`. step budget → `truncated`. catch 는 비종료 subgoal.
   `info["subgoals"] = {"caught": n, "gyms_defeated": m}`.
7. **tests** — 아래 검증.

## 검증 방법
- pytest: 모드 전환, env 내 배틀 1턴/스텝, subgoal 리워드(+1 on 격파, 0 그 외), 승→격파/패→복귀, 결정론,
  scripted nav+battle 가 ≥1 gym 격파.
- `check_env`(확장 obs) 계속 통과. `env-validation`·`scaffolding` 기존 테스트 회귀 0(종료-의미 테스트는 갱신).
- `run-tdd.py`(mypy/ruff/pytest/build).

## 리스크
- **obs space 변경 → 회귀**: env-validation 의 baseline/determinism, scaffolding 의 obs 테스트가 깨질 수
  있음 → 새 obs 로 통과하도록 함께 업데이트. check_env 가 1차 가드.
- **종료 의미 변경**: scaffolding AC6 evolve. 명시적·의도적 — test 업데이트로 흡수, plan 에 기록.
- **action_space 재해석 모호성**: 같은 Discrete(6)이 모드별 다른 의미 → obs 의 `in_battle` 로 에이전트가
  구분. action_space 자체는 불변(check_env·기존 호환).
- **스코프 팽창**: party 빌딩(catch→팀)·아이템 env 노출·다중 보스 party·최종보스는 **본 task 밖**(후속/EC5).
  본 task = "배틀이 월드에서 gated checkpoint 로 돈다 + subgoal 리워드" 최소.
- **무한 배틀**: 엔진 `max_turns` truncate → BATTLE 도 무한루프 없음(패 처리).

## Acceptance Criteria (G1 통과 시 freeze)
- [ ] **AC1 (gym 배치)**: `reset(seed)` 가 N≥1 gym 타일을 시드 결정론 배치(creature 와 비겹침); 상태/obs 에
  `gyms_defeated` 노출. 동일 시드 → 동일 배치. (test)
- [ ] **AC2 (모드 전환)**: 미격파 gym 타일 진입 → `in_battle=1` ∧ obs 가 양측 active(hp·type) 반영; 배틀
  종료 → `in_battle=0`. (test)
- [ ] **AC3 (에이전트 제어 배틀)**: BATTLE 에서 action 0-3=무브 j, 4=스위치; 상대 scripted; 매 env step=1턴;
  `battle.py` 엔진으로 해소. (test)
- [ ] **AC4 (RLVR subgoal 리워드)**: gym 보스 격파 → reward=+1 ∧ `info["subgoals"]["gyms_defeated"]` 증가;
  이동·배틀 무브·턴·패배 = reward 0(dense shaping 없음). (test)
- [ ] **AC5 (종료)**: 전 gym 격파 → `terminated=True`; step budget 초과 → `truncated=True`; catch 는 비종료
  subgoal(scaffolding 종료-의미 테스트 갱신). (test)
- [ ] **AC6 (결정론)**: 동일 시드 + 동일 행동 시퀀스 → 동일 trajectory(배틀 포함). (test)
- [ ] **AC7 (Gymnasium 준수)**: 확장 `observation_space` 로 `check_env(skip_render_check=True)` 통과;
  obs ∈ space(양 모드). (test)
- [ ] **AC8 (≥1 boss 격파, M1-EC5 부분)**: test-local scripted 정책(overworld 내비 + 배틀)이 한 에피소드에서
  ≥1 gym 격파. (test)
- [ ] **AC9 (툴체인 green)**: `ruff check .` ∧ `mypy src` ∧ `pytest -q` ∧ `python -m build` 통과;
  env-validation·scaffolding 회귀 0.
