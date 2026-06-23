---
slug: battle-system-family
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/envs/**
  - src/critter_gym/env_family.py
  - src/critter_gym/genre_generalization.py
  - src/critter_gym/registration.py
  - tests/**
extracted_to: []
supersedes: []
---

# Family C — a structurally-distinct **battle system** (genre-generalization, stronger axis)

> 작성일: 2026-06-23 | 상태: 계획

## 목표

DESIGN §3.1.1 (B) 장르 일반화의 **정직한 약점을 메우는 세 번째 env family** 추가. 직전 세션이
세운 `env_family`/`genre_generalization` 토대(2 family)는 **측정 머신**일 뿐 장르 주장이 아니다 — 그
이유는 family B(`ForageEnv`)가 **수집 메커닉 1축**만 다르고 **배틀 시스템을 A와 공유**해서, A-튜닝
greedy 정책이 gap≈0으로 전이됐기 때문(축이 관대 = 신호 빈약).

family C는 **배틀 시스템 자체를 바꾼다** = family B가 결여한 "더 강한 구조 축". 핵심 의사결정 규칙을
"숨은 타입표 추론 + 매치업 + 스위칭"에서 **타입-무관 자원(스태미나)·commit 결투**로 교체. A에서
load-bearing이던 *타입 추론 스킬이 family C에서는 무용* → A-튜닝 정책이 **전이되지 않아** 비자명한
env-level gap 신호를 낳는다. 이것이 family B가 만들지 못한 정직한 신호다.

**EC 매핑**: M3 신뢰성 + DESIGN §3.1.1 (B) 토대 강화. (B)를 "진짜 주장"으로 끌어올리는 이니셔티브의
다음 슬라이스(3번째 family). M5 custom-env 표면의 첫 진짜 예시.

**정직성 원칙(freeze 전 합의)**: acceptance는 *"장르 일반화를 증명한다"*가 **아니라** *측정 머신을 3
family로 확장 + family C가 구조적으로 비자명(A-정책 비전이) + 정직 보고*로 freeze. 3 family도 여전히
"많은 구조-상이 family" 미달 → 토대 강화지 증명 아님. gap은 signal, threshold 아님(직전 3 task 패턴 계승).

## 선행 조건

- `env_family.py` 계약(`conforms`: `Discrete(6)` + `REQUIRED_OBS_KEYS`) + registry(`register_family`/`make_family`) — **재사용**
- `genre_generalization.measure_genre_generalization` (2-family pairwise) — **3 family로 확장 필요**
- `ForageEnv` 패턴(CritterEnv 서브클래스, 단일 메서드 override) — family C의 템플릿
- `Battle`/`_step_battle` 경로(commit_mode 등) — family C가 override할 지점
- **freeze 전 pilot**(아래 §검증) — family C 배틀 축의 (a) 달성가능성 (b) 비자명 신호 (c) winnability 검증

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/envs/duel_env.py` (신규) | family C `DuelEnv(CritterEnv)` — 배틀 경로 override (타입-무관 stamina/commit 결투) | 신규, 격리 |
| `src/critter_gym/registration.py` | `CritterGym-duel-v0` 등록 + `_register_families`에 `"duel"` 추가 | 저 (append) |
| `src/critter_gym/genre_generalization.py` | 2-family pairwise → **다(多)-family** leave-one-out env-level 측정 확장 | 중 (API 확장, 무회귀) |
| `src/critter_gym/env_family.py` | (필요 시) family C도 만족하는지 계약 확인 — 변경 최소 | 저 |
| `tests/test_duel_env.py` (신규) | family C 계약 충족 + same-seed→배틀 trajectory가 A와 상이(시드변형 환원불가) + winnability | 신규 |
| `tests/test_genre_generalization.py` | 다-family 측정 + A-정책 비전이(비자명 gap) 신호 테스트 추가 | 저 (append) |

### 영향 범위 (import 그래프)

- `DuelEnv`는 `CritterEnv` 서브클래스 → family A/B 코드 **무변경**(ForageEnv 선례와 동일).
- `genre_generalization` 확장은 기존 `GenreGapReport`/2-family 호출 **무회귀**(새 다-family 함수 추가, 기존 시그니처 보존).
- core CI numpy-only 유지(배틀 시스템은 numpy/stdlib만). `[rl]`/`[render]` 무영향.

## Step별 계획

1. **(freeze 전) Pilot / design-note** — `DuelEnv` 프로토타입으로 검증: ① `conforms` 통과 ② same-seed+same-actions 배틀 trajectory가 family A와 상이(시드변형 아님) ③ winnable(타입-무관 결투에서 scripted가 이길 수 있음) ④ **A-튜닝 greedy 정책이 family C로 전이 안 됨**(gap이 family B의 ≈0과 달리 비자명). **⑤ (L1 measurement reviewer 반영) gap이 *구조적 스킬 불일치*임을 입증 — *정책-특정 대조*: family C에 적합한 reference 정책(C-appropriate, 예: stamina/commit 규칙을 아는 scripted)은 C로 작은 gap으로 전이하는데 A-튜닝 정책은 큰 gap을 보여야 함.** ④만으로는 "family C가 그냥 어려워서 어떤 단순 정책도 floor"라는 trivial confound와 구분 안 됨 → ⑤가 gap을 *skill-structural*로 확정. 미달 시 진입 안 함(typechart-depth 선례: 정직 descope). 결과를 plan/report에 기록 후 G1.
2. **Red** — `test_duel_env.py`: 계약 충족 + 구조-distinctness(배틀 trajectory A≠C) + winnability 테스트 작성(fail 확인).
3. **Green** — `DuelEnv` 구현: 타입-무관 stamina/commit 배틀(ATTACK/CHARGE/GUARD류 결정 규칙). obs/action 계약 유지(`Discrete(6)`, REQUIRED_OBS_KEYS — type 필드는 채우되 배틀 동역학에서 무의미). `CritterGym-duel-v0` 등록 + family registry `"duel"` 등록.
4. **Green** — `genre_generalization` 다-family 확장(leave-one-out: train families → unseen family C gap). 기존 2-family API 무회귀.
5. **측정 + 정직 보고** — random/greedy로 {critter, forage, duel} env-level gap 측정. family C가 A-정책 비전이로 family B보다 큰 gap 보이는지 *신호*로 기록(threshold 아님). DESIGN §3.1.1 (B) 문단 갱신(2 family→3, 여전히 토대; honesty 가드 점검).
6. **Refactor** — 배틀 시스템 seam 정리(필요 시), 무회귀 확인.

## Pilot 결과 (2026-06-23, freeze 선결 — 통과)

scratchpad 프로토타입 `DuelEnv`(타입-무관 charge/commit RPS 결투: ATTACK>CHARGE>GUARD>ATTACK, charge가 공격 배율) + nav 동일·배틀만 변주한 정책으로 5조건 검증:

| 조건 | 결과 | 수치 |
|---|---|---|
| ① conforms | ✅ | `conforms(DuelEnv)=True` |
| ② 구조적 상이 (배틀상태 시그니처, 배틀 진입 시드) | ✅ | seed 1000000·1000003: A_sig≠C_sig (배틀 미도달 시드는 동일=당연) |
| ③ winnable | ✅ | C-appropriate held-out mean=4.333 (3 gym 격파+진화) |
| ④ A-튜닝 비전이 | ✅ | A-tuned가 C에서 0.583, gap **+3.917** |
| ⑤ skill-structural 대조 | ✅ | C에서 C-appr 4.333 ≫ A-tuned 0.583 ≈ random 0.250; C-appr cross-gap만 −0.167 |

→ gap은 *난이도 confound*가 아니라 *스킬 구조* 때문(C-적합 정책은 양방향 전이, A-튜닝만 C로 비전이). **진입 승인 가능**.

**Pilot이 드러낸 설계 노트 (구현에 반영)**:
- (N1) AC2 distinctness는 generic `trajectory_signature`(reward+caught만 추적)로는 family C 배틀 차이를 못 잡음 → **배틀 진입 + enemy_hp/in_battle/승패 포함 시그니처**로 테스트.
- (N2) C-appropriate 정책이 duel charge 상태를 읽어야 함 → 실제 `DuelEnv`는 **duel charge를 obs에 노출**(`conforms`가 REQUIRED_OBS_KEYS *초과* 키 허용 — 계약 무위반)해 특권 접근 없이 공정 플레이. family-agnostic 정책은 추가 키 무시.

## 검증 방법

- **Pilot 게이트(freeze 선결)**: 위 Step 1의 4개 조건을 스크립트로 확인. 비자명 gap 미달 시 → 배틀 축 재설계 또는 사용자에게 descope 보고(typechart-depth 선례: 불가 시 정직 축소).
- `python3 -m pytest -q` — 신규 family C 테스트 + 전체 무회귀(160→증가, 회귀 0).
- `check_env` 5종(fixed/procgen/commit/forage/**duel**) 통과.
- family A/B 무회귀(배틀 공유 안 하므로 코드 무변경 확인).
- `mypy src` / `ruff check .` / `python -m build` clean.

## 리스크

1. **family C가 또 "관대한 축"이 될 위험**(gap≈0) → freeze 전 pilot이 A-정책 비전이를 명시 검증, 미달 시 진입 안 함.
2. **타입-무관 배틀이 obs 계약의 `player_type`/`enemy_type`를 무의미하게** → 계약은 키 존재만 요구(동역학 무관), 정직하게 "family C에서 type 필드는 vestigial" 문서화.
3. **다-family 측정 확장이 기존 2-family API 회귀** → 새 함수로 추가, 기존 시그니처/테스트 보존.
4. **스코프 과대**(배틀 엔진 대수술) → env-level 서브클래스 override로 최소화(ForageEnv 선례), 배틀 엔진 공용 변경 회피.

## Acceptance Criteria (G1 통과 시 freeze)

> 성능/주장이 아니라 **측정 + 정직 보고**로 freeze (직전 3 task 패턴). gap은 signal.

- **AC1** — `DuelEnv`(family C)가 `env_family.conforms` 계약 충족(`Discrete(6)` + REQUIRED_OBS_KEYS) + `CritterGym-duel-v0` 등록 + family registry `"duel"` 등록.
- **AC2** — family C는 **배틀 시스템이 구조적으로 상이**: 배틀에 진입하는 시드·액션에서 **배틀상태(enemy_hp/in_battle/승패) 시그니처가 family A와 다름**(시드변형 환원불가; pilot N1대로 generic reward+caught 시그니처 아님). 테스트로 입증.
- **AC3** — family C가 **observable 상태만으로 winnable**(degenerate·특권접근 아님): duel charge를 obs에 노출(pilot N2, REQUIRED 초과 키 = 계약 무위반) → obs만 읽는 C-appropriate scripted 정책이 held-out 시드에서 보스 격파 가능(pilot 4.333 재현).
- **AC4** — `genre_generalization`가 **3 family**(critter/forage/duel) env-level gap 측정(leave-one-out 또는 pairwise). 기존 2-family API 무회귀.
- **AC5** — **측정 산출 + 정직 보고**(report.md에 기록): random/greedy의 {A,B,C} env-level gap + **정책-특정 대조**(C-적합 reference는 C로 작은 gap, A-튜닝은 큰 gap = gap이 *skill-structural*이지 trivial 난이도 아님)를 기록. family C가 family B 대비 비자명 신호인지 *signal*로 서술(threshold 아님). 3 family도 토대지 증명 아님 명시.
- **AC6** — 무회귀: family A/B 코드 무변경, 전체 테스트 회귀 0, **check_env 5 gym id**(`CritterGym-v0`/`-procgen-v0`/`-commit-v0`/`-forage-v0`/**`-duel-v0`** — 기존 4 + duel) 통과, mypy/ruff/build clean. DESIGN §3.1.1 (B) + honesty 가드 점검(과대표현 차단).
