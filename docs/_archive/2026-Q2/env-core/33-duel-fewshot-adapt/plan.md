---
slug: duel-fewshot-adapt
initiative: env-core
status: active
started: 2026-06-24
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

# duel-fewshot-adapt — duel 제로샷 불가 *메커니즘 입증* + few-shot 적응 곡선 측정

> 작성일: 2026-06-24 | 상태: 계획

## 목표

#32가 (B)를 "real but structurally bounded"로 국소화: 메커닉 이웃(critter/forage/muster)은 전이되나
**duel(타입무관 RPS/스태미나)로는 robust 실패(+1.73)**. 사전 탐색에서 그 *원인*이 드러남:
**duel의 RPS가 의존하는 `player_charge`/`enemy_charge` obs가 train 3 family에선 항상 0(degenerate)**
→ 정책이 charge 사용을 배울 gradient가 없음 → **제로샷 duel 전이는 표현 트릭으로 풀 수 없는 원리적 한계**.

이 task는 두 가지를 한다:
1. **제로샷 불가 메커니즘을 *입증*** — train family 롤아웃 내내 charge ≡ 0임을 가드(테스트)로 박제.
   "genre 전이는 새 메커닉이 *train 분포에서 degenerate한 obs*에 의존할 때 제로샷 불가"라는 일반 명제.
