# QA Checklist — jax-ppo-tuned (G1 freeze)

> Frozen: 2026-06-25. Mode: standard.

## 사전약정 결정규칙 (데이터 보기 전 고정 — p-hacking 차단)

- **R1 (학습)**: `learning_verdict` — `mean_late − mean_early ≥ std_late` → "학습".
- **R2 (PPO ≥ A2C)**: 동일 config·예산서 tuned PPO held-out eval ≥ A2C-lite eval → "개선".
- **R3 (headroom, held-out gym-clear 기준, 고정 임계)**:
  - `PPO ≤ 0.75 × oracle` → **"hard-and-learnable (headroom 큼)"** (PPO가 oracle의 75% 미만).
  - `PPO ≥ 0.75 × oracle` → **"PPO가 거의 닫음 (덜 hard)"** → 방향 reframe·정지 보고.
  - (oracle = `measure_learnability` held-out gym-clear mean, scripted ceiling proxy.)

## Acceptance (frozen → 결과)

- [x] AC1 ✅: proper PPO(`PPOConfig`+`train_ppo`: GAE(λ)+bootstrap+clipped surrogate+adv-norm+K-epoch minibatch, jit+vmap). smoke 곡선 상승(R1 branch a).
- [x] AC2 ✅: `gae` 순수함수 + property 3종(numpy ref·γ1λ1↔MC·λ0↔1-step TD) + `evaluate_gym_clears`(∈[0,num_gyms]).
- [x] AC3 ✅: default PPO 0.59=oracle 1.84의 32% / hard PPO 1.06=oracle 7.28의 15%, held-in/out gap + oracle headroom(R3 hard-and-learnable).
- [x] AC4 ✅: R2 PPO≥A2C 양 config(default 2.53 vs 0.78 / hard 2.56 vs 1.88).
- [x] AC5 ✅: 365 passed(360+5), A2C/jax_env 무변경.
- [x] AC6 ✅: CPU·single·작은 net·oracle proxy·이 예산 한정·gym-clear vs return 구분 라벨(docs).
- [x] AC7 ✅: pilot이 gae property·PPO 학습·headroom 파이프라인 입증 + R1/R2/R3 임계 고정. falsify 0.
- [x] AC8 ✅: mypy(27)/ruff/pytest(365)/build clean + 문서(jax-throughput.md·DESIGN·competitive-analysis·INITIATIVE) + CHANGELOG(task-end).

## Default pass-criteria
- [ ] 신규 코드 테스트 동반(TDD). L3 APPROVED. feature→PR.
