---
slug: reasoning-load-bearing
initiative: env-core
status: active
started: 2026-06-22
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/battle.py
  - src/critter_gym/types.py          # scope 정정(구현 중 발견): AC2 super_mult 가 TypeChart 에 거주
  - src/critter_gym/region.py         # scope 정정: super_mult 를 generate_region→chart 로 전달
  - src/critter_gym/party.py          # scope 정정: gym_boss 보스 strength 파라미터화 (AC2)
  - src/critter_gym/envs/critter_env.py
  - src/critter_gym/registration.py
  - tests/test_meta_difficulty.py
  - tests/test_battle.py
  - tests/test_reasoning_gate.py
extracted_to: []
supersedes: []
---

# 추론 load-bearing — team-commit 보스전으로 infer-the-meta 증명가능하게

> 작성일: 2026-06-22 | 상태: 계획
> 전진 EC: **M3 신뢰성** + **DESIGN §3.1.1 open problem 해소** (추론 load-bearing: future-work → 실증).
> 선행 pilot: freeze 전 achievability pilot **통과** (메모리 `team-commit-makes-inference-load-bearing`).

## 목표

`typechart-depth`(archive 15)가 pilot로 *불가 입증*했던 **"infer-the-meta가 load-bearing"** 을, **battle-economy
재설계(team-commit 보스전)** 로 *실증가능하게* 만든다. 측정으로 다음 두 순서를 held-out 시드에서 보인다:

1. **Gate 0 (선결)**: `oracle ≫ type_blind` — 타입지식이 *결정적*. (지난 실패의 진짜 원인: force-switch
   공짜 순회가 blind를 1.0으로 만들어 타입지식이 무의미했음.)
2. **Gate 1 (주장)**: `infer > probe` — *교차배틀 추론*이 *배틀내 probing*을 이김. team-commit이 배틀내
   probing을 구조적으로 불가능하게 만들고, 보스타입 재출현(이미 ship: 34/40)을 추론이 amortize.

이게 우리 헤드라인 novelty("infer the hidden meta")를 *속 빈 강정 → load-bearing*으로 바꾼다.

## 선행 조건

- ✅ **achievability pilot 통과** (freeze 전, throwaway `/tmp`). team-commit(보스전 크리처 1마리 commit,
  mid-battle switch·force-switch 순회 불가), sup=3, b_hp=140, b_atk=18 → `oracle 1.00 ≫ blind 0.52` /
  `infer 0.83 > probe 0.47`. 7 config가 두 게이트 동시 통과(sup∈{2,3,4} robust). → 메모리 SSOT.
- ✅ `typechart-depth`: 타입 풀 12, 보스 타입 에피소드 내 재출현, winnability 보장 (이 task의 토대).
- ✅ 측정 스택(`generalization`/`scoreboard`) 정책-비의존 — 4-arm 게이트 테스트가 재사용.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/battle.py` | team-commit 모드 — 보스전에서 mid-battle switch + faint force-switch 비활성(또는 party-of-1 commit 경로) | **높음** | 배틀 엔진 코어. M1 일반 배틀 무회귀 필수 (플래그/모드로 격리) |
| `src/critter_gym/envs/critter_env.py` | 보스 checkpoint가 team-commit 배틀 진입 — 보스 전 크리처 commit 선택 노출 | **높음** | obs/action 계약 영향 가능 → 최소 변경 원칙 |
| `src/critter_gym/registration.py` | procgen-v0 난이도 = pilot-검증 config(super_mult·boss strength) 반영 또는 신규 id | 중 | winnability 경계 유지 |
| `tests/test_reasoning_gate.py` (신규) | scripted 4-arm(oracle/type_blind/probe/infer) × held-out 시드 → 두 게이트 assert | **높음** | pilot 로직의 product화 (numpy-only, `[rl]` 불요) |
| `tests/test_meta_difficulty.py` | team-commit 메커니즘 단위 테스트 추가 | 중 | 기존 honesty 가드와 정합 |
| `tests/test_battle.py` | team-commit 모드 단위 + 일반 배틀 무회귀 | 중 | |
| `DESIGN.md` §3.1.1 | "open problem → 실증" 승격 (정직하게: scripted-arm 증명, 학습은 별개) | 중 | docs (scope 밖 path지만 honesty 핵심) |

### 영향 범위 (import 그래프)

`battle.py` ← `critter_env.py` ← `baselines.py`/`demo.py`/`scoreboard.py`. team-commit을 **모드 플래그로
격리**(기본 off = M1 동작 불변)해 하류 무회귀. `types.SUPER_EFFECTIVE`는 상수 — 난이도 튜닝이 이 값을
바꾸면 전 배틀에 전파되므로, env-config 파라미터화 vs 상수 변경 중 **무회귀 안전한 쪽** 택1 (Step 2 결정).

## Step별 계획 (TDD)

1. **Step 1 — team-commit 배틀 모드 (Red→Green)**: `battle.py`에 보스전 commit 모드 추가(mid-battle
   switch·force-switch 순회 차단; party-of-1 commit 경로). 일반 배틀은 기본 off로 불변. 단위 테스트 먼저.
2. **Step 2 — 난이도 파라미터화 (Red→Green)**: super_mult·boss strength를 env/registration config로
   노출(상수 하드코딩 회피). winnability 경계(맞으면 승·틀리면 패) 유지 테스트.
3. **Step 3 — env 통합 (Red→Green)**: `critter_env.py` 보스 checkpoint가 commit 모드 진입 + commit 선택
   action 노출. obs/action shape 불변 + `check_env` 통과.
4. **Step 4 — 4-arm 게이트 테스트 (Red→Green)**: `tests/test_reasoning_gate.py` — scripted 4 arm을
   product API로 구현, held-out 시드에서 두 게이트 assert. pilot 수치 재현 확인.
5. **Step 5 — DESIGN §3.1.1 정직 갱신 + honesty 가드 유지**: "scripted-arm으로 load-bearing 실증; 학습
   정책이 추론을 학습하는지는 후속" 명시. 기존 과대표현 가드 테스트 무회귀.

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build` (canonical clean).
- `tests/test_reasoning_gate.py`: held-out 시드 N≥40에서 `oracle − type_blind ≥ 0.2` AND `infer − probe ≥ 0.1`.
- M1 무회귀: `test_battle.py`/`test_gym_battle.py`/결정론·FIXED_CHART 불변. `check_env`(fixed + procgen-v0).
- train≠held-out 누수 0 유지.

