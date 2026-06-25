---
slug: recurrent-baseline
initiative: hard-benchmark
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md           # memory load-bearing Update + Q1 보정
  - docs/explanation/competitive-analysis.md      # gap register "a hard benchmark" 보정
  - docs/_active/difficulty-scaling/INITIATIVE.md  # Q1(headroom-baseline-strength) 정직 보정
changelog_entry: docs/CHANGELOG.md
---

# 메모리는 load-bearing인가 — 결과 보고서 (hard-benchmark #1)

## 요약 (수치 표)

연구 질문: 부분관측(작은 시야) 하에서 **메모리 있는(recurrent) agent가 메모리 없는(feedforward) agent보다
본질적으로 잘하는가** = 메모리가 load-bearing인가? **답 = YES, robust.**

부분관측 commit world (grid 10, **5×5 egocentric view**, 3 gyms, A2C, 3 seed, matched greedy eval):

| arch | held-out gym-clears | % of oracle |
|---|---|---|
| feedforward A2C (h256) | 0.50 ± 0.14 | 18% |
| **recurrent A2C (GRU h128)** | **1.29 ± 0.33** | **46%** |
| oracle / type_blind | 2.81 / 1.06 | — |

**memory effect = rec − ff = +0.79**, vs max(std) 0.33 → **robust 분리 → 메모리 LOAD-BEARING.**
recurrent net이 *더 좁은데도*(h128 < ff h256) ~2.5× → 이득은 **recurrence(메모리)이지 capacity 아님**.

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 사전약정 판정 (rec−ff > max std) | ✅ | +0.79 > 0.33 → LOAD-BEARING (3 seed, oracle 대비 % 보고) |
| AC2 non-vacuity / correctness | ✅ | recurrent 학습 curve 상승(pilot/test) + feedforward와 **동일 eval 경로**(`evaluate_gym_clears` vs `evaluate_gym_clears_recurrent` 동일 protocol: argmax greedy·no reset·gyms_defeated) |
| AC3 무회귀 + feedforward byte-identical | ✅ | recurrent=추가 API만, feedforward `init_params`/`apply_policy`/`train`/`train_ppo`/`evaluate_gym_clears` 무변경. 419→**423**(+4) |
| AC4 G2 | ✅ | mypy(28)·ruff·pytest exit=0·build 1.0.0rc1 |
| AC5 정직 보고 + Q1 보정 | ✅ | jax-throughput.md Update + Q1 "robust headroom" 보정(robust=feedforward 한정, recurrence가 부분관측 headroom 크게 회복 18%→46%, 단 46%서 잔존). 한계 명시 |

## 핵심 결과 + Q1 정직 보정

**메모리는 CritterGym의 부분관측 하에서 robust하게 load-bearing이다.** 이는 두 가지를 의미:

1. **벤치마크 변별력**: env가 메모리 있는/없는 agent를 선명히 가른다(18% vs 46%) — 좋은 벤치마크 성질.
2. **Q1(headroom-baseline-strength) 헤드라인 정직 보정**: Q1은 "headroom이 *cheap feedforward 스케일링*에
   robust"를 입증하며 **"recurrent 미배제"**를 명시 caveat로 남겼다. 본 task가 그 축을 직접 측정 →
   **headroom의 상당 부분은 *메모리 없음* 한계였고, recurrence가 그걸 크게 회복**(feedforward 18% → recurrent
   46% of oracle). 따라서 정확한 그림은 *"절대적으로 hard"*가 아니라 **"메모리를 요구하는 부분관측 과제이고,
   메모리 agent가 절반쯤(46%) 회복하나 oracle엔 못 닿는다(headroom 잔존)"**.

## 정직한 경계 (과대 금지)

- **A2C 한정** — recurrent PPO 아님. Q1은 PPO였으므로 *"recurrent가 Q1의 PPO headroom을 닫는다"*는 깨끗한
  연결은 **recurrent PPO**(sequence-preserving minibatch, 고난도 구현)로 재봐야 확정. 본 결과는 *A2C 내*
  memory effect(+ feedforward PPO 대비 정성적 시사).
- recurrent도 **46%에서 멈춤** → "풀림/이미 hard" 아님. 의미 있는 headroom 잔존.
- 3 seed·CPU·단일 partial-obs config(grid10/patch2/min_gyms=3)·param-match 아님(FF가 더 넓음=이득이 memory
  임을 보강)·oracle=scripted proxy.
- 부분관측 scout가 grid16(더 큰 지도)은 A2C 학습 불가로 inconclusive였음 — grid10/patch2가 측정 가능한 sweet spot.

## 변경 파일 상세

**수정**
- `src/critter_gym/jax_train.py` (+~200): 신규 recurrent API(`gru_init_params`/`gru_step`/
  `recurrent_policy_value`/`make_recurrent_rollout`/`recurrent_a2c_loss`/`train_recurrent`/
  `evaluate_gym_clears_recurrent`). feedforward 경로 **전부 무변경**.

**신규**
- `scripts/recurrent_baseline.py`: 부분관측 config서 ff vs rec A2C 측정 + 사전약정 판정(matched eval).
- `tests/test_jax_recurrent.py` (+4): GRU shape/loss-finite/train smoke/eval-range.

**문서**: jax-throughput.md(memory Update) + competitive-analysis(gap register 보정) + difficulty-scaling
INITIATIVE(Q1 보정).

## 타입 체크 / 빌드 결과

- mypy 0 err(28). ruff clean. pytest exit=0(423 passed, 2 skipped). build 1.0.0rc1.
- 측정: `scripts/recurrent_baseline.py --runs 3` (재현). freeze 전 pilot(verify_recurrent, 3 seed matched)이
  동일 verdict(load-bearing) 입증.
