---
slug: difficulty-dynamic-range
initiative: difficulty-scaling
status: completed
ended: 2026-06-24
supersedes: [discriminating-difficulty]
extracted_to:
  - DESIGN.md                                  # §3.1.1 "Discrimination resolution" 문단 + pilot 발견
  - docs/explanation/competitive-analysis.md   # "a hard benchmark" 갭 register 행
  - docs/_active/difficulty-scaling/INITIATIVE.md  # task 2 행 + pilot 발견 박제
changelog_entry: docs/CHANGELOG.md (difficulty-scaling 섹션)
---

# difficulty-dynamic-range — 결과 보고서

## 한 문단 요약 (수식 없이)

직전 아이디어("플레이어 카드를 다양하게 줘서 변별")는 freeze 전 pilot이 **틀렸다고 밝혀줬습니다** — 가위바위보 구조상 고정 카드 하나가 우연히 절반을 이겨 소용이 없었고, 사실 똑똑/멍청 플레이는 *이미* 점수가 갈리고 있었습니다. 진짜 문제는 "한 판의 도장이 평균 2개뿐"이라 점수 범위가 좁다는 것. 그래서 **도장 수를 늘려 점수 범위를 넓혔더니**, 잘하는 플레이(oracle)와 못하는 플레이(blind)의 점수차가 **1.3 → 4.9로 또렷하게 벌어졌습니다**(도장 8개 기준). 그러면서도 "외운 게 아니라 일반화한다"(gap≈0)는 성질은 유지됐고, 학습한 AI는 아직 oracle(7)보다 한참 낮은 1.7이라 **앞으로 실력을 가를 여지가 큽니다.** "AI가 아예 못 푸는 초고난도"는 훨씬 큰 일이라 정직하게 다음 과제로 남겼습니다.

## 요약 (수치)

| 측정 | 결과 | 비고 |
|---|---|---|
| 변별 분해능 (oracle−type_blind spread) | **+1.31(3 gym) → +2.56(5) → +4.88(8)** 단조↑ | scripted, held-out, gym-clear-only |
| winnability (oracle/num_gyms @8) | **0.88** (≥0.70 ✓) | 스케일에서 천장 유지 |
| 사전약정 verdict | **`resolution-up`** | spread@8≥2.0 ✓ · 단조 ✓ · win≥0.70 ✓ |
| 학습 gap @8 (PPO 60k, 3run) | held-in 1.67 / held-out 1.85 / **gap −0.19±0.60 = `gap≈0-signal`** | 분해능↑하며 일반화 유지 |
| headroom | PPO 1.67 ≪ oracle 7.06 | 변별 여지 큼(미래 hard-benchmark) |
| 테스트 | 287 → **294** (+7, 회귀 0) | min_gyms 기본 None 무회귀 |
| canonical | mypy(26)/ruff/build clean | |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 region min_gyms | ✅ | `generate_region(...,min_gyms=None)` floor/exact, 명시 시만 검증, 재출현 pool 보존. |
| AC2 env config | ✅ | `CritterEnv(min_gyms=None)` opt-in → generate_region 전달. 기본 None 무회귀. |
| AC3 측정 코드 | ✅ | `discrimination_resolution`/`classify_resolution`/`_main_resolution`/`_main_range_gap`. |
| AC4 정직 보고 | ✅ | DESIGN/competitive-analysis: resolution-up + gap≈0 + **"PPO 못 푸는 hard-benchmark 범위 밖" 명시** + 직전 pilot falsify 박제. |
| AC5 테스트 | ✅ | 7 numpy-only(min_gyms 정확/범위/검증/무회귀 byte-identical / 변별 property / winnability / classify_resolution 단위). |
| AC6 CI 불변 | ✅ | 294 passed/2 skipped(회귀 0), jax not in core, canonical clean. |
| AC7 pilot | ✅ | freeze 전 R1(분해능)·R2(winnability)·R3(재출현=pool 보존) 측정 → 사전약정 `resolution-up` 기계적 확정. |
| AC8 문서 | ✅ | DESIGN §3.1.1 + competitive-analysis + INITIATIVE + CHANGELOG(task-end). JAX 후속(R5) 명시. broken-link 0. |

## 변경 파일 상세

**수정**
- `src/critter_gym/region.py` — `generate_region(..., min_gyms=None)`: vary 시 gym-count floor/exact. 기본 None=`_MIN_GYMS`(byte-identical 무회귀, 명시 시만 검증). 재출현 pool 보존.
- `src/critter_gym/envs/critter_env.py` — `min_gyms` opt-in config → generate_region.
- `scripts/difficulty_generalization.py` — `DISCRIM_BASE`/`DISCRIM_GYMS` + `ResolutionRow`/`discrimination_resolution`/`classify_resolution`(사전약정) + `--resolution`(scripted, numpy) + `--range-gap`(학습 gap).

**신규**
- `tests/test_difficulty_dynamic_range.py` (7 tests, numpy-only).

**문서**: DESIGN §3.1.1(Discrimination resolution 문단 + pilot 발견) · competitive-analysis(a hard benchmark 행) · INITIATIVE(task 2 + pilot 박제) · CHANGELOG.

## 발견된 이슈 / 정직한 한계

- **pilot이 원래 메커닉(스타터 다양화)을 falsify** — 정직 reframe(동적 범위로 피벗). 직전 `discriminating-difficulty` slug는 미구현 정리, 발견은 박제. *bounded-YOLO 중에도 정지조건(pilot falsify) 발동 → 사용자에 보고 후 재설계.*
- **분해능 ≠ 절대 난이도** — 본 task는 변별 *분해능*(점수 범위)을 키운 것이지 "PPO가 oracle에 못 닿는 hard-benchmark"가 아님(명시적 범위 밖, future work).
- **infer ≈ oracle** (한 번 보면 추론 자명) — 이 메트릭만으로 inference 단독 load-bearing 증명 아님(scripted gate 몫).
- scripted 측정·학습 gap single-config·N=16·multi-run(3) — 신호. 회귀 가드: min_gyms=None byte-identical.
- **JAX 무변경** — `jax_env`/`jax_train`은 3-gym 하드코딩, 본 task 미반영 → 후속 `jax-difficulty-report`(R5).

## 흡수처 (extracted_to)

| 정보 | 흡수처 |
|---|---|
| pilot 발견(다양화 falsify) + 동적 범위 resolution 결과 | DESIGN §3.1.1 "Discrimination resolution" 문단 |
| "a hard benchmark" 비교우위 진전 + 한계 | competitive-analysis 갭 register |
| 사전약정 resolution 규칙 | 코드 `classify_resolution` (SSOT) + plan/qa-checklist |

ADR 가치: 없음(기존 difficulty-scaling narrative + 코드로 충분).

## 검증 결과
mypy clean(26) · ruff clean · pytest 294 passed/2 skipped(회귀 0) · build OK · AC6 jax not in core. L3 2/2 APPROVED(plan-reviewer 코드 정합성 + qa-verifier).
