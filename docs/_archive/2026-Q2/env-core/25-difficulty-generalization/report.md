---
slug: difficulty-generalization
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - DESIGN.md#3.1.1   # "Toward hard-and-gap≈0": learned-policy experiment + pilot falsification
changelog_entry: docs/CHANGELOG.md (env-core, 2026-06-23)
---

# 난이도 일반화 (학습정책 gap-at-difficulty) — 결과 보고서

## 요약

DESIGN §3.1.1 "hard-and-gap≈0" 로드맵 전진. **pilot이 "깨끗한 단조 scripted 사다리"를 falsify**(난이도 다차원:
num_types=추론난이도는 blind엔 *쉬움* / 보스 stat=cliff / oracle 천장 ~0.6) → **학습정책 gap 실험**으로 reframe.
여러 **난이도 점**에서 PPO를 held-in 학습→held-in vs held-out gap 측정(기존 `measure_generalization` 재사용,
held-in eval은 `split_train_pool`로 학습시드와 disjoint).

| 난이도 점 (PPO 40k, N=16/16) | held-in (±std) | held-out (±std) | gap |
|---|---|---|---|
| d0_mild | 0.938 ±1.30 | 0.562 ±0.86 | +0.375 |
| d1_medium | 0.688 ±1.21 | 0.250 ±0.43 | +0.438 |
| d2_hard | 1.000 ±1.70 | 0.938 ±1.64 | +0.062 |

→ **모든 점의 gap이 per-seed std 안**(std가 gap을 swamp) — 가장 어려운 d2 포함, 학습정책에서도 gap≈0과 *consistent*.
**정직 한계**: 큰 std·저예산(절대성능 향상 여지)에서 "gap이 std 내"는 *약한 증거*(작은 real gap을 zero와 구분 못 함),
"일반화 입증"이 아니라 *신호*. (L3 honesty SUGGEST 반영해 script/DESIGN 문구 hedge.)

| 검증 | 결과 |
|---|---|
| 테스트 | **183 passed**/2 skipped (181→183, +2 smoke, 회귀 0) |
| mypy/ruff/build | clean (22 files) |
| `[rl]` smoke | pass(importorskip) |
| core CI | numpy-only 유지(PPO는 `[rl]` 뒤) |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 스크립트 ≥3 config + train_and_gap + disjoint | ✅ | CONFIGS 3종, `split_train_pool`로 held-in∩learn=∅, `measure_generalization` |
| AC2 importorskip smoke + 누수 가드 | ✅ | `test_difficulty_generalization.py` 2종 pass |
| AC3 정직(점 not 사다리, 학습정책, 신호) | ✅ | docstring/main + DESIGN |
| AC4 실측 + N 고정 + std 병기 | ✅ | 위 표(N16/16, ±std), gap-within-std 정직 서술 |
| AC5 DESIGN §3.1.1 갱신 | ✅ | "Toward hard-and-gap≈0" 문단(falsification+방법+결과+caveat) |
| AC6 무회귀+numpy-only+toolchain | ✅ | 183 passed, mypy/ruff/build clean, honesty 가드 |

전 AC ✅. acceptance를 *측정+정직 보고*로 freeze("gap≈0 입증" 아님).

## 변경 파일 상세

**신규**
- `scripts/difficulty_generalization.py` (`[rl]`) — 난이도 점 3종 + `train_and_gap`(PPO held-in→`measure_generalization`) + main(±std 병기·정직 footer).
- `tests/test_difficulty_generalization.py` — importorskip smoke(유한 GapReport + config=점).

**수정**
- `DESIGN.md` (§3.1.1) — "Toward hard-and-gap≈0" 문단: pilot falsification(scripted 사다리 불가, 다차원/cliff/oracle 천장) + 학습정책 방법 + gap-within-std 결과 + caveat.

## 발견된 이슈 (심각도)

- **(중, pilot 결과)** "깨끗한 단조 난이도 사다리"는 현 env 구조로 불가(다차원·cliff·oracle 천장) — typechart-depth식 정직 reframe. config=점, 측정=학습정책 gap.
- **(낮음, L3 반영)** gap-within-large-std는 약한 증거 → script/DESIGN 문구를 "consistent with, 입증 아님"으로 hedge.
- **(낮음)** 단일run·저예산(40k)·N16 = 신호. 다중run·고예산은 향후.

## 흡수처 매핑 (extracted_to)

- **DESIGN.md §3.1.1** — hard-and-gap≈0의 학습정책 실험 방법·pilot falsification·결과 신호 흡수. 측정 스크립트는 `[rl]` 소비자(기존 generalization 재사용, 새 core 모듈 불요).

## 타입 체크 / 빌드 결과

mypy: Success (22) · ruff: clean · build: OK · pytest: 183 passed/2 skipped.
