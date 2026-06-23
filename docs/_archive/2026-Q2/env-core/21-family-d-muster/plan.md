---
slug: family-d-muster
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/envs/**
  - src/critter_gym/genre_generalization.py
  - src/critter_gym/registration.py
  - tests/**
  - DESIGN.md
extracted_to: []
supersedes: []
---

# Family D — collection-gated power (progression axis) — (B) 4번째 family

> 작성일: 2026-06-23 | 상태: 계획

## 목표

(B) 장르 일반화 토대를 **네 번째 구조-상이 family**로 확장 + env-level held-out split(train {A,B,C}→unseen D)
데모. 기존 축: A=action-collect, B=contact-collect(*수집* 축), C=type-agnostic duel(*배틀-시스템* 축). family D는
DESIGN이 명시한 세 번째 축 = **진행(progression) 메커닉**: `MusterEnv` = **수집이 배틀력을 좌우**(잡은 creature가
파티 공격력 강화) + 강한 보스 → 보스를 이기려면 *먼저 수집해 muster*해야 함. 수집과 배틀을 의존 관계로 결합.

**Pilot(freeze 전, 통과)**: 강한 보스(boss_hp 300)에서 family D gym-clear — **pure_rush(수집 안 함) 0.00 ≪ muster
(catch 4 후 격파) 1.25** = 깨끗한 skill-structural 분리. **family A에선 muster=rush=0.00**(catch가 버프 안 줘 muster
스킬 무용) → muster 스킬이 *D에선 load-bearing, A에선 무용* = family C와 평행한 정책-특정 대조(난이도 confound 아님:
D는 muster로 winnable). conforms ✓, same-seed→A≠D trajectory ✓.

**EC 매핑**: 활성 M3 신뢰성 + (B) 토대 4-family 확장. arXiv writeup이 인용할 4-family 토대.

**정직성 원칙**: acceptance = *4번째 family 추가 + env-level 측정 + 정직 보고*로 freeze(증명 아님). 4 family도 여전히
"많은 구조-상이 family" 미달 → 토대 강화. 핵심 신호 = **정책-특정 대조**(muster≫rush on D, muster 무용 on A),
LOO cross-family 평균 gap은 D가 강한 보스라 난이도 confound 포함 → 대조로 통제 + 캐비엣 명시.

## 선행 조건

- `env_family`(conforms+registry), `genre_generalization`(LOO + 레퍼런스 정책) — 토대 재사용/확장
- `MusterEnv`는 `CritterEnv` 서브클래스(catch 경로 override) — family B/C 선례
- pilot로 강한-보스 calibration(muster load-bearing) 확정

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/envs/muster_env.py` (신규) | family D `MusterEnv(CritterEnv)` — CATCH 성공 시 파티 공격력 +N (collection-gated power) | 신규, 격리 |
| `src/critter_gym/registration.py` | `CritterGym-muster-v0` + family `"muster"`(강한 보스 calibration — family 정체성) | 저 (append) |
| `src/critter_gym/genre_generalization.py` | 레퍼런스 정책 2종 추가(`rush_policy` 순수 직행·catch 안 함 / `muster_policy` 수집-우선) — D 대조 instrument. LOO는 family 리스트에 "muster" 추가로 자동 4-family | 저 (append) |
| `tests/test_muster_env.py` (신규) | conforms+등록 + 구조적 상이(same-seed→A≠D, catch 버프) + winnable(muster) + skill-structural 대조(muster≫rush on D, muster 무용 on A) | 신규 |
| `tests/test_genre_generalization.py` | 4-family LOO + family D 대조 신호 | 저 (append) |
| `DESIGN.md` (§3.1.1 (B)) | 3→4 family, 진행 축, 정책-특정 대조 신호 + 난이도 confound 캐비엣 | 저 |

## Step별 계획

1. **(freeze 전) Pilot** — 완료. 강한-보스 calibration·skill-structural 대조·구조적 상이 입증.
2. **Red** — `test_muster_env.py`: 계약+등록 / same-seed→A≠D(catch 버프로 배틀상태 시그니처 상이) / winnable(muster) / **대조**(muster≫rush on D ∧ muster≈rush on A=스킬 무용). fail 확인.
3. **Green** — `MusterEnv` 구현(CATCH 성공 시 `c.attack += _MUSTER_ATK`), `CritterGym-muster-v0`+family `"muster"` 등록(강한 보스 calibration), `genre_generalization`에 `rush_policy`/`muster_policy` 레퍼런스 추가.
4. **Green** — `test_genre_generalization.py`: 4-family LOO(held_out 집합={A,B,C,D}) + family D 대조 신호 테스트.
5. **보고** — DESIGN §3.1.1 (B) 갱신(4 family, 진행 축, 대조 신호, 난이도 confound 캐비엣). 여전히 토대.
6. **Refactor + 무회귀**.

## 검증 방법

- `pytest -q` — 신규 family D 테스트 + 전체 무회귀(174→증가, 회귀 0).
- `check_env` 6종(fixed/procgen/commit/forage/duel/**muster**).
- family A/B/C 무회귀(MusterEnv 서브클래스, 기존 코드 무변경).
- mypy/ruff/build clean, honesty 가드 무회귀.

## 리스크

1. **난이도 confound** (D 강한 보스 → LOO cross-family 평균 gap이 mechanic+난이도 혼재) → 헤드라인을 **정책-특정 대조**(muster≫rush on D, muster 무용 on A)로 두고, raw LOO gap은 보조+캐비엣 명시. muster가 D를 이기므로(1.25) "그냥 어려움" 아님 입증.
2. **family D가 다른 boss config 사용**(A/B/C는 _FAMILY_CFG) → family 정체성의 일부로 정직 표기. 대조가 난이도 아닌 스킬임을 통제.
3. **`rush_policy`/`muster_policy` 공정성** — 둘 다 obs-only·family-agnostic. nav 공유, 차이는 "수집 우선 여부"뿐 → 수집 스킬 격리.
4. **서브클래스가 family A 회귀** → 기존 코드 무변경, 무회귀 테스트.

## Acceptance Criteria (G1 통과 시 freeze)

> *4번째 family + env-level 측정 + 정직 보고*로 freeze. 신호지 증명 아님.

- **AC1** — `MusterEnv`(family D)가 `conforms` 계약 충족 + `CritterGym-muster-v0` 등록 + family registry `"muster"` 등록.
- **AC2** — 구조적 상이: CATCH 성공 시 파티 공격력 강화 → same-seed+같은-액션에서 family A와 **배틀상태 trajectory 상이**(시드변형 환원불가). 테스트 입증.
- **AC3** — winnable: obs-only `muster_policy`가 held-out 시드에서 **보스를 격파**(gym-clear > 0). *절대 수치(1.25) 아닌 "격파 발생"으로 검증* — "gap=signal, threshold 아님" 원칙(L1 measurement reviewer 반영).
- **AC4** — `genre_generalization` **4-family LOO**(critter/forage/duel/muster) 측정 + 기존 2-family·LOO API 무회귀.
- **AC5** — **정책-특정 대조 + 정직 보고**: family D에서 `muster_policy > rush_policy`(수집-강화 스킬 load-bearing)이고 family A에선 `muster ≈ rush`(스킬 무용) → gap이 *skill-structural*(대조 *방향*으로 검증, 크기 freeze 아님). raw LOO gap의 난이도 confound는 캐비엣으로 명시. 4 family도 토대지 증명 아님.
- **AC6** — 무회귀: family A/B/C 무변경, 전체 테스트 회귀 0, **check_env 6 gym id**(기존 5 `CritterGym-v0`/`-procgen-v0`/`-commit-v0`/`-forage-v0`/`-duel-v0` + **`-muster-v0`**), mypy/ruff/build clean, honesty 가드 무회귀. DESIGN §3.1.1 (B) 갱신.
