---
slug: difficulty-dynamic-range
initiative: difficulty-scaling
status: active
started: 2026-06-24
acceptance_freeze: true
domains: [rl-env]
task_type: env
mode: standard
scope_paths:
  - src/critter_gym/region.py
  - src/critter_gym/envs/critter_env.py
  - scripts/difficulty_generalization.py
  - tests/test_difficulty_dynamic_range.py
  - docs/explanation/competitive-analysis.md
  - DESIGN.md
  - docs/CHANGELOG.md
  - docs/_active/difficulty-scaling/INITIATIVE.md
extracted_to: []
supersedes: [discriminating-difficulty]
---

# difficulty-dynamic-range — gym 수 확대·안정화로 변별 분해능↑ (pilot 발견 기반, numpy-first)

> 작성일: 2026-06-24 | 상태: 계획 | 마일스톤: **M3 신뢰성** (difficulty-scaling INITIATIVE; (A) "hard-and-gap≈0"의 *hard* 쪽 — 변별 분해능)

## 한 문단 요약 (수식 없이)

직전 슬러그(`discriminating-difficulty`)의 pilot이 중요한 걸 밝혔습니다: "이길 카드가 없어서 막힌다"는 진단은 *틀렸고*, 똑똑한 플레이(oracle)와 멍청한 플레이(blind)는 *이미* 점수가 갈립니다(gym당 +1.0). 진짜 문제는 **한 판에 도장(gym)이 평균 2개뿐**이라 점수 범위가 좁아 "얼마나 잘하는지"를 **세밀하게 구별 못 한다**는 것이었습니다. 또 카드를 다양하게 줘도 가위바위보 구조상 *고정 카드 하나가 우연히 절반을 이겨* 별 도움이 안 됐습니다. 그래서 이번엔 **도장 수를 늘리고 안정화**해서 점수 범위를 넓힙니다 — 그러면 잘하는 AI와 못하는 AI의 점수 차가 (2 vs 1이 아니라) 6 vs 3처럼 *또렷하게* 벌어져 **변별 분해능이 올라갑니다.** 추론이 가능하려면 같은 타입이 한 판에 다시 나와야 하므로(재출현) 그 구조는 **건드리지 않습니다.** "PPO조차 못 푸는 초고난도"는 훨씬 큰 일이라 이번 범위 밖으로 정직히 둡니다.

## 목표 / 동기 (pilot 발견 박제)

직전 pilot(measure_learnability, d2_hard, held-out, gym-clear-only):
- **winnability 정상**: oracle 2.06 ≈ 에피소드당 실제 gym 수(vary 평균 ~2.0) — oracle은 존재하는 gym 거의 다 클리어. "천장 ~0.6"은 max(3) 대비 분수였을 뿐.
- **변별 이미 존재**: oracle 2.06 vs type_blind 1.06 = **spread +1.0/gym**.
- **다양화 무력**: 토너먼트 차트에선 고정 챔피언 하나가 ~절반 우연 카운터 → 보스 풀 넓혀도 spread 0.35→0.54로 미미.
- **재출현↓ 금지**: 차트가 seed별 생성이라 재출현 없으면 in-episode 추론 불가 → moat 붕괴.

**→ 확실한 변별 레버 = 동적 범위**. gym 수가 평균 2(범위 1–3)로 좁아 변별 *분해능*과 절대 spread가 압축됨. **gym 수를 늘리고 안정화**(예: 정확 8)하면 oracle−blind 절대 spread가 ~비례 확대(2 vs 1 → 예: ~6 vs ~3)되어 능력 변별이 또렷해진다. 추론 구조(재출현)는 보존. 

**acceptance = 측정 + 정직 보고**(§4 교훈, 성능 freeze 아님): gym 수↑가 (i) 변별 절대 spread를 키우는지(분해능↑) + (ii) winnability/oracle 천장이 스케일에서 유지되는지 + (iii) 학습 gap이 ≈0 유지인지를 사전약정 규칙으로 보고. **numpy-first**(JAX 재포트는 후속 R5). **범위 밖 정직 명시**: "PPO가 oracle에 못 닿는 hard-benchmark"는 본 task 아님(future work).

## 선행 조건

