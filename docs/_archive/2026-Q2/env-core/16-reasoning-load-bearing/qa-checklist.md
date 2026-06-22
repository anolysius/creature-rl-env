# QA Checklist — reasoning-load-bearing (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK (scope creep 방지).

## Acceptance Criteria (frozen at G1)

- [x] **AC1** ✅ — `Battle(commit_mode=True)` (battle.py): switch no-op + faint=즉시패배(force-switch off).
  단위 테스트 3건(`test_commit_mode_*`). M1 배틀 불변(기본 off; `test_battle` 42 passed, force-switch 회귀 포함).
- [x] **AC2** ✅ — `TypeChart.super_mult` + `generate_typechart`/`generate_region`/env 스레딩; `gym_boss(hp/atk/df)`
  보스 strength; env `super_mult/boss_*/commit_battles` 파라미터; `CritterGym-commit-v0` 등록. winnability 필터
  재사용. 테스트 5건(super_mult 2 + env knob 3).
- [x] **AC3** ✅ — `tests/test_reasoning_gate.py`: 42 고정 시드(`range(1000,1042)`), product 엔진(commit_mode).
  **Gate 0 = 0.479 ≥ 0.2** (oracle 1.000 / type_blind 0.521), **Gate 1 = 0.363 ≥ 0.1** (infer 0.836 / probe 0.473).
  4 arm 평균 출력. pilot(0.48/0.36) 재현. 4 테스트 통과.
- [x] **AC4** ✅ — M1 무회귀 42 passed(`test_battle`/`test_gym_battle`/`test_determinism`/`test_compliance`/`test_types`).
  `check_env` ×3(fixed/procgen-v0/commit-v0) OK. train≠held-out 누수 0(`test_train_and_heldout_charts_differ_no_leak`).
  baseline 128 → 140 (신규 12건만 증가, 2 skipped 동일).
- [x] **AC5** ✅ — DESIGN §3.1.1 재작성("team-commit 으로 scripted-arm 실증; 학습 정책의 *학습* 은 follow-up").
  honesty 가드 재정의(`test_source_does_not_overclaim_learned_inference`): learnability 과대표현 차단 +
  "load-bearing"엔 scripted/follow-up 캐비엣 강제. types/region/registration 통과.
- [x] **AC6** ✅ — `mypy src` clean(16 files) · `ruff check .` clean · `pytest` 140 passed/2 skipped · `build` OK.

## L1 이력
- round 1: plan-reviewer(opus) SUGGEST(verification: 시드 고정+margin 명시) / qa-verifier APPROVE → SUGGEST_CUTOFF.
- SUGGEST 흡수: AC3 에 고정 시드 집합 + pilot margin 통과여유 명시 후 G1 진입.
- **G1 GO (2026-06-22)**: 사용자 승인 → acceptance_freeze:true. 이후 AC 추가 금지.
