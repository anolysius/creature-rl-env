---
slug: strict-battle
initiative: hard-benchmark
status: active
started: 2026-07-02
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/battle.py
  - src/critter_gym/envs/critter_env.py
  - src/critter_gym/jax_env.py
  - tests/test_strict_battle.py
  - tests/test_jax_strict_battle_parity.py
  - scripts/strict_battle_scout.py
  - docs/reference/strict-battle.md
extracted_to: []
supersedes: []
---

# strict-battle — 전투 경제 confound 상환 (opt-in: 비효과 공격 데미지 0)

> 작성일: 2026-07-02 | 상태: 계획 | 마일스톤: **M3-EC4** (arXiv writeup 신뢰성 —
> 논문 §5 한계 (i) "attrition 승리 confound" 상환 + 잠재 판매-티어 레버 scout)

## 목표

현 전투 규칙은 `damage = max(1, ...)` — **비효과(< NEUTRAL) 공격도 최소 1 데미지**가
항상 들어간다. 그래서 타입 상성을 추론하지 않고도 "버티기(attrition)" 만으로 gym 을
이길 수 있고, gym-clear 지표의 추론-변별력이 흐려진다 (논문 §5 한계 (i)).

본 task 는 **opt-in 변형 `strict_battle`** 을 추가한다:

- **규칙**: 유효타(effectiveness ≥ NEUTRAL=1.0)는 기존 `max(1, ...)` 그대로,
  **비효과타(effectiveness < NEUTRAL)는 데미지 0** (min-1 클램프 제거).
