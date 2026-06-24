---
slug: transfer-budget-recovery
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
  - docs/explanation/genre-generalization.md
extracted_to: []
supersedes: []
---

# transfer-budget-recovery — 더 큰 예산으로 held-in 2.5 회복 검정 + (회복 시) gap 재측정

> 작성일: 2026-06-23 | 상태: 계획

## 목표

#31(transfer-capacity-budget)이 밝힘: **lever는 예산**(150k 2.07 → 250k 2.44, std 조임, 회복임계
2.5 *근접*)**이지 용량 아님**(큰 net robust 하락). PARTIAL — 250k에서 2.5 미달이라 full-LOO gap
재측정을 **보류**했고, "다음 probe = 더 큰 예산"으로 남겨둠.

이 task는 그 probe를 실행한다: **baseline-net(용량 배제) 예산을 더 올리면(예: 400k·500k) widened
held-in이 2.5를 robust하게 넘는가?**
- **넘으면(RECOVERY)** → generalist-mediocrity confound가 예산으로 *제거 가능* → #31이 보류한
  **full-LOO confound-reduced gap을 재측정**(held-in 회복 상태의 진짜 (B) 전이 신호). (B)를
  토대/신호 → *조건부 주장*("충분한 예산이면 회복 + 전이")으로 이동 시도.
- **안 넘으면(PLATEAU)** → 예산도 수확체감으로 막힘 → **값싼 경로(예산·용량) 모두 한계** →
  (B) 완전 회복엔 *비싼/다른* 접근(메커닉-범용 표현·메타-RL) 필요로 정직 확정 + 박제.

→ 양쪽 다 결정적. **이게 "예산 lever"의 끝을 보는 task.**

