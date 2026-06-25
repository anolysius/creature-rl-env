---
slug: jax-ppo-tuned
initiative: jax-throughput
status: active
started: 2026-06-25
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env, perf]
scope_paths:
  - src/critter_gym/jax_train.py
  - scripts/ppo_baseline.py
  - tests/test_jax_ppo.py
extracted_to: []
supersedes: []
---

# tuned PPO 베이스라인 + oracle-headroom 정량화 (KR1)

> 작성일: 2026-06-25 | 상태: 계획 | Initiative: jax-throughput (task 8) | 자율 런 KR1

## 목표

`jax_train`의 A2C-lite(truncated returns·단일 grad step·no clip)를 **제대로 된 PPO**(GAE(λ) +
value bootstrap + clipped surrogate + K-epoch minibatch + adv-norm, 전부 on-device jit+vmap)로
올리고, **tuned PPO가 oracle에 얼마나 닿는지(headroom)** 를 default + high-gym(hard) config에서
정량 측정한다.

**왜 (KR1·moat·마케팅)**: 벤치마크의 *결과 표 실체* = 신뢰할 RL 베이스라인 + capability headroom.
"우리 env는 *학습 가능*(gap≈0)하지만 *tuned PPO도 oracle에 한참 못 미친다*(hard-and-learnable)"가
moat 층2/3의 핵심 마케팅 명제. 현재는 A2C-lite "신호"뿐 → tuned PPO로 격상.

**Acceptance 성격(§4 교훈)**: *성능 목표가 아니라* **측정 + 정직 보고**로 freeze. 사전약정 결정규칙으로
p-hacking 차단. PPO가 oracle을 닫아버리거나(=덜 hard) 학습 안 되면(=신호 없음) → **정직 reframe·정지**.

## 선행 조건

- `jax_train.py` (A2C-lite + `EnvSpec`/`default_env_spec`/`difficulty_env_spec`/`build_region_bank`/
  `make_rollout`/`evaluate`/`learning_verdict`) — 재사용.
- `jax_env.py` (parity 0, commit + non-commit) — **무변경**(parity 보존).
- numpy SSOT (read-only 참조): `learnability.measure_learnability`(oracle/infer/type_blind/probe
  gym-clear means — headroom 비교 ceiling), `region.generate_region`.
