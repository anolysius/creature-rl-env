---
slug: learnability-precision
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/learnability.py
  - scripts/learnability.py
  - tests/test_learnability.py
  - DESIGN.md
extracted_to: []
supersedes: []
---

# learnability 정밀 재측정 — gym-clear-only 메트릭으로 caveat 해소

> 작성일: 2026-06-23 | 상태: 계획

## 목표

#17(`learnability-measurement`)의 **정직한 caveat 1번**을 메운다: 현재 `run_episode` return =
**격파(+1) + 진화(+1) 합산** → `learned`가 `oracle`을 "넘는" 착시(진화 보상이 cross-arm gap을 noise).
정밀 주장을 위해 **gym-clear-only 메트릭**(진화와 분리한 보스 격파율)을 도입해 reference arm·learned를
*깨끗하게* 비교한다.

**Pilot(freeze 전, 통과)**: held-out 16시드, commit LCFG에서 gym-clear-only(=`sum(env._gym_defeated)`) 측정 —
oracle/infer **2.06(69%)** ≫ type_blind 1.25(42%) > probe 1.00(33%). 합산 return(oracle/infer 3.25)을
부풀린 진화(~1.19)가 제거되고 **load-bearing 순서(oracle≥infer≫type_blind>probe)는 유지**. → 메트릭 분리가
착시를 제거하면서 신호를 보존함을 입증.

**EC 매핑**: 활성 M3 신뢰성 + (A) learnability 정밀화. arXiv writeup(M3-EC4)이 인용할 수치 견고화 — 선행 task.

**정직성 원칙**: acceptance는 성능/주장이 아니라 *메트릭 분리 + 정직 보고*로 freeze. gym-clear-only는 더
깨끗한 비교지 여전히 단일 config의 신호. 다중 *학습* run(학습 분산)은 `[rl]` 스크립트 옵션으로 노출하되
core CI 비검증(헤비/머신 의존) — 정직하게 표기.

## 선행 조건

