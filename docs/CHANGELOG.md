# Changelog

All notable task-level changes are appended here by `/task-end` (one line per task).

## env-core
- **2026-06-21** — `gym-boss-progression` (standard, **M1-EC3/EC4**): 배틀 엔진을 `CritterEnv.step`에 연결 — 월드 gym=gated checkpoint, OVERWORLD↔BATTLE 모드 머신, 보스 격파=boolean subgoal 리워드(+1, RLVR). obs 확장(in_battle+양측 active hp·type+gyms_defeated), action_space Discrete(6) 모드별 재해석. 종료 진화(catch 비종료, 전 gym 격파→terminated). 처음으로 "탐험→배틀→보스 격파"가 한 에피소드에서 동작(scripted seed3 2 gym 격파 14스텝). Acceptance 9/9, 45 tests green, check_env 통과, 회귀 0. _(commit pending)_
- **2026-06-21** — `battle-system` (standard, **M1-EC1**): 턴제 배틀 sub-MDP 엔진 — 고정 타입표(rock-paper-scissors) + 타입 상성 데미지 + 스위치 + 아이템(potion) + scripted 상대. 완전 결정론(랜덤 없음, RLVR/재현성). `types.py`/`creatures.py`/`battle.py` 독립 모듈(env 통합은 M1-EC3). Acceptance 9/9, 35 tests green. 활성 마일스톤 M1 첫 EC 충족. _(commit pending)_
- **2026-06-21** — `product-roadmap` (standard, docs-only): 제품 마일스톤 SSOT 신설 — `docs/reference/milestones.md`(M0–M5 goal·exit criteria·구성 task·DESIGN 매핑) + `docs/explanation/roadmap.md`(순서 근거·킬러 데모·master-plan↔roadmap 구분). "매 task 는 활성 마일스톤의 미충족 EC 에서 내려온다" 규율을 CLAUDE.md(auto-load)에 hook-up. 즉흥적 task 생성 차단. Acceptance 7/7, broken-link 0. _(commit pending)_
- **2026-06-21** — `env-validation` (standard): 벤치마크 성립성 검증 레이어 — Gymnasium `check_env` 통과 + 베이스라인 spread(random 0.38 ≪ greedy 2.44) + train/test held-out 일반화 + throughput 회귀 가드(실측 ~266k steps/s/core, 목표 50k의 5배). `random_policy`/`greedy_policy` 패키지 동봉, PPO 학습 데모(`[rl]` extra, trained 2.90 vs random 1.49). 무거운 deps는 core에서 분리. Acceptance 7/7, 18 tests green. _(commit pending)_
- **2026-06-21** — `scaffolding` (standard): CritterGym 제품 코드 첫 줄 — `src/critter_gym/` src-layout 패키지 + hatchling 빌드 + ruff/mypy/pytest 툴체인 + 10×10 catch-only `CritterEnv` (Gymnasium API, seeded 결정론, RLVR boolean subgoal 리워드, `gymnasium.make("CritterGym-v0")` 등록). Acceptance 8/8, 12 tests green, HARNESS-PORT-MANIFEST §(c) 커플링 #1–#4 정합 확정. _(commit pending)_

