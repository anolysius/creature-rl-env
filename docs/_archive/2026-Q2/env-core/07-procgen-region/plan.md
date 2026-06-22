---
slug: procgen-region
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
milestone: M2
exit_criteria: [M2-EC1]
scope_paths:
  - src/critter_gym/region.py
  - src/critter_gym/party.py
  - src/critter_gym/envs/**
  - src/critter_gym/registration.py
  - tests/**
extracted_to: []
supersedes: []
---

# procgen-region — 시드→절차 생성 region + train/test 분리 (M2-EC1)

> 작성일: 2026-06-21 | 상태: 계획 | **마일스톤 M2 (moat) · M2-EC1**

## 목표
**우리 moat 의 첫 벽돌.** 지금까지 M1 은 고정월드라 포켓몬 레드처럼 암기가 가능했다. 시드가 **region 의
내용**(creature 수·위치, gym 수·위치·보스 타입)을 절차 생성하도록 명시적 생성기로 구조화하고, **train
seed vs held-out test seed 를 분리**해 "처음 보는 세계에서 일반화하는가"를 측정 가능하게 만든다.

**M2-EC1 충족 정의**: "시드 → 절차 생성 region (맵·biome·spawn·gym 시퀀스); train/test 시드 분리."

## 설계 결정 (plan 에서 고정)
- **obs 형태 불변 (Gymnasium 계약 + Procgen 관례)**: `grid_size` 등 *obs-space 차원에 영향을 주는 값은 고정*,
  시드는 **내용**(개수·위치·타입)만 변주. obs 경계는 **max 값**(max_creatures/max_gyms)으로 잡아 모든 시드에서
  obs ∈ space.
- **`vary` 플래그(기본 False) — 무회귀**: `CritterEnv(vary=False)`(기본)는 현재 고정 동작 그대로(M1 테스트
  불변). `vary=True` 면 region 생성기가 개수/타입을 시드별 [min,max] 범위에서 변주.
- **생성기 순수성**: `generate_region(seed, ...)` 는 `np.random.default_rng(seed)` 로 자기완결(동일 시드 →
  동일 region). env 는 이를 호출만.
- **타입표는 본 task 밖**: region 은 보스 *타입을 고름*(고정 타입표 기준). 절차 *타입표*(infer-the-meta)는
  M2-EC2 `procgen-typechart`.
- **vary 범위 + 종료 계약 (L1 BLOCK-1 흡수)**: vary=True 시 gym 수 ∈ **[1, max_gyms]** (`min_gyms≥1` 강제) →
  종료 계약(`step` 의 `all(_gym_defeated)` ∧ `num_gyms>0` 가드)이 항상 유효(0-gym 에피소드·즉시종료·무한 없음).
  creature 수 ∈ [1, max_creatures]. 위치는 grid 에 disjoint·in-bounds.
- **split overrun 가드 (L1 BLOCK-2 흡수)**: `TEST_SEED_OFFSET`(예 1_000_000) 큰 상수. `train_seeds(n, start=0)`
  는 `start + n ≤ TEST_SEED_OFFSET` 를 **강제(초과 시 ValueError)** → train 범위가 test 범위를 침범(누수)하는
  것을 구조적으로 차단. `test_seeds(n)` = `range(TEST_SEED_OFFSET, TEST_SEED_OFFSET+n)`.

## 작업 범위
### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | criticality | 비고 |
|---|---|---|---|
| `src/critter_gym/region.py` | 신규 | critical | `Region` 데이터클래스 + `generate_region(seed,...)` + train/test split 헬퍼 |
| `src/critter_gym/party.py` | 갱신 | critical | `gym_boss` 가 보스 *타입*을 받도록(고정 시퀀스는 타입으로 derive) |
| `src/critter_gym/envs/critter_env.py` | 갱신 | critical | reset 이 `generate_region` 위임, `vary` 플래그, gym 보스 타입 보관 |
| `src/critter_gym/registration.py` | 갱신 | critical | `CritterGym-procgen-v0`(vary=True) 등록 |
| `tests/test_region.py` | 신규 | low | 생성기 결정론·변주·split 분리 |
| `tests/test_gym_battle.py`·`tests/test_env.py` | 갱신 | low | procgen 모드 통합·무회귀 |

### 영향 범위 (import 그래프)
- `region.py` → numpy + types. `critter_env.py` → region. `party.gym_boss(type)` 시그니처 변경 →
  `critter_env._maybe_enter_battle` 호출부 갱신(보관한 region 의 보스 타입 전달).
- obs 경계가 max 기준 → check_env·기존 obs 테스트 재검증(vary=False 기본이라 회귀 0 목표).

## Step별 계획
1. **region.py** — `Region(grid_size, creatures: list[pos], gyms: list[(pos, ElementType)], agent_start)`.
   `generate_region(seed, grid_size, max_creatures, max_gyms, *, vary) -> Region`:
   - `rng = np.random.default_rng(seed)`. vary=False → 개수=max, 보스 타입=고정 시퀀스; vary=True → 개수 ∈
     [min,max], 보스 타입 = rng 추출(고정 타입표의 타입 중). 위치는 disjoint·in-bounds 배치.
   - **train/test split**: `train_seeds(n, start=0)` = `range(start, start+n)`; `test_seeds(n)` =
     `range(TEST_SEED_OFFSET, TEST_SEED_OFFSET+n)`(disjoint 보장 큰 offset). `is_held_out(seed)` 헬퍼.
2. **party.py** — `gym_boss(boss_type: ElementType, index: int = 0)` 로 변경(타입 기반). 고정 `_BOSS_TYPES`
   는 유지하되 region 생성기가 vary=False 시 그 시퀀스를 사용.
3. **critter_env.py** — `__init__(vary=False, max_creatures=…, max_gyms=…)`; obs 경계 max 기준. `reset(seed)`
   → `generate_region(seed, …, vary=self.vary)` 로 creature/gym/start 배치, gym별 보스 타입 보관.
   `_maybe_enter_battle` 가 보관 타입으로 `gym_boss(type, idx)` 생성. 나머지(배틀/진화/리워드/종료) 불변.
4. **registration.py** — `CritterGym-procgen-v0` (vary=True) 등록. `CritterGym-v0` 는 그대로(vary=False).
5. **tests** — 아래.

## 검증 방법
- pytest: 생성기 결정론(동일 시드 동일 region)·변주(다른 시드 다른 region)·split disjoint·무누수, env
  procgen 통합(procgen region 에서 scripted 가 gym 격파), 무회귀(기존 54), check_env(양 변형).
- `run-tdd.py`(mypy/ruff/pytest/build).

## 리스크
- **party.gym_boss 시그니처 변경 → 호출부**: critter_env 한 곳. 함께 갱신. (저위험)
- **obs 경계 max 전환**: vary=False 에서도 caught/gyms_defeated high 가 max 로 — 기존 값은 max 이내라 안전.
  check_env 1차 가드.
- **train/test 누수**: split 이 실제 disjoint 인지 테스트로 pin(같은 seed 가 양쪽에 안 들어감 + region 동일성
  비교). offset 방식이라 구조적으로 disjoint.
- **스코프 팽창**: 절차 *타입표*·biome 시각효과·난이도 곡선 튜닝은 M2-EC2/후속. 본 task=region 내용 생성 + split.

## Acceptance Criteria (G1 통과 시 freeze)
- [ ] **AC1 (생성기 결정론)**: `generate_region(seed,...)` 가 동일 시드 → 동일 `Region`(creatures·gyms·
  start 동일); 위치는 grid 내 + 서로 disjoint. (test)
- [ ] **AC2 (시드별 변주)**: `vary=True` 에서 다른 시드들이 서로 다른 region 생성(개수·gym 타입·위치 중 변주
  존재 — 표본 비교). (test)
- [ ] **AC3 (env 위임 + 무회귀 + 종료 계약)**: `reset(seed)` 가 `generate_region` 으로 에피소드 구성;
  `vary=False`(기본)는 기존 동작 보존(기존 54 테스트 green); **vary=True 에피소드는 항상 gym 수 ≥1**
  (min_gyms≥1) → 종료 계약 유효(즉시종료/무한 없음). (test + 회귀)
- [ ] **AC4 (train/test split + overrun 가드)**: `train_seeds`/`test_seeds` 가 **disjoint** 시드 집합 생성;
  train 시드 region ≠ test 시드 region(누수 0); `train_seeds(start+n > TEST_SEED_OFFSET)` 는 **ValueError**
  (침범 가드); 규약 문서화. (test)
- [ ] **AC5 (procgen 변형 등록)**: `gymnasium.make("CritterGym-procgen-v0")` 가 vary=True env 반환;
  `check_env(skip_render_check)` 통과; obs ∈ space 가 **train 시드 ∧ held-out(test) 시드 표본 모두**에서
  성립(경계=max). (test)
- [ ] **AC6 (결정론 보존)**: 동일 시드 + 동일 행동 시퀀스 → 동일 trajectory (fixed·procgen 양 모드). (test)
- [ ] **AC7 (M1 동작 보존)**: procgen region 에서도 배틀·gym 격파·진화가 동작(scripted 가 procgen 시드에서
  ≥1 gym 격파). (test)
- [ ] **AC8 (툴체인 green)**: `ruff` ∧ `mypy src` ∧ `pytest` ∧ `build`; 기존 54 테스트 회귀 0; check_env 통과.
