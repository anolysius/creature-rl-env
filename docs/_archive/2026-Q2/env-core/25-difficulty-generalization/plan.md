---
slug: difficulty-generalization
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - scripts/difficulty_generalization.py
  - tests/test_difficulty_generalization.py
  - DESIGN.md
extracted_to: []
supersedes: []
---

# 난이도 일반화 — 학습정책 gap-at-difficulty 실험 ("hard-and-gap≈0")

> 작성일: 2026-06-23 | 상태: 계획

## 목표

DESIGN §3.1.1 로드맵: "쉬운 env에서 gap≈0은 능력 예측력 약함 → 난이도를 올리며 seed split 유지해 *hard-and-gap≈0*".
**진짜 측정 = 학습 정책**(scripted은 암기 불가라 gap≈0이 trivial). 여러 **난이도 config**에서 PPO를 held-in 시드에
학습→**held-in vs held-out 일반화 gap**을 측정해 "난이도 강도가 올라가도 gap≈0(암기 아닌 일반화)이 유지되는가"를
*신호*로 보고. 기존 `critter_gym.generalization.measure_generalization` 재사용.

**Pilot이 falsify한 것(정직 계승)**: "깨끗한 단조 난이도 사다리 + scripted 측정"은 불가 입증 — 난이도가 **다차원**
(num_types=추론난이도는 blind엔 *쉬움*; 보스 stat=승리난이도는 **cliff**), oracle 천장 ~0.625(스타터 3종 vs 12 타입).
→ config를 "**난이도 점(points)**"으로 두지 "calibrated 사다리"로 주장 안 함. 측정은 *학습정책 gap*.

**EC 매핑**: 활성 M3 신뢰성 + (A) "hard-and-gap≈0" 전진. 비교분석 갭 register의 "난이도" 항목 직결.

## 선행 조건

- `critter_gym.generalization`(`measure_generalization`/`split_train_pool`/`GapReport`) — 재사용
- `scripts/learnability.py`/`train_ppo.py` — PPO 래핑 + held-in eval 분리 패턴 선례
- pilot(완료): 난이도 다차원·cliff·oracle 천장 입증 → config=점, 측정=학습 gap

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/difficulty_generalization.py` (신규, `[rl]`) | N개 난이도 config(증가하는 knob 강도) × PPO held-in 학습 → `measure_generalization`로 held-in vs held-out gap. `split_train_pool`로 held-in eval을 학습시드와 disjoint | 신규, `[rl]` 격리 |
| `tests/test_difficulty_generalization.py` (신규) | `importorskip` smoke(tiny budget, 1 config) → GapReport 유한 + held-in/held-out 분리 가드 | 신규 |
| `DESIGN.md` (§3.1.1) | "hard-and-gap≈0"은 학습정책 실험(스크립트)·scripted 난이도 proxy는 다차원(정직) + 측정 결과 신호 | 저 |

## Step별 계획

1. **(freeze 전) Pilot** — 완료(깨끗한 사다리 falsify → 학습 gap 실험으로 reframe).
2. **Red** — `test_difficulty_generalization.py`: 스크립트 `train_and_gap` import + tiny PPO budget 1 config → `GapReport` 유한, held-in/held-out split 가드(누수 ValueError) 테스트. `importorskip` 격리.
3. **Green** — `scripts/difficulty_generalization.py`: 난이도 config 점들(예: d0 mild → d2 commit+큰차트+강보스) + `train_and_gap(config, timesteps, seed)`(PPO held-in 학습→`measure_generalization`) + `main`(config별 gap 출력 + "gap≈0 유지?" 정직 서술).
4. **실측 + 보고** — modest budget으로 config별 PPO 학습→gap 측정(killer-demo/learnability 선례). 결과를 report+DESIGN에 *신호*로 기록.
5. **무회귀** — 전체 테스트(181 + smoke)·mypy·ruff·build.

## 검증 방법

- `pytest -q` — smoke(importorskip) 포함 전체 무회귀(181 불변, sb3 있으면 smoke pass).
- `measure_generalization` 재사용(누수 가드 상속) — held-in/held-out 분리 ValueError 동작.
- 실측 gap 수치는 report에 *신호*로(단일run·N·비CI 정직 표기).
- DESIGN §3.1.1: scripted 난이도 proxy 다차원·cliff(pilot) + 학습정책 gap이 진짜 측정 명시.
- mypy/ruff/build clean. core CI numpy-only 유지(PPO는 `[rl]` 뒤).

## 리스크

1. **"난이도 사다리" 과대주장** → config=점, "calibrated 단조" 주장 0. pilot falsification을 DESIGN/report에 명시.
2. **gap이 난이도서 커지면?**(일반화 깨짐) → *정직 보고*(hard에서 gap↑면 그게 결과). freeze는 측정+보고지 "gap≈0 입증" 아님.
3. **단일 run·작은 N** → 신호로 표기, 다중run은 향후([rl]).
4. **PPO 비용** → smoke는 tiny, 실측은 modest budget(머신 의존, 비CI).

## Acceptance Criteria (G1 통과 시 freeze)

> *측정 산출 + 정직 보고*로 freeze (성능/"gap≈0 입증" 아님). config=난이도 점, 측정=학습정책 gap.

- **AC1** — `scripts/difficulty_generalization.py`(`[rl]`): ≥3 난이도 config(증가 knob 강도) + `train_and_gap`(PPO held-in 학습 → `measure_generalization` held-in vs held-out gap). held-in eval은 `split_train_pool`로 학습시드와 disjoint.
- **AC2** — `tests/test_difficulty_generalization.py`: `importorskip` smoke(tiny budget) → `GapReport` 유한 산출 + held-in/held-out split 누수 가드 동작.
- **AC3** — **정직 보고**: config는 "난이도 점"(calibrated 단조 사다리 아님 — pilot이 falsify: 난이도 다차원·cliff·oracle 천장). 측정은 *학습정책 gap*(scripted gap≈0은 trivial). 결과는 단일run·N modest·비CI = *신호*.
- **AC4** — 실측 산출: config별 PPO 학습→held-in/held-out gap 수치를 report에 기록. **N_heldin/N_heldout 고정**(learnability 선례 16/16) + **`EvalResult.std`(per-seed 표준편차)를 gap 옆에 표시**해 작은 N에서 작은 gap이 유의해 보이지 않게(L1 reviewer 반영). 난이도 강도↑에서 gap 거동을 정직 서술 — gap≈0(±std 내) 유지면 신호, 깨지면 그대로 보고.
- **AC5** — DESIGN §3.1.1 갱신: "hard-and-gap≈0"은 학습정책 실험(스크립트)이고 scripted 난이도 proxy는 다차원/cliff(pilot)임을 정직 명시.
- **AC6** — 무회귀: 전체 테스트 회귀 0(181 + smoke), core CI numpy-only(PPO는 `[rl]`), mypy/ruff/build clean. honesty 가드 무회귀.
