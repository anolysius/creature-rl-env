# QA Checklist — learnability-measurement (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK (scope creep 방지).

## Acceptance Criteria (frozen at G1)

- [x] **AC1** ✅ — `_commit_window`(critter_env): action 4 cycle(배틀 턴 미소모·보스 미공격) + 첫 move lock.
  enemy_type 관측. `test_champion_action.py` 5건(cycle/lock/관측/비-commit 무회귀/check_env). M1 obs 무변경(phase 플래그 불요).
- [x] **AC2** ✅ — `critter_gym.learnability`(numpy-only): reference arm 4종(env-aware) + `measure_learnability` +
  split 가드. `test_infer_beats_probe_through_the_action_ux`로 액션 UX 경유 infer>probe 재현(oracle≥infer>probe).
- [x] **AC3** ✅ — `scripts/learnability.py`(`[rl]`): `train_and_measure` PPO→대조 리포트. `test_ppo_learnability_smoke`
  (importorskip, 256 steps) CI 통과.
- [x] **AC4** ✅ — PPO **100k** 실행(commit-v0 grid5/3gym): learned held-out **4.00** ≫ type_blind 1.88·probe 1.56,
  infer-ref 3.25 수준 이상 → **양성 learnability 신호**. DESIGN §3.1.1 follow-up 갱신(caveat: return=격파+진화 합산 노이즈/단일run/N16).
- [x] **AC5** ✅ — M1·procgen·commit-v0 무회귀(48 passed + check_env ×3) + honesty 가드 무회귀. baseline 140→151(신규11).
- [x] **AC6** ✅ — `mypy src`(17) clean · `ruff` clean · `pytest` 151 passed/2 skipped · `build` OK. core numpy-only.

## L1 이력
- round 1: plan-reviewer(opus, verdict-first) APPROVE / qa-verifier APPROVE → **APPROVED**.
- soft 흡수: AC4 에 정량 컷오프(100k / N20·N20 고정시드) 명시 후 G1 진입.

## 정직성 불변식 (이 task 의 핵심)
acceptance 는 *성능 결과* 가 아니라 *하네스·측정·정직보고* 를 freeze. PPO 가 infer 도달=（A) learnability 완성 /
미달=「구조는 추론 허용, X budget PPO 는 미학습 → Y 필요」라는 정직한 결과. 둘 다 통과. (typechart-depth/§4 교훈.)
