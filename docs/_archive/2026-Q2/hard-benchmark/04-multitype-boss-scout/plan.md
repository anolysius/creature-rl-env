---
slug: multitype-boss-scout
initiative: hard-benchmark
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env, perf]
scope_paths:
  - src/critter_gym/region.py
  - src/critter_gym/party.py
  - src/critter_gym/envs/critter_env.py
  - src/critter_gym/learnability.py
  - src/critter_gym/jax_env.py
  - src/critter_gym/jax_train.py
  - tests/test_multitype_boss.py
  - tests/test_jax_multitype_boss_parity.py
  - scripts/multitype_boss_scout.py
extracted_to: []
supersedes: []
mode: heavy
task_type: env
---

# 다중-타입 보스 — env 변경 + JAX parity + scout (hard-benchmark #4)

> 작성일: 2026-07-01 | 상태: 계획 | 추진: hard-benchmark "더 깊은 절대 난이도"(#3 후속). **de-risked 슬라이스**(사용자 선택): env 변경 + parity 0 + 1-seed scout. 무거운 다중-seed 헤드룸 측정은 후속 task.

## 목표

hard-benchmark #1–#3 이 "메모리 load-bearing"·"메모리 agent 에게도 절대 hard(grid16 공간/호라이즌)"를
settled 했다. #3 scout 는 grid>16(공간 확장)이 학습불가로 inconclusive 임을 확인 → 공간 레버는 소진.
남은 "더 깊은" 레버는 **추론 깊이**: **다중-타입 보스**(gym 보스가 타입 2개). 방어 타입이 2개면
effectiveness 가 두 타입의 **곱**이라 유리 무브 판정이 더 깊은 추론을 요구한다. 두 번째 타입은
**obs 에서 숨긴다**(primary 만 노출) → 에이전트는 배틀 결과로 secondary 를 *추론*해야 함(CritterGym
hidden-rule inference moat 와 정합).

**본 task 범위(de-risked)**: (1) 다중-타입 보스 env 변경(**opt-in**, default off → byte-identical),
(2) **JAX parity 0 게이트**(numpy 다중-타입 보스 env ↔ `jax_env` 다중-타입 보스 env 궤적 일치),
(3) **1-seed scout**(학습가능 + 단일-타입보다 더 어려움 신호). **다중-seed 사전약정 헤드룸 측정은
명시적으로 후속 task**(#3 방법론과 동일 — pilot/scout 로 전제 검증 후 본측정).

**정직성(이니셔티브 계승)**: 1-seed scout = **신호이지 증명 아님**(proxy·budget·seed·CPU 라벨).
"다중-타입 보스가 더 어렵다"를 multi-seed robust 로 **입증하는 것은 후속**임을 scout 출력·문서에 명시.
헤드라인 금지.

## 선행 조건 + 범위 축소 논거

- **numpy 전투는 이미 다중-타입 지원**: `battle.py:damage`/`scripted_opponent` 가
  `chart.multi_effectiveness(move.type, defender.types)` 사용, `types.py:multi_effectiveness` 가
  방어 타입들의 곱. `creatures.py:Creature.types: tuple[ElementType, ...]` 복수. → **battle.py/
  types.py/creatures.py 변경 불필요**. 보스에 2 타입을 채우기만.
- **jax_env 는 자체 인라인 전투**(`jax_battle.py`/`jax_battle_full.py` 미호출; `jax_env.py:347-358,
  441-444` 가 `s.eff[a_mt, btype]` 직접 gather). → **훈련 경로는 `jax_env.py` 만** 다중-타입화.
  독립 포트 `jax_battle.py`/`jax_battle_full.py` 는 단일-타입 유지(그들의 parity 테스트는 numpy 단일-
  타입 보스가 불변이라 무영향). **범위 밖**.
- 사전약정 판정 재사용: `headroom.classify_headroom`(frac=0.75) 은 **후속 측정 task** 용 — 본 scout 는
  학습·난이도 *신호*만.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 종류 | 영향도 | 변경 요지 |
|---|---|---|---|
| `region.py` | 수정 | 중 | `generate_region(..., boss_secondary=False)` opt-in; `Region` 에 `boss_secondary_types` 필드(default all-None → byte-identical) |
| `party.py` | 수정 | 낮 | `gym_boss` 가 secondary 타입(옵션) 받아 `Creature` types=(t1,) 또는 (t1,t2) |
| `envs/critter_env.py` | 수정 | 중 | `_gym_secondary` 병렬 저장; 보스 생성 시 2 타입 전달; obs `enemy_type`=primary 만(shape 불변) |
| `learnability.py` | 수정 | 중 | oracle(`_favorable_type`/`_target_type`)이 enemy 전체 타입(primary+secondary)으로 `multi_effectiveness` 유리무브 선택(오라클은 env 내부서 두 타입 앎) |
| `jax_env.py` | 수정 | 중(perf·핵심) | `gym_type2`(MAX_GYMS,) sentinel 필드; 전투 eff=곱(마스크); obs `enemy_type`=primary 만; reset 이 region 의 secondary 전파 |
| `jax_train.py` | 수정 | 낮 | `multitype_hard_env_spec()`(또는 flag) — grid16 hard config + boss_secondary on |
| `tests/test_multitype_boss.py` | 신규 | 낮 | numpy: opt-in 2타입 보스 배치·effectiveness 곱·obs primary-only·backward-compat off·oracle 다중타입 |
| `tests/test_jax_multitype_boss_parity.py` | 신규 | 낮 | numpy↔jax_env 다중-타입 보스 parity 0(obs+reward+term+trunc) + train smoke |
| `scripts/multitype_boss_scout.py` | 신규 | 낮(런타임) | 1-seed scout: parity 0 확인 + recurrent PPO 학습 + 단일 vs 다중 타입 난이도 대조 신호 + 정직 라벨 |

### 영향 범위

- `generate_region`/`Region` 소비처 다수(env·jax·eval). **opt-in default off 로 byte-identical** — 전체
  스위트로 회귀 0 확인. `jax_env` obs shape 불변(secondary 숨김)이라 기존 parity 테스트 무영향.

## Step별 계획 (correctness/parity-first — 망가진 다중타입=misleading)

**Step 1 (Red→Green): numpy 다중-타입 보스 (opt-in, hidden secondary)**
- `region.py`: `Region` 에 `boss_secondary_types: tuple[ElementType | None, ...] = ()` 추가(빈=all
  single, byte-identical). `generate_region(..., boss_secondary: bool = False)`; True 면 gym 마다
  primary 와 **다른** secondary 타입 1개 draw(결정론 rng, primary≠secondary), gyms 는 `(coord,
  primary)` 그대로 + `boss_secondary_types` 병렬. False 면 현행과 완전 동일.
- `party.py`: `gym_boss(primary, index, *, secondary=None, ...)` → Creature types=(p,) 또는 (p,s).
- `critter_env.py`: `_gym_secondary` 저장, `_maybe_enter_battle` 가 secondary 전달. obs `enemy_type`
  = `ea.types[0]`(primary) 유지(shape (1,) 불변 — secondary 숨김).
- 테스트(test_multitype_boss): boss_secondary=True 시 보스 types 길이 2·primary≠secondary /
  effectiveness 가 곱(단일 대비 다른 damage) / obs enemy_type=primary only / **off 면 Region·env
  byte-identical**(같은 seed 동일 궤적).

**Step 2 (Red→Green): oracle 가 다중-타입 방어자 처리**
- `learnability.py`: `_favorable_type`/`_Arm._target_type` 이 enemy 의 전체 타입 튜플로
  `_region_chart.multi_effectiveness` 기반 유리무브 선택(오라클=chart-knowing expert, env 내부서
  두 타입 접근). single-type 경로는 동작 불변.
- 테스트: 2타입 보스에서 oracle 이 곱-effectiveness 최대 무브 선택 / single-type 회귀 없음.

**Step 3 (Red→Green): jax_env 다중-타입 + parity 0 게이트**
- `jax_env.py`: `JaxEnvState.gym_type2: (MAX_GYMS,) int32`(sentinel = 값 없음), reset 이 region
  `boss_secondary_types` 전파. 전투 damage 의 `s.eff[a_mt, btype]` → `eff[a_mt,t1] * (mask ?
  1.0 : eff[a_mt,t2])` 곱. obs `enemy_type`=primary(불변).
- 테스트(test_jax_multitype_boss_parity): `_run_parity` 골격 재사용 — numpy `CritterEnv`(multitype
  region) ↔ `make_jax_env`(같은 region) 동일 seed·action 궤적 **0 mismatch**(obs 전 key+reward+
  term+trunc; random + gym-clearing policy; train·held-out seed) + `train_recurrent_ppo` 짧은 smoke
  유한 곡선.

**Step 4 (scout): `scripts/multitype_boss_scout.py` + hard config**
- `jax_train.py`: `multitype_hard_env_spec()`(grid16 hard config + boss_secondary on) 추가(기존 spec
  byte-identical). scout(1 seed, 짧은 iter): (i) parity 0 재확인, (ii) recurrent PPO **학습**(유한
  향상 곡선), (iii) **단일-타입 vs 다중-타입** 같은 config 에서 oracle-frac 대조.
- **L1 SUGGEST 반영 — 수치 격차 + 임계 명시**: scout 출력이 단일/다중 oracle-frac 를 **둘 다 수치로**
  찍고 그 **격차(Δ, %p)를 명시**하되, "**1 seed 이라 robust 임계 없음**; 이 Δ 는 raw single-run
  신호이며 robust 판정에는 다중-seed(≥3)+사전약정 규칙 필요"라고 **함께 라벨**한다(사후 "X%p 이상
  이면 더 어렵다" 식 헤드라인 오남용 방지). 후속 측정 task 에서 임계·seed 를 사전약정.

## 검증 방법

- `.venv/bin/python -m pytest -q` 전체 green, 회귀 0(baseline 592; opt-in off byte-identical).
- 신규 parity 테스트 **0 mismatch**. numpy 다중타입 테스트 green.
- `ruff check` / `mypy`(수정 src). 
- `.venv/bin/python scripts/multitype_boss_scout.py --quick` 무오류 + parity 0 + 학습 곡선 + 난이도
  신호 + 정직 라벨. (full scout 는 시간↑ — --quick 로 CI-safe smoke.)

## 리스크

| 리스크 | 완화 |
|---|---|
| **JAX parity 깨짐**(다중타입 곱 eff numpy↔jax 불일치) | parity 0 게이트가 hard 선결(Step 3). 곱 공식·sentinel 마스크를 numpy `multi_effectiveness`와 정확히 대응. random+gym-clearing 궤적으로 검증. |
| **하위호환**(region/env 소비처 회귀) | opt-in default off → byte-identical. Region 신규 필드 default 빈 튜플. 전체 스위트 회귀 0. |
| **scout 과대해석**(1-seed→"더 어렵다" 입증) | scout·문서·report 에 "신호이지 증명 아님, multi-seed=후속" 명시. 헤드라인 금지(이니셔티브 정직 문화). |
| **런타임**(JAX 학습 CPU) | scout `--quick`(짧은 iter) 로 smoke; full 측정은 후속 task. 테스트 parity 는 짧은 궤적. |
| heavy 다파일 회귀 표면 | correctness/parity-first + 각 Step Red→Green + 전체 스위트. jax_battle.py/full 범위 밖(단일타입 불변). |

## Acceptance Criteria (G1 통과 시 freeze)

1. **numpy 다중-타입 보스**(opt-in): `generate_region(boss_secondary=True)` 가 gym 마다 primary≠
   secondary 2타입 보스 배치(결정론), `Region.boss_secondary_types` 병렬 필드. off 면 byte-identical.
   effectiveness 는 두 타입 곱(battle 재사용). obs `enemy_type`=primary only(secondary 숨김, shape 불변).
2. **oracle 다중-타입**: oracle arm 이 enemy 전체 타입으로 `multi_effectiveness` 유리무브 선택(chart-
   knowing expert 유지); single-type 회귀 없음.
3. **jax_env 다중-타입 + parity 0**: `jax_env` 가 다중-타입 보스 effectiveness(곱)를 반영, obs primary
   only. numpy↔jax_env parity **0 mismatch**(obs+reward+term+trunc; random+gym-clearing; train·
   held-out seed).
4. **회귀 0 + 하위호환**: 전체 스위트 592 → all pass(opt-in off byte-identical), ruff/mypy clean.
   독립 포트 jax_battle.py/full 불변(범위 밖).
5. **scout**: `scripts/multitype_boss_scout.py` (+`multitype_hard_env_spec`) 가 `--quick` 무오류 —
   parity 0 + recurrent PPO 학습(유한 곡선) + 단일/다중 oracle-frac 를 **둘 다 수치+격차 Δ(%p)로**
   출력하고 **"1-seed raw 신호·robust 임계 없음·multi-seed(≥3) 사전약정 측정=후속"** 라벨 동반
   (헤드라인 오남용 방지) + proxy·CPU 라벨.
6. 신규 테스트(test_multitype_boss/test_jax_multitype_boss_parity)가 AC1–3 커버. CHANGELOG 1줄.
   후속 task 시드(다중-seed 사전약정 헤드룸 측정)를 report 에 명시.
