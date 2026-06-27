---
slug: sealed-eval-harness
initiative: eval-product
status: active
started: 2026-06-26
acceptance_freeze: true
domains: [rl-env]
mode: standard
task_type: general
scope_paths:
  - src/critter_gym/eval_harness.py
  - tests/test_eval_harness.py
  - scripts/eval_harness_demo.py
extracted_to: []
supersedes: []
---

# Sealed held-out eval harness — 봉인 held-out + agent 제출 → RLVR 검증 채점 (M5 enabler 프로토타입)

> 작성일: 2026-06-26 | 상태: 계획

## 목표

M5 비공개 eval 제품의 **기능 토대**를 프로토타입으로 만든다 — moat 메커니즘("외울 수도 오염될 수도 없는
eval")을 *실행 가능한 코드*로 입증. 핵심 3요소: (1) **봉인 held-out eval 세트**(평가자만 아는 secret 블록,
재생성·결정론), (2) **agent 제출 인터페이스**(`act(obs)->action` — 학습 정책·scripted·LLM-agent 공통),
(3) **RLVR 검증 채점 + 오염 가드**(verifiable subgoal로만 채점 + "제출자가 이 eval로 학습 안 함"을 검증).

**moat 메커니즘 (왜 팔리나)**: env seed→world 결정론 + held-out 구역(seed ≥ 1,000,000, train < 1M). 평가자가
held-out 구역의 비공개 블록을 골라 신선한 세계 생성 → 거기서 채점. 제출자는 그 블록을 모르고, 선언한 train
seed가 eval과 겹치면 가드가 검출 → **점수의 신뢰성이 검증 가능**(고정 벤치마크가 못 주는 것).

## 선행 조건 (전부 존재, src/critter_gym/)

- `region.py`: `TEST_SEED_OFFSET`=1,000,000, `heldout_seeds(n)`, `is_held_out(seed)`.
- `generalization.py`: `split_train_pool`.
- `learnability.py`: `run_episode(env_factory, policy, seed)->EpisodeOutcome(episode_return, gyms_cleared,
  evolutions)`, `reference_arm(arm)` (oracle/type_blind/...), `as_env_policy(obs_policy)`.
