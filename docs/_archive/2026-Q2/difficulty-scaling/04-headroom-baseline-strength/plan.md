---
slug: headroom-baseline-strength
initiative: difficulty-scaling
status: active
started: 2026-06-25
mode: standard
task_type: general
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/jax_train.py
  - scripts/ppo_baseline.py
  - tests/test_jax_ppo.py
extracted_to: []
supersedes: []
---

# 강한 baseline에도 oracle headroom이 살아남나? (절대 난이도 진단 Q1)

> 작성일: 2026-06-25 | 상태: 계획 | gap register: "robust learnability result / a hard benchmark"

## 목표 (연구 질문)

우리의 헤드라인 "hard-and-learnable"(tuned PPO가 oracle의 **21–28%**, 5-run robust)는 **"tiny MLP·150–200
iter" 예산에서** 측정됐다. 그래서 절대 난이도의 *진짜* 질문은: **그 headroom이 *실질적으로 강한* PPO
baseline에도 살아남나?**

- **(a) 살아남음** → env는 약한 baseline 때문이 아니라 *구조적으로* 학습-headroom이 큼 = **"이미 hard
  benchmark"**(강력한 결과, spec 변경 0, JAX 재포트 0).
- **(b) 닫힘** → 기존 headroom은 부분적으로 baseline 약함의 산물 = **env가 강한 agent엔 toy 확정** →
  부분관측 등 *비싼* 난이도 레버(Q2) 투자 정당화.
- **(c) oracle 초과** → scripted oracle이 유효 천장이 아님 → 더 강한 reference 필요(지표 caveat).

**이건 비싼 일(Q2: spec 변경·JAX 재포트) 전에 해야 할 가장 싼 진단**이고, JAX 엔진이 강한 baseline을 싸게
훈련 가능케 해서(0.66–1.1M steps/s) 지금 할 수 있다. difficulty-scaling 이니셔티브가 "다음 task: 강한 PPO
baseline"으로 이미 지목했고, competitive-analysis gap register "stronger baselines to confirm headroom"과 정합.

**문헌 근거**(웹): Procgen/Craftax에서 강한 baseline의 정석 레버 = **아키텍처 스케일링(width↑·depth) + 예산↑**
("larger architectures significantly improve sample efficiency and generalization"). 우리 현재 net=1-hidden-layer
MLP·hidden64. → 강한 baseline = 더 깊고/넓게 + 더 오래(co-scale).

## 선행 조건

- main HEAD `03149f8`, 415 tests green. `jax_train.py`: `init_params`(1-hidden-layer MLP)·`apply_policy`·
  `PPOConfig`(hidden/iters/batch/epochs/num_minibatches…)·`train_ppo`·`evaluate_gym_clears`. `headroom.py
  classify_headroom`(frac=0.75·k=1.0, 사전약정). `scripts/ppo_baseline.py`(default+hard, `--runs`).
