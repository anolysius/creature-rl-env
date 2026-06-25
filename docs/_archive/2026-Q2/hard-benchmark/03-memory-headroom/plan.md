---
slug: memory-headroom
initiative: hard-benchmark
status: active
started: 2026-06-25
acceptance_freeze: true
domains: [rl-env]
mode: standard
task_type: general
scope_paths:
  - src/critter_gym/jax_train.py
  - tests/test_jax_hard_config_parity.py
  - scripts/hard_benchmark_memory.py
extracted_to: []
supersedes: []
---

# Memory-agent headroom — is the env hard *even for a strong memory agent*? (hard-benchmark #3)

> 작성일: 2026-06-25 | 상태: 계획

## 목표

competitive-analysis gap register의 **"a hard benchmark" ❌(toy)**에서 아직 미해결로 남은 조각은
"**강한/메모리 agent에게도** oracle headroom이 큰가"다. #1·#2가 보인 것: 부분관측에서 메모리가
load-bearing(memoryless→floor)이고 recurrence가 headroom을 일부 회복(grid10/5×5서 recurrent PPO
**53%** of oracle). 즉 grid10 sweet-spot은 메모리 agent에겐 *절반쯤 풀리는* 난이도다.

본 task = env를 **더 깊게**(큰 지도 + 긴 호라이즌 + gym 수↑, 부분관측 5×5 유지) 만들어, **방금 만든
가장 강한 agent(recurrent PPO)에게도 oracle headroom이 robust하게 크게 남는** config를 정식화·측정한다.
이는 "memoryless에 hard"(#1·#2)를 넘어 "**memory agent에게도 hard**"(절대 난이도)로 한 칸 올린다.

**scout 신호(1 seed)**: grid16·5gym·420step·5×5에서 oracle 4.69(winnable, ~all gym 클리어) ·
feedforward PPO 13% · **recurrent PPO 23%**(학습됨, branch a) — recurrent-baseline scout가 "grid16=A2C
학습불가 inconclusive"로 둔 지점을 **recurrent PPO는 학습하되 큰 headroom 잔존**. grid10(53%)→grid16(23%)
급락 = 메모리 agent에게도 hard. (단 1 seed → multi-seed robust 확정이 본 task.)

## 선행 조건

- #2 recurrent PPO done: `train_recurrent_ppo`/`evaluate_gym_clears_recurrent` 존재(가장 강한 agent).
- `headroom.classify_headroom`(frac=0.75·k=1.0, numpy-only, 데이터 전 고정) 존재 — 사전약정 판정 재사용.
- JAX env는 **config-driven**(`JaxEnvConfig(grid, patch_radius, max_gyms, max_steps, boss…)`) → grid16/5gym은
  **re-port 불요**(JaxEnvConfig 인스턴스). 단 이 새 shape의 **JAX↔numpy parity는 미검증** → 본 task가 검증.
- `[jax]`+`[rl]`(CI numpy-only importorskip).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/jax_train.py` | **추가만**(`hard_env_spec()` 헬퍼: grid16/5gym/420st/5×5 EnvSpec) | 저 | 기존 spec/train/eval 전부 byte-identical. depth knob 등 무변경 |
| `tests/test_jax_hard_config_parity.py` | 신규 | 저(test) | **parity 0** 검증: 새 grid16/5gym config서 JAX env ↔ numpy `CritterEnv` 궤적 일치(oracle=numpy·agent=JAX가 같은 env임을 보장) + train smoke |
| `scripts/hard_benchmark_memory.py` | 신규 | 저(script) | ff PPO vs rec PPO vs oracle @grid16/5gym, 사전약정 headroom 규칙 |

### 영향 범위 (import 그래프)

- `jax_train.py`는 `__init__` 미import(jax optional) → core/default suite 무영향. `hard_env_spec`는 신규
  심볼; `default_env_spec`/`difficulty_env_spec` 무변경 → #2까지의 모든 테스트 회귀 0.

## Step별 계획

> **커밋 경계**: 본 task는 lifecycle 끝(L3 APPROVED 후)에 **1 커밋**(green+verify+측정 산출 일괄) — 이
> 프로젝트 관례(#1·#2 동일). pilot/측정은 산출물(script/docs)로 남고 별도 커밋 아님.

1. **(red)** `tests/test_jax_hard_config_parity.py`: grid16/5gym/420st/patch2 config서 (a) JAX
   `make_jax_env(cfg)` vs numpy `CritterEnv(**cfg)` **parity 0**(random + gym-clearing policy, train·
   held-out seed, obs key+reward+term+trunc) (b) `train_recurrent_ppo` 짧은 smoke가 유한 곡선.
2. **(green)** `jax_train.py`에 `hard_env_spec()` 추가(EnvSpec; `difficulty_env_spec` 패턴 — JaxEnvConfig +
   numpy region_fn). 기존 심볼 무변경.
3. **(verify)** mypy·ruff·pytest(parity 0 포함)·build. 기존 경로 byte-identical 재확인.
4. **pilot(freeze 전 — 본 프로젝트 표준 lifecycle step, plan 불완전 아님)**: 사전약정 결정규칙을 **데이터
   보기 전에** 검증하기 위한 단계. grid16/5gym 2-3 seed로 (i) parity 0, (ii) recurrent PPO 학습(branch a)·
   oracle winnable, (iii) recurrent PPO ≪ oracle(headroom 방향)·timing 확인. recurrent PPO가 학습 못 하면
   (곡선 flat) → 더 쉬운 config로 reframe(grid14, scout가 rec 42% 확인). pilot은 *전제·임계 sanity*용이고
   AC3 임계(frac=0.75·k=1.0)는 G1 freeze 시 **데이터와 무관하게** 고정된다.
5. **공식 측정**(`scripts/hard_benchmark_memory.py`, CPU·≥3 seed): 고정된 사전약정 규칙으로 verdict 산출.

## 검증 방법

- pytest: 신규 parity(0 mismatch) + smoke + 기존 전체 green(회귀 0). mypy(28)·ruff·build clean.
- parity 0가 "oracle(numpy)와 agent(JAX)가 같은 env"를 보장 → headroom 측정 신뢰의 전제.
- 공식 script가 grid16/5gym서 ff PPO·rec PPO·oracle 측정.

## 리스크

- **R1 recurrent PPO도 grid16 학습 불가** → inconclusive(grid16 A2C 학습불가 선례). **완화**: scout가
  recurrent PPO는 grid16서 학습(branch a, 23%) 확인. 그래도 multi-seed서 flat이면 grid14로 reframe.
- **R2 parity mismatch**(새 shape) → 측정 무효. **완화**: parity 테스트가 freeze 전(pilot)·G2서 게이트.
  config-driven 포트라 grid6/8gym parity 선례 있음(test_jax_difficulty_parity).
- **R3 memory가 grid16서 무력**(scout mem-gap +0.44지만 noisy) → "그냥 sparse-hard"일 수도. **완화**:
  rec>ff를 secondary로 보고(메모리 여전히 도움 확인). 단 *주 결론은 "memory agent에게도 headroom 큼"*
  (rec≪oracle)이지 mem-gap 크기 아님 — mem-gap 작아도 주 결론 유효.
- **R4 헤드라인 reframe**: recurrent PPO가 grid16서도 oracle 근접(≥0.75)하면 "hard 아님" → **멈추고 사람
   보고**. scout 23%라 가능성 낮음.

## Acceptance Criteria (G1 통과 시 freeze)

> **freeze 대상 = 사전약정 결정규칙**(결과 아님).

- **AC1 (parity 게이트 — 측정 신뢰 전제)**: 새 grid16/5gym/420st/patch2 config서 JAX env ↔ numpy
  `CritterEnv` **parity 0 mismatch**(obs 전 key + reward + terminated + truncated, random + gym-clearing
  policy, train·held-out seed). oracle(numpy)와 agent(JAX)가 byte-identical env임을 입증.
- **AC2 (learnable + winnable)**: oracle이 winnable(held-out oracle gym-clears ≥ 0.5·num_gyms = 존재
  gym 다수 클리어) **그리고** recurrent PPO가 학습(R1 `learning_verdict` branch "a", 다수 seed).
- **AC3 (memory agent에게도 hard — 사전약정 결정규칙; pass/fail = frozen 3-branch 분류)**: 판정 함수
  `headroom.classify_headroom`의 임계 **frac=0.75·k=1.0을 G1 freeze 시 데이터와 무관하게 고정**(데이터는
  *어느 branch가 나오는지*만 결정 — 사후 임계 변경 0, p-hacking 차단). 가장 강한 agent(recurrent PPO)의
  held-out gym-clears(≥3 seed)에 적용한 출력 branch가 acceptance:
    - `hard-and-learnable`(낙관상한 mean+std ≤ 0.75·oracle) → **(a) hard-for-memory-agent robust** = PASS
      (절대 난이도 입증, 헤드라인 결론).
    - `ppo-closes`(mean−std ≥ 0.75·oracle) → **(b) memory-closes** = 이 config는 메모리 agent엔 hard 아님
      → 정직 reframe(헤드라인 흔들림 → **멈추고 사람 보고**).
    - `inconclusive`(std가 gap 잠식) → 더 많은 seed 또는 config 조정.
  결과가 어느 branch든 ±std+caveat로 정직 보고(날조 0). **secondary**(결론 아님, 부기만): rec_mean >
  ff_mean이면 "메모리 여전히 load-bearing".
- **AC4 (회귀 0)**: 기존 spec/train/eval/parity 경로 byte-identical(추가만). **passing 테스트 수 427
  유지/증가**(신규 parity·smoke 추가분만큼 증가), 2 skip 유지. mypy(28 files)·ruff·build clean.
- **AC5 (정직 경계 명시)**: oracle=scripted proxy·budget·seed수·CPU·single config·강한 agent=recurrent
  PPO(SOTA 아님)·grid16 한정 라벨. jax-throughput.md + competitive-analysis(gap register "a hard
  benchmark"/"absolute difficulty") + INITIATIVE 갱신. CHANGELOG append.
- **AC6 (freeze 전 pilot 게이트)**: 공식 전 pilot로 parity 0·recurrent PPO 학습·headroom 방향·timing
  확인. recurrent PPO 학습 실패 시 더 쉬운 config(grid14)로 reframe(새 slug 불요).