## 리스크

- **R1 (높음)**: team-commit이 obs/action 계약을 깨 하류(baselines/demo/scoreboard) 회귀. → 모드 플래그
  격리 + 기본 off + `check_env`/throughput 가드로 차단.
- **R2 (중)**: scripted-arm 게이트가 통과해도 *학습* 정책이 추론을 학습한단 보장 없음. → DESIGN에 **정직히
  분리 명시**(achievability ≠ learnability). 헤드라인 과대 금지(typechart-depth honesty 문화 유지).
- **R3 (중)**: 난이도를 상수(`SUPER_EFFECTIVE`)로 바꾸면 전 배틀 전파 → M1 회귀. → config 파라미터화로 격리.
- **R4 (낮음)**: winnability 경계가 좁아 일부 시드 비-winnable. → 보스 풀 winnability 필터 재사용(이미 존재).

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: team-commit 보스전 모드 — 보스전에서 크리처 1마리 commit, mid-battle switch + faint force-switch
  순회 불가. 단위 테스트로 검증. **일반(M1) 배틀 동작 불변**(기본 off).
- **AC2**: 난이도(super_mult·boss strength)가 env/registration config로 노출 — 상수 하드코딩 아님.
  winnability 경계 유지(맞는 commit 승 / 틀린 commit 패) 테스트.
- **AC3**: `tests/test_reasoning_gate.py`가 **고정 held-out 시드 집합**(예: `seed ∈ [1000, 1040)`, 42 시드 —
  코드에 상수로 못박아 재현가능)에서 **Gate 0** `oracle_mean − type_blind_mean ≥ 0.2` AND **Gate 1**
  `infer_mean − probe_mean ≥ 0.1` 을 assert하고 통과. 4 arm은 product API(numpy-only)로 구현.
  - **통과 여유 명시**(L1 plan-reviewer SUGGEST 흡수): pilot 실측 margin = Gate0 **0.48**(임계 0.2의 2.4×),
    Gate1 **0.36**(임계 0.1의 3.6×). 임계를 margin보다 보수적으로 두어 N=42 시드 분산에서 안정. 산출된
    4-arm 평균은 테스트가 함께 출력(회귀 시 디버깅·정직성 가시화).
- **AC4**: **M1 완전 무회귀** — `test_battle`/`test_gym_battle`/결정론/FIXED_CHART/`check_env`(fixed+procgen-v0)
  모두 통과. train≠held-out 누수 0.
- **AC5**: DESIGN §3.1.1 정직 갱신 — "team-commit으로 추론 load-bearing을 **scripted-arm 실증**; 학습
  정책의 추론 *학습*은 후속" 명시. 기존 honesty 가드 테스트 무회귀(과대표현 재발 차단).
- **AC6**: 툴체인 canonical clean (`mypy src`·`ruff`·`pytest -q`·`build`).