- **선행 경고(transfer-capacity-budget 학습)**: 이 env에서 *capacity만* 키우면 작은 예산서 underfit→오히려
  하락, *예산*은 250–500k까지 도움. → capacity와 budget을 **함께** 키워야 함. **non-vacuity 가드 필수**:
  강한 config가 실제로 tiny baseline보다 held-out 높아야(안 그러면 "headroom robust"가 망가진 net의 공허한
  산물).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/jax_train.py` | **default-preserving depth 노브** 추가: `init_params`/`apply_policy`가 `depth≥1` 지원(depth=1·hidden64 = 기존 byte-identical, A2C/PPO 무변경). `PPOConfig`에 `depth` 필드(default 1) | 중 (코어 train 모듈; default 보존이 핵심) |
| `scripts/ppo_baseline.py` | `--strong`(강한 config 프리셋: 더 깊+넓+긴) + tiny-vs-strong 대조 출력 + **non-vacuity 가드**(strong ≥ tiny held-out) + 사전약정 3-branch verdict | 중 |
| `tests/test_jax_ppo.py` | depth≥2 net의 `init_params`/`apply_policy` shape + train smoke(curve 상승) + depth=1 byte-identical 회귀 | 소 |

### 영향 범위

- `init_params`/`apply_policy`는 A2C `train`과 PPO `train_ppo`가 공유. **depth=1 default 보존**이 비협상
  (A2C 데모·기존 PPO·`test_jax_train.py`/`test_jax_ppo.py` 무회귀). depth는 compile-time 상수(Python 분기).
- `ppo_baseline.py`는 스크립트(테스트 아님). `reproduce_results.py`가 호출하나 default 인자 무변경.

## Step별 계획

1. **(pre-freeze pilot)** scratchpad에서 (i) depth≥2 net이 train·curve 상승 확인 (ii) **강한 config가 tiny
   baseline보다 held-out 높음**(non-vacuity) (iii) 강한 PPO의 held-out vs oracle을 default+hard에서 측정 →
   3-branch 중 어디로 가는지 ballpark. **싼 일이므로 pilot이 곧 결론에 근접** → 결과로 plan 정직 확정.
2. `jax_train.py`: `init_params(key, obs_dim, hidden, depth=1)` — depth=1이면 기존 키(w1/b1/wpi/wv) 그대로,
   depth≥2면 w2/b2… 추가. `apply_policy`가 hidden 레이어 수 추론(compile-time). `PPOConfig.depth` 추가.
3. `ppo_baseline.py`: `--strong` 프리셋(예: depth2·hidden256·iters↑, co-scaled) + tiny/strong 둘 다 측정 +
   non-vacuity 가드 + `classify_headroom`로 strong PPO의 3-branch robust verdict.
4. `tests/test_jax_ppo.py`: depth≥2 shape/train smoke + depth=1 byte-identical.
5. G2 + 강한 baseline 측정 실행(default+hard, ≥3 seed). 결과를 정직 보고(어느 branch·무엇을 의미).

## Pilot 결과 박제 (2026-06-25, freeze 전 — stage 1 config-only)

width 64→256 + iters 150→600(co-scale, 3 seed), tiny vs strong PPO held-out vs oracle:
- **default**: tiny 0.29(15%) → **strong 0.56(29%)** of oracle 1.94. non-vacuity ✓(0.56>0.29). **branch (a)
  headroom-ROBUST**(낙관상한 0.70 ≤ frac·oracle 1.45).
- **hard**: tiny 0.96(14%) → **strong 1.96(28%)** of oracle 7.06. non-vacuity ✓(1.96>0.96). **branch (a)
  ROBUST**(낙관상한 2.34 ≤ 5.30).
- 즉 4×-wide/4×-long 스케일이 성능을 **약 2배**로 올렸지만(→ tiny baseline이 under-powered였음 = non-vacuity
  실재) 여전히 **~28% of oracle에서 plateau**. headroom은 tiny-MLP 산물이 아님 → (a) 강한 신호.
- **falsify 없음 — 사전약정 3-branch 규칙·non-vacuity 머신이 잘 정의됨을 검증.** 본 task는 *depth 추가 +
  budget 더 밀어* "강한 baseline"을 *신뢰가능*하게 만들고 분류기 결과를 정직 보고. **freeze 대상은 결과가
  아니라 결정규칙** → 어느 branch든 freeze 안전.

## 검증 방법

- `pytest tests/test_jax_ppo.py -q` 무회귀 + 신규 depth 테스트 green.
- `scripts/ppo_baseline.py --strong --runs 3` 가 tiny·strong 대조 + non-vacuity 가드 + 3-branch verdict 출력.
- G2: mypy·ruff·pytest(415+ green)·build.
- **사전약정 결정규칙(데이터 전 고정, freeze 시 박제)** — 아래 AC1.

## 리스크

- **강한 config가 underfit(transfer 선례)** → "headroom robust"가 공허. → **non-vacuity 가드**(strong ≥
  tiny held-out)가 필수 선결. 가드 실패 시 config 재튜닝(예산↑ 우선, capacity는 budget과 동반).
- **oracle 초과(branch c)** → scripted oracle이 천장 아님. 정직하게 "지표 한계"로 보고(reframe 아님, 측정 결과).
- **default 보존 깨짐** → A2C/기존 PPO 회귀. → depth=1 byte-identical 테스트로 가드.
- **연구 결과 미보장**: 어느 branch든 *정직한 측정*이 산출물. 성능 약속 아님.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (사전약정 결정규칙, 데이터 전 고정)**: 강한 PPO held-out gym-clears를 default+hard에서 R≥3 seed
  측정. `classify_headroom`(frac=0.75·k=1.0)로:
  - **(a) headroom-robust**: 양 config에서 낙관상한(mean+k·std) ≤ frac·oracle → "강한 baseline에도 headroom
    robust" (env 이미 hard 신호).
  - **(b) headroom-closes**: 어느 config서 strong PPO mean ≥ frac·oracle (또는 비관하한 mean−k·std ≥
    frac·oracle) → "scaling이 headroom을 실질 축소" → Q2(부분관측 등) 정당화.
  - **(c) exceeds-oracle**: 어느 config서 strong PPO mean > oracle → "oracle은 유효 천장 아님" (지표 caveat).
- **AC2 (non-vacuity 가드)**: 강한 config가 tiny baseline 대비 held-out gym-clears **증가**(strong > tiny)임을
  검증 — 안 그러면 "headroom robust"는 망가진 net의 공허한 결과이므로 verdict 보류·재튜닝.
- **AC3 (무회귀)**: depth=1·hidden64 default가 byte-identical(A2C `train`·기존 PPO·`test_jax_{train,ppo}.py`
  무회귀). 415+ tests green.
- **AC4 (G2)**: mypy·ruff·pytest·build clean.
- **AC5 (정직 보고)**: 어느 branch든 결과를 jax-throughput.md/difficulty-scaling INITIATIVE에 정직 기록 —
  강한 baseline의 정의(depth/width/budget·문헌 근거)·한계(CPU·R seed·oracle=scripted proxy·이 capacity 상한)
  명시. **(a)면 "이미 hard" 과대 금지**(scripted proxy·이 baseline class 한정), **(b)면 toy 확정→Q2 다음**.