- `[jax]`/`[rl]` extra. 코어/CI numpy-only 유지.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/jax_train.py` | `PPOConfig` + `train_ppo`(GAE+clip+epochs+adv-norm) + `gae` 순수함수 + `evaluate_gym_clears`(oracle와 동일 지표) | **높음** | A2C `train`/`evaluate` **보존**(기존 테스트·jax_rl_demo 무회귀) |
| `scripts/ppo_baseline.py` | 신규 — default+hard config PPO 학습→held-in/out gap + oracle-headroom 표 | 신규 | 정직 framing |
| `tests/test_jax_ppo.py` | 신규 — importorskip smoke(PPO 학습 곡선 상승) + `gae` property 테스트 + gym-clear eval smoke | 신규 | |

### 영향 범위

- `jax_train.py`는 `__init__` 미import(`[jax]` 뒤) → 코어 CI 무영향.
- A2C `train`/`a2c_loss`/`evaluate`/`make_rollout` **무변경** → `test_jax_train.py`(importorskip smoke)
  무회귀. PPO는 *추가* API(`train_ppo`).
- `jax_env` 무변경 → 모든 parity 테스트 무회귀.

## Step별 계획

**Step 1 (Red)**: `tests/test_jax_ppo.py` — (a) `gae` 순수함수 property(γ=1·λ=1이면 Monte-Carlo
returns−V와 일치, λ=0이면 1-step TD), (b) `train_ppo` smoke(작은 config로 곡선 상승·shape), (c)
`evaluate_gym_clears` smoke(gym-clear count ∈ [0, num_gyms]). 처음엔 FAIL.

**Step 2 (Green — PPO 구현)**:
1. `gae(rewards, values, dones, last_value, gamma, lam)` 순수함수 — `lax.scan` reverse, value
   bootstrap(rollout 끝 last_value), GAE(λ) advantage + returns=adv+values.
2. `make_rollout`를 확장하거나 PPO용 rollout(values·logp도 수집) — A2C rollout 보존하고 PPO는
   value+logp 포함 trajectory 수집(별도 rollout 또는 옵션).
3. `ppo_loss`(clipped surrogate: ratio=exp(logp−logp_old), min(ratio·adv, clip(ratio,1±ε)·adv) +
   value MSE(옵션 clip) − ent bonus) + adv 정규화.
4. `train_ppo(seeds, PPOConfig, spec)` — rollout→GAE→K epoch×minibatch(jit) Adam update. 곡선 반환.
5. `evaluate_gym_clears(params, seeds, spec)` — greedy rollout 후 종료 시 gyms_defeated 평균(oracle
   gym-clear와 비교 가능 지표).

**Step 3 (측정·headroom)**: `scripts/ppo_baseline.py` — default + high-gym(hard) config에서 PPO
학습, held-in/out gym-clear + episode return + gap, **oracle(measure_learnability) 대비 headroom**.
사전약정 결정규칙(아래) 적용. 실측 기록.

**Step 4 (문서)**: jax-throughput.md(PPO 베이스라인 Update) + DESIGN §3.1.1/§4 + competitive-analysis
(headroom = hard-benchmark 데이터점). difficulty-scaling INITIATIVE 교차참조.

## 사전약정 결정규칙 (데이터 보기 전 고정 — freeze 전 pilot이 임계 고정)

- **R1 (학습)**: `learning_verdict`(기존) — `mean_late − mean_early ≥ std_late`면 "학습". 미달이면
  학습 신호 없음 정직 보고.
- **R2 (PPO ≥ A2C)**: 동일 config·동예산서 tuned PPO held-out eval ≥ A2C-lite eval면 "개선". 미달이면
  "이 config·예산서 PPO가 A2C-lite를 못 넘음" 정직 보고(실패 아님, 측정).
- **R3 (headroom)**: held-out gym-clear 기준 `oracle − PPO ≥ HEADROOM_MIN`(freeze 전 고정, 예:
  oracle의 25%)면 **"hard-and-learnable(headroom 큼)"**; PPO가 oracle의 ≥75%면 **"PPO가 거의
  닫음(덜 hard)"** → 방향 reframe·정지 보고.

## 검증 방법

- **freeze 전 pilot (게이트)**: 작은 예산으로 (a) `gae` property 통과 (b) `train_ppo` 곡선 상승 (c)
  headroom 파이프라인 end-to-end 실행 + 사전약정 임계 고정. pilot이 학습/headroom 전제를 falsify하면
  정직 reframe·정지.
- TDD: `pytest tests/test_jax_ppo.py -q`.
- 무회귀: 360 tests green(특히 `test_jax_train.py` A2C smoke). jax_env parity 무회귀.
- canonical: mypy·ruff·pytest·build.

## 리스크

| 리스크 | 완화 |
|---|---|
| PPO가 작은 net·저예산서 A2C 안 넘음 | R2가 *측정*(성능 freeze 아님). 정직 보고. 예산/하이퍼는 honest caveat. |
| headroom 비교 지표 불일치(return vs gym-clear) | `evaluate_gym_clears`로 oracle과 **동일 gym-clear 지표** 측정. |
| oracle가 scripted ceiling proxy(완전 천장 아님) | 정직 라벨 — oracle=scripted 상한 근사, "닿음/못닿음"은 신호. |
| single-run 노이즈 | `--runs N`으로 multi-run mean±std(예산 허용 시). 사전약정 std 규칙. |
| GAE/PPO 구현 버그 → 조용한 잘못된 학습 | `gae` property 테스트(γλ 극값) + L3 코드 정합 + 곡선 sanity. |
| jax_train 변경이 A2C 무회귀 깸 | PPO는 *추가* API. A2C `train`/`evaluate` 무변경. smoke 가드. |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `jax_train`에 proper PPO 추가 — `PPOConfig` + `train_ppo`(GAE(λ)+value bootstrap +
  clipped surrogate ε + K-epoch minibatch + adv-norm, on-device jit+vmap). smoke가 학습 곡선 상승(R1) 입증.
- **AC2**: `gae` 순수함수 + property 테스트(γ=1·λ=1 ↔ MC, λ=0 ↔ 1-step TD) + `evaluate_gym_clears`
  (oracle와 동일 gym-clear 지표, ∈[0,num_gyms]).
- **AC3 (headroom 측정, 사전약정)**: default + high-gym(hard) config서 tuned PPO held-in/out gym-clear
  + episode return + gap + **oracle 대비 headroom**(R3 사전약정 sign rule)을 `scripts/ppo_baseline.py`로
  실측·보고. 정직 single/few-run.
- **AC4 (PPO ≥ A2C, 사전약정 R2)**: 동일 config·예산서 tuned PPO eval ≥ A2C-lite eval면 개선 보고;
  미달이면 정직 "no-improvement" 보고(측정이지 실패 아님).
- **AC5 (무회귀)**: 360 tests green. A2C `train`/`evaluate`·`jax_env` 무변경(parity 보존). jax_train
  backward-compatible.
- **AC6 (정직 범위)**: CPU·single/few-run·작은 net·oracle=scripted ceiling proxy·gym-clear vs return
  지표 구분·하이퍼 미세튜닝 한계 라벨. 헤드라인 과대 0.
- **AC7 (사전약정 pilot)**: freeze 전 pilot이 gae property·PPO 학습·headroom 파이프라인 입증 + 임계
  고정. PPO 학습 실패 또는 headroom 소멸(PPO가 oracle 닫음)이면 정직 reframe·정지 보고.
- **AC8**: `mypy src`·`ruff check .`·`pytest -q`·`python -m build` clean. 문서(jax-throughput.md +
  DESIGN + competitive-analysis + INITIATIVE) 갱신. CHANGELOG 1줄.

## Pilot 결과 (freeze 전 전제 검증 + 사전약정 결정규칙)

**파이프라인 입증 (falsify 0)**: `gae` property 3종(γ=1·λ=1↔MC / λ=0↔1-step TD / numpy ref 일치) +
`train_ppo` 학습(R1 branch a) + headroom end-to-end 모두 통과. PPO 학습 실패·headroom 소멸 **없음**
→ reframe 불요.

**실측 (CPU·single run, 사전약정 R1/R2/R3 적용)** — quick(60 iter)과 full(200 iter) 일관:

| config | PPO held-out gym-clear | oracle | type_blind | PPO/oracle | gap(in−out) | A2C | R2 | R3 |
|---|---|---|---|---|---|---|---|---|
| default(3 gym) | 0.59 | 1.84 | 0.59 | **32%** | +0.12 | 0.78 | PPO 2.53≥0.78 | hard-and-learnable |
| hard(8 gym) | 1.06 | 7.28 | 2.03 | **15%** | −0.09 | 1.88 | PPO 2.56≥1.88 | hard-and-learnable |

- **R1**: 양 config 학습(branch a). **R2**: 양 config서 tuned PPO ≥ A2C-lite(특히 hard서 A2C-lite는
  거의 붕괴, PPO가 격차 큼). **R3**: 양 config PPO ≤ 0.75×oracle(15·32% ≪ 75%) → **hard-and-learnable**,
  reframe/정지 조건 **미발동**.
- **striking 정직 발견**: hard config서 tuned PPO(1.06) < 비추론 type_blind(2.03) — capability ladder
  oracle 7.28 ≫ type_blind 2.03 > PPO 1.06 선명. 현 tuned-PPO-baseline은 oracle이 쓰는 추론을 못 깸.
- **정직 caveat**: single run·작은 net·CPU·200 iter(더 큰 compute/튜닝은 PPO↑→headroom은 *이 예산*
  기준)·oracle=scripted ceiling proxy·held-out gym-clear gap은 single-run 노이즈(±). multi-run rigor는
  difficulty-scaling 이니셔티브 후속.
