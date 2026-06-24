---
slug: duel-fewshot-adapt
initiative: env-core
status: completed
ended: 2026-06-24
extracted_to:
  - docs/explanation/genre-generalization.md   # (B) 스레드 종결: 제로샷 불가 메커니즘 + few-shot SLOW
changelog_entry: docs/CHANGELOG.md (env-core, duel-fewshot-adapt)
---

# duel-fewshot-adapt — 제로샷 불가 메커니즘 입증 + few-shot 적응 곡선 — 결과 보고서 ((B) 스레드 종결)

## 1. 제로샷 불가 메커니즘 (AC1, numpy-only, 결정론)

`charge_trace`로 입증: train family(critter/forage/muster)를 seed=0 200-step 롤아웃하면 charge **내내 0**
(degenerate), duel은 battle 중 charge **>0**. → duel RPS가 의존하는 obs가 train서 상수라 **gradient 0 →
제로샷 학습 불가**. **일반 명제**: genre 전이는 새 메커닉이 *train 분포에서 degenerate한 obs*에 의존하면 제로샷 불가.

## 2. few-shot 적응 곡선 (AC2, base 150k, 5 run)

| adapt budget (duel fine-tune) | duel held-out (±run-std) |
|---|---|
| 0 (zero-shot) | 0.650 ±0.204 |
| 25,000 | 0.588 ±0.102 |
| 50,000 | 0.762 ±0.557 |
| **100,000** | **1.450 ±0.482** |

**사전약정 verdict = SLOW** (z₀=0.65, σ₀=0.20; ≤50k는 z₀+σ₀=0.85 안=노이즈, 100k에야 1.45로 명확 상회).

## 3. 정직한 결론 ((B) 스레드 종결)

- **제로샷 duel 전이는 *원리적으로* 불가** — degenerate feature(charge)라 학습 신호 없음(메커니즘 입증됨).
- **few-shot 적응은 SLOW** — 25k/50k는 제로샷과 노이즈 내 구분 불가, **100k(≈base의 2/3)에야 ~2배 상승**.
  → duel RPS는 *거의 새로 배우는 진짜 새 skill*이지 빠른 전이가 아님.
- 단일-seed pilot(50k≈1.63)은 또 노이즈였고 **multi-run이 4번째로 교정**(50k 5-run mean 0.76).
- **(B) 최종**: 학습 정책이 **메커닉 이웃(수집+타입상성)은 제로샷 전이**, **구조적으로 새 배틀시스템(duel)은
  제로샷 원리 불가(degenerate)+느린 few-shot(~100k)으로만 회복** = **sharply characterized partial result**
  (open도 solved도 아님). 제로샷≠few-shot은 다른 주장으로 구분 보고.

**caveat**: base 150k 단일 config·N16·결정론 보스·held-out eval seed는 fine-tune seed와 분리. zero-shot 0.65는
base 예산 의존(#32 400k base의 0.93과 다름) — 본 run 내부 z₀ 기준으로 판정(하드코딩 숫자 아님).

## 계획 대비 실적 (✅)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 제로샷 불가 메커니즘 가드 | ✅ | `test_charge_degenerate_in_train_families`(charge≡0 train/>0 duel), numpy-only 결정론 |
| AC2 few-shot 적응 곡선 + smoke | ✅ | `fewshot_adapt_curve`(0/25k/50k/100k, run-간 mean±std), `test_fewshot_adapt_curve_smoke` |
| AC3 사전약정 z₀+σ₀ 판정 | ✅ | **SLOW** 자동 판정 + ±std + 제로샷≠few-shot caveat |
| AC4 [rl] smoke + 결정론 | ✅ | fewshot smoke + charge 가드 결정론(seed 고정) |
| AC5 무회귀 + 툴체인 | ✅ | 197→199 passed(+2), mypy 22/ruff/build clean, core numpy-only |
| AC6 DESIGN + genre-generalization.md + CHANGELOG | ✅ | 제로샷 불가 메커니즘 + few-shot SLOW + 스레드 종결 반영 |
| AC7 freeze 전 pilot | ✅ | pilot(50k 단일seed 1.63)+timing; multi-run서 SLOW로 정정(예측대로) |

## 변경 파일 상세
**수정**
- `scripts/genre_learned_transfer.py` — `charge_trace`(numpy-only degenerate 진단) + `FewShotPoint`/`fewshot_adapt_curve`(base 학습→duel continue-learning 적응 곡선) + `--fewshot` CLI(제로샷 불가 메커니즘 명시 + 사전약정 verdict). **env 코어 무변경**.
- `tests/test_genre_learned_transfer.py` — `test_charge_degenerate_in_train_families`(numpy-only) + `test_fewshot_adapt_curve_smoke`(importorskip).
- `DESIGN.md` §3.1.1 — 제로샷 불가 메커니즘 + few-shot SLOW + (B) 스레드 종결.
- `docs/explanation/genre-generalization.md` — §5 결론 + §6 frontier를 "제로샷 원리 불가 + 느린 few-shot"으로 종결.

## 발견된 이슈 (심각도)
- (방법론, 4번째 사례) 단일-seed pilot이 적응 곡선을 과대평가(50k≈1.6 vs 5-run 0.76). multi-run 필수 재확인.
- (설계 통찰) **degenerate-feature 원리** — genre 벤치마크가 "제로샷 전이 가능 메커닉"을 만들려면, 새 메커닉의
  obs feature가 train 분포에서 *변동*해야 함(상수면 제로샷 원리 불가). 향후 env 설계 지침.

## 정직한 한계 / 다음 task
- base 150k 단일 config·N16·결정론 보스. 더 큰 base/적응 예산·메타-RL은 미탐.
- **(B) 스레드는 여기서 정직하게 종결 가능** — sharply characterized partial result로 arXiv 패키징.
- 더 가려면: 메커닉-범용 표현/메타-RL로 *빠른* cross-battle-system 적응(현재 SLOW를 줄이기). 또는 갭 register의
  다른 축(난이도 스케일·JAX 속도)으로 피벗 — 제품 신뢰성·채택 게이트.

## 타입 체크 / 빌드 결과
- pytest 199 passed, 2 skipped · mypy 22 files clean · ruff clean · build OK.
