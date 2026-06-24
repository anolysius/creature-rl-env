---
slug: jax-difficulty-report
initiative: jax-throughput
status: active
started: 2026-06-24
acceptance_freeze: true
domains: [rl-env]
task_type: env
mode: standard
scope_paths:
  - src/critter_gym/jax_env.py
  - src/critter_gym/jax_train.py
  - scripts/jax_rl_demo.py
  - tests/test_jax_difficulty_parity.py
  - docs/explanation/jax-throughput.md
  - DESIGN.md
  - docs/CHANGELOG.md
  - docs/_active/jax-throughput/INITIATIVE.md
extracted_to: []
supersedes: []
---

# jax-difficulty-report (R5) — jax_env config화로 동적 범위(고-gym) 재포트 + parity + jax_train 가속

> 작성일: 2026-06-24 | 상태: 계획 | 마일스톤: **M4** (jax-throughput; difficulty-dynamic-range의 R5 후속)

## 한 문단 요약 (수식 없이)

방금 우리는 "도장 수를 늘리면 변별이 또렷해진다"를 느린 numpy 버전에서 증명했습니다(`difficulty-dynamic-range`). 그런데 그 측정(특히 학습)은 느립니다 — 도장 8개짜리 PPO 학습이 오래 걸렸죠. 지난번 만든 **빠른 JAX 엔진**은 도장 수가 3개로 **고정**돼 있어 그 고-gym 설정을 못 돌립니다. 이번 작업은 JAX 엔진을 **설정 가능**하게 바꿔(도장 수·격자 크기·보스 스탯 등) 고-gym 설정도 돌리게 하고, **원본과 한 글자도 안 틀리는지(parity)** 확인한 뒤, 그 위에서 학습을 돌려 **고-gym 학습이 얼마나 빨라지는지** 보여줍니다. 즉 "빠른 엔진 + 변별 분해능"을 합칩니다. 기본 설정(도장 3개)은 그대로 둬서 기존 것은 안 깨집니다.

## 목표

