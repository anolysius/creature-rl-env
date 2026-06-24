---
slug: transfer-capacity-budget
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

# transfer-capacity-budget — 용량+예산 *동시* 스케일로 widened held-in 회복 검정 (B의 cheap/expensive 경계 종결)

> 작성일: 2026-06-23 | 상태: 계획

## 목표

#30(transfer-skill-policy)은 net을 키웠지만 **예산은 50k 고정**이라 큰 net이 **underfit**해서
held-in이 오히려 떨어졌다. #28은 예산만 올렸고(150k, baseline net) held-in이 ~2.07까지 *약간*
올랐다. **아직 안 해본 단 하나의 값싼-ish 점 = 용량(net)과 예산을 *동시에* 스케일**하는 것.

이 task는 그 점을 검정한다: **큰 net + 충분한 예산이면 단일 정책이 3 family를 마스터해서 widened
held-in을 #26 수준(≈2.9)으로 회복하는가?**
- **회복하면(held-in↑)** → generalist-mediocrity confound가 *제거 가능*하다는 첫 증거 → 그 위에서
  gap을 재측정해 (B) 전이 신호의 *진짜* 강도를 본다(confound 줄어든 상태).
- **회복 못 하면** → compute(#28)·net-only(#30)·**용량+예산 동시(이 task)** 세 값싼 경로가 전부
  실패 → (B)의 generalist-mediocrity는 **구조적**이고, 남은 건 *비싼/다른* 접근(메커닉-범용 표현·
  메타-RL)뿐 — **cheap/expensive 경계를 완전히 종결**(정직한 결정적 음성).

→ **양쪽 다 결정적**: 이 task는 (B)에서 값싼 경로를 닫는 마지막 실험.

### ⚠️ 정직성 불변식 (freeze 규율)
- 성공 = **용량+예산 동시 스케일의 held-in 효과를 측정+정직 보고**이지 "held-in 올렸다"가 아니다.
- **사전약정(pre-registered) 결정규칙**(#28 임계 계승, 사후 편향 차단): widened held-in(muster fold
  앵커, run-간 mean)이
  - **회복(confound 제거 경로)** ⇐ held-in ≥ **2.5**(#26의 2.94에 근접) 그리고 net-only/budget-only
    천장(#30 1.15 / #28 2.07)을 run-std 넘어 상회.
  - **부분 개선(불충분)** ⇐ held-in이 budget-only 천장(~2.07)보다는 오르나 2.5 미만.
  - **경계 종결(결정적 음성)** ⇐ held-in이 ~2.07 천장을 run-std 안에서 못 넘음(동시 스케일도 무효).
- **freeze 전 pilot 필수** — 큰 net×큰 예산은 이 세션 최대 compute. pilot로 (i) timing(전체 추정),
  (ii) 큰 net이 큰 예산에서 held-in *오르는 방향*인지(underfit 풀리는지), (iii) 어느 결과든 정직 보고
  가능 확인. 비현실적 compute거나 가정 falsify 시 예산/net/fold 조정·reframe.

### 마일스톤 매핑
- M5/moat 층2. M3 공개 EC보다 먼저(기능 준비 우선). G1에서 override 재확인.

## 선행 조건
- **#30 transfer-skill-policy(머지됨)** — `train_and_transfer(..., net_arch=, scale_obs=)`,
  `_loo`/`_loo_multirun`, `--runs`/`--improved`, `_ScaleObs`. 이 위에 **예산↑ + net 크기 조합**을 얹는다.
  (이미 `net_arch`/`timesteps`/`--runs`가 인자라 새 코드 표면은 작다 — 주로 실측 + 보고.)

## 작업 범위

### 핵심 설계 (L1/pilot로 정련)
1. **용량×예산 sweep(작게)** — `net_arch` ∈ {baseline, [256,256]} × `timesteps` ∈ {50k(기준), 높음(예:
   250k)} 조합으로 widened held-in을 multi-run 측정. 핵심 대조: **(big-net, high-budget) vs
   (baseline-net, high-budget=#28) vs (big-net, 50k=#30)** — underfit이 예산으로 풀리는지 격리.
   scale_obs는 #30서 무효였으니 기본 off(혼란 변수 제거), 단 옵션 유지.
2. **천장 대조 보고** — #26(2.94)·#28 budget-only(2.07)·#30 net-only(1.15)를 같은 표에 기준선으로.
   동시 스케일이 천장을 넘는지 사전약정 규칙으로 판정.
3. **(held-in 회복 시) gap 재측정** — confound 줄어든 설정의 multi-run LOO gap을 #28과 같은 축으로.
   회복 못 하면 "held-in 미회복 → gap 재측정 불요 + cheap/expensive 경계 종결" 정직 기록.

### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/genre_learned_transfer.py` | (필요 시) sweep/대조 출력 헬퍼 + 천장 기준선 표. 노브는 기존 재사용. `[rl]` | 저~중 |
| `tests/test_genre_learned_transfer.py` | sweep/대조 smoke(importorskip, tiny) | 신규 케이스 |
| `DESIGN.md` §3.1.1 | 동시 스케일 결과(회복/경계 종결) 정직 반영 | 문서 |

### 영향 범위 (import 그래프)
- core CI numpy-only 유지(PPO `[rl]` 뒤 importorskip). 실측 비-CI 오프라인.
- 새 학습 코드 표면 작음(노브 이미 존재) → 회귀 위험 낮음. 주 비용은 compute(실측 시간).

## Step별 계획
1. **(freeze 전 pilot)** (big-net, high-budget) 1 fold(→muster)를 돌려 (a) held-in이 #28 천장(2.07)·
   #30(1.15) 대비 오르는 방향인지, (b) timing(전체 sweep 추정). underfit이 안 풀리면(held-in≤천장)
   조기 신호 → 예산을 더 올릴지/경계 종결로 reframe할지 freeze 전 결정.
2. sweep/대조 출력 + 천장 기준선 표 구현(TDD: Red smoke 먼저). 노브 재사용.
3. 사전약정 규칙 판정 + ±std + caveat.
4. smoke 테스트(importorskip, tiny).
5. **실측 sweep**(오프라인 [rl], 적정 예산·run) → 결과 기록. 비용 큼 → fold/조합 silent 축소 금지.
6. DESIGN §3.1.1 + CHANGELOG 정직 갱신(회복=경로 확보 / 미회복=cheap/expensive 경계 종결).

## 검증 방법
- pytest 전체 무회귀(195 유지/증가), mypy/ruff/build clean.
- `[rl]` smoke: sweep/대조가 tiny budget에서 finite held-in 산출(importorskip), 결정론.
- 실측은 코드 근거 + run-간 std + caveat 동반(날조 0). #26/#28/#30 천장과 같은 metric/축.

## 리스크
- **R1 compute 비용(이 세션 최대)** — big-net×high-budget×multi-run×fold. → pilot timing 후 예산/run/
  fold 현실적 freeze. 1차는 **anchor muster fold**로 held-in 회복 여부 확인 → 회복 시에만 full LOO 확대.
  비용 임계(rules/80 §D 200k 토큰)·wall-clock 모니터, 축소는 출력 명시.
- **R2 held-in 안 오름(가정 falsify)** — 동시 스케일도 무효. → 정직 결정적 음성(cheap/expensive 경계
  종결), (B)=구조적 open problem 확정. pilot로 사전 신호 확인.
- **R3 결과 과대해석** — held-in 회복돼도 "전이 입증" 금지. gap 재측정도 ±std·단일config caveat.
- **R4 scope creep** — 메커닉-범용 표현/메타-RL/커스텀 extractor까지 가면 비대. 이 task=용량×예산
  sweep *측정*까지. 표현/메타-RL은 별도 후속(genre-generalization.md 남은 경로).

## Acceptance Criteria (G1 통과 시 freeze)

> 성능/주장형이 아니라 **동시 스케일 효과 측정 + 정직 보고**로 freeze. "held-in 올렸다"가 acceptance가 아니다.

- **AC1** 용량(net_arch)×예산(timesteps) 조합으로 widened held-in을 multi-run 측정·출력하고, **#26(2.94)·
  #28 budget-only(~2.07)·#30 net-only(1.15) 천장을 같은 표에 기준선**으로 병기(같은 gap/held-in metric).
- **AC2** **사전약정 결정규칙**으로 판정: muster fold run-간 held-in이 (회복 ≥2.5 ∧ 천장 상회) / (부분
  >2.07,<2.5) / (경계 종결 ≤2.07 within std) 중 어디인지. 결과가 어디든 ±run-std + caveat로 정직 보고.
- **AC3** (held-in 회복 시) 동시-스케일 설정 multi-run LOO **gap을 #28과 같은 축**으로 재측정. 회복 못 하면
  "held-in 미회복 → gap 재측정 불요 + **cheap/expensive 경계 종결**" 정직 기록(조건부).
- **AC4** `[rl]` smoke(importorskip)로 sweep/대조 무회귀 + 결정론(seed 고정). core CI numpy-only 유지.
- **AC5** 기존 테스트 무회귀(195 유지/증가) + mypy/ruff/build clean.
- **AC6** DESIGN §3.1.1 정직 갱신(회복=경로 / 미회복=경계 종결) + `genre-generalization.md`의 "남은 비싼
  경로" 갱신 + M5/층2 + CHANGELOG 1줄.
- **AC7** (freeze 전) pilot로 (i) big-net×high-budget held-in 방향(천장 상회 여부), (ii) timing(전체 추정
  현실성), (iii) 결정론, (iv) 어느 결과든 정직 보고 가능 확인. 비현실/falsify 시 조정·reframe(새 slug 불요).