- `envs/critter_env.py`: `info["subgoals"]={caught, gyms_defeated, evolved}` (RLVR boolean subgoals).
- 순수 numpy → **core 모듈**(JAX 불필요), CI 테스트 가능(importorskip 아님).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/eval_harness.py` | 신규 | 중 | 독립 모듈, 기존 심볼만 import(env/learnability/region/generalization 무변경) |
| `tests/test_eval_harness.py` | 신규 | 저(test) | 봉인 disjoint·채점 결정론·오염 가드·RLVR subgoal·인터페이스 |
| `scripts/eval_harness_demo.py` | 신규 | 저(script) | 봉인 세트 등록 + random/oracle/blind agent 제출→scorecard + 오염 가드 데모 |

### 영향 범위

- 신규 독립 모듈 — 기존 코드 import만(무변경). `__init__` 노출 여부는 보수적으로(직접 import 경로 유지) →
  전체 테스트 회귀 0.

## 설계 (구현 윤곽)

- `SealedEvalSet(master_seed, n_worlds, env_config)` — held-out 구역에서 `master_seed`로 결정된 **비공개
  블록** `_eval_seeds()`(secret offset; 제출자 비공개). `env_factory()`(commit-v0 numpy). `train_region()`
  = "<1M 아무 seed" 안내(제출자가 학습 가능한 구역). 같은 master_seed→같은 봉인 세트(재현), 다른 master_seed
  →다른 신선한 세계(재생성).
- `Agent` Protocol: `act(obs)->int`(obs-only; scripted reference는 `as_env_policy` 어댑트).
- `Scorecard`(NamedTuple): n_worlds·mean_gyms_cleared·subgoal rates(cleared_rate=≥1 gym 비율·caught/evolved
  rate)·vs reference(oracle·type_blind 동일 봉인 seed서) → frac_of_oracle·sealed certificate.
- `score_agent(agent, sealed, *, reference=("oracle","type_blind"))->Scorecard` — 봉인 seed마다 run_episode,
  RLVR subgoal 집계 + 참조 arm 동일 seed 채점.
- `verify_sealed(declared_train_seeds, sealed)->SealedCertificate(ok, n_eval, n_train, overlap, all_eval_heldout)`
  — 오염 가드: declared_train ∩ eval == ∅ **그리고** declared_train 전부 train 구역(<1M). leak 시 ok=False.

## Step별 계획
> 커밋 경계: lifecycle 끝 1 커밋(관례).
1. **(red)** `tests/test_eval_harness.py`: (a) `_eval_seeds` 전부 held-out·master_seed 결정론·다른 seed→다른
   블록 (b) verify_sealed: clean train→ok / eval과 겹치는 train→ok=False(leak 검출) / train 구역 밖→ok=False
   (c) score_agent: oracle agent가 random보다 높은 mean_gyms·frac_of_oracle∈[0,1]·subgoal rate∈[0,1] (d)
   Agent Protocol 어댑트(scripted/obs-only).
2. **(green)** `eval_harness.py` 구현(위 설계). 기존 심볼만 import.
3. **(green)** `scripts/eval_harness_demo.py`: 봉인 세트 등록 + random/oracle/type_blind 제출→scorecard 출력
   + 오염 가드 데모(정상 train vs leak 시도).
4. **(verify)** mypy(src)·ruff·pytest(신규+기존 442 무회귀)·build clean.

## 검증 방법
- pytest: 신규 테스트 + 기존 442 green(회귀 0). mypy(28→증가)·ruff·build clean.
- 봉인 disjoint·오염 가드(leak 검출)·RLVR 채점·결정론이 코드로 입증.
- demo가 moat 메커니즘(봉인+제출+검증+오염가드)을 end-to-end 시연.

## 리스크
- **R1 과대("제품 완성")**: 프로토타입을 hosted 제품으로 과장. **완화**: 모든 산출에 "in-process 봉인
  컨벤션·단일 머신·numpy·고객/공개 없음" 경계 명시.
- **R2 봉인이 진짜 비공개 아님**(in-process라 secret이 객체 안에 있음). **완화**: 정직 명시 — 실제 제품은
  서버측 secret seed + 제출 샌드박스 필요. 프로토타입은 *메커니즘 데모*.
- **R3 회귀**: 기존 모듈 변경 0(import만). **완화**: src 기존 파일 무수정 — 신규 모듈만.

## Acceptance Criteria (G1 통과 시 freeze)
- **AC1 (봉인 held-out)**: `SealedEvalSet._eval_seeds()` 전부 `is_held_out`(≥1M); 같은 master_seed→동일
  블록(결정론), 다른 master_seed→다른 블록(재생성). 테스트로 입증.
- **AC2 (오염 가드 — moat 핵심)**: `verify_sealed`가 (a) clean 선언 train→ok=True (b) eval과 겹치는 train→
  ok=False·overlap>0 (leak 검출) (c) train 구역 밖(≥1M) 선언→ok=False. 결정론 테스트.
- **AC3 (RLVR 검증 채점)**: `score_agent`가 verifiable subgoal로만 채점(mean_gyms_cleared·cleared_rate·
  caught/evolved rate·frac_of_oracle). oracle agent mean_gyms > random; 모든 rate∈[0,1]·frac_of_oracle≥0.
  hand-tuned 점수 0.
- **AC4 (제출 인터페이스)**: `Agent` Protocol `act(obs)->int` + scripted reference 어댑트. demo가 random/
  oracle/type_blind 제출→scorecard end-to-end.
- **AC5 (회귀 0 + 정직 경계)**: 기존 src 무변경, 전체 442 무회귀, mypy(28→증가)·ruff·build clean. 산출에
  "프로토타입·in-process 봉인·단일 머신·numpy·hosted 제품/고객/공개 아님" 경계 명시. INITIATIVE/CHANGELOG.