- `critter_gym.learnability` (`run_episode`/`measure_learnability`/`LearnabilityReport`/reference arms) — 확장 대상
- `scripts/learnability.py` (PPO 학습→arm 대조, `[rl]`) — gym-clear-only 보고로 갱신 + 다중 run 옵션
- `env._gym_defeated`(격파 수)·`env._evolved`(진화 수) — 분리 메트릭 소스 (이미 존재, obs 무변경)

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/learnability.py` | `EpisodeOutcome`(return/gyms_cleared/evolutions) 도입 + `run_episode`가 outcome 반환 + `LearnabilityReport`에 gym-clear-only means 추가(combined와 병기) | 중 (API 확장, 무회귀) |
| `scripts/learnability.py` | 보고를 gym-clear-only 중심으로 + `--runs N`(다중 PPO seed 평균, 단일run caveat 완화) | 저 (`[rl]`, 소비자) |
| `tests/test_learnability.py` | gym-clear-only 메트릭이 진화와 분리됨 + 순서(oracle≥infer>type_blind≥probe) + combined API 무회귀 | 저 (append) |
| `DESIGN.md` (§3.1.1 follow-up) | learnability 문단에 "gym-clear-only로 정밀 재측정, 진화 분리, 순서 유지" 반영 | 저 |

### 영향 범위

- `learnability.py`는 측정 전용(obs/env step 무변경). `run_episode` 시그니처가 float→`EpisodeOutcome`로 바뀌면
  `arm_mean`/`measure_learnability` 내부 호출 갱신 필요 — **공개 `measure_learnability` 시그니처는 보존**, report에
  gym-clear-only 필드 *추가*만(소비자 무회귀). numpy-only 유지. `[rl]` 스크립트는 소비자.

## Step별 계획

1. **(freeze 전) Pilot** — 완료(위). 메트릭 분리 achievability·순서 보존 입증.
2. **Red** — `test_learnability.py`: gym-clear-only가 진화와 분리(oracle combined>gym-clear) + 순서(oracle≥infer>type_blind≥probe, gym-clear 기준) + `measure_learnability` combined 무회귀 테스트 작성(fail 확인).
3. **Green** — `EpisodeOutcome` + `run_episode` outcome 반환 + `LearnabilityReport`에 `heldin_gyms`/`heldout_gyms`(gym-clear-only) 추가, `to_markdown`에 병기. `arm_mean`/`measure_learnability` 갱신(combined 보존).
4. **Green** — `scripts/learnability.py`: gym-clear-only 중심 보고 + `--runs N` 다중 PPO seed 평균(±range), 단일run caveat 완화. `importorskip` smoke 무회귀.
5. **보고** — DESIGN §3.1.1 follow-up 문단 갱신(진화 분리 정밀 재측정, 순서 유지; 여전히 단일 config·다중run은 [rl]).
6. **Refactor + 무회귀** — 전체 테스트·mypy·ruff·build.

## 검증 방법

- `pytest -q` — 신규 gym-clear-only 테스트 + 전체 무회귀(171→증가, 회귀 0).
- `measure_learnability` combined API 무회귀(기존 호출부·스크립트).
- `[rl]` smoke(`importorskip`) 무회귀.
- mypy/ruff/build clean.

## 리스크

1. **`run_episode` float→`EpisodeOutcome` 변경이 소비자 회귀** → 공개 `measure_learnability`/report combined 필드 보존, gym-clear는 *추가* 필드. 내부 호출만 갱신.
2. **gym-clear-only가 순서를 뒤집을 위험** → pilot이 순서 보존 입증(oracle≥infer≫type_blind>probe). 미달이면 정직 보고.
3. **다중 run이 헤비/머신 의존** → core CI 비검증, `[rl]` 스크립트 옵션 + 정직 표기(단일run caveat는 완화지 제거 아님).
4. **(L1 measurement reviewer) ceiling-compression confound** — gym-clear-only는 [0, num_gyms=3] bounded count → 진화-인플레이션을 제거하는 대신 **천장 압축**(oracle 이미 2.06/3=69%) 도입. 강한 arm끼리 gap이 3 근처에서 붕괴 가능 = num_gyms=3이 민감도 한계. DESIGN/report에 *명시 caveat*.
5. **(L1 measurement reviewer) oracle==infer 구분불가** — pilot에서 oracle=infer=2.06. 이 config는 gym 타입이 충분히 재출현해 **한 번 보면 추론이 자명**해져 infer가 oracle을 따라잡음 → gym-clear-only가 oracle/infer를 분리 못 함(추론이 *load-bearing 스킬*임을 이 메트릭만으로는 증명 못 함). 흥미로운 실측이나 *과대해석 금지* — DESIGN/report에 caveat로 명시(AC3 순서를 `oracle≥infer` 등호 허용으로 둔 이유).

## Acceptance Criteria (G1 통과 시 freeze)

> *메트릭 분리 + 정직 보고*로 freeze (성능/주장 아님). 신호지 튜닝 수치 아님.

- **AC1** — `EpisodeOutcome`(return/gyms_cleared/evolutions) 도입 + `run_episode`가 이를 반환(보스 격파와 진화 분리).
- **AC2** — `LearnabilityReport`가 **gym-clear-only means**를 combined와 **병기**(held-in/held-out, 각 arm + learned). `to_markdown` 표에 노출.
- **AC3** — gym-clear-only 메트릭이 **진화 보상과 분리**됨을 테스트로 입증(oracle combined > oracle gym-clear; 진화분 = 차이) + **load-bearing 순서 보존**(gym-clear 기준 oracle≥infer, 둘 다 > type_blind≥probe).
- **AC4** — 기존 공개 API 무회귀: `measure_learnability` 시그니처 + combined 필드 보존, `scripts/learnability.py` `importorskip` smoke 통과.
- **AC5** — `scripts/learnability.py`가 gym-clear-only 중심 보고 + `--runs N` 다중 PPO seed 평균(단일run caveat 완화). 정직 표기(다중run·[rl] 비CI).
- **AC6** — 무회귀: 전체 테스트 회귀 0, mypy/ruff/build clean. DESIGN §3.1.1 follow-up 갱신 — 진화 분리 정밀 재측정·순서 유지 + **잔여 caveat 정직 명시**: (i) gym-clear ceiling(num_gyms=3, 천장 압축), (ii) oracle==infer 구분불가(config가 한 번 보면 추론 자명, 이 메트릭만으로 추론 load-bearing 증명 아님), (iii) 단일 config·N modest·다중run [rl]비CI. honesty 가드 무회귀.
