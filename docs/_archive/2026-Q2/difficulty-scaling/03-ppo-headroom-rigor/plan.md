---
slug: ppo-headroom-rigor
initiative: difficulty-scaling
status: active
started: 2026-06-25
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/headroom.py
  - scripts/ppo_baseline.py
  - tests/test_headroom.py
extracted_to: []
supersedes: []
---

# PPO oracle-headroom multi-run rigor — single-run 신호를 robust 주장으로

> 작성일: 2026-06-25 | 상태: 계획 | Initiative: difficulty-scaling (task 3) | 자율 런 KR1-hardening

## 목표

`jax-ppo-tuned`가 single-run으로 보인 **"tuned PPO가 oracle의 15–32%만 도달(hard-and-learnable)"**
헤드라인을 **multi-run(≥5 seed) + 사전약정 std-across-runs 결정규칙**으로 굳힌다. 과거 (B) 스레드에서
single-run이 노이즈로 4회 교정됐으므로, 이 마케팅 중심 주장을 "신호" → "robust"로 격상하는 것이 핵심.

**왜 (moat·마케팅)**: 벤치마크 결과 표의 신뢰도 = 헤드라인이 seed 노이즈가 아님을 보이는 것. "frontier
RL이 우리 hard 벤치의 oracle 15–32%만, *seed 전반 robust하게* 도달"이 방어 가능한 명제.

**Acceptance 성격**: *성능 아닌 측정+정직 보고*. 사전약정 결정규칙(데이터 전 고정)으로 p-hacking 차단.
multi-run서 headroom이 사라지면(PPO가 oracle 닫음) → 정직 reframe·정지.

## 선행 조건

