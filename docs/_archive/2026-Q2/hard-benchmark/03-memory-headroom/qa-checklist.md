# QA Checklist — memory-headroom (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ hard-benchmark #3 — "env가 *강한 메모리 agent(recurrent PPO)에게도* hard한가" (절대 난이도).
> ⚠ 성공 = correct(parity 0) + robust 측정 + 정직 보고. (a)hard-for-memory / (b)memory-closes-reframe(사람보고)
> / inconclusive 셋 다 valid.

## Acceptance Criteria (frozen at G1)

- [x] **AC1 (parity 게이트)** ✅ — `test_jax_hard_config_parity.py` grid16/5gym/420st/patch2서 **parity 0
  mismatch**(13 obs key + reward + term + trunc, random[5 seed] + gym-clearing[6] + held-out[2] policy).
  oracle(numpy)=agent(JAX) byte-identical env 입증.
- [x] **AC2 (learnable + winnable)** ✅ — oracle 4.69 ≥ 0.5·5=2.5 (winnable) AND recurrent PPO learns=True
  (R1 branch "a", 5 seed 다수).
- [x] **AC3 (frozen 3-branch 분류)** ✅ → **(a) hard-for-memory-agent ROBUST**. classify_headroom(frac=0.75,
  k=1.0, freeze 시 고정): recurrent PPO 5 seed 2.01±1.05, opt-bound mean+std **3.06 ≤ 0.75·oracle 3.52**
  → `hard-and-learnable`. **(b) ppo-closes 미발동**(헤드라인 reframe 없음·사람보고 불요). secondary:
  rec−ff +1.49(≈4× ff) → 메모리 여전히 load-bearing.
- [x] **AC4 (회귀 0)** ✅ — 추가만(`hard_env_spec` + 기존 byte-identical). 427→**442 passed**(+15), 2 skipped,
  exit 0. mypy 28 clean·ruff clean·build(1.0.0rc1) clean.
- [x] **AC5 (정직 경계 명시)** ✅ — jax-throughput.md Update(memory-headroom) + competitive-analysis(gap
  register "a hard benchmark" + matrix "Difficulty(absolute)" ❌→◐) + INITIATIVE #3. 경계 라벨(recurrent
  PPO≠SOTA·CPU·5 seed 고분산 std1.05·grid16 단일·oracle proxy·param-match 아님). CHANGELOG=task-end.
- [x] **AC6 (freeze 전 pilot 게이트)** ✅ — pilot(--quick 2 run ~27s): parity 0·recurrent PPO 학습(24%)·
  oracle winnable·headroom 큼·timing 현실적. falsify 없음 → 공식 진행. **3 seed 경계선(52%±0.97, opt-bound
  3.41 vs 3.52)→5 seed(43%±1.05, opt-bound 3.06)로 robust 굳힘**(multi-seed 교정 문화).

## L1 이력
- round 1: plan-reviewer **SUGGEST**(커밋 경계 명시) / qa-verifier **BLOCK**(AC3 conditional·AC6 pilot) → BLOCKED.
- round 2 (selective): AC3를 frozen 3-branch 분류로·AC6를 표준 lifecycle step으로 명시 + 커밋 경계 흡수 +
  AC4 "427 passing" 명확화 → qa-verifier **APPROVE**. plan-reviewer SUGGEST 흡수 → APPROVED.

## 정직성 불변식
#1·#2 계승: parity 0(oracle=numpy·agent=JAX 같은 env), 사전약정 규칙(데이터 전 고정), multi-seed(single-run
노이즈 4회 교정 문화), non-vacuity/secondary 구분. 헤드라인보다 정직성 — (b) reframe도 숨기지 않고 사람 보고.
