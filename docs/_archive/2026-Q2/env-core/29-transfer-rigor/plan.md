---
slug: transfer-rigor
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - scripts/genre_learned_transfer.py
  - tests/test_genre_learned_transfer.py
  - tests/**
  - DESIGN.md
extracted_to: []
supersedes: []
---

# transfer-rigor — multi-run + higher-budget로 widened-train 전이 신호 robust 재측정

> 작성일: 2026-06-23 | 상태: 계획

## 목표

#27(genre-transfer-policy)가 "wider train(duel 포함)이 unseen-family 전이 gap을 +2.56→~0/음수로
좁힌다"는 **양성 신호**를 측정했다. 단 결정적 **caveat**: widened-train의 held-in 절대성능도
2.94→1.1~2.0으로 떨어져(**generalist-mediocrity** — 1 net·동예산·3 family), 좁아진/음수 gap이
*균일 평범*을 일부 반영해 **강한 전이의 증명이 아니다**. 또 단일run이라 run-간 분산을 모른다.

이 task는 그 두 caveat를 정면으로 메운다:
- **(a) 절대 skill 향상** — PPO 예산을 #27의 50k보다 크게(예: 150k) 올려 **held-in 절대성능을
  끌어올린 뒤** gap을 재측정. held-in이 회복되면 좁은 gap이 "평범 때문"이 아님을 가린다.
- **(b) multi-run/multi-seed** — LOO를 여러 seed로 반복해 **per-fold gap을 run-간 mean ± std**로
  보고. 단일run 우연을 분산 밴드로 통제.

### ⚠️ 정직성 불변식 (freeze 규율)
- 성공 = **robust 측정 + 정직 보고**이지 "신호가 확증됐다"가 아니다.
  - 예산↑로 held-in이 회복되고도 gap이 좁게(또는 음수로) 유지 + run-std 안에서 안정 → **신호 강화**
    (B가 주장에 더 가까워짐, 그래도 증명 아님).
  - held-in을 올렸더니 gap이 다시 벌어진다 → **#27의 좁은 gap은 generalist-mediocrity 아티팩트**
    였다는 정직한 reframe(음성도 valid 결과).
  - run-std가 크면 "신호가 분산에 묻힘 = 아직 불확실"로 정직 보고.
- **freeze 전 pilot 필수** — 예산↑×multi-run×4 fold는 compute가 크다. pilot로 (a) timing/feasibility,
  (b) held-in이 실제로 오르는지 1 fold 확인, (c) 정직 framing 확인. 가정 falsify 시 reframe.

### 마일스톤 매핑
- M5/moat 층2. M3 공개 EC보다 먼저(기능 준비 우선). G1에서 override 재확인.

## 선행 조건
- **#27 genre-transfer-policy(머지됨)** — `train_and_transfer_loo`/`--loo`, `TransferReport`,
  `_MultiFamilyEnv`, 4 family 공유 obs(#32). 이 위에 multi-run 집계 + 예산 노브를 얹는다.

## 작업 범위

### 핵심 설계 (L1/pilot로 정련)
1. **multi-run LOO 집계** — `train_and_transfer_loo`를 여러 seed로 반복하는 래퍼
   (`train_and_transfer_loo_multirun` 또는 `--runs N`): per-fold로 run들의 held-in/held-out/gap을
   모아 **mean ± std-across-runs** 보고. 기존 단일run 함수는 보존(하위호환).
2. **예산 노브** — `--timesteps` 기본을 올리거나(예: 150k) CLI로 명시. #27의 50k와 **같은 metric**
   으로 대조(held-in 절대 상승 여부 + gap 변화).
3. **정직 출력** — #27 결과(50k 단일run)와 이 task(높은 예산, multi-run) 표를 나란히: held-in이
   회복됐는가 + gap이 run-std 안에서 좁게 유지되는가 + 음수 gap 해석 caveat 유지.

### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/genre_learned_transfer.py` | multi-run LOO 집계(`--runs N`) + 예산↑ + #27 대조·run-std 출력. `[rl]` | 중 — 실험 진입점 |
| `tests/test_genre_learned_transfer.py` | multi-run smoke(importorskip, tiny budget·2 run) + 집계 형태 가드 | 신규 케이스 |
| `DESIGN.md` §3.1.1 | robust 재측정 결과 정직 반영(신호 강화/아티팩트 어느 쪽이든) | 문서 |

### 영향 범위 (import 그래프)
- core CI numpy-only 유지(PPO `[rl]` 뒤 importorskip). 실측은 비-CI 오프라인.

## Step별 계획
1. **(freeze 전 pilot)** 높은 예산 1 fold + 2 run을 저예산-검증 규모로 돌려 (a) held-in이 실제 오르는
   경향, (b) multi-run 집계 동작, (c) wall-clock 추정(전체 run 비용 가늠), (d) 정직 framing 확인.
   compute가 비현실적이면 예산/run 수를 plan에서 조정(freeze 전).
2. multi-run 집계 함수 + `--runs N` 구현(TDD: Red smoke 먼저).
3. #27 대조 + run-std 출력 + 음수 gap/held-in 해석 caveat.
4. smoke 테스트(importorskip, tiny) + 집계 형태 가드.
5. **실측 run**(오프라인 [rl], 적정 예산·run 수) → 결과 기록.
6. DESIGN §3.1.1 + CHANGELOG 정직 갱신(신호 강화 또는 아티팩트 reframe).

## 검증 방법
- pytest 전체 무회귀(193 유지/증가), mypy/ruff/build clean.
- `[rl]` smoke: multi-run LOO가 tiny budget·2 run에서 per-fold mean±std 산출(importorskip).
- 실측은 코드 근거 + run-간 std + caveat 동반(날조 0). #27(50k 단일run) 및 #26(+2.56)과 같은 metric.

## 리스크
- **R1 compute 비용 과다**(예산↑×run×4 fold) → rules/80 §D 200k 토큰과 별개로 wall-clock 큼.
  pilot로 timing 측정 후 예산/run 수를 현실적으로 freeze. 필요시 fold 수 축소(주요 fold 우선) — 단
  축소는 출력에 명시(silent 축소 금지).
- **R2 결과 과대해석** — 신호가 강화돼도 "전이 입증" 금지. run-std·단일config·결정론 보스 caveat 유지.
- **R3 held-in이 예산↑로도 안 오름** — 환경이 본질적으로 어렵거나 정책/obs 한계. 그럼 "절대 skill은
  예산만으론 안 오른다 → 정책/obs 개선이 다음"으로 정직 reframe(이 task 결과로서 valid).
- **R4 scope creep** — 정책/obs 표현 개선(아키텍처 변경)까지 끌어들이면 비대. 이 task=예산↑+multi-run
  *측정*까지. 정책 개선은 별도 후속.

## Acceptance Criteria (G1 통과 시 freeze)

> 성능/주장형이 아니라 **robust 측정 + 정직 보고**로 freeze. "신호 확증"이 acceptance가 아니다.

- **AC1** multi-run LOO(`--runs N`/집계 함수)가 widened-train 4 family LOO를 **여러 seed로 반복**해
  per-fold **held-in/held-out/gap을 run-간 mean ± std**로 출력. #27(50k 단일run)·#26(+2.56)과
  **같은 gap metric**(held_in−held_out).
- **AC2** **높은 예산**(>#27의 50k)에서 측정하고, **held-in 절대성능이 #27 대비 올랐는지**를 보고.
  결과를 **사전 약정(pre-registered) 결정규칙**으로 해석(사후 narrative 편향 방지 — qa SUGGEST 흡수).
  기준은 unseen-`muster` fold를 #26(+2.56)·#27(−0.25)과 같은 축으로 본다:
  - **신호 강화** ⇐ widened held-in 평균이 #27(≈1.1–2.0)보다 유의히 상승(예: muster fold held-in ≥ 2.5,
    #26의 2.94에 근접) **그리고** 평균 fold gap이 run-std 안에서 ≤ +0.5로 유지(좁음).
  - **generalist-mediocrity 아티팩트 reframe** ⇐ held-in이 올랐는데 평균 fold gap이 #26 쪽으로 재확대
    (예: muster fold gap > +1.0).
  - **불확실(신호가 분산에 묻힘)** ⇐ run-간 std가 gap 크기와 비슷하거나 더 큼(부호 불안정).
  - 임계는 **freeze 시점에 사전 등록**된 값이며, 결과가 어디에 떨어지든 그대로 보고(±run-std + caveat,
    날조 0). 단일 config·결정론 보스 caveat 유지.
- **AC3** `[rl]` smoke(importorskip)로 multi-run 집계(tiny budget·≥2 run) 무회귀. core numpy-only 유지.
- **AC4** 기존 테스트 무회귀(193 유지/증가) + mypy/ruff/build clean.
- **AC5** DESIGN §3.1.1 정직 갱신(이 task 결과 — 신호 강화/아티팩트 어느 쪽이든) + M5/층2 매핑.
- **AC6** CHANGELOG 1줄 append.
- **AC7** (freeze 전) pilot로 **정량 게이트** 확인: (i) **timing** — 1 fold×2 run의 wall-clock을
  측정해 전체(4 fold×N run×예산) 추정이 현실적인지(비현실적이면 예산/run/fold 수를 freeze 전 조정,
  silent 축소 금지), (ii) **held-in 경향** — 예산↑ 1 fold가 #27의 50k held-in보다 **오르는 방향인지**
  (안 오르면 R3 reframe: "예산만으론 절대 skill 안 오름→정책/obs가 다음"), (iii) multi-run 집계 동작 +
  AC2 사전약정 규칙으로 어느 결과든 정직 보고 가능 확인. 가정 falsify 시 plan 조정/reframe 후 재평가
  (freeze 전이라 새 slug 불요).
