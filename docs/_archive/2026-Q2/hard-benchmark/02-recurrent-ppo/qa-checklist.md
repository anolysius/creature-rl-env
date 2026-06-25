# QA Checklist — recurrent-ppo (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ hard-benchmark #2 — "recurrence가 *PPO* headroom을 닫는가" (Q1 PPO와 #1 A2C 메모리 효과의 깨끗한 연결).
> ⚠ 정직성 불변식: 성공 = **correct 구현 + robust 측정 + 정직 보고**이지 "recurrence가 도움된다 확증"이 아니다.
> recurrence-helps(a)/neutral-reframe(b)/headroom-closes-사람보고(c) 셋 다 valid 결과.

## Acceptance Criteria (frozen at G1)

- [x] **AC1 (correctness 게이트)** ✅ — `test_jax_recurrent_ppo.py` 4 테스트 통과:
  `test_recurrent_ppo_rollout_replay_matches`(rollout logp/values == replay tol 1e-4) +
  `test_recurrent_replay_env_axis_permutation_invariant`(perm 불변 tol 1e-4) + loss finite + train smoke.
  시퀀스 보존 minibatch 결정론 입증.
- [x] **AC2 (학습)** ✅ — recurrent PPO `learning_verdict` branch "a"(곡선 상승), 공식 3 seed 모두 learns=True
  (feedforward PPO도 learns=True).
- [x] **AC3 (메모리 load-bearing under PPO)** ✅ → **branch (a) recurrence-helps-PPO robust**. 실측(CPU·3
  seed·250 iter·Q1 default config): ff PPO(h256) **0.46±0.08=24% of oracle(1.94)** vs rec PPO(GRU h128)
  **1.02±0.19=53%**, memory effect **+0.56 > max(std) 0.19**. rec 53% < 0.75·oracle(1.45) → **(c)
  headroom-CLOSES 미발동**(헤드라인 reframe 없음, 사람보고 stop 불요).
- [x] **AC4 (회귀 0)** ✅ — 추가만(기존 경로 byte-identical). 423→**427 passed**(+4), 2 skipped, exit 0.
  mypy 28 clean·ruff clean·build(1.0.0rc1 wheel) clean.
- [x] **AC5 (정직 경계 명시)** ✅ — jax-throughput.md Update(recurrent-ppo) + competitive-analysis gap
  register("robust learnability result" 행) + hard-benchmark INITIATIVE #2 행 갱신. 경계 라벨(PPO≠SOTA·
  CPU·3 seed·single config·param-match 아님·oracle proxy·A2C↔PPO config 다름→within-config gap만). CHANGELOG=task-end.
- [x] **AC6 (freeze 전 pilot 게이트)** ✅ — pilot(--quick 2 run ~23s): correctness 통과·rec PPO 학습
  (ff 11% vs rec 34%, +0.44>0.16)·timing 현실적(공식 3 run/250 iter ~108s). falsify 없음 → 공식 진행.

## L1 이력
- round 1: plan-reviewer **APPROVE**(5축) / qa-verifier **BLOCK**(AC2 learning_verdict 미정의) → BLOCKED.
- round 2 (selective): AC2를 사전약정 R1 정량 규칙으로 보강 → qa-verifier **APPROVE**. 2/2 APPROVE → APPROVED.

## 정직성 불변식
#1 recurrent-baseline 계승: correctness 먼저(망가진 recurrent=misleading "메모리 무용"), matched eval(가짜
effect 차단), single-run은 노이즈→multi-seed, non-vacuity(FF가 더 넓은데 floor면 이득=memory). 사전약정
결정규칙으로 사후 narrative 편향 차단. 결과값 아닌 correct+robust 측정+정직 보고로 freeze.
