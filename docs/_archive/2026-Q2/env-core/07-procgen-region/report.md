---
slug: procgen-region
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
milestone: M2
exit_criteria: [M2-EC1]
---

# Report — procgen-region (시드→절차 region + train/test split) · M2-EC1 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약
**우리 moat 의 첫 벽돌.** 시드가 region 내용(creature 수·위치, gym 수·위치·보스 타입)을 절차 생성하도록
명시적 순수 생성기로 구조화하고, **train / held-out(test) 시드를 구조적으로 분리**해 일반화 측정의 토대를
마련했다. `CritterGym-procgen-v0` 등록. Acceptance 8/8, **64 tests green**, check_env(fixed+procgen) 통과.

## 산출물
| 파일 | 변경 | 내용 |
|---|---|---|
| `src/critter_gym/region.py` | 신규 | `Region` + `generate_region(seed,vary)` 순수 생성기 + `train_seeds`/`heldout_seeds`/`is_held_out` |
| `src/critter_gym/party.py` | 갱신 | `gym_boss(boss_type, index)` 타입 기반 |
| `src/critter_gym/envs/critter_env.py` | 갱신 | reset→generate_region 위임, `vary` 플래그, gym 보스 타입 보관, 종료 가드 len 기반, 무시드 reset split-safe |
| `src/critter_gym/registration.py` | 갱신 | `CritterGym-procgen-v0` (vary=True) 등록 |
| `tests/test_region.py` | 신규 | 생성기 결정론·변주·split disjoint·overrun·무누수 (6) |
| `tests/test_gym_battle.py` | 갱신 | procgen 통합·등록·결정론·M1 보존 (4) |

## Acceptance 결과 (G1 freeze ↔ 실측, 1:1)
- ✅ AC1 생성기 결정론 — 동일 시드 동일 Region; 위치 grid내·disjoint
- ✅ AC2 시드별 변주 — vary 에서 gym수{1,2,3}·creature수{1,3,4,5}·15 distinct boss-seq; min gym≥1
- ✅ AC3 env 위임 + 무회귀 + 종료계약 — reset→generate_region; vary=False 기존 54 green; vary 항상 gym≥1
- ✅ AC4 train/test split + overrun 가드 — disjoint, `train_seeds` overrun→ValueError, region 무누수
- ✅ AC5 procgen 등록 + 준수 — `make("CritterGym-procgen-v0")` vary=True; check_env; obs∈space train∧held-out
- ✅ AC6 결정론 보존 — 동일 시드+행동 → 동일 trajectory (fixed·procgen 양 모드)
- ✅ AC7 M1 동작 보존 — procgen region 에서 배틀·gym격파·진화; scripted 가 procgen 시드 ≥1 gym 격파
- ✅ AC8 툴체인 — ruff∧mypy(10)∧pytest(64)∧build∧check_env(fixed+procgen); 기존 54 회귀 0

## 설계 메모 (후속 인계)
- **obs 형태 불변(Procgen 관례)**: grid_size 고정, 시드는 *내용*만 변주, obs 경계=max(num_creatures/num_gyms) → 모든 시드 obs∈space.
- **순수 생성기**: `generate_region(seed)` 는 `default_rng(seed)` 로 자기완결 — 동일 시드 동일 region. (env 의 `self.np_random` 과 분리 — reproducibility 명확.)
- **split**: `TEST_SEED_OFFSET=1_000_000`. train=[0,offset), test=[offset,…). `train_seeds(start+n>offset)`→ValueError(누수 가드).
- **split-safe 무시드 reset (L3 SUGGEST 흡수)**: `reset(seed=None)` 은 파생 시드를 `[0, TEST_SEED_OFFSET)` 로 클램프 → 무시드 실행이 held-out 월드를 우연히 뽑지 못함.
- **vary=False 기본 = 무회귀**: `CritterGym-v0` 는 M1 고정월드 그대로; `CritterGym-procgen-v0` 가 절차 변형.

## L3 리뷰 반영
- @plan-reviewer (Opus): SUGGEST(determinism) — 무시드 reset 이 held-out 시드를 뽑아 split 누수 가능 → 파생 시드를 TEST_SEED_OFFSET 미만으로 클램프(split-safe). 반영.
- @qa-verifier: APPROVE — AC 8/8 정합, 회귀 0, moat 불변식(분리·결정론·obs 일관) 성립.

## 마일스톤 M2 진행
- [x] **M2-EC1** 시드→절차 region + train/test 분리 ← 본 task
- [ ] M2-EC2 절차 *타입표* (infer-the-meta) — `procgen-typechart`
- [ ] M2-EC3 train/test 누수 0 + held-out 새 맵·타입표 (EC1 이 region 절반 — 타입표는 EC2)
- [ ] M2-EC4 PPO train-vs-test 갭 측정·리포트 — `generalization-harness`

## 후속
- 다음 권장: `procgen-typechart`(M2-EC2 — 시드별 내부정합 타입표, infer-the-meta; 진짜 암기 불가의 핵심).
- 그 후 `generalization-harness`(M2-EC4 — PPO train/test 갭, 킬러 데모 토대).
- region 변주 축 확장(biome·spawn 밀도·escalating 난이도)은 후속 튜닝.
