---
slug: multitype-boss-headroom
initiative: hard-benchmark
status: active
started: 2026-07-02
acceptance_freeze: true
domains: [rl-env, perf]
scope_paths:
  - src/critter_gym/headroom.py
  - tests/test_headroom.py
  - scripts/multitype_boss_headroom.py
  - docs/reference/multitype-boss.md
extracted_to: []
supersedes: []
mode: standard
task_type: general
---

# 다중-타입 보스 헤드룸 — 다중-seed 사전약정 측정 (hard-benchmark #5)

> 작성일: 2026-07-02 | 상태: 계획 | 추진: hard-benchmark #4(scout)의 명시적 후속. scout 가
> 전제(parity 0·recurrent PPO 학습·양쪽 winnable·1-seed Δ+3.4pp)를 검증했으므로 이제 **본측정**.

## 목표

#4 scout 의 1-seed 신호("숨은 2번째 보스 타입이 더 깊은 난이도")를 **다중-seed(≥3) + 사전약정
판정 규칙**으로 robust 하게 입증하거나 반증한다. 질문 2개:

- **(A) 절대 난이도**: 다중-타입 config 가 *가장 강한 agent(recurrent PPO)에게도* hard 인가?
  → #3 과 동일한 사전약정 `classify_headroom(frac=0.75, k=1.0)` 을 **다중-타입 config 의**
  recurrent PPO held-out gym-clears 에 적용.
- **(B) 상대 깊이**: 다중-타입이 단일-타입보다 **robust 하게 더 어려운가**? oracle 천장이 config
  마다 다르므로(5.00 vs 3.62) **oracle-fraction 으로 정규화**해 비교. 사전약정 depth 규칙(아래).

**정직성(이니셔티브 계승)**: 판정 규칙·임계는 **G1 freeze 시 데이터와 무관하게 고정**(p-hacking
차단). 어떤 branch 가 나와도 그대로 보고(반증 포함 — "not-deeper" 면 그대로 기록). proxy·budget·
seed·CPU 라벨. #3 선례: 임계 고정 후 seed 확충(3→5)은 허용(노이즈 교정), 임계 변경은 불가.

## 사전약정 판정 규칙 (G1 freeze 시 데이터와 무관하게 고정)

