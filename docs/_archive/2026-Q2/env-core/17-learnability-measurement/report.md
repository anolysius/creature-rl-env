---
slug: learnability-measurement
initiative: env-core
status: completed
ended: 2026-06-22
mode: standard
result: passed
milestone: M3
exit_criteria: [M3-EC-reliability]
extracted_to:
  - DESIGN.md   # §3.1.1 — learnability follow-up: 학습 정책이 추론을 획득하는가(양성 신호 + caveat)
changelog_entry: docs/CHANGELOG.md
supersedes: []
---

# Report — learnability-measurement · 학습 정책이 추론을 *학습*하는가

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md) (AC1–AC6)
> 의존: `CritterGym-commit-v0`(reasoning-load-bearing, PR #20) — 이 브랜치 stack.

## 요약 — (A) 스토리 완성 (구조 허용 → 학습 정책이 실제 획득)

`reasoning-load-bearing`은 *task 구조*가 추론을 강제함을 scripted-arm으로 증명했다. 이 task는 그 정직한
follow-up: **학습 정책(PPO)이 commit-v0에서 실제로 추론을 획득하는가**. (1) 학습 정책이 추론을 *표현*할 수
있는 **챔피언-선택 액션 UX**를 만들고, (2) reference arm과 대조하는 **측정 하네스**를 만들고, (3) 측정을
실행해 정직히 보고했다.

**PPO 100k 측정 (commit-v0, grid5/3gym, eval N=16):**

| arm | held-in | held-out | gap |
|---|---|---|---|
| oracle | 3.19 | 3.25 | −0.06 |
| infer | 3.19 | 3.25 | −0.06 |
| type_blind | 1.50 | 1.88 | −0.38 |
| probe | 1.69 | 1.56 | +0.13 |
| **learned (PPO)** | 2.69 | **4.00** | −1.31 |

→ 학습 정책이 held-out에서 type_blind(1.88)·probe(1.56)를 **결정적으로 상회**, infer-reference(3.25) 수준
이상 = **맹목/추측이 아닌 효과적 챔피언 선택을 학습**. **양성 learnability 신호** — (A) 차별점이 구조뿐
아니라 *학습 에이전트 수준*에서도 작동.

## 정직한 caveat (헤드라인 과대 금지 — typechart-depth 문화)

- **return = gym격파 + 진화 합산** → learned(4.0)가 oracle/infer(3.25)를 "넘는" 건 *진화 보상* 포함이지 순수
  추론 우위 아님. 절대 cross-arm 비교는 노이즈. 견고한 주장 = "learned ≫ probe/blind, infer 수준 이상".
- **eval N=16 + 단일 run + easy config**(grid5/3gym) → 정밀 벤치 아님. held-out≥held-in(gap 음수)은 노이즈
  범위지만 **gap≈0 = 암기 아님**(moat 일관)에는 부합.
- 따라서 acceptance는 *성능 임계*가 아니라 *측정 산출 + 정직 보고*로 freeze했고(AC3/AC4), 결과는 **신호**로
  보고 — 정밀 수치 헤드라인 아님.

## 계획 대비 실적 (AC1–AC6)

| AC | 결과 |
|---|---|
| AC1 챔피언-선택 액션 UX | ✅ `_commit_window`(action 4 cycle=무턴/무피해, 첫 move lock) + 5 테스트 + check_env. **M1 obs 무변경**(phase 플래그 불요 — "유리하면 attack 아니면 switch" 전략이 동역학에 암묵 내장) |
| AC2 측정 하네스 | ✅ `learnability.py`(numpy-only): env-aware reference 4종 + `measure_learnability` + split 가드. 액션 UX 경유 `oracle≥infer>probe` |
| AC3 학습 스크립트 | ✅ `scripts/learnability.py`(`[rl]`) `train_and_measure` + importorskip smoke(256 steps) |
| AC4 측정 실행+정직 보고 | ✅ PPO 100k 실행 → 위 표 + DESIGN §3.1.1 follow-up 갱신(양성 신호+caveat) |
| AC5 무회귀 | ✅ M1·procgen·commit-v0 48 passed + check_env ×3 + honesty 가드. 140→151 |
| AC6 toolchain | ✅ mypy(17)·ruff·pytest 151/2skip·build clean |

## 변경 파일 상세

| 파일 | 내용 |
|---|---|
| `critter_env.py` | `_commit_window` — commit 배틀 turn-0 챔피언-선택(action 4 cycle=무턴/무피해, 첫 move lock). commit 모드 한정·M1 obs 무변경 |
| `learnability.py` (신규) | numpy-only env-level 측정: env-aware reference arm 4종 + `measure_learnability`(held-in/out split 가드) + `as_env_policy` |
| `scripts/learnability.py` (신규) | `[rl]`: PPO commit-v0 학습 → reference 대조 리포트(`train_and_measure`) |
| `tests/test_champion_action.py` (신규) | 액션 UX 결정론 5건 |
| `tests/test_learnability.py` (신규) | 측정 API 계약 6건(infer>probe 경유 + smoke) |
| `DESIGN.md` | §3.1.1 follow-up: 학습 정책 양성 신호 + caveat 정직 기록 |

## 발견된 이슈 (심각도)

- **(중·정직성) return 메트릭이 격파+진화 합산** — 순수 챔피언-선택 품질을 분리 못 함. learned가 oracle을
  넘는 착시. 견고 주장으로 한정 보고. **후속**: gym-clear-only 메트릭으로 정밀 재측정.
- **(낮) 측정 1회·easy config** — 정밀 벤치 아님. 후속: 다중 run·seed·config 스윕, 학습곡선.

## 흡수처 매핑 (extracted_to)

- **`DESIGN.md` §3.1.1** — learnability follow-up 단락을 "미측정"에서 "양성 신호(+caveat)"로 갱신. 이 task의
  유일 evergreen 결정.

## 후속 (follow-up)

1. **정밀 재측정** — gym-clear-only 메트릭 + 다중 run/seed/config + 학습곡선(M3-EC4 arxiv writeup 본문).
2. (B) 장르 일반화 — 두 번째 구조-상이 env + env-level held-out split(진짜 해자 ②층).

## 툴체인 결과
- `pytest` → **151 passed, 2 skipped**(140 baseline + 신규 11: champion 5 + learnability 6)
- `mypy src` → Success(17) · `ruff` → clean · `build` → OK
- `check_env`(fixed/procgen-v0/commit-v0) 통과 · M1 48 passed 무회귀
- PPO 100k 측정 로그: `/tmp/learnability_run.log`(throwaway) → 수치는 본 report에 보존
