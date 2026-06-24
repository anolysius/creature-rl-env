---
slug: difficulty-gap-rigor
initiative: difficulty-scaling
status: completed
ended: 2026-06-24
extracted_to:
  - DESIGN.md   # §3.1.1 "Toward hard-and-gap≈0" — multi-run rigor result
changelog_entry: docs/CHANGELOG.md
---

# 난이도 gap rigor — multi-run + 사전약정 결과 보고서

#24 가 남긴 honest limit(난이도 점 gap 이 전부 큰 per-seed std 안 = 저예산·단일run 약한 신호)을, **multi-run
(std-across-runs) + 예산↑ + 사전약정 결정규칙**으로 정밀화. env 무변경(JAX 재포트 위험 없음).

## 요약 (수치 표 — PPO 100k, 5 runs, N=16/16)

| 난이도 점 | held-in | held-out | gap ± std-across-runs | 사전약정 verdict |
|---|---|---|---|---|
| d0_mild (3 types) | 1.100 | 1.325 | **−0.225 ±0.350** | `gap≈0-signal` |
| d1_medium (8 types) | 1.212 | 1.450 | **−0.237 ±0.489** | `gap≈0-signal` |
| d2_hard (12 types, 강보스) | 1.538 | 1.938 | **−0.400 ±0.896** | `gap≈0-signal` |

사전약정 임계(데이터 보기 전 고정): `floor=0.3`, `k=1.0`. gap_std = **std-across-runs**.

## ⭐ 정직 verdict (AC5/AC7)

**AC7 분기 (a) — "hard-enough(현 knob 한도)-and-gap≈0" 신호, 단 질문이 이동.**

1. **#24 대비 진짜 업그레이드.** #24 는 *한 run 내 per-seed std* 로 "gap within std"(약한 증거, 작은 real
   gap 을 0 과 구분 불가)였다. 이번은 (i) **held-in 이 floor(0.3) 훨씬 위**(1.1~1.5 = 정책이 실제로 깸,
   generalist-mediocrity 아날로그 아님) (ii) **std-across-runs**(gap 점추정의 run간 변동)로 판정 → gap≈0 이
   *단일run 노이즈가 아니라* 5 run 에 걸쳐 robust. 예산 40k→100k 가 held-in 을 비floor 로 끌어올림.
2. **세 점 모두 `gap≈0-signal`, real-gap 미출현.** 난이도 knob 을 올려도(d2: 12 types·강보스) env 는 명확한
   train→test 일반화 갭을 *안* 보인다. d2 서 held-in 이 오히려 1.538 로 상승(정책이 가장 어려운 점도 학습).
3. **정직 caveat (과대 금지).**
   - gap 이 일관되게 **약한 음수**(−0.23~−0.40, held-out 이 살짝 쉬움 = 난이도 비대칭이지 super-transfer 아님)
     — 단 전부 std 안이라 부호는 불안정.
   - **std-across-runs 가 난이도와 함께 커짐**(0.35→0.49→**0.90**). d2 의 std 는 gap 의 ~2배 → *가장 어려운
     점에서 작은 real gap 을 정밀히 배제하지 못함*. "robustly consistent with gap≈0"이지 "gap=0 입증" 아님.
   - 난이도 "점"은 단조 사다리 아님(#24 falsify). held-out ~1.9/3(보통) → **현 knob 이 능력을 변별할 만큼
     충분히 어렵진 않을 수 있음** — 이게 다음 질문.
4. **함의 — 재설계 동기의 *재정의*.** gap-correctness 는 문제가 아니다(real-gap 안 나옴 → "gap≈0 깨짐" 걱정
   불요). 그러나 "hard-and-gap≈0"의 *hard* 쪽이 미해결: 현 난이도 knob(타입수·보스 stat)은 gap 을 만들지도,
   능력을 강하게 변별하지도 못함(held-out 1.9/3). **env 재설계의 진짜 동기는 "gap 교정"이 아니라 "변별력 있는
   난이도"** — 학습 정책이 *쉽게* 풀지 못할 구조적 난이도(예: oracle 천장 해소 + 더 깊은 추론 부하). 단 그건
   env 메커닉 변경 = JAX 재포트(jax-throughput R5) 동반.

## 계획 대비 실적 (✅)

- ✅ **AC1** `train_and_gap_multirun`(N run → gap mean ± std-across-runs) + `--runs N` CLI. 기존
  `train_and_gap`/단일run main 경로 유지(`_main_singlerun`).
- ✅ **AC2** 사전약정 `classify_gap(gap_mean, gap_std, heldin_mean)` 순수함수, `floor=0.3`·`k=1.0`(데이터
  보기 전 고정, plan/qa-checklist 박제).
- ✅ **AC3** `classify_gap` 결정론 단위 테스트(3 라벨 경계, **CI numpy-only** — sb3 불요) + multi-run smoke
  (importorskip).
- ✅ **AC4** 실측 background 100k×5runs×d0/d1/d2 — 표 위. gap mean ± std-across-runs + 점별 verdict. multi-run.
- ✅ **AC5** 정직 verdict 박제(위) — std-across-runs 병기, 과대 금지, 재설계 동기 재정의.
- ✅ **AC6** 회귀 0 — 281→283 tests green, mypy(25)/ruff/build clean, core numpy-only. DESIGN §3.1.1 갱신.
- ✅ **AC7** 사전약정 분기 (a) 확정(real-gap 미출현·held-in 비floor → gap≈0 robust; 단 변별 난이도 미해결).
- ✅ **AC8** 툴체인 green.

## 변경 파일 상세

| 파일 | 신규/수정 | 내용 |
|---|---|---|
| `scripts/difficulty_generalization.py` | 수정 | `GAP_FLOOR`/`GAP_K` 사전약정 상수 + `classify_gap`(순수함수, 3 라벨) + `MultiRunGap` dataclass(std-across-runs) + `train_and_gap_multirun` + `--runs N` CLI + `_main_singlerun` 분리(무회귀). |
| `tests/test_difficulty_generalization.py` | 수정 | `classify_gap` 결정론 단위(3 라벨 경계, numpy-only) + multi-run smoke(importorskip). |

## 흡수처 매핑 (extracted_to)
- `DESIGN.md §3.1.1` — "Toward hard-and-gap≈0" 문단에 multi-run rigor 결과(약한신호→robust gap≈0 + 변별
  난이도 미해결) 흡수. 측정 스크립트는 `[rl]` 소비자.

## 타입 체크 / 빌드 결과
mypy src: Success(25) · ruff: All checks passed · build OK · pytest: 283 passed, 2 skipped.
