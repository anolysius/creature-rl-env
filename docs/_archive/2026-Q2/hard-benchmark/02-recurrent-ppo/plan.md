---
slug: recurrent-ppo
initiative: hard-benchmark
status: active
started: 2026-06-25
acceptance_freeze: true
domains: [rl-env]
mode: standard
task_type: general
scope_paths:
  - src/critter_gym/jax_train.py
  - tests/test_jax_recurrent_ppo.py
  - scripts/recurrent_ppo_baseline.py
extracted_to: []
supersedes: []
---

# Recurrent PPO — does memory close the *PPO* headroom under partial observability? (hard-benchmark #2)

> 작성일: 2026-06-25 | 상태: 계획

## 목표

`recurrent-baseline`(hard-benchmark #1)은 **A2C 안에서만** 메모리 load-bearing을 보였다(부분관측
5×5 view·grid10서 feedforward A2C 18% vs recurrent GRU A2C 46% of oracle). 그러나 Q1
(`headroom-baseline-strength`)의 headroom 진단은 **PPO**로 측정됐다. 둘 사이에 깨끗한 연결이 없다 —
"recurrence가 *PPO* headroom을 닫는가"는 미확정(initiative 핵심 질문 #1의 PPO 버전).

본 task = **동일 부분관측 config(Q1의 `default` config = grid10·5×5 view·3 gyms·num_types 8)**에서
**recurrent PPO vs feedforward PPO**를 같은 matched greedy-eval yardstick으로 대조해, A2C에서 본
메모리 효과가 더 강한 PPO 알고리즘에서도 robust하게 재현되는지 확정한다.

**고난도 핵심**: PPO는 minibatch를 위해 `(T,B)`를 평탄화하고 **시간축까지 셔플**한다(현 `train_ppo`
line 519–528). 이는 recurrence를 깬다(hidden state는 순서 의존). → **sequence-preserving
minibatch**: 시간축(T)은 보존하고 **env축(B)만 셔플**, 각 minibatch에서 저장된 `h0[env]`로부터 GRU를
시퀀스 재생(done시 reset)해 logits/values를 복원 → clipped surrogate. (A2C는 full-rollout이라 셔플이
없어 쉬웠지만 PPO는 이 분리가 필수.)

**correctness 먼저**(initiative 정직성 문화·mandate): 망가진 recurrent PPO는 "메모리 무용"이라는
misleading 결론을 낳는다. 비교를 신뢰하기 **전에** 구현 정합성을 결정론적으로 입증한다(아래 AC1).

## 선행 조건

- `recurrent-baseline` done(#1): GRU 셀(`gru_init_params`/`gru_step`/`recurrent_policy_value`),
  recurrent rollout/eval(`make_recurrent_rollout`/`recurrent_a2c_loss`/`train_recurrent`/
  `evaluate_gym_clears_recurrent`)이 이미 존재 — 재사용 재료.
- `jax-ppo-tuned` done: `train_ppo`/`make_ppo_rollout`/`ppo_loss`/`gae`/`PPOConfig` 존재 — PPO 골격.
- `default_env_spec()`(grid10·patch_radius2·5×5·3gym·num_types8) = **부분관측** = recurrent-baseline의
  부분관측 world와 동일 = Q1 `default` config. (대조: `difficulty_env_spec()` hard config는 grid6에
  patch_radius5 → 11×11 patch>격자 = **완전관측** → 메모리 무용 예상 = 자연 control.)
- `[jax]`+`[rl]` extra (CI는 numpy-only `importorskip`).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/jax_train.py` | **추가만** (append, 파일 끝 recurrent 섹션 뒤) | 중 | feedforward·A2C·PPO·recurrent-A2C 경로 **전부 무변경** (byte-identical) — 기존 테스트 회귀 0 보장 |
| `tests/test_jax_recurrent_ppo.py` | 신규 | 저(test) | shape smoke + **correctness 결정론 테스트**(hidden replay 정합·env-축 permutation 불변) + train smoke |
| `scripts/recurrent_ppo_baseline.py` | 신규 | 저(script) | 부분관측 config서 ff PPO vs rec PPO matched eval + 사전약정 규칙 |

### 영향 범위 (import 그래프)

- `jax_train.py`는 `critter_gym.__init__`에서 import 안 됨(jax optional) → core/default test suite 무영향.
- 추가 심볼만 도입(`recurrent_ppo_loss`/`make_recurrent_ppo_rollout`/`train_recurrent_ppo`). 기존
  `train_ppo` 등 미변경 → `test_jax_ppo.py`/`test_jax_train.py`/`test_jax_recurrent.py` 회귀 0.

## Step별 계획

1. **(red)** `tests/test_jax_recurrent_ppo.py` 작성 — 신규 API 대상:
   - shape smoke: rollout이 `(T,B,...)` traj + `logp_old`/`values`/`last_value`/`h0` 반환.
   - **correctness-1 (hidden replay 정합)**: rollout이 수집한 per-step logits와 loss-replay가 재생한
     logits이 **동일**(tol). 시퀀스 보존 입증.
   - **correctness-2 (env-축 permutation 불변)**: B축을 임의 perm으로 minibatch해 `h0[perm]`로 재생한
     결과가 perm 안 한 재생을 동일 perm으로 정렬한 것과 **일치**. → 시간축 셔플 없음·env셔플 안전 입증.
   - train smoke: `train_recurrent_ppo` 짧은 run이 길이 맞는 finite curve 생성.
2. **(green)** `jax_train.py`에 추가:
   - `make_recurrent_ppo_rollout(init_state, env)` — `make_ppo_rollout` + GRU hidden 스레딩
     (`make_recurrent_rollout` 패턴). 반환: `(state, h, traj, last_value)` where
     traj=`(flat, actions, logp_old, values, rewards, dones)`, **+ rollout 시작 시 사용한 `h0` 노출**.
   - `recurrent_ppo_loss(params, flat_mb, actions_mb, logp_old_mb, adv_mb, returns_mb, dones_mb, h0_mb,
     clip, ent_coef, vf_coef)` — `(T, B_mb)` 미니배치에서 `h0_mb`로 GRU 시퀀스 재생(done reset) →
     clipped surrogate + value MSE − entropy(`ppo_loss` 형태, recurrent 재생만 추가).
   - `train_recurrent_ppo(seeds, PPOConfig, *, seed, spec)` — 매 iter: rollout → `gae`(기존 재사용,
     `(T,B)` last_value bootstrap) → epochs × (B축 perm으로 num_minibatches 분할; **T축 보존**) 업데이트.
     eval은 기존 `evaluate_gym_clears_recurrent` 재사용(matched).
3. **(verify)** mypy·ruff·pytest·build. feedforward/A2C/PPO 경로 byte-identical 재확인.
4. **pilot(freeze 전)**: 부분관측 default config 3-seed matched로 ff PPO vs rec PPO 예비 측정 +
   correctness 테스트 통과 확인. 전제(recurrence가 PPO서도 도움) falsify면 정직 reframe(branch b).
5. **공식 측정**(`scripts/recurrent_ppo_baseline.py`, CPU·≥3 seed): 사전약정 규칙으로 verdict.

## 검증 방법

- `python -m unittest`/pytest: 신규 테스트 + 기존 전체 green(회귀 0; 2 skip 유지).
- `mypy src`(현 28)·`ruff check .`·`python -m build` clean.
- correctness 테스트가 hidden replay 정합·permutation 불변을 결정론으로 보장(구현 신뢰의 게이트).
- 공식 script가 부분관측 config서 matched ff vs rec PPO 측정.

## 리스크

- **R1 망가진 recurrent PPO** → misleading. **완화**: AC1 correctness 게이트(replay 정합+perm 불변)를
  비교 측정 *전에* 통과 필수. 망가지면 비교 무효.
- **R2 PPO가 부분관측서 학습 불가**(grid16 A2C 학습불가 선례) → inconclusive. **완화**: default
  config(grid10/5×5)는 recurrent A2C가 이미 학습됨(46%)이 입증된 sweet spot. PPO도 학습 기대.
- **R3 헤드라인 reframe**: recurrent PPO가 oracle headroom을 *닫으면*(≥0.75 oracle) "large headroom"
  헤드라인이 흔들림. **이 경우 멈추고 사람 보고**(mandate stop 조건). branch (c).
- **R4 비용**: CPU multi-seed PPO×2 arch. **완화**: `--quick` smoke + 공식은 3 seed, default config만
  필수(hard config 완전관측 대조는 secondary/시간 허용 시).

## Acceptance Criteria (G1 통과 시 freeze)

> **freeze 대상은 결과가 아니라 사전약정 결정규칙**(p-hacking 차단).

- **AC1 (correctness 게이트 — 비교 신뢰의 전제)**: `tests/test_jax_recurrent_ppo.py`의 결정론 테스트
  통과 — (a) rollout-수집 logits == loss-replay logits(tol 1e-4), (b) env-축 permutation 불변
  (`h0[perm]` 재생 == 비-perm 재생의 perm 정렬, tol 1e-4). 시퀀스 보존 minibatch가 recurrence를
  깨지 않음을 결정론으로 입증.
- **AC2 (학습)**: recurrent PPO가 부분관측 default config서 학습한다. 판정 = **기존 사전약정 규칙 R1**
  `jax_train.learning_verdict`(데이터 전 고정, importable): 학습 곡선의 마지막 20% 윈도 평균이 첫 20%
  윈도 평균을 **late-window 표준편차보다 크게** 상회하면(`mean_late − mean_early ≥ std_late`) branch
  **"a"**(학습), 아니면 "b". recurrent A2C(`train_recurrent`)·tuned PPO가 같은 규칙으로 판정된 선례와
  동일 메트릭(mean reward-per-env-step 곡선).
- **AC3 (메모리 load-bearing under PPO — 사전약정 규칙)**: matched held-out gym-clears에서
  `rec_mean − ff_mean > max(rec_std, ff_std)` (robust separation, recurrent-baseline와 동일 규칙 형태)
  → **(a) recurrence-helps-PPO**(메모리가 PPO headroom도 닫는다). 미충족 →
  **(b) recurrence-neutral-PPO**(A2C 메모리 효과가 이 예산 PPO엔 미전이 — 정직 reframe). 추가로
  rec PPO가 `≥ 0.75·oracle` 도달 시 **(c) headroom-CLOSES → 멈추고 사람 보고**(헤드라인 reframe).
- **AC4 (회귀 0)**: feedforward/A2C/tuned-PPO/recurrent-A2C 경로 byte-identical(기존 테스트 전부 green).
  mypy/ruff/build clean.
- **AC5 (정직 경계 명시)**: 보고에 proxy(oracle=scripted)·budget·seed수·CPU·single config·param-match
  여부·A2C↔PPO 비교 한정 라벨. jax-throughput.md + competitive-analysis(gap register) + hard-benchmark
  INITIATIVE 갱신.