- `jax_train.train_ppo`/`evaluate_gym_clears` (jax-ppo-tuned) — 재사용(무변경).
- `scripts/ppo_baseline.py` (이미 `--runs N` 지원) — robust verdict 추가.
- `learnability.measure_learnability` oracle (read-only).

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/headroom.py` | 신규 — `classify_headroom` 순수함수(numpy-only, 사전약정 frac=0.75·k=1.0) + `HeadroomVerdict` | 신규(CI numpy-only) |
| `scripts/ppo_baseline.py` | multi-run PPO/oracle ratio mean±std + `classify_headroom` robust verdict | 낮음 |
| `tests/test_headroom.py` | 신규 — `classify_headroom` 단위(numpy-only CI) | 신규 |

**영향**: `headroom.py`는 numpy-only(jax 미import) → **코어 CI에 포함**(jax_train과 달리). `jax_train`/
`jax_env` 무변경.

## Step별 계획

**Step 1 (Red)**: `tests/test_headroom.py` — `classify_headroom`: (a) PPO runs가 oracle 대비 robust
하게 낮으면(mean+k·std ≤ frac·oracle) `hard-and-learnable`, (b) PPO가 oracle에 근접(mean−k·std ≥
frac·oracle)이면 `ppo-closes`, (c) 그 사이면 `inconclusive`. 경계값·빈입력 가드. FAIL.

**Step 2 (Green)**: `src/critter_gym/headroom.py` — `HeadroomVerdict`(verdict·ppo_mean·ppo_std·
oracle·ratio) + `classify_headroom(ppo_runs, oracle, *, frac=0.75, k=1.0)`. 순수·결정론.

**Step 3 (측정)**: `ppo_baseline.py`가 `--runs` PPO gym-clear들을 모아 `classify_headroom` 적용,
mean±std + verdict 보고. 5-run으로 default+hard 실측.

**Step 4 (문서)**: jax-throughput.md PPO Update의 수치를 multi-run mean±std로 갱신 + robust verdict.
difficulty-scaling INITIATIVE task 3 행 + DESIGN §3.1.1 robust 라벨.

## 사전약정 결정규칙 (데이터 전 고정)

held-out gym-clear, k=1.0, frac=0.75:
- `mean(PPO) + k·std(PPO) ≤ frac × oracle` → **`hard-and-learnable`**(낙관적 PPO 상한도 oracle 75% 미만).
- `mean(PPO) − k·std(PPO) ≥ frac × oracle` → **`ppo-closes`**(비관적 PPO 하한도 75% 이상) → reframe·정지.
- 그 외 → **`inconclusive`**(robust 판정 불가, 더 많은 run/budget 필요 정직 보고).

## 검증 방법

- **freeze 전 pilot**: 임계(frac·k) 고정 + multi-run 파이프라인 작은 예산으로 end-to-end + `classify_headroom`
  property. headroom이 multi-run서 `ppo-closes`로 뒤집히면 reframe·정지.
- TDD: `pytest tests/test_headroom.py`(numpy-only, CI).
- 무회귀: 365 green + 신규. canonical.

## 리스크

| 리스크 | 완화 |
|---|---|
| multi-run서 headroom inconclusive(std 큼) | 사전약정이 inconclusive를 정직 결과로 인정. run↑ 권고 보고. |
| PPO가 multi-run서 oracle 닫음(`ppo-closes`) | reframe·정지(정지 조건). 단 single-run 15–32%로 볼 때 낮음. |
| 5-run × 2 config 시간 | JAX 빠름(single-run 36s) → 5-run ~3분 feasible. |
| headroom.py가 jax 끌어옴(CI 깸) | numpy-only 강제(jax 미import), import 순수성 테스트. |

## Acceptance Criteria (G1 freeze)

- **AC1**: `headroom.py` `classify_headroom` 순수함수(사전약정 frac=0.75·k=1.0) + `HeadroomVerdict`.
  numpy-only(jax 미import).
- **AC2**: `tests/test_headroom.py` 단위 — 3 verdict 경계 + 빈입력 가드(numpy-only CI 통과).
- **AC3 (robust 측정, 사전약정)**: `ppo_baseline.py --runs 5`가 default+hard서 PPO gym-clear mean±std
  + oracle + ratio + `classify_headroom` verdict 보고. 실측 기록.
- **AC4 (무회귀)**: 365 tests green + 신규. `jax_train`/`jax_env` 무변경. core CI numpy-only 유지
  (headroom.py CI 포함).
- **AC5 (정직)**: multi-run mean±std·CPU·작은 net·이 예산·oracle proxy 라벨. headroom verdict가
  사전약정 규칙 기계적 적용.
- **AC6 (pilot)**: freeze 전 pilot이 임계 고정 + multi-run 파이프라인 + classify property 입증.
  `ppo-closes`로 뒤집히면 reframe·정지.
- **AC7**: `mypy src`·`ruff`·`pytest -q`·`build` clean. 문서(jax-throughput.md robust 갱신 + INITIATIVE +
  DESIGN §3.1.1) + CHANGELOG 1줄.

## Pilot 결과 (freeze 전 전제 검증 + 사전약정 적용)

**파이프라인 입증 (falsify 0)**: `classify_headroom` property 7종(3 verdict 경계 + ratio + 빈입력/
oracle≤0 가드) 통과 + multi-run(5) end-to-end. 임계(frac=0.75·k=1.0) 데이터 전 고정.

**실측 (CPU·5-run, 사전약정 classify_headroom)**:

| config | PPO held-out (5-run) | oracle | PPO/oracle | 낙관상한(mean+std) | 임계(0.75×oracle) | gap | verdict |
|---|---|---|---|---|---|---|---|
| default(3 gym) | 0.52±0.06 | 1.84 | **28%** | 0.58 | 1.38 | +0.20 | **hard-and-learnable (robust)** |
| hard(8 gym) | 1.52±0.28 | 7.28 | **21%** | 1.80 | 5.46 | +0.12 | **hard-and-learnable (robust)** |

- 낙관적 PPO 상한(0.58/1.80)도 임계(1.38/5.46)를 한참 밑돎 → **headroom이 seed 노이즈 아님 입증**.
  single-run(32%/15%)이 multi-run(28%/21%)으로 일관. R2 PPO≥A2C 양 config. **ppo-closes 미발동**(reframe 불요).
- hard서 PPO(1.52) < type_blind(2.03) 유지(multi-run) — capability ladder robust.
- **정직 caveat**: 5-run·작은 net·CPU·200iter·oracle=scripted proxy. 더 큰 budget/net은 PPO↑(headroom은
  이 baseline 기준). std는 default(0.06) tight, hard(0.28) 다소 큼이나 verdict 여유 큼.