- 기존 `learnability`(oracle/infer/type_blind/probe, gym-clear-only) + `difficulty_generalization`(`classify_gap`, multi-run) **재사용**.
- 재출현 구조(`generate_region`의 보스 pool) **보존** — 추론 가능성 유지(pilot 교훈).
- env 코어 무회귀: 기본(M1·기존 commit-v0·기존 difficulty 점) **무변경** — gym-수 제어는 **opt-in**(기본값 = 현 동작).
- **JAX 무변경**: `jax_env`/`jax_train`은 _MAX_GYMS=3 하드코딩 → 본 task 무변경. 검증되면 후속 `jax-difficulty-report`(R5).
- **branch**: `feature/difficulty-dynamic-range` (이미 생성). main 직접 금지.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/region.py` | param 추가 | 중 | `generate_region(..., min_gyms=None)` — vary 시 `n_gyms = randint(min_gyms, max_gyms+1)`. 기본 None=현 `_MIN_GYMS`(=1) 무변경. `min_gyms==max_gyms`면 정확 개수. 재출현 pool 로직 보존(`pool_size=max(2,n_gyms//2)`는 그대로 — gym↑면 재출현도 늘어 추론 room↑). |
| `src/critter_gym/envs/critter_env.py` | config 추가 | 중 | `min_gyms: int \| None = None` config → generate_region에 전달. 기본 None=무회귀. obs `gyms_defeated` bound(=num_gyms) 불변. |
| `scripts/difficulty_generalization.py` | 추가 | 중 | (i) 고-gym config(들)(num_gyms=8, min_gyms=8) (ii) **변별 분해능 측정**(gym수 ∈ {3,5,8}서 oracle−type_blind 절대 spread, `measure_learnability` 재사용) + 사전약정 규칙 함수 (iii) gap(multi-run+`classify_gap`). |
| `tests/test_difficulty_dynamic_range.py` | 신규 | 중 | numpy-only: ① region min_gyms(정확 개수·범위·기본 무변경) ② 변별 property(고-gym서 oracle−type_blind 절대 spread > 저-gym, 고정 seed) ③ winnability(oracle이 고-gym서도 대부분 클리어) ④ backward-compat(기본 config 동일 trajectory). |
| `docs/explanation/competitive-analysis.md` | 갱신 | 저 | "a hard benchmark" 행(변별 분해능 진전 + 정직 한계). |
| `DESIGN.md` | 갱신 | 저 | §3.1.1 "Toward hard-and-gap≈0" — pilot 발견 + 동적 범위 결과 1문단. |
| `docs/CHANGELOG.md` · `INITIATIVE.md` | append | 저 | task-end. |

### 영향 범위 (import 그래프)

`generate_region` ← `critter_env`(reset), `jax_env`(jax_reset — **본 task 미사용 param**), bench/baseline scripts. `min_gyms` 기본 None이라 **모든 기존 호출 무변경**. `learnability`/`generalization`/`difficulty_generalization` 재사용. **jax_env/jax_train 무변경**. 기존 287 tests 무회귀.

## Step별 계획

> **G1 freeze 전 PILOT** — 직전 슬러그 pilot이 *measure-first*로 메커닉을 falsify한 교훈. 이번엔 *동적 범위가 실제로 절대 spread를 키우는지*를 freeze 전 측정(사전약정 규칙으로 분기). (이미 측정한 현-config baseline = oracle−blind ~1.0/gym, 평균 2 gym.)

1. **region min_gyms** — `generate_region`에 floor/exact 제어. pilot: num_gyms ∈ {3,5,8}(min=max)서 평균 gym 수·재출현(타입당 gym 수) 확인.
2. **env config** — `min_gyms` opt-in. 기본 None 무회귀(동일 trajectory) 확인.
3. **변별 분해능 측정(pilot 핵심)** — 각 gym 수서 `measure_learnability`로 oracle/infer/type_blind 절대 gym-clear + spread. 사전약정 규칙으로 "분해능↑ 달성" 판정.
4. **학습 gap** — 고-gym config서 학습 정책 gap(multi-run + `classify_gap`) — gap≈0 유지(분해능↑하면서 일반화 보존 = 강한 결과) or real-gap(둘 다 결과).
5. **테스트 + 문서**.

## 검증 방법

- **CI(numpy-only)**: 기본 무회귀 → 287 tests green. 신규 property 테스트 numpy-only(scripted, 결정론). PPO는 script(`[rl]`, importorskip).
- **canonical**: `mypy src`·`ruff check .`·`pytest -q`·`python -m build` clean.
- **분해능 입증**: 고-gym서 oracle−type_blind 절대 spread > 저-gym(사전약정 margin) + winnability 유지. 정직 보고(과대 금지·범위 밖 명시).

## 리스크 / Pilot (freeze 전)

| # | 리스크 | Pilot 검증 | 분기 |
|---|---|---|---|
| R1 | **분해능이 안 커짐** — gym↑인데 oracle/blind 둘 다 비례 상승해 *비율*만 같고 절대 spread 도움 안 됨. | gym ∈ {3,5,8}서 절대 spread 측정. | (a) 절대 spread 확대 → 달성 / (b) 미확대 → 정직 reframe(동적 범위로 불충분, 한계 보고). |
| R2 | **고-gym서 winnability/ceiling 붕괴** — gym 많아지면 oracle이 못 다 깸(max_steps·내비·강보스). | oracle gym-clear/num_gyms 비율. | 비율 유지면 OK; 떨어지면 max_steps↑(config) 동반 or 정직 보고. |
| R3 | **재출현 희석** — gym↑인데 pool도 커져 타입당 gym 수가 줄면 추론 room↓(infer→probe). | 타입당 gym 수 측정(pool_size 보존하므로 gym↑면 재출현↑ 기대). | 희석되면 pool_size 조정(재출현 유지). |
| R4 | **gap 깨짐** — 고-gym서 held-in floor 또는 real-gap. | 학습 gap multi-run. | `classify_gap` 사전약정대로 보고(전부 정직 결과). |
| R5 | **무회귀 위반** — min_gyms 기본값이 기존 동작 바꿈. | 기본 None서 기존 seed 동일 trajectory 테스트. | 위반 0이어야. |

**사전약정 결정규칙 (데이터 보기 전 고정):**
- **분해능↑ 달성 (R1)**: scripted, 고-gym config(num_gyms=8, min=8)서 **oracle − type_blind 절대 gym-clear spread ≥ 2.0**(현 baseline ~1.0의 ≥2배) **AND** num_gyms ∈ {3,5,8}서 spread가 **단조 증가**(gym↑→spread↑). 둘 다 충족 = 달성. 미충족 = 정직 reframe.
- **winnability 유지 (R2)**: 고-gym서 oracle gym-clear / num_gyms ≥ 0.70(현 ~1.0 수준 유지 — 스케일에서 천장 안 무너짐).
- **gap (R4)**: 기존 `classify_gap`(floor=0.3·k=1.0), std-across-runs. 어느 결과든 정직 보고.
- **무회귀 (R5)**: min_gyms=None일 때 기존 generate_region 출력 byte-identical(동일 seed→동일 region).

**정직성 사전약정 (박제):**
- 변별 주장 = scripted oracle vs blind **절대 spread 확대**(분해능)로만. "어려운 벤치"의 *분해능* 측면 진전이지, "PPO가 못 푸는 hard-benchmark"는 **명시적 범위 밖**(future work — 더 깊은 추론/전략 필요).
- 직전 pilot의 다양화-falsify를 정직 박제(헛된 메커닉 회피 기록). JAX 미포함=후속 라벨.
- 학습 결과 single-config·N·multi-run caveat. pilot이 R1 falsify하면 정직 reframe.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1** — `region.py` `generate_region(..., min_gyms=None)`: vary 시 gym 수 floor/exact 제어. 기본 None=`_MIN_GYMS`(무변경). 재출현 pool 로직 보존.
- **AC2** — `critter_env.py` `min_gyms: int|None = None` opt-in config → generate_region 전달. 기본 None=무회귀. obs 형태 불변.
- **AC3** — `difficulty_generalization.py`에 (i) 고-gym config (ii) **변별 분해능 측정**(gym ∈ {3,5,8}서 oracle−type_blind 절대 spread, `measure_learnability` 재사용) + 사전약정 규칙 함수 (iii) gap(multi-run + `classify_gap`).
- **AC4** — **측정 + 정직 보고**(성능 freeze 아님). 헤드라인이 사전약정 결정규칙(분해능↑ 달성/미달 + winnability + gap verdict)과 일치 + caveat 라벨. **"PPO 못 푸는 hard-benchmark는 범위 밖" 명시**.
- **AC5** — `tests/test_difficulty_dynamic_range.py`(numpy-only): region min_gyms(정확/범위/기본 무변경) / 변별 property(고-gym 절대 spread > 저-gym, 고정 seed) / winnability(고-gym oracle 대부분 클리어) / backward-compat(기본 동일 trajectory).
- **AC6** — core CI numpy-only 불변: 287 tests 무회귀(기본 None opt-in), PPO `[rl]` importorskip. canonical clean.
- **AC7** — **freeze 전 pilot**으로 R1(분해능)·R2(winnability)·R3(재출현) 측정 → 사전약정 규칙이 분기 확정. falsify 시 정직 reframe. pilot 결과·규칙·확정 분기 report 박제.
- **AC8** — 문서: DESIGN §3.1.1(pilot 발견 + 동적 범위 결과 + 범위 밖 명시) + competitive-analysis + CHANGELOG + INITIATIVE. JAX 재포트 후속(R5) 명시. broken-link 0.

## 후속 / 마일스톤

- **JAX 재포트(후속 `jax-difficulty-report`, R5)**: 동적 범위 검증되면 `jax_env` _MAX_GYMS 가변화 재포트.
- **더 깊은 hard-benchmark(별도 이니셔티브급)**: "PPO가 oracle에 못 닿는" 변별(다중타입 보스·부분관측·전략 깊이)은 본 task 밖 — 큰 연구. 본 task는 *분해능* 한 레버.
- **커밋 단위**(feature/difficulty-dynamic-range): ① region min_gyms+테스트 → ② env config → ③ pilot 후 측정+문서.
