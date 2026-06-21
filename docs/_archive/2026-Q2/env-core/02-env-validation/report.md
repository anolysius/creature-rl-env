---
slug: env-validation
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
---

# Report — env-validation (벤치마크 성립성 검증 레이어)

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약
`CritterEnv` 가 *RL 벤치마크로 성립하는가*를 재현 가능한 가드로 박았다. Gymnasium 표준 `check_env` 통과,
베이스라인 spread(random≪greedy), train/test held-out 일반화, throughput 을 모두 테스트·스크립트로
고정. 무거운 학습 deps(torch/sb3)는 core 에서 분리(`[rl]` extra). Acceptance 7/7, 18 tests green.

## 산출물
| 파일 | 내용 |
|---|---|
| `src/critter_gym/baselines.py` | `random_policy`(floor) + `greedy_policy`(chase+boustrophedon sweep, numpy only) |
| `src/critter_gym/__init__.py` | baselines export |
| `tests/test_compliance.py` | Gymnasium `check_env` 통과 |
| `tests/test_baselines.py` | 유효 행동 + spread 가드(target 비례 margin) |
| `tests/test_determinism.py` | 전체 trajectory 결정론 + 시드별 상이 |
| `tests/test_throughput.py` | steps/s 측정 + 보수적 floor(5k) 회귀 가드 |
| `scripts/benchmark.py` | held-out random/greedy 평균 + steps/s 리포트 CLI |
| `scripts/train_ppo.py` | (optional, `[rl]`) PPO 학습 데모 — 학습후>random+0.5 단언 |
| `pyproject.toml` | `[rl]` optional extra (stable-baselines3) |

## Acceptance 결과 (G1 freeze ↔ 실측, 1:1)
- ✅ AC1 Gymnasium 준수 — `check_env(skip_render_check=True)` 통과
- ✅ AC2 베이스라인 — `random_policy`/`greedy_policy` import + 유효 행동(0–5)
- ✅ AC3 spread 가드 — held-out(50000–50099): **random 0.38 < greedy 2.44 ≤ 3** (random>0, greedy>random, greedy≥0.5·target)
- ✅ AC4 일반화/결정론 — 동일 시드 전체 trajectory 동일, 시드별 상이, `benchmark.py` 재현
- ✅ AC5 throughput — `rate ≥ 5000` 단언 통과; **실측 ~266,000 steps/s/core** (DESIGN §4 목표 50k 의 ~5배 초과)
- ✅ AC6 PPO 데모 — `train_ppo.py`([rl]): **trained 2.90 ≥ random 1.49 + 0.5**, exit 0. 곡선: 8k→2.42, 16k→2.93, 24k→3.00, 40k→2.90. core deps 에 torch/sb3 불포함.
- ✅ AC7 툴체인 green — torch 없이 ruff ∧ mypy(5 files) ∧ pytest(18) ∧ build(sdist+wheel)

## 벤치마크 성립성 — 무엇이 증명됐나
- **준수**: 표준 `check_env` 통과 → RL 생태계 상호운용.
- **spread 존재**: random 0.38 ≪ greedy 2.44 → 자명하지도(random 이 max 아님), 불가능하지도(random>0) 않음.
- **학습 가능**: PPO 가 held-out 에서 random 대비 유의미 상승(1.49→2.90) → 보상 신호가 정책을 끌어올림.
- **일반화 측정**: 학습/평가 시드 분리(held-out 50000+) → 암기 아닌 일반 전략. 우리 moat 의 실측 장치.
- **빠름**: 266k steps/s/core (numpy, 미최적). JAX 포팅 전에도 목표 초과.

## L3 리뷰 반영
- @plan-reviewer SUGGEST(verification): spread margin 절대값 `+0.5` → target 비례(`greedy ≥ 0.5·target` + strict `greedy>random`)로 교체 — 환경 파라미터 변경 시 flaky 방지.
- @qa-verifier: APPROVE (AC 7/7 수치 검산 정합).
- 비차단 관찰(후속 고려): greedy 바닥-우측 코너 stuck 가능성(환경 boundary 처리 의존), `train_ppo.py` 학습 중 env 시드 미고정(데모 수준 허용).

## 후속 seed
- `env-core/subgoal-chain` — evolve/gym boss verifiable subgoal (DESIGN §3.5). 본 가드들이 회귀 방지.
- `env-core/procgen-typechart` — 시드별 type 매트릭스 (DESIGN §3.1).
- `perf/jax-hotpath` — JAX 포팅, throughput 가드가 회귀 감지 (DESIGN §4).
- greedy 코너 stuck 견고화 / train_ppo 학습 시드 고정 (소규모 후속).