- **양방향 대칭**: 보스→플레이어 공격에도 동일 규칙 (엔진 레벨 규칙).
- **기본 off = byte-identical**: 기존 수치(oracle 2.81/4.69, PPO 11–16%, rec 43%,
  티어, 논문 수치) 전부 무변경 유지. `boss_secondary`(#4) 와 동일한 opt-in 선례.
- **scout**: strict on/off 에서 scripted 변별폭(oracle − type_blind gyms_cleared
  spread) 확대 여부를 무료(numpy·scripted) 실측. 확대되면 판매 티어 후보로 후속.

## 선행 조건 (이미 충족)

- **매치업 보장(#15, `region.generate_region`)**: vary 모드는 모든 보스 타입이
  "파티가 strictly super-effective 무브를 가진 타입"만으로 draw 됨(`exploitable`
  필터). fixed 모드는 3-cycle 로 자명. → strict 에서도 **unwinnable 세계 없음**.
- **다중타입 보스와의 합성**: 보장된 무브 s\* 는 eff(s\*, primary)=super_mult(≥2.0)
  이고 secondary 최악이 0.5 → 곱 ≥ 1.0 = NEUTRAL → strict 에서도 데미지 > 0 인
  무브가 항상 존재. (AC3 에서 seed-sweep 으로 실검증.)
- **parity 게이트 선례**: `tests/test_jax_multitype_boss_parity.py` 패턴 재사용.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향 |
|---|---|---|
| `src/critter_gym/battle.py` | `Battle(strict_battle=False)` + `damage()` 에 strict 규칙 (단일 choke point) | 기본 off → 무영향 |
| `src/critter_gym/envs/critter_env.py` | `strict_battle=False` kwarg → `Battle(...)` 전달 (2곳: `__init__`, `_maybe_enter_battle`) | 기본 off → 무영향 |
| `src/critter_gym/jax_env.py` | `JaxEnvConfig.strict_battle: bool = False` (NamedTuple 꼬리 추가) + 데미지 4지점 strict 분기 (commit `fight` 2 + `noncommit_battle_branch` 2) | 정적 python bool 분기 → off 시 jaxpr 동일 |
| `tests/test_strict_battle.py` (신규) | 규칙 단위 + default-off 동일성 + winnability sweep | +테스트 |
| `tests/test_jax_strict_battle_parity.py` (신규) | strict on numpy↔JAX parity 0 (commit + noncommit) | +테스트 |
| `scripts/strict_battle_scout.py` (신규) | scripted 변별폭 scout (정직 라벨) | 도구 |
| `docs/reference/strict-battle.md` (신규) | evergreen 레퍼런스 (multitype-boss.md 선례) | 문서 |

### 영향 범위 (import 그래프)

- `battle.Battle` 소비자: `envs/critter_env.py`(gym 전투), `envs/duel_env.py`(자체
  duel 경제 — `Battle` 미사용, **범위밖**), `learnability`(CritterEnv 경유).
- `jax_battle.py`/`jax_battle_full.py`: 훈련 경로 아님 — **범위밖** (#4 선례 그대로).
- `scripted_opponent`: gym 보스는 무브 1개(파티 크리처도 1무브)라 argmax 선택이
  strict 와 무관 — 변경하지 않고 주석으로 불변식 명시.
- `env_tier`/`eval_package`: 이번 task 범위밖 (scout 결과가 좋을 때 후속 task 에서
  티어 knob 로 편입 검토).

## Step별 계획

1. **Red**: `tests/test_strict_battle.py` 작성 — (a) 비효과타 데미지 0, (b) 유효타
   기존 그대로(max(1,...) 클램프 유지), (c) strict off 기본값 byte-identical
   (고정 seed episode trace 비교), (d) winnability sweep — vary·num_types=8·
   min_gyms=num_gyms·boss_secondary ∈ {off,on} × seed ≥ 200 에서 모든 보스에
   strict-damage>0 파티 무브 존재.
2. **Green(numpy)**: `battle.py` `damage()` strict 규칙 + `Battle.__init__` 플래그,
   `critter_env.py` kwarg 플럼빙.
3. **Green(JAX)**: `JaxEnvConfig.strict_battle` + 데미지 4지점 분기
   (`jnp.where(eff < 1.0, 0.0, _damage(...))`, 정적 bool 이면 off 경로는 기존 식
   그대로 — byte-identical 보장).
4. **Parity**: `tests/test_jax_strict_battle_parity.py` — strict on 구성
   (hard config + boss_secondary on/off, commit + noncommit) numpy↔JAX
   obs 전 key + reward + term + trunc **0 mismatch**.
5. **Scout**: `scripts/strict_battle_scout.py` — held-out seed 에서 oracle vs
   type_blind (+infer) gyms_cleared 를 strict off/on 으로 실측, spread 변화 출력.
   1-run·scripted·no-threshold 정직 라벨, 헤드라인 금지 문구 포함.
6. **문서**: `docs/reference/strict-battle.md` + CHANGELOG (task-end).

## 검증 방법

- `.venv/bin/python -m pytest -q` — 전체 (baseline 650 + 신규, 회귀 0)
- `mypy src` · `ruff check .`
- scout 실행 출력을 report.md 에 기록 (수치는 결과보고이지 AC 아님 — falsify 도
  그대로 보고)

## 리스크

| 리스크 | 대응 |
|---|---|
| strict + 양측 비효과 → 상호 데미지 0 교착 | `Battle.max_turns`(200) truncation 이 기존대로 무승부 처리 → env 는 전투 이탈, 보상 0. 테스트로 명시 커버 |
| JAX 분기가 off 경로 numeric 을 건드림 | 정적 python bool 로 컴파일-타임 분기 — off 면 기존 식 문자 그대로. 기존 parity 테스트 전체가 게이트 |
| scripted_opponent 의 max(1,...) 점수와 엔진 strict 데미지 불일치 | 현 세계는 크리처당 1무브라 선택 불변 — 불변식 주석 + 다무브 도입 시 재검토 노트 |
| winnability 는 "데미지 가능"이지 "승리 보장" 아님 | 의도된 난이도 (오답 커밋 처벌). AC3 는 unwinnable-세계-없음만 보장 |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (default-off byte-identical)**: `strict_battle` 미지정/False 시 기존 동작과
  완전 동일 — 고정 seed episode trace 동일성 테스트 + 기존 전체 테스트(650) 회귀 0.
- **AC2 (strict 규칙)**: strict on 에서 effectiveness < NEUTRAL 인 공격의 데미지 0,
  ≥ NEUTRAL 인 공격은 기존 `max(1, ...)` 과 동일 — 단위 테스트 (양방향: 플레이어→
  보스, 보스→플레이어).
- **AC3 (winnability sweep)**: vary·num_types=8·min_gyms=num_gyms 구성에서
  boss_secondary off/on 각각 seed ≥ 200 sweep — 모든 보스에 strict-damage > 0 인
  파티 무브가 존재 (unwinnable 세계 0건).
- **AC4 (JAX parity 0)**: strict on (commit + noncommit, boss_secondary off/on)
  numpy↔JAX 동일 시드·동일 액션열에서 obs 전 key + reward + terminated +
  truncated **0 mismatch**; 기존 parity 테스트 전부 무회귀.
- **AC5 (scout 실측 + 정직 라벨)**: `scripts/strict_battle_scout.py` 가 strict
  off/on 의 oracle−type_blind spread 를 held-out seed 에서 출력하고, 1-run·
  scripted·no-threshold·헤드라인-금지 라벨을 포함. 결과 수치의 방향은 AC 가
  아니다 (확대 실패도 그대로 보고).
- **AC6 (문서)**: `docs/reference/strict-battle.md` evergreen 1장 (규칙·opt-in
  계약·경계·후속 조건).