- **(A) `classify_headroom(rec_multi_runs, oracle_multi, frac=0.75, k=1.0)`** (기존 함수 재사용,
  임계 #3 과 동일):
  - `hard-and-learnable`(mean+std ≤ 0.75·oracle) → **(a) hard-for-memory-agent ROBUST**
  - `ppo-closes`(mean−std ≥ 0.75·oracle) → **(b) closes — reframe, 사람 보고 stop**
  - else → inconclusive → seed 확충(임계 불변) 또는 정직 보고.
- **(B) depth 규칙 (신규 헬퍼 `classify_depth`)** — run 별 oracle-fraction
  (`frac_i = gym_clears_i / oracle`, config 별 oracle 로 정규화) 에 대해:
  - `deeper-robust`: `mean(frac_single) − mean(frac_multi) > max(std_single, std_multi)`
    **그리고** 양쪽 oracle winnable(≥ 0.5·num_gyms). (#1·#2 의 "effect > max std" 관례.)
  - `not-deeper`: `mean(frac_single) − mean(frac_multi) ≤ 0` → scout Δ 반증, 그대로 보고.
  - else → `inconclusive`.
- **runs**: 기본 3. borderline(±1 std 이내) 시 5 로 확충(임계 불변, #3 선례). budget: CPU,
  recurrent PPO 만(질문이 "가장 강한 agent" 이므로 ff 불요 — #3 이 ff floor 는 이미 측정).

## 선행 조건

- #4 산출물(main): `multitype_hard_env_spec`/`hard_env_spec`, parity 0 게이트
  (`test_jax_multitype_boss_parity.py`), `boss_secondary` opt-in, scout(전제 검증).
- `headroom.classify_headroom`(사전약정 A 재사용), `train_recurrent_ppo`/
  `evaluate_gym_clears_recurrent`, `learning_verdict`, numpy oracle(`reference_arm`).
- 참조 패턴: `scripts/hard_benchmark_memory.py`(#3 의 공식 측정 script 구조 — --quick/--runs,
  사전약정 출력, 정직 라벨).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 종류 | 영향도 | 변경 요지 |
|---|---|---|---|
| `src/critter_gym/headroom.py` | 수정(추가만) | 낮음 | `classify_depth(single_fracs, multi_fracs, ...)` 순수 함수 + verdict NamedTuple. 기존 `classify_headroom` 무변경 |
| `tests/test_headroom.py` | 수정(추가만) | 낮음 | classify_depth 3-branch 단위 테스트(deeper/not-deeper/inconclusive/입력검증) |
| `scripts/multitype_boss_headroom.py` | 신규 | 낮음(런타임) | 공식 측정 script: --quick/--runs, 사전약정 A+B 적용, 정직 라벨 |
| `docs/reference/multitype-boss.md` | 수정 | 낮음 | "Scout finding" 아래 측정 결과 섹션 추가(branch 그대로) |

기존 env/JAX 코드 **무변경**(#4 가 전부 준비). additive.

### 영향 범위

- `headroom.py` 추가만 → 기존 `classify_headroom` 소비처(#3 script) 무영향. script 는 신규.

## Step별 계획

**Step 1 (Red→Green): `classify_depth` 사전약정 헬퍼**
- `headroom.py` 에 `DepthVerdict` NamedTuple + `classify_depth(single_fracs, multi_fracs)` —
  위 (B) 규칙 그대로. 순수 numpy, 데이터 없이 규칙만 구현.
- 테스트: deeper-robust(gap>max std) / not-deeper(gap≤0) / inconclusive(0<gap≤max std) /
  빈 입력 ValueError / 단일 run(std=0) 경계.

**Step 2 (Red→Green): 공식 측정 script**
- `scripts/multitype_boss_headroom.py` — `hard_benchmark_memory.py` 구조 미러링:
  `--quick`(pilot smoke) / `--runs N`(기본 3). 흐름: 두 config(단일=`hard_env_spec`, 다중=
  `multitype_hard_env_spec`) 각각 oracle(numpy)+winnable 확인 → recurrent PPO ×N runs 학습
  → held-out gym-clears → run 별 oracle-fraction → **(A) classify_headroom(다중)** +
  **(B) classify_depth** → branch 출력 + 정직 라벨(CPU·N-seed·recurrent PPO 非SOTA·oracle
  proxy·grid16 단일 config·frac/k frozen 명시).
- smoke 테스트는 두지 않음(#3 도 script 자체는 무테스트 — 로직은 Step 1 헬퍼+기존 함수에 있고
  script 는 조립. `--quick` pilot 이 wiring 검증).

**Step 3 (pilot → 본측정)**
- pilot: `--quick --runs 1`(짧은 iter) 로 wiring·branch 출력 확인(freeze 된 규칙이 데이터 보기
  전에 print 되는지 확인).
- **본측정**: `--runs 3`(full iter 250, #3=300 과 유사 budget, CPU 백그라운드 실행) → 결과를
  report·reference 에 branch 그대로 기록. borderline 시 5 확충(임계 불변).

**Step 4 (문서)**: `multitype-boss.md` 에 "Measured (multi-seed)" 섹션 — branch·수치·경계 그대로.
scout 의 "1-seed raw" 경고를 측정 결과로 대체(또는 inconclusive 면 유지+확충 계획).

## 검증 방법

- `.venv/bin/python -m pytest -q` 전체 green, 회귀 0(baseline 620).
- `ruff check` / `mypy src/critter_gym/headroom.py`.
- pilot `--quick` 무오류 + 사전약정 규칙이 결과 전에 출력.
- 본측정 완주 + branch 출력. **어떤 branch 든 성공**(반증도 결과 — 정직 보고가 AC).

## 리스크

| 리스크 | 완화 |
|---|---|
| **p-hacking 외양** — 결과 보고 임계/규칙 조정 | 규칙·임계 G1 freeze(본 plan §사전약정). 변경 불가, seed 확충만 허용(#3 선례). |
| 본측정 런타임(CPU, 6+ trainings) | 백그라운드 실행+폴링. pilot 으로 wiring 선검증. #3 이 동급 budget 완주 선례. |
| inconclusive(고분산 — #3 도 std 1.05) | 사전약정에 확충 경로 명시(3→5, 임계 불변). 그래도 inconclusive 면 정직 보고+후속. |
| scout Δ 반증(not-deeper) | 그대로 보고(반증도 가치 — 레버 무효면 다른 레버로). 헤드라인 금지 문화. |

## Acceptance Criteria (G1 통과 시 freeze)

1. `headroom.classify_depth` 신규(순수·사전약정 규칙 그대로) + 단위 테스트(3 branch+경계).
   기존 `classify_headroom` 무변경.
2. **사전약정 freeze**: (A) `classify_headroom(frac=0.75, k=1.0)` on 다중-config recurrent PPO,
   (B) `classify_depth`(gap>max std ∧ 양쪽 winnable → deeper-robust; gap≤0 → not-deeper),
   runs 기본 3(borderline 시 5, 임계 불변) — 본 plan 에 고정되었고 script 가 결과 전에 규칙을 출력.
3. `scripts/multitype_boss_headroom.py` — `--quick` pilot 무오류, 두 config oracle+winnable,
   recurrent PPO ×N, (A)+(B) branch 출력, 정직 라벨(CPU·seed·非SOTA·proxy·frozen 명시).
4. **본측정 완주**(≥3 runs, full budget): (A)·(B) branch 산출 — **어떤 branch 든 그대로 보고**
   (반증 포함). borderline 시 확충 후 최종 branch.
5. 회귀 0(전체 스위트, baseline 620), ruff/mypy clean.
6. `multitype-boss.md` 측정 결과 섹션 갱신(branch·수치·경계 그대로). CHANGELOG 1줄.