2. **few-shot 적응 곡선 측정** — train{critter,forage,muster} 정책을 **held-out duel에서 소예산
   fine-tune**(adapt budget 사다리: 0/25k/50k/100k)하며 duel held-out 점수를 측정. 제로샷(0.93, #32)
   대비 적응이 점수를 *얼마나 빨리* 끌어올리는가 = duel이 few-shot으로 닿는지.

→ 결과는 "제로샷은 구조적 불가, few-shot은 [가능/느림]" — (B)의 frontier를 정확히 규정.

### ⚠️ 정직성 불변식 (freeze 규율)
- 성공 = **제로샷 불가 메커니즘 입증 + few-shot 적응 곡선 측정 + 정직 보고**이지 "전이 풀었다"가 아니다.
- **사전약정 결정규칙**(zero-shot duel held-out = #32의 **0.93** 기준선): adapt budget 사다리에서 duel
  held-out mean이
  - **ADAPTS** ⇐ 소예산(≤50k) 적응으로 0.93을 run-std 넘어 유의 상승(duel 직접학습 수준 ~2+ 방향).
  - **SLOW** ⇐ 큰 적응(100k)에야 오르거나 미미.
  - **NO** ⇐ 적응해도 0.93 부근 정체(거의 없을 결과지만 가능).
- **freeze 전 pilot 필수** — fine-tune 적응이 동작하고 곡선이 의미를 내는지 + timing 확인. base 정책
  학습 예산은 tractable하게(예: 150k; 400k 전체 회복은 비용 큼 — adapt 곡선엔 base가 *고정 출발점*이면 충분).
  가정 falsify(적응 자체가 비현실적/불안정) 시 reframe.

### 마일스톤 매핑
- M5/moat 층2. M3 공개 EC보다 먼저. G1에서 override 재확인. **이번 세션 (B) 스레드의 마무리 task 후보.**

## 선행 조건
- **#32 transfer-budget-recovery(머지됨)** — `train_and_transfer`(PPO, net/budget 노브), `_MultiFamilyEnv`,
  `_family_factory`, `evaluate`, `heldout_seeds`. few-shot은 학습된 `model`을 duel 환경에서 `model.learn`
  추가 호출(continue-learning)로 구현 — 새 의존성 불필요(sb3 기존).

## 작업 범위

### 핵심 설계 (L1/pilot로 정련)
1. **제로샷 불가 메커니즘 가드** — `charge_is_degenerate_in(train_families)` 류 헬퍼/테스트: train family
   롤아웃(reset+다수 step) 내내 `player_charge`/`enemy_charge` == 0 확인. duel에선 battle 중 >0 됨 대조.
2. **few-shot 적응 곡선** — `fewshot_adapt_curve(train_families, target, base_timesteps, adapt_budgets,
   n_runs)`: base 정책 학습(train families) → 각 adapt budget마다 **target(duel) 환경에서 추가 학습** →
   duel held-out 점수 측정. 0 adapt = 제로샷(#32 재현). 곡선을 run-간 mean±std로.
3. **사전약정 판정 출력** — zero-shot 0.93 기준선 + 적응 곡선 + ADAPTS/SLOW/NO verdict.

### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/genre_learned_transfer.py` | `charge_is_degenerate_in` + `fewshot_adapt_curve` + `--fewshot` CLI(곡선+verdict). `[rl]` | 중 — 진입점 |
| `tests/test_genre_learned_transfer.py` | degenerate-charge 가드(non-[rl], 결정론) + few-shot smoke(importorskip, tiny) | 신규 |
| `DESIGN.md` §3.1.1 | 제로샷 불가 메커니즘 + few-shot 적응 결과 정직 반영 | 문서 |
| `docs/explanation/genre-generalization.md` | frontier 규정(제로샷 불가 원인 + few-shot) 갱신 | 문서 |

### 영향 범위 (import 그래프)
- core CI numpy-only 유지(few-shot/PPO는 `[rl]` 뒤 importorskip). degenerate-charge 가드는 numpy-only(가능).
- 새 학습 코드 표면 작음(continue-learning) → 회귀 위험 낮음. 주 비용 = compute(base 학습 + 적응).
- **구현 위치 = `scripts/genre_learned_transfer.py`에 한정**(few-shot = 학습된 `model`을 duel `_MultiFamilyEnv`로
  바꿔 `model.learn(adapt_budget)` 추가 호출 = sb3 continue-learning). **`envs/`·`wrappers/`·env 코어 무변경**
  (새 adapter 클래스 없음). scope_paths에 src/ 없음 = env 회귀 표면 0.

## Step별 계획
1. **(freeze 전 pilot)** base{critter,forage,muster}@적정예산 → duel에서 25k·50k 적응 1-2 seed로
   (a) duel 점수가 0.93 위로 *오르는지*, (b) timing(전체 곡선 추정). 적응 불안정/비현실 시 예산·budget
   사다리 조정 또는 reframe.
2. degenerate-charge 가드(numpy-only 테스트) + `fewshot_adapt_curve` 구현(TDD: Red 먼저).
3. `--fewshot` CLI(zero-shot 기준선 + 곡선 + 사전약정 verdict).
4. smoke 테스트(importorskip, tiny) + 결정론.
5. **실측**(오프라인 [rl]) base + adapt 곡선(multi-run) → 결과 기록.
6. DESIGN §3.1.1 + genre-generalization.md + CHANGELOG 정직 갱신(제로샷 불가 + few-shot 결과).

## 검증 방법
- pytest 전체 무회귀(197 유지/증가), mypy/ruff/build clean.
- degenerate-charge 가드: train family 롤아웃서 charge≡0, duel battle서 charge>0 (numpy-only, 결정론).
- `[rl]` smoke: few-shot 곡선이 tiny budget에서 finite 점수 산출(importorskip).
- 실측은 코드 근거 + run-간 std + caveat 동반(날조 0). zero-shot 0.93(#32)과 같은 metric.

## 리스크
- **R1 compute** — base 학습 + adapt 사다리 × multi-run. → pilot timing 후 base 예산·adapt budget·run
  현실적 freeze. base는 고정 출발점이라 *한 번* 학습 후 여러 adapt 측정 재사용 가능(비용 절감). 축소 명시.
- **R2 적응이 안 됨/불안정(falsify)** — continue-learning이 unstable. → 정직 결과(few-shot도 어렵다) 또는
  adapt budget/lr 조정. pilot로 사전 확인.
- **R3 fine-tune이 held-out 순수성 깸 우려** — few-shot 적응은 *의도적으로* held-out에서 적응하는 별도
  metric(제로샷과 구분 보고). zero-shot(0 adapt)도 같은 표에 둬 혼동 방지. held-out eval seed는 adapt
  seed와 분리.
- **R4 결과 과대해석** — 적응돼도 "genre 전이 풀림" 금지. "few-shot 적응 가능"과 "제로샷 전이"는 다른 주장.
- **R5 scope creep** — RecurrentPPO/메타-RL/대규모 HPO 금지. 이 task=메커니즘 입증 + fine-tune 적응 곡선까지.

## Acceptance Criteria (G1 통과 시 freeze)

> 성능/주장형이 아니라 **메커니즘 입증 + 적응 곡선 측정 + 정직 보고**로 freeze. "전이 풀었다"가 acceptance가 아니다.

- **AC1** **제로샷 불가 메커니즘 가드** — 신규 테스트 `test_charge_degenerate_in_train_families`(numpy-only,
  결정론): 각 train family(critter/forage/muster)를 **고정 seed=0으로 reset 후 scripted `nav_toward_gyms`
  정책으로 200 step 롤아웃**, 매 step `player_charge`/`enemy_charge` == 0 단언. 대조: duel을 같은 방식으로
  롤아웃하면 **battle 중 charge가 한 번이라도 >0**이 됨을 단언(`max charge > 0`). → "train서 degenerate(상수0)
  obs → 그 obs 의존 메커닉은 제로샷 불가" 명시. (헬퍼 `charge_trace(family, seed, steps)` → charge 값 리스트.)
- **AC2** **few-shot 적응 곡선** — `fewshot_adapt_curve(train_families, target, base_timesteps, adapt_budgets,
  n_runs)` + 신규 smoke `test_fewshot_adapt_curve_smoke`(importorskip, tiny): base{train} 정책을 held-out
  `duel`에서 adapt budget 사다리(**0 포함**)로 fine-tune하며 duel held-out 점수 run-간 mean±std 측정·출력.
  SMART 단언: (a) 곡선 길이 == len(adapt_budgets), (b) 모든 점 finite, (c) **0-adapt 점 == zero-shot**(추가학습
  0, 이번 run base의 제로샷 duel 점수 — #32의 ~0.9 ballpark, 본 run의 0-adapt를 *이후 점들의 baseline*으로 사용).
- **AC3** **사전약정 결정규칙**(이번 run의 0-adapt 제로샷을 baseline z₀, 그 run-std σ₀ 기준 — 하드코딩 숫자 아님):
  - **ADAPTS** ⇐ 소예산(≤50k) adapt의 duel mean > z₀ + σ₀ 를 유의 상회(적응 빠름).
  - **SLOW** ⇐ 100k adapt에서야 z₀ + σ₀ 상회.
  - **NO** ⇐ 최대 adapt에서도 z₀ + σ₀ 안(적응 미미).
  결과 어디든 ±std + caveat(**제로샷≠few-shot 구분**, held-out eval seed는 adapt seed와 분리, 단일 config). 날조 0.
- **AC4** `[rl]` smoke(importorskip) few-shot 곡선 무회귀 + degenerate 가드 결정론. core CI numpy-only 유지.
- **AC5** 기존 테스트 무회귀(197 유지/증가) + mypy/ruff/build clean.
- **AC6** DESIGN §3.1.1 + `genre-generalization.md` 정직 갱신(제로샷 불가 메커니즘 + few-shot 결과) +
  M5/층2 + CHANGELOG 1줄.
- **AC7** (freeze 전) pilot로 (i) duel 적응 점수 방향(0.93 위로 오름?), (ii) timing, (iii) 결정론,
  (iv) 어느 결과든 정직 보고 가능 확인. 비현실/falsify 시 조정·reframe(새 slug 불요).