### ⚠️ 정직성 불변식 (freeze 규율)
- 성공 = **더 큰 예산의 held-in 효과 측정 + (회복 시) gap 재측정 + 정직 보고**이지 "회복했다"가 아니다.
- **사전약정 결정규칙**(#31 임계 2.5 계승, goalpost 이동 금지): muster fold run-간 held-in mean이
  - **RECOVERY** ⇐ **≥ 2.5** (그리고 250k 2.44를 run-std 넘어 상회 = 진짜 상승).
  - **PLATEAU(수확체감)** ⇐ 예산을 올려도 held-in이 250k(2.44)에서 run-std 안으로 정체(추가 상승 무).
  - **APPROACHING** ⇐ 2.44는 넘으나 2.5 미달(여전히 느리게 상승 중).
- RECOVERY 시에만 AC3(full-LOO gap 재측정) 트리거. 결과가 어디든 ±run-std + caveat로 정직 보고.
- **freeze 전 pilot 필수** — 이 세션 최대 compute(500k baseline ~140s/fold 추정). pilot로 (i) 500k
  single point가 2.5로 *향하는지/정체인지*, (ii) timing(full sweep+LOO 추정 현실성), (iii) 어느 결과든
  정직 보고 가능 확인. 비현실/falsify(향상 정체) 시 예산 상한/run/fold 조정·reframe.

### 마일스톤 매핑
- M5/moat 층2. M3 공개 EC보다 먼저(기능 준비 우선). G1에서 override 재확인.

## 선행 조건
- **#31 transfer-capacity-budget(머지됨)** — `held_in_sweep`/`SweepRow`/`--sweep`,
  `HELD_IN_CEILINGS`/`RECOVERY_THRESHOLD`, `train_and_transfer_loo_multirun`. **코드 표면 작음**:
  budget ladder는 `held_in_sweep` 재사용(임의 budget configs), gap 재측정은 `loo_multirun` 재사용.
  주로 budget 파라미터화 + 실측 + 보고.

## 작업 범위

### 핵심 설계 (L1/pilot로 정련)
1. **예산 사다리 확장** — baseline-net(net_arch=None, 용량 배제)으로 budget ∈ {250k(ref), 400k, 500k}
   를 `held_in_sweep`로 multi-run 측정. `--budgets` CLI로 임의 사다리 주입(하드코딩 회피).
2. **사전약정 판정** — held-in이 2.5 RECOVERY / 2.44 PLATEAU / APPROACHING 중 어디인지.
3. **(RECOVERY 시) full-LOO gap 재측정** — 회복 예산에서 `loo_multirun`을 #28과 같은 축으로 돌려
   confound-reduced 전이 gap을 4 fold 보고. PLATEAU면 "예산 한계 → 비싼 경로 필요" 정직 기록.

### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/genre_learned_transfer.py` | `--budgets` (held_in_sweep 임의 사다리) + (RECOVERY 시) loo_multirun 재측정 경로. `[rl]` | 저 (노브 재사용) |
| `tests/test_genre_learned_transfer.py` | `--budgets` 파라미터화 smoke(importorskip, tiny) | 신규 케이스 |
| `DESIGN.md` §3.1.1 | 예산 사다리 끝 결과(RECOVERY/PLATEAU) + (회복 시) confound-reduced gap 정직 반영 | 문서 |

### 영향 범위 (import 그래프)
- core CI numpy-only 유지(PPO `[rl]` 뒤 importorskip). 실측 비-CI 오프라인.
- 코드 표면 작음(파라미터화) → 회귀 위험 낮음. 주 비용 = compute(실측 wall-clock).

## Step별 계획
1. **(freeze 전 pilot)** baseline-net @500k 1 fold(→muster) single/2-seed로 (a) held-in이 250k(2.44)
   대비 *오르는지/정체인지*(2.5 향하는지), (b) timing(full sweep+LOO 추정). 정체면(향상 falsify) 예산
   상한·fold 수 freeze 전 조정 또는 PLATEAU 조기 reframe.
2. `--budgets` 파라미터화 구현(TDD: Red smoke 먼저). held_in_sweep 재사용.
3. 예산 사다리 실측 + 사전약정 판정.
4. **(RECOVERY 시)** 회복 예산에서 full-LOO gap 재측정(loo_multirun).
5. smoke 테스트(importorskip, tiny) + 결정론.
6. DESIGN §3.1.1 + genre-generalization.md + CHANGELOG 정직 갱신(RECOVERY/PLATEAU).

## 검증 방법
- pytest 전체 무회귀(196 유지/증가), mypy/ruff/build clean.
- `[rl]` smoke: `--budgets` 사다리가 tiny budget에서 finite held-in 산출(importorskip), 결정론.
- 실측은 코드 근거 + run-간 std + caveat 동반(날조 0). #26/#28/#31 천장과 같은 metric/축.

## 리스크
- **R1 compute 비용(세션 최대)** — 큰 예산×multi-run×(사다리+LOO). → pilot timing 후 예산 상한·run·
  fold 현실적 freeze. 1차 anchor fold 사다리로 RECOVERY 여부 확인 → RECOVERY 시에만 full-LOO 확대.
  rules/80 §D 비용·wall-clock 모니터, 축소는 출력 명시(silent 금지).
- **R2 held-in 정체(PLATEAU, falsify)** — 예산도 막힘. → 정직 결정적 결과(예산 lever 한계, (B) 완전
  회복엔 비싼 경로). pilot로 사전 신호.
- **R3 RECOVERY를 과대해석** — 2.5 넘어도 단일 config·anchor fold·결정론 보스 caveat. gap 재측정도
  ±std·"조건부 신호지 일반 주장 아님" 한정.
- **R4 scope creep** — 메커닉-범용 표현/메타-RL/대규모 HPO까지 가면 비대. 이 task=예산 사다리 끝 +
  (회복 시) gap 재측정까지. 표현/메타-RL은 별도 후속.

## Acceptance Criteria (G1 통과 시 freeze)

> 성능/주장형이 아니라 **예산 효과 측정 + (회복 시) gap 재측정 + 정직 보고**로 freeze. "회복했다"가 acceptance가 아니다.

- **AC1** baseline-net(용량 배제) **예산 사다리**(≥1개 250k 초과 점, 예 400k·500k)를 `--budgets`로 multi-run
  측정·출력 + #26(2.94)/#28(2.07)/#31(250k 2.44) 기준선 병기(같은 held-in metric).
- **AC2** **사전약정 결정규칙**으로 판정: muster fold run-간 held-in mean이 RECOVERY(≥2.5 ∧ 2.44 상회) /
  PLATEAU(250k서 정체) / APPROACHING(>2.44,<2.5) 중 어디인지. 결과 어디든 ±run-std + caveat, 날조 0.
- **AC3** **(RECOVERY 시에만)** 회복 예산에서 `loo_multirun`으로 **full-LOO confound-reduced gap을 #28과
  같은 축** 재측정·보고. PLATEAU/APPROACHING이면 "held-in 미회복 → gap 재측정 불요 + 예산 lever 한계"
  정직 기록(조건부, 실제 skip).
- **AC4** `[rl]` smoke(importorskip)로 `--budgets` 사다리 무회귀 + 결정론(seed 고정). core CI numpy-only 유지.
- **AC5** 기존 테스트 무회귀(196 유지/증가) + mypy/ruff/build clean.
- **AC6** DESIGN §3.1.1 정직 갱신(RECOVERY/PLATEAU + 회복 시 gap) + `genre-generalization.md` 갱신 +
  M5/층2 + CHANGELOG 1줄.
- **AC7** (freeze 전) pilot로 (i) 500k held-in 방향(2.5 향함/정체), (ii) timing(전체 추정 현실성),
  (iii) 결정론, (iv) 어느 결과든 정직 보고 가능 확인. 비현실/falsify 시 조정·reframe(새 slug 불요).
