---
slug: headroom-baseline-strength
initiative: difficulty-scaling
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md          # PPO headroom — robust-to-scaling update
  - docs/explanation/competitive-analysis.md     # gap register "robust learnability result"
changelog_entry: docs/CHANGELOG.md
---

# 강한 baseline에도 oracle headroom이 살아남나? — 결과 보고서 (절대 난이도 진단 Q1)

## 요약 (수치 표)

연구 질문: 헤드라인 "hard-and-learnable"(PPO ≈ oracle의 21–28%)가 *tiny MLP·짧은 훈련* 산물인가, 아니면
*강한 baseline*에도 살아남는 진짜 난이도인가?

**사전약정 3-branch 결과 = (a) headroom-ROBUST** (양 config). 강한 baseline = capacity×budget 스윕의 **최선**.

| config | tiny d1/h64 | **best strong (wide d1/h256)** | deep d2/h256 | oracle | 판정 |
|---|---|---|---|---|---|
| default (3-gym) | 0.56 (31%) | **0.76 (41%)** | 0.33 (18%) | 1.84 | (a) robust (opt-bound 0.89 < 1.38) |
| hard (8-gym) | 1.44 (20%) | **1.83 (25%)** | 1.49 (20%) | 7.28 | (a) robust (opt-bound 2.05 < 5.46) |

**budget 평탄성 검증 (wide d1/h256, held-out % of oracle, 3 seed):**

| budget | i600 | i1200 | i2400 | i4000(~20M steps) |
|---|---|---|---|---|
| default | 41% | 34% | 41% | 38% |
| hard | 25% | 27% | 25% | 24% |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 사전약정 3-branch (a/b/c) | ✅ | `classify_headroom`(frac0.75·k1.0)가 best-strong 런에서 양 config **(a) hard-and-learnable** — opt-bound가 0.75·oracle 한참 밑 |
| AC2 non-vacuity (best-strong > tiny) | ✅ | default 0.76>0.56, hard 1.83>1.44. **깊은 net(d2)·과예산은 vacuous**(d2 0.33<tiny 0.56)임을 가드가 포착 → best-of-sweep로 정직 정의 |
| AC3 무회귀 + depth=1 byte-identical | ✅ | 415→**419**(+4 depth 테스트), `test_init_params_depth1_byte_identical` green, A2C/기존 PPO 무변경 |
| AC4 G2 | ✅ | mypy(28)·ruff·pytest exit=0·build clean |
| AC5 정직 보고 | ✅ | (a)지만 "이미 hard" 과대 금지 — *cheap feedforward 스케일링 한정* robust, SOTA/recurrent/대형 미배제, oracle=scripted proxy, 3 seed·CPU 명시 |

## 핵심 결과 (정직)

**headroom은 약한-baseline 산물이 아니다 — 그러나 cheap 스케일링으로 닫히지도 않는다.**

1. **(a) robust**: best strong PPO가 oracle의 **41%(default)/25%(hard)**에서 plateau. tiny 대비 non-vacuously
   강함(width 64→256가 ~+10pp). opt-bound가 0.75·oracle 한참 밑 → 양 config robust.
2. **capacity는 레버가 아니다**: depth 1→2가 **오히려 하락**(d2 < d1). transfer-capacity-budget 선례
   ("bigger net robustly hurts")를 headroom 세팅에서 재현.
3. **budget도 레버가 아니다**: wide net이 i600에서 사실상 plateau, **i4000(~20M steps)에서도 i600보다
   안 나음**. 더 많은 compute로 못 닫음.
4. → **병목은 baseline의 capacity/compute가 아니다.** env가 보유한 학습-headroom은 표준 cheap 스케일링에
   robust.

## 정직한 경계 (과대 금지)

- **이 결과가 배제한 것**: *cheap feedforward MLP 스케일링*(width/depth/budget)이 gap을 닫는다는 가설.
- **배제하지 못한 것**: 근본적으로 다른/강한 agent — recurrent·메모리(POPGym/Craftax 교훈)·훨씬 큰 모델·
  더 나은 알고리즘(RND·world-model)·광범위 HP 튜닝. 이들은 여전히 닫을 수 있음. → **"robust"=표준 cheap
  스케일링에 robust**, "어떤 agent도 못 닫음"이 **아님**.
- oracle = scripted ceiling **proxy**(gym 위치+chart 봄), 진짜 optimum 아님.
- 3 seed·CPU·commit-mode default+hard·feedforward MLP(1–2층, ≤i4000).

## 절대 난이도(Q1→Q2) 함의

- **Q1 답**: "hard-and-learnable" headroom은 **실재**하고 약한-net 산물이 아니며 cheap 스케일링으로 안 닫힘
  → env는 현 baseline class엔 **trivially toy가 아님**. 헤드라인 자산 강화.
- **부분적으로 열린 것**: "*SOTA/recurrent* agent에도 hard인가"는 미해결(cheap MLP만 배제). 그래서 *더 강한
  agent에 대한* 절대 난이도를 원하면 **Q2(부분관측 등 spec 레버)가 여전히 동기**. 단 Q1이 "비싼 Q2 전에
  cheap 스케일링부터 배제"라는 순서를 정직하게 닫음.

## 변경 파일 상세

**수정**
- `src/critter_gym/jax_train.py` (+~30): `init_params`/`apply_policy`에 **default-preserving depth 노브**
  (depth=1 byte-identical, depth≥2 trunk 레이어 추가·compile-time 추론) + `PPOConfig.depth` + `train_ppo`가
  `config.depth` 전달.
- `scripts/ppo_baseline.py` (+~55): `--strong` — capacity×budget 스윕(tiny/wide/deep), **best-of-sweep**를
  강한 baseline으로, 사전약정 3-branch + non-vacuity 가드.
- `tests/test_jax_ppo.py` (+4): depth=1 byte-identical / depth≥2 shape / forward / depth=2 train smoke.

## 타입 체크 / 빌드 결과

- mypy: 0 err (28 files). ruff: clean. pytest: exit=0 (419 passed, 2 skipped). build: 1.0.0rc1 OK.
- 측정: `scripts/ppo_baseline.py --strong --runs 3` (재현). budget-plateau = run-derived 보조 측정.
