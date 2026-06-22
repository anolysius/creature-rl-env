---
slug: creature-evolution
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
milestone: M1
exit_criteria: [M1-EC2]
scope_paths:
  - src/critter_gym/creatures.py
  - src/critter_gym/party.py
  - src/critter_gym/envs/**
  - tests/**
extracted_to: []
supersedes: []
---

# creature-evolution — 진화를 long-horizon 투자 결정으로 (M1-EC2)

> 작성일: 2026-06-21 | 상태: 계획 | **마일스톤 M1 · M1-EC2 (M1의 마지막 미충족 EC)**

## 목표
DESIGN §3.4 의 **진화 = 의도적 장기 투자 결정**을 구현해 **M1 을 닫는다**. 한 creature 를 반복해서
배틀에 투입(투자)해 레벨을 올리면 임계에서 진화해 강해진다 — "어느 creature 에 투자할지"가 long-horizon
선택. 진화는 boolean-verifiable subgoal 리워드(RLVR).

**M1-EC2 충족 정의**: "진화가 long-horizon 투자 결정으로 동작 (level/item gated)."

## 선행 조건
- M1-EC1/EC3/EC4 완료 (`battle.py` 엔진 + `CritterEnv` 배틀 통합 + subgoal 리워드).
- 결정론 유지(레벨·진화에 RNG 없음). M1 고정월드.
- **진화 트리 깊이 1**(base → evolved 1단계), 단순 level 임계. 깊은 트리·아이템 진화·EVOLVE 명시 액션은 후속.

## 설계 결정 (plan 에서 고정)
- **레벨 획득**: 배틀 승리 시 *그 시점 active 플레이어 creature* 의 `level += 1`. (catch 기반 XP·복잡한 경제는 후속.)
- **진화**: `level >= evolve_level`(기본 2 = 첫 승리 후) 도달 시 **자동 진화**(action space 불변 — Discrete(6)).
  진화 = evolved form 의 강화 stats 로 교체(이름·max_hp·atk·def·speed↑), hp 비례 스케일.
- **payoff 를 non-vestigial 로 (L1 @plan-reviewer SUGGEST 흡수)**: 진화 보상이 *마지막 배틀에만* 발생하는
  헛수고가 되지 않도록 — **`num_gyms` 기본 3**(DESIGN "N escalating gyms" 정합)으로 horizon 확보 + 보스
  타입을 **`[GRASS, GRASS, WATER]`** 로 배치해 한 creature(FIRE)가 2 gym 을 커버 가능 → FIRE 가 gym0 승리로
  *첫 진화* 후 evolved 상태로 gym1 을 처리(=진화가 *이후* 배틀에서 실제 payoff). 깊은 "집중 투자 vs 타입
  스위칭" trade-off 는 M2 의 escalating gym 수가 늘며 자연 심화 — M1 은 메커니즘 + 비-헛수고 payoff 까지.
- **리워드(RLVR)**: 진화 발생 시 +1 ∧ `info["subgoals"]["evolved"]++`. 레벨업 자체·부분 진행 = 0.

## 작업 범위
### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | criticality | 비고 |
|---|---|---|---|
| `src/critter_gym/creatures.py` | 갱신 | critical | `level`, evolved-form 스펙, `gain_level`/`can_evolve`/`evolve()` |
| `src/critter_gym/party.py` | 갱신 | critical | 스타터 creature 에 진화 스펙(evolved stats) 부여 |
| `src/critter_gym/envs/critter_env.py` | 갱신 | critical | 승리 시 레벨업·자동 진화·리워드·obs(`evolved`,`player_level`)·info |
| `tests/test_creatures.py` | 갱신 | low | 레벨·진화 메커니즘 단위 |
| `tests/test_gym_battle.py` | 갱신 | low | 승리→레벨업→진화→subgoal 리워드·결정론·통합 |

### 영향 범위 (import 그래프)
- `creatures.py` 자기완결(types 만 의존). `party.py`→creatures. `critter_env.py`→party/creatures/battle.
- obs 에 `evolved`(+배틀 시 `player_level`) 추가 → `check_env`·기존 obs 테스트 재검증(회귀 0 목표).
- 기존 battle/gym 동작 불변 — 승리 처리에 레벨업·진화 후처리만 추가.

## Step별 계획
1. **creatures.py** — `Creature` 에 `level: int = 1`. evolved form 스펙(예: `evolved: EvolvedForm | None`,
   `evolve_level: int`). `gain_level()`(level+1), `can_evolve`(level≥evolve_level ∧ evolved 존재 ∧ 미진화),
   `evolve()`(stats→evolved, max_hp 상향+hp 비례, name 변경, can_evolve→False). 결정론.
2. **party.py** — 스타터 3종에 evolved form 부여(예: max_hp·atk 상향, evolve_level=2). 보스는 진화 없음.
3. **critter_env.py** — `_step_battle` 승리 분기에서 active creature `gain_level()`; `can_evolve` 면 `evolve()`,
   `_evolved += 1`, `reward += 1`. obs 에 `evolved`(0..party), 배틀 시 `player_level` 추가. info subgoals 에 `evolved`.
4. **종료 불변**: 종료는 여전히 전 gym 격파(진화는 종료 조건 아님 — subgoal 일 뿐).
5. **tests** — 아래.

## 검증 방법
- pytest: 레벨/진화 단위(creatures), env 승리→레벨업→임계 진화→reward+1·info, evolved 가 base 보다 강함,
  결정론, check_env(확장 obs), 통합(scripted 가 한 creature 집중 투입 시 진화 발생).
- `run-tdd.py`(mypy/ruff/pytest/build). 기존 45 테스트 회귀 0(obs 변경 흡수).

## 리스크
- **obs 확장 회귀**: `evolved`/`player_level` 추가 → check_env·기존 obs 테스트 갱신 필요. 1차 가드 check_env.
- **레벨 경제 단순화 비판**: 배틀 승리=+1레벨은 단순하나 M1 의도(메커니즘+투자 narrative). 정교한 XP 곡선은 후속.
- **진화 stats 밸런싱**: 너무 강하면 배틀 trivial → evolved 는 적당히(예 +60% hp/atk). 테스트는 *상대적*
  강함(evolved > base)만 단언해 밸런싱 수치에 brittle 하지 않게.
- **스코프 팽창**: EVOLVE 명시 액션·진화 취소·깊은 트리·아이템 진화는 의도적 후속(M1 깊이 1).

## Acceptance Criteria (G1 통과 시 freeze)
- [ ] **AC1 (진화 데이터 모델)**: `Creature` 가 `level` + evolved-form 스펙 보유; `gain_level`/`can_evolve`/
  `evolve()` 결정론; `evolve()` 가 stats 상향 + 이름 변경 + 재진화 불가. (test, creatures)
- [ ] **AC2 (배틀 승리 레벨업)**: 배틀 승리 시 그 시점 active 플레이어 creature 의 `level` 이 +1. (test, env)
- [ ] **AC3 (임계 게이트 진화)**: `level ≥ evolve_level` 도달 시 자동 진화(강화 stats); 미만이면 진화 안 함. (test)
- [ ] **AC4 (RLVR 진화 subgoal)**: 진화 발생 시 reward +1 ∧ `info["subgoals"]["evolved"]` 증가; 레벨업
  자체·부분 진행 = 0 (dense shaping 없음). (test)
- [ ] **AC5 (evolved 가 더 강함)**: evolved form 이 base 대비 더 큰 stats(예 max_hp·attack) — 투자 payoff. (test)
- [ ] **AC6 (obs 노출 + 준수)**: obs 가 `evolved`(+배틀 시 `player_level`) 노출; `check_env(skip_render_check)`
  통과; obs ∈ space 양 모드. (test)
- [ ] **AC7 (결정론)**: 동일 시드 + 동일 행동 시퀀스 → 동일 trajectory(레벨·진화 포함). (test)
- [ ] **AC8 (통합/투자, 비-vestigial payoff)**: scripted 정책이 한 creature 를 배틀에 집중 투입 → 진화 발생
  (evolved≥1) ∧ **진화한 creature 가 이후(같은 에피소드 내) 배틀에서 사용됨**(payoff 가 마지막 배틀에만
  국한되지 않음을 pin); 기존 gym/catch subgoal 정상. (test, num_gyms=3 구성)
- [ ] **AC9 (툴체인 green)**: `ruff` ∧ `mypy src` ∧ `pytest` ∧ `build`; 기존 45 테스트 회귀 0.
