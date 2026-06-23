---
slug: genre-generalization-foundation
initiative: env-core
status: active
started: 2026-06-22
acceptance_freeze: true
task_type: env
mode: heavy
domains: [rl-env]
scope_paths:
  - src/critter_gym/envs/**
  - src/critter_gym/env_family.py
  - src/critter_gym/genre_generalization.py
  - src/critter_gym/registration.py
  - tests/test_env_family.py
  - tests/test_genre_generalization.py
extracted_to: []
supersedes: []
---

# genre-generalization-foundation — (B) 장르 일반화의 측정 토대 (이니셔티브 1번째 슬라이스)

> 작성일: 2026-06-22 | 상태: 계획
> 전진: **DESIGN §3.1.1 (B)** = 진짜 해자 ②층(M5 커스텀 env와 동일 바). 인수인계서 §3-B.
> ⚠ **(B)는 이니셔티브급** — 본 task는 *전체가 아니라 토대 첫 슬라이스*. 더 많은 env 패밀리는 후속 task.

## 목표

지금까지의 일반화는 **instance-level**(같은 생성기, 다른 시드)뿐이다. (B) 장르 일반화 = **environment-level**
(구조-상이 env 패밀리 사이) 일반화. 이 task는 그 측정을 *end-to-end로 가능하게 하는 최소 토대*를 만든다:

1. **env-family 추상화** — 여러 구조-상이 수집형 RPG env가 공유하는 obs/action 계약(또는 어댑터) +
   family registry. 한 정책이 여러 env에서 작동 가능.
2. **두 번째 *구조-상이* env(family B)** — CritterEnv(family A)와 **문서화된 구조적 차이**(다른 수집/진행
   메커닉)를 갖되 동일 obs/action 계약 공유. *최소하지만 진짜 구조 차이*(단순 시드 변형 아님).
3. **environment-level split + 측정** — train family A → eval **unseen** family B 의 env-level 일반화 갭을
   `genre_generalization`으로 측정(기존 instance-level `generalization`과 직교 재사용).

**⚠ 정직성 설계(learnability/§4 교훈 적용)**: acceptance를 "env-level gap≈0 (장르 일반화 입증)"으로 freeze
하지 **않는다**(2개 패밀리로는 장르 주장 불가 — 그건 다수 패밀리 후속). acceptance = **추상화·두 번째 env·
env-level 측정 하네스가 동작 + 측정 산출 + family B의 구조적 차이를 정직히 문서화**. gap 결과는 *신호*로 보고.

## 선행 조건

- ✅ CritterEnv(family A) + `generalization`(instance-level, env_factory 재사용 가능) + `learnability` 패턴.
- ✅ Gymnasium `Env[dict, int]` 계약. obs=Dict, action=Discrete(6).
- ⚠ **설계 리스크 선검토(Step 0)**: "구조-상이"를 어디까지로 정의하면 obs/action 공유와 양립하는가 —
  freeze 전 design note로 family B의 구조 차이 축을 명시(수집 메커닉 vs 배틀 vs 진행). over/under-claim 회피.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `env_family.py` (신규) | env-family 추상화 — 공유 obs/action 계약 Protocol/base + family registry(이름→factory) | **높음** | CritterEnv가 이미 만족하는 계약을 형식화 |
| `src/critter_gym/envs/` (신규 env) | family B = 구조-상이 최소 env(다른 수집/진행 메커닉, 동일 obs/action) | **높음** | 진짜 구조 차이(시드 변형 아님) + check_env |
| `genre_generalization.py` (신규) | environment-level 측정 — train family → eval unseen family 갭(`generalization` 재사용/직교) | 중 | numpy-only, 정책-비의존 |
| `registration.py` | family B env id 등록 | 낮 | 기존 id 무변 |
| `tests/test_env_family.py` (신규) | 추상화 계약 + registry + family B check_env + family A 무회귀 | **높음** | |
| `tests/test_genre_generalization.py` (신규) | env-level 측정 API 계약 + split 의미(A↔B) | 중 | numpy-only |

### 영향 범위 (import 그래프)

`env_family.py`(계약) ← family A(CritterEnv)·family B ← `genre_generalization.py`(측정). 기존 `generalization`
(instance-level)은 직교 — env-family는 그 위 레이어. CritterEnv 자체는 **무변경**(계약을 사후 형식화만).

## Step별 계획 (TDD)

0. **Step 0 — 구조-상이 design note(freeze 전)**: family B의 구조 차이 축을 1개로 명확히 택1(예: *수집
   메커닉* — catch-on-tile(A) vs defeat-to-collect(B)). obs/action 공유 양립 확인. **측정가능 판별 기준**:
   다른 transition/collect 코드 경로 ≥1 → same-seed·same-actions에서 A≠B trajectory(AC2). plan에 박고 G1 freeze.
1. **Step 1 — env-family 추상화 (Red→Green)**: 공유 obs/action 계약 Protocol/base + family registry.
   CritterEnv가 계약을 만족함을 테스트로 형식화(무변경).
2. **Step 2 — family B 최소 env (Red→Green)**: 구조-상이 env(Step 0 축) 구현, 동일 obs/action, `check_env`
   통과. family A 무회귀.
3. **Step 3 — env-level 측정 (Red→Green)**: `genre_generalization` — train family → eval unseen family 갭.
   reference 정책(random/scripted)으로 측정 API 계약 검증.
4. **Step 4 — 측정 산출 + 정직 보고**: A↔B env-level 측정 1회 → family B 구조 차이 + 갭을 report에 정직 기록.
   "2 패밀리=토대지 장르 주장 아님" 명시. DESIGN §3.1.1 (B) 상태 갱신(토대 착수).

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build` (canonical clean, 신규 core numpy-only).
- family A 완전 무회귀(기존 전체 + check_env ×3). family B check_env 통과.
- env-family registry/계약 단위 테스트. env-level 측정 API 계약(train A→eval B 실행).

## 리스크

- **R1 (높음·정직성)**: 2개 패밀리로 "장르 일반화 입증"은 과대 — 그건 다수 패밀리 필요. → **acceptance를
  gap 결과로 freeze 안 함**. 토대+측정+정직 문서화로 한정. 결과는 신호.
- **R2 (높음·설계)**: family B가 "구조-상이"가 아니라 사실상 시드 변형이면 (B) 무의미. → Step 0 design note로
  구조 차이 축 명시 + report에 차이를 구체 문서화(검증 가능하게).
- **R3 (높음·범위)**: 이니셔티브급을 한 task에 욱여넣기. → 최소 family B + 토대만. 다수 패밀리·강한 주장은 후속.
- **R4 (중)**: 공유 obs/action 계약이 family B를 너무 제약(구조 차이 못 냄). → 어댑터 허용 + obs/action 재해석.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `env_family.py` — 공유 obs/action 계약(Protocol/base) + family registry. CritterEnv(family A)가
  계약을 만족함을 테스트로 형식화(**CritterEnv 무변경**).
- **AC2**: **family B** = 구조-상이 최소 env. 동일 obs/action 계약, `check_env` 통과, registry 등록.
  **family A(M1/procgen/commit) 완전 무회귀.** **구조-상이 측정가능 판별 기준**(qa BLOCK + plan SUGGEST 흡수):
  family B는 family A와 **다른 transition/collect/progression 코드 경로 ≥1**을 가져, **동일 시드·동일 액션
  시퀀스**로 실행했을 때 family A와 **다른 obs/reward trajectory**를 산출한다(= 시드 변형으로 환원 불가).
  이를 테스트로 검증(same-seed-same-actions → A ≠ B trajectory).
- **AC3**: `genre_generalization.py`(numpy-only, 정책-비의존) — train family → eval **unseen** family env-level
  측정 API. reference 정책으로 train-A→eval-B 측정이 실행됨(API 계약 테스트).
- **AC4**: **측정 1회 실행 + 정직 보고**. **객관 합격 기준**(gap 값 자체는 threshold 아님 — 2 패밀리로 장르
  입증 불가, 정직성): (a) env-level 측정이 train-A→eval-B로 **실행 완료**, (b) AC2의 **구조-상이 판별 기준
  통과**(same-seed→A≠B trajectory 테스트 green), (c) report에 **갭 수치 + family B 구조 차이 구체 문서화 +
  "2 패밀리=토대, 장르 주장 아님" 명시 + DESIGN §3.1.1 (B) 상태 갱신**. gap 결과는 *신호*로 보고(threshold 무).
- **AC5**: family A 완전 무회귀 — **postcondition**: 기존 전체 통과 유지(baseline 151 passed/2 skipped 대비
  **감소 0**, 신규 테스트만 증가 = 151+N) + `check_env`가 **CritterGym-v0/procgen-v0/commit-v0 3종** 통과 +
  honesty 가드 무회귀.
- **AC6**: 툴체인 canonical clean(`mypy src`·`ruff`·`pytest -q`·`build`). 신규 core 모듈 numpy-only.
