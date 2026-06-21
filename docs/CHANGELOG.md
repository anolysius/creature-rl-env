# Changelog

All notable task-level changes are appended here by `/task-end` (one line per task).

## env-core
- **2026-06-21** — `env-validation` (standard): 벤치마크 성립성 검증 레이어 — Gymnasium `check_env` 통과 + 베이스라인 spread(random 0.38 ≪ greedy 2.44) + train/test held-out 일반화 + throughput 회귀 가드(실측 ~266k steps/s/core, 목표 50k의 5배). `random_policy`/`greedy_policy` 패키지 동봉, PPO 학습 데모(`[rl]` extra, trained 2.90 vs random 1.49). 무거운 deps는 core에서 분리. Acceptance 7/7, 18 tests green. _(commit pending)_
- **2026-06-21** — `scaffolding` (standard): CritterGym 제품 코드 첫 줄 — `src/critter_gym/` src-layout 패키지 + hatchling 빌드 + ruff/mypy/pytest 툴체인 + 10×10 catch-only `CritterEnv` (Gymnasium API, seeded 결정론, RLVR boolean subgoal 리워드, `gymnasium.make("CritterGym-v0")` 등록). Acceptance 8/8, 12 tests green, HARNESS-PORT-MANIFEST §(c) 커플링 #1–#4 정합 확정. _(commit pending)_

