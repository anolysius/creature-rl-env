---
slug: difficulty-gap-rigor
initiative: difficulty-scaling
status: active
started: 2026-06-24
acceptance_freeze: true
mode: standard
domains: [rl-env]
scope_paths:
  - scripts/difficulty_generalization.py
  - tests/test_difficulty_generalization.py
extracted_to: []
supersedes: []
---

# 난이도 gap rigor — #24 약한 신호를 multi-run + 예산↑ + 사전약정으로 정밀화

> 작성일: 2026-06-24 | 상태: 계획 | 이니셔티브: difficulty-scaling (M3 신뢰성/(A))

## 목표

#24(difficulty-generalization)가 남긴 honest limit 을 해소한다. #24 는 난이도 점 3종(d0/d1/d2)의 held-in/
held-out gap 이 전부 **큰 per-seed std 안**이라 "gap≈0 과 consistent"라는 *약한 신호*만 줬다(저예산 40k·
**단일run**이라 작은 real gap 을 0 과 구분 불가). (B) `transfer-rigor`가 단일seed 신호를 multi-run 으로 4번
교정한 규율을 (A)에 적용: **`--runs N`(std-ACROSS-RUNS) + 예산↑ + 사전약정 결정규칙**으로 재측정하고, "hard
서도 gap≈0 robust"인지 "real gap 출현"인지 **정직 verdict**를 낸다. 핵심 통찰: "gap 이 real 이냐"의 불확실성은
**run 간 std**(gap 점추정의 run-to-run 변동)이지 #24 가 쓴 *한 run 내 per-seed std* 가 아니다.

**측정 정밀화이지 env 재설계 아님** — env 메커닉 무변경(스타터/보스 그대로) → JAX 포트 재작업(jax-throughput
R5) 없음. rigor 결과가 재설계 필요성·방향을 결정(사전약정 분기).

전진: M3 신뢰성 / (A) "hard-and-gap≈0" 정밀화.

## 선행 조건

- #24 산출 `scripts/difficulty_generalization.py`([rl]) + `tests/test_difficulty_generalization.py` +
  DESIGN §3.1.1 "Toward hard-and-gap≈0". 본 task 가 그 위에 multi-run 확장.