`difficulty-dynamic-range`가 numpy에서 입증한 **고-gym 동적 범위 설정**을 JAX 벡터화 엔진으로 재포트(jax-throughput R5). 현 `jax_env`는 `_GRID=10`·`_MAX_STEPS=200`·`_MAX_GYMS=3`·`_BOSS_*` 하드코딩이라 그 설정을 못 돌림. **config화**(factory)해 고-gym commit 설정을 mirror하고, **numpy `CritterEnv` 대비 parity 0 mismatch**(재현성 북극성 #3)를 재확립한 뒤, `jax_train`이 고-gym 설정에서 학습 가능하게 해 **고-gym 학습을 vmap으로 가속**(현 sb3 `--range-gap`은 느림).

**acceptance = parity + 측정/정직 보고**(§4 교훈): parity가 게이트(가짜 속도 금지), 속도는 vmap 한정·CPU·single-run 정직 framing. 기본 config 무회귀(parity 보존).

## 선행 조건

- `jax_env`(#42, family A commit, parity 0) + `jax_train`(jax-rl-demo, JAX-native A2C) **위에** config화 레이어.
- 대상 config = `difficulty-dynamic-range`의 `DISCRIM_BASE` + num_gyms=8/min_gyms=8: grid_size=6·max_steps=160·patch_radius=5·num_types=12·super_mult=3.0·boss_hp=150·boss_atk=16·commit·vary. (party는 3-스타터 그대로 — 다양화 안 함.)
- num_types/super_mult는 이미 `region.chart` 경유로 흐름(jax_reset). config화 대상 = grid·patch_radius·max_steps·max_gyms·boss_hp·boss_atk(·boss_def·boss_spd 기본).
- **branch**: G1 후 `feature/jax-difficulty-report`. main 직접 금지.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/jax_env.py` | config factory | **중-상** | `JaxEnvConfig`(NamedTuple: grid·patch_radius·max_steps·max_gyms·boss_hp/atk/def/spd) + `make_jax_env(cfg)` → (reset/step/encode) 클로저. **기존 module-level `jax_env_step`/`jax_reset`/`encode_obs`/`make_env_step`는 default-config 인스턴스로 보존**(import·기존 parity·bench·jax_train 무변경). JAX static-shape라 cfg는 compile-time 상수(factory 클로저). |
| `src/critter_gym/jax_train.py` | config-aware | 중 | `build_region_bank`/`train`/`evaluate`가 config(+region-gen 인자: grid·max_creatures·max_gyms·min_gyms·super_mult)를 받아 factory의 reset/step 사용. 기본 인자=현 동작(무회귀). |
| `tests/test_jax_difficulty_parity.py` | 신규 | 중 | `importorskip("jax")`: 고-gym difficulty config서 jax(make_jax_env(cfg)) vs 실제 `CritterEnv(**cfg)` **full parity**(obs 13키[patch 11×11 포함]+reward+term+trunc, random+gym-clearing 정책, fixed+vary). |
| `scripts/jax_rl_demo.py` | flag 추가 | 저 | `--difficulty` — 고-gym config로 jax_train 학습 + throughput(vmap) vs sb3 `--range-gap` 대비 + (선택) 학습 gym-clear. 정직 framing. |
| `docs/explanation/jax-throughput.md` | 갱신 | 저 | R5 update 블록(config화 + 고-gym parity + 가속). |
| `DESIGN.md` | 갱신 | 저 | §4 R5 1줄. |
| `docs/CHANGELOG.md` · `INITIATIVE.md` | append | 저 | task-end. |

### 영향 범위 (import 그래프)

`make_jax_env` 신규. module-level fns = `make_jax_env(DEFAULT_CFG)` 결과로 보존 → `test_jax_env_parity`·`test_jax_battle_parity`·`bench_throughput`·`jax_train`(기본 경로) **무변경**. `jax_train` config 인자는 기본값=현 동작. core CI numpy-only 불변(jax importorskip). 기존 294 tests 무회귀.

## Step별 계획

> **G1 freeze 전 PILOT 필수** — #42처럼 새 config parity가 미묘한 mismatch를 드러낼 수 있음(truncated 독립성·patch>grid 패딩·가변 gym 마스크). freeze 전 고-gym parity를 실측(0 mismatch 게이트).

1. **config factory** — `JaxEnvConfig` + `make_jax_env(cfg)`. 기본 cfg = 현 상수 → module-level fns 보존. pilot: 기존 parity 테스트 그대로 green(무회귀).
2. **고-gym parity(pilot 핵심)** — difficulty config로 make_jax_env(cfg) vs CritterEnv(cfg) full parity. **0 mismatch가 freeze 게이트.** mismatch 시 원인 수정(patch 패딩·gym 마스크 등).
3. **jax_train config-aware** — build_region_bank/train/evaluate가 cfg+region 인자 받게. 고-gym 학습 tracer OK + 가속 측정.
4. **데모** — `jax_rl_demo --difficulty`: 고-gym vmap 학습 throughput vs sb3, 정직 보고.
5. **테스트 + 문서**.

## 검증 방법

- **CI(numpy-only)**: 기본 무회귀 → 294 tests green. 신규 parity 테스트 importorskip.
- **로컬 [jax]**: 고-gym parity 0 mismatch + 학습 tracer OK + throughput 측정.
- **canonical**: `mypy src`·`ruff check .`·`pytest -q`·`python -m build` clean.

## 리스크 / Pilot (freeze 전)

| # | 리스크 | Pilot | 분기 |
|---|---|---|---|
| R1 | **고-gym parity mismatch** — patch_radius>grid 패딩·8-gym 마스크·truncated 독립성 등 미묘차. | 고-gym config full parity 실측. | 0 mismatch → 진행 / mismatch → 원인 수정 후 재측정(parity는 비협상 게이트). |
| R2 | **config화가 기존 parity 깸** — factory 리팩터가 default 경로 변경. | 기존 parity 3종 테스트 green. | 위반 0이어야(default cfg=현 상수). |
| R3 | **고-gym 학습 tracer/shape 에러** — 8-gym·큰 patch가 jit/vmap서 실패. | jax_train 고-gym smoke. | 에러 시 수정(static shape 정합). |
| R4 | **가속 미미** — 고-gym 발산 심해 vmap 이득↓. | vmap 학습 steps/s vs sb3 동 config. | 측정값 정직 보고(부등식 성립 시만 "빠르다"). |

**사전약정 결정규칙 (freeze):**
- **parity 게이트 (R1/R2)**: 고-gym difficulty config + 기존 3종 config 모두 **0 mismatch**(obs 13키+reward+term+trunc). 미충족 = 수정(비협상).
- **speed (R4)**: "빠르다"는 vmap 고-gym 학습-rollout env-steps/s `>` numpy sb3 동 config steps/s 성립 시에만. 절대 배율 사전 임계 없음(측정값 보고).
- **무회귀 (R2)**: 기본 config jax_env_step/jax_reset 출력 = 현재와 동일(기존 parity 테스트 green).

**정직성 사전약정 (박제):**
- parity 0 mismatch가 가짜 속도 차단(재현성 보존). 속도 이득=vmap 한정·CPU·single-run.
- 이번은 *family A commit·고-gym* 재포트지 difficulty *전체* JAX화 아님(scripted resolution arms는 numpy-only 유지 — env 내부 peek). 정직 라벨.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1** — `jax_env.py` `JaxEnvConfig` + `make_jax_env(cfg)` factory(reset/step/encode 클로저). module-level `jax_env_step`/`jax_reset`/`encode_obs`/`make_env_step` = default-config 인스턴스로 **보존**(import 무변경).
- **AC2** — `jax_train.py` `build_region_bank`/`train`/`evaluate` config-aware(cfg + region-gen 인자). 기본값=현 동작(무회귀). 고-gym 학습 tracer OK.
- **AC3** — `tests/test_jax_difficulty_parity.py`(importorskip): 고-gym difficulty config서 jax vs `CritterEnv(**cfg)` **full parity 0 mismatch**(obs 13키[patch 포함]+reward+term+trunc, random+gym-clearing, fixed+vary).
- **AC4** — `scripts/jax_rl_demo.py --difficulty`: 고-gym vmap 학습 throughput vs sb3 동 config 정직 비교 + framing. "빠르다"는 부등식 성립 시만.
- **AC5** — core CI numpy-only 불변: 294 tests 무회귀(기존 parity 3종 green=R2), 신규 importorskip. canonical clean.
- **AC6** — **freeze 전 pilot**으로 R1(고-gym parity)·R2(무회귀)·R3(tracer)·R4(speed) 측정 → 사전약정 규칙 분기. parity mismatch는 비협상 수정. pilot 결과 report 박제.
- **AC7** — 측정/정직 보고: parity 0 mismatch 박제 + 속도=vmap·CPU·single-run 라벨 + "family A commit·고-gym 한정(difficulty 전체 JAX화 아님)" 명시.
- **AC8** — 문서: jax-throughput.md(R5 update) + DESIGN §4 + CHANGELOG + INITIATIVE. broken-link 0.

## 후속

- **더 깊은 hard-benchmark**(별도, 본 task 밖). scripted resolution arms의 JAX화(arms가 env 내부 peek → 비자명, 후속).
- **커밋 단위**(feature/jax-difficulty-report): ① config factory(+무회귀) → ② 고-gym parity 테스트 → ③ jax_train config-aware+데모+문서.
