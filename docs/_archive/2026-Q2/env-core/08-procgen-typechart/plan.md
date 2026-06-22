---
slug: procgen-typechart
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
milestone: M2
exit_criteria: [M2-EC2]
scope_paths:
  - src/critter_gym/types.py
  - src/critter_gym/region.py
  - src/critter_gym/envs/**
  - tests/**
extracted_to: []
supersedes: []
---

# procgen-typechart — 시드별 내부정합 타입표 (M2-EC2, infer-the-meta)

> 작성일: 2026-06-21 | 상태: 계획 | **마일스톤 M2 (moat) · M2-EC2 — moat 의 핵심 novelty**

## 목표
DESIGN §3.1 의 가장 독창적인 novelty: **시드마다 다른, 내부적으로 정합한 타입 상성표**. 지금은 맵·배치만
절차 생성되고 타입표는 고정(FIRE>GRASS>WATER)이라 에이전트가 그 한 표를 외울 수 있다. 시드별 차트를
생성하면 — 에이전트가 **고정표를 가정할 수 없고 경험에서 메타를 추론(infer-the-meta)** 해야 한다.
이것이 "진짜 암기 불가"의 핵심.

**M2-EC2 충족 정의**: "시드 → 절차 생성 내부정합 타입표 (infer-the-meta; 고정표 암기 방지)."

## 설계 결정 (plan 에서 고정)
- **TypeChart 데이터 주도화**: 현재 모듈-레벨 하드코딩 `_BEATS`(3-cycle)를 **인스턴스 데이터**(beats map)로.
  `TypeChart()`(무인자) = 기존 M1 고정 차트(FIXED_CHART, FIRE>GRASS>WATER) — **API·동작 무회귀**.
  `effectiveness`/`multi_effectiveness` 시그니처 유지. TypeChart 는 비교 가능(== — region 결정론 테스트용).
- **생성기**: `generate_typechart(seed, types, *, vary) -> TypeChart`. vary=False → FIXED_CHART. vary=True →
  각 타입쌍(i<j)을 `default_rng(seed)` 로 방향 결정(i super vs j XOR j super vs i). **내부정합 보장**:
  antisymmetric(A super vs B ⟹ B not-very vs A), self=neutral, 모순 0(구성상). 결정론(동일 시드 동일 차트).
- **차트는 obs 에 노출 안 함 (infer-the-meta 핵심)**: obs 는 타입 *id*(player_type/enemy_type)만 — 효과
  *관계*는 미노출. 에이전트는 배틀 데미지 결과로 추론. (obs 키 procgen-region 대비 불변.)
- **scripted 차트 전달 (기존 버그 수정)**: 현재 `_step_battle` 는 `scripted_opponent(state, Side.B)` 를
  *차트 없이* 호출 → 항상 고정 차트 사용. 시드별 차트를 Battle·scripted_opponent 양쪽에 전달하도록 수정.
- **K=3 유지**: 타입 수 확장(더 풍부한 메타)·procgen creature 타입은 의도적 후속. 본 task=차트 절차생성 메커니즘.

## 작업 범위
### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | criticality | 비고 |
|---|---|---|---|
| `src/critter_gym/types.py` | 갱신 | critical | `TypeChart` 데이터 주도(beats)+비교가능, `FIXED_CHART`, `generate_typechart(seed,types,vary)` |
| `src/critter_gym/region.py` | 갱신 | critical | `Region` 에 `chart: TypeChart` 필드; `generate_region` 이 시드로 차트 생성 |
| `src/critter_gym/envs/critter_env.py` | 갱신 | critical | region 차트를 `Battle(...,chart=)` + `scripted_opponent(...,chart=)` 에 전달 |
| `tests/test_types.py` | 갱신 | low | 데이터주도·생성기 정합·변주 |
| `tests/test_region.py`·`tests/test_gym_battle.py` | 갱신 | low | region 차트·env 통합·무회귀 |

### 영향 범위 (import 그래프)
- `region.py` → `types.generate_typechart`. `critter_env.py` → region.chart 사용. `battle.py` 불변(Battle·
  scripted_opponent 이미 chart 파라미터 보유 — 호출부만 수정).
- obs 불변(차트 미노출). check_env 재검증(무회귀 목표).

## Step별 계획
1. **types.py** — `TypeChart` 를 `frozen dataclass`(beats: frozenset[(attacker,defender)] super 관계)로.
   `effectiveness(a,b)`: (a,b)∈beats→SUPER / (b,a)∈beats→NOT_VERY / else NEUTRAL. `TypeChart()` 기본=FIXED.
   `FIXED_CHART` = M1 3-cycle. `generate_typechart(seed, types=list(ElementType), *, vary=False)`: vary 시
   각 쌍 방향을 rng 로 결정해 beats 구성.
2. **region.py** — `Region.chart: TypeChart`. `generate_region(...)` 가 `generate_typechart(seed, vary=vary)`
   로 차트 포함. (region 결정론 테스트는 chart 비교 포함 — TypeChart eq 로 성립.)
3. **critter_env.py** — `_maybe_enter_battle` 가 `Battle(state, chart=self._region_chart)`; `_step_battle` 가
   `scripted_opponent(battle.state, Side.B, chart=self._region_chart)`. reset 이 region.chart 보관.
4. **tests** — 아래.

## 검증 방법
- pytest: TypeChart 데이터주도(기본=fixed)·생성기 정합(antisymmetric/self-neutral/결정론)·시드별 변주,
  env 통합(시드별 차트가 실제 데미지에 반영; scripted 가 차트 인지), region 차트 train/test 분리, 무회귀(64),
  check_env(fixed+procgen).
- `run-tdd.py`(mypy/ruff/pytest/build).

## 리스크
- **TypeChart 리팩터 회귀**: 기존 test_types·battle 가 `TypeChart()`·effectiveness 사용 → 기본=FIXED 로
  동작 보존. 1차 가드 기존 64 테스트.
- **scripted 차트 버그 수정의 파급**: 기존 gym/battle 테스트가 *고정 차트 가정* 으로 통과 중 → 수정 후에도
  fixed 모드(vary=False)에선 동일 차트라 무회귀. procgen 모드만 시드별 차트.
- **K=3 변주 제한(2^3=8 차트)**: 3 타입이라 차트 경우의 수 제한적 — infer-the-meta *메커니즘* 은 충족하나
  메타 깊이는 K 확장(후속)에서. plan 에 명시.
- **차트 obs 누수**: 효과 관계가 obs 에 새면 추론 불필요 → AC 로 obs 키 불변 + 관계 미노출 pin.

## Acceptance Criteria (G1 통과 시 freeze)
- [ ] **AC1 (TypeChart 데이터 주도 + 무회귀)**: `TypeChart` 가 beats 데이터로 구성; `TypeChart()`(무인자)=
  M1 FIXED_CHART(FIRE>GRASS>WATER); `effectiveness`/`multi_effectiveness` 동작·시그니처 유지; TypeChart 비교 가능. (test)
- [ ] **AC2 (생성기 내부정합 + 결정론)**: `generate_typechart(seed, vary=True)` 가 내부정합 차트 — antisymmetric
  (a super vs b ⟹ b not-very vs a), self=neutral, 모순 0; 동일 시드 → 동일 차트. (test)
- [ ] **AC3 (시드별 변주)**: 다른 시드들이 서로 다른 차트 생성(표본 비교 — 전부 동일 아님); **표본 중 ≥1 시드의
  차트가 FIXED_CHART 와 다름**을 단언(K=3·8차트라 vacuous-pass 방지 — L1 SUGGEST 흡수). (test)
- [ ] **AC4 (obs 미노출 — infer-the-meta)**: obs 가 효과 *관계* 를 노출하지 않음(타입 id 만); obs 키가
  procgen-region 대비 불변. 에이전트는 차트를 obs 로 알 수 없음. (test)
- [ ] **AC5 (env 통합 + scripted 차트 수정)**: vary 모드에서 에피소드의 `Battle` ∧ `scripted_opponent` 가
  **그 시드의 차트** 사용(데미지가 시드별 효과 반영 — 동일 공격/방어 타입쌍이 차트에 따라 super/not-very
  로 갈림); fixed 모드는 FIXED_CHART. **검증은 FIXED_CHART 와 다름이 보장된 특정 시드로** 수행(동일
  공격/방어 타입쌍이 fixed 와 반대 효과가 되는 시드를 골라 데미지 차이 단언 — vacuous-pass 방지). (test)
- [ ] **AC6 (region 차트 + train/test)**: `Region`(vary) 가 시드별 `chart` 보관; train 시드 차트 vs held-out
  시드 차트가 표본에서 다름(누수 0). (test)
- [ ] **AC7 (결정론 + M1 보존)**: 동일 시드 + 행동 → 동일 trajectory(procgen); vary=False = M1(기존 64 green);
  check_env(fixed+procgen) 통과. (test)
- [ ] **AC8 (툴체인 green)**: `ruff` ∧ `mypy src` ∧ `pytest` ∧ `build`; 기존 64 회귀 0; check_env 통과.