- `.venv` 에 sb3 2.7.1 설치됨([rl]). 실측은 **background**(sb3 numpy PPO, 100k×3 config×N run = ~수십 분).
- 측정 인프라 `critter_gym.generalization`(`measure_generalization`/`split_train_pool`, region split+leak
  guard) 재사용 — 새 core 모듈 불요(#24 패턴).

## 작업 범위

### 수정 대상 파일 (영향도 표)
| 파일 | 신규/수정 | 영향도 | 설명 |
|---|---|---|---|
| `scripts/difficulty_generalization.py` | 수정 | 중 | `train_and_gap_multirun(config, timesteps, runs)` 추가(서로 다른 PPO seed N run → gap **mean ± std-across-runs**) + `--runs N` CLI + 사전약정 결정규칙 함수 `classify_gap(gap_mean, gap_std, heldin_mean)`(→ `gap≈0 신호`/`real-gap`/`inconclusive`) + main 의 표·verdict 갱신. 기존 `train_and_gap`(단일run) 유지(smoke 호환). |
| `tests/test_difficulty_generalization.py` | 수정 | 저 | multi-run smoke(tiny budget, runs=2, 유한 결과) + `classify_gap` 결정론 단위 테스트(경계: gap<std→신호 / gap>std→real / heldin<floor→inconclusive). importorskip 유지. |

### 영향 범위 (import 그래프)
- 둘 다 `[rl]` 소비자/테스트 — core 무영향. `classify_gap` 은 순수함수(numpy-only, importorskip 불요 단위
  테스트 가능). 기존 281 tests 무회귀. env/core 무변경.

## Step별 계획

1. **pilot (freeze 전, 필수)** — (a) `classify_gap` 결정규칙을 **데이터 보기 전** 확정(사전약정): 임계 명시
   (예: |gap_mean| ≤ k·gap_std → 신호 / gap_mean > k·gap_std ∧ 난이도↑서 증가 → real-gap / heldin_mean <
   floor → inconclusive; k·floor 값 pilot 전 고정). (b) tiny multi-run(runs=2, timesteps=2k, 1 config)로
   **wiring + 1k step 당 벽시계**를 실측해 본 measurement 의 budget×runs feasibility 추정(예: 100k×3×5 가
   background 몇 분인지). pilot 이 (i) wiring 깨지거나 (ii) budget 이 비현실적이면 → 정직 reframe(예산/run 하향).
2. **multi-run 구현** — `train_and_gap_multirun`: runs 회 서로 다른 seed 로 `train_and_gap` 호출, gap 들의
   mean ± std(across-runs) 집계(+ held-in/held-out mean across-runs). `GapReport` 재사용 또는 경량 집계 dataclass.
3. **사전약정 결정규칙** — `classify_gap` 순수함수 + main 이 각 난이도 점에 적용해 verdict 라벨 출력.
4. **재측정(background)** — `--runs N --timesteps T`(pilot 가 정한 값)로 d0/d1/d2 실측. 결과를 report 에 기록.
5. **정직 verdict** — multi-run 결과로 #24 신호가 robust 한지/real-gap 인지/inconclusive 인지 박제 +
   env 재설계 필요성 함의. DESIGN §3.1.1 갱신(약한신호→multi-run rigor 결과).

**커밋 단위**: (c1) `classify_gap` + multi-run 함수 + `--runs` + 테스트 / (c2) 실측 결과 + verdict·report·DESIGN(task-end).

## Freeze 전 pilot 결과 + 사전약정 (2026-06-24)

**사전약정 결정규칙 (데이터 보기 전 고정 — p-hacking 차단):** `classify_gap(gap_mean, gap_std, heldin_mean)`,
임계 `floor=0.3`, `k=1.0`:
- `heldin_mean < 0.3` → **`inconclusive`** (정책이 거의 못 깸 → 일반화 논할 수 없음, generalist-mediocrity 아날로그)
- `gap_mean > 1.0·gap_std` → **`real-gap`** (robust 양성 gap = env 가 hard benchmark, Procgen 식 train→test 갭)
- `|gap_mean| ≤ 1.0·gap_std` → **`gap≈0-signal`** (run간 변동이 gap 을 swamp = gap≈0 과 robust consistent)
- `gap_mean < -1.0·gap_std` → **`inconclusive`** (held-out 이 더 쉬움 = 난이도 비대칭, 전이 아님)

여기서 `gap_std` = **std-ACROSS-runs**(gap 점추정의 run간 변동) — #24 가 쓴 *한 run 내 per-seed std* 가 아님(이게 rigor 의 핵심).

**타이밍 pilot (실측):** d0 config 2k step = 2.4s → **1.21s / 1k step**. 따라서 **100k × 3 config × 5 run ≈
30분 background = feasible**. wiring 확인(multi-run = `train_and_gap` 을 다른 seed 로 N회 루프 + gap 집계).
**확정 budget = 100k timesteps, 5 runs**(#24 의 40k·단일run 대비 예산↑ + multi-run). pilot 이 가정 falsify
안 함 → 본 scope 진행.

## 검증 방법

- `pytest -q` — 281 무회귀 + 신규 multi-run smoke + `classify_gap` 단위 테스트 green. CI numpy-only 유지
  (PPO smoke 는 importorskip, `classify_gap` 은 numpy-only).
- `mypy src`(jax_env 등 25) / `ruff check .` / `python -m build` clean. (script 는 mypy files=src 밖이나
  ruff 는 커버 — ruff clean 필수.)
- 실측: `--runs N` background. **단일run 아닌 multi-run** 으로 결론(방침). 사전약정 결정규칙으로 사후 편향 차단.

## 리스크

- **R1**: sb3 PPO 100k×3×N 이 background 로도 너무 김 → pilot 가 벽시계 실측 후 budget/runs 하향(정직 reframe).
- **R2**: multi-run 후에도 std-across-runs 가 커 gap 이 inconclusive 일 수 있음 — 그것도 **정직한 결과**(예산↑
   필요 신호). 헤드라인 강요 금지.
- **R3 (사후 편향)**: 결정규칙을 데이터 본 뒤 정하면 p-hacking → **freeze 전 pilot 서 사전약정**(임계 고정).
- **R4**: 난이도 점이 단조 사다리가 아님(#24 falsify) — "난이도↑서 gap 증가" 판정은 점들의 *경향*으로만(단조
   주장 금지). classify 는 점별 독립 + 경향 보조.
- **R5(이니셔티브)**: 본 task 는 env 무변경이라 JAX 재포트 위험 없음. (env 재설계는 후속 task 의 리스크.)

## Acceptance Criteria (G1 통과 시 freeze)

> 원칙: 성능/주장 아닌 **측정 + 정직 보고**로 freeze. 사전약정 결정규칙으로 사후 편향 차단. 결론은 multi-run.

- **AC1**: `scripts/difficulty_generalization.py` 에 `train_and_gap_multirun`(N run → gap **mean ± std-
  across-runs**) + `--runs N` CLI 추가. 기존 `train_and_gap` 유지(무회귀).
- **AC2**: **사전약정 결정규칙** `classify_gap(gap_mean, gap_std, heldin_mean)` 순수함수 — `gap≈0-signal`/
  `real-gap`/`inconclusive` 라벨. 임계는 **freeze 전 pilot 서 데이터 보기 전 고정**(plan/pilot 에 명시).
- **AC3**: `tests/test_difficulty_generalization.py` — multi-run smoke(tiny, importorskip) + `classify_gap`
  결정론 단위 테스트(3 라벨 경계 커버, numpy-only).
- **AC4**: 실측(background, `--runs N`, pilot 가 정한 budget) — d0/d1/d2 gap **mean ± std-across-runs** +
  각 점의 `classify_gap` 라벨을 report 에 기록. **single run 아닌 multi-run**.
- **AC5**: 정직 verdict report 박제 — #24 약한신호 대비 multi-run rigor 결과(robust gap≈0 / real-gap /
  inconclusive)와 **env 재설계 필요성 함의**. 과대 금지(std-across-runs 병기).
- **AC6**: 회귀 0 — 기존 281 tests green, mypy/ruff/build clean, core numpy-only 유지. DESIGN §3.1.1 갱신
  (약한신호 → multi-run 결과로 정정/강화).
- **AC7 (사전약정 분기)**: 재측정 결과로 verdict 분기(이미 사전약정된 classify 임계로) — (a) hard 점 gap≈0
  robust → "hard-enough-and-gap≈0 신호, 재설계 덜 시급" / (b) real-gap 출현 → "env 가 hard benchmark(자체로
  (A) 결과)" / (c) inconclusive(heldin floor/std 큼) → "예산/정책 필요, 재설계 전 측정 보강". 어느 분기든 정직 보고가 DoD.
