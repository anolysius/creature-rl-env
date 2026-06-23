---
slug: learnability-precision
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - DESIGN.md#3.1.1   # learnability follow-up: gym-clear-only metric + ceiling/oracle==infer caveats
changelog_entry: docs/CHANGELOG.md (env-core, 2026-06-23)
---

# learnability 정밀 재측정 — 결과 보고서

## 요약 (수치 표)

#17의 caveat 1번(return = 격파+진화 **합산** → learned가 oracle 넘는 착시) 해소. **gym-clear-only 메트릭**
(보스 격파 수, 진화 분리) 도입으로 reference arm·learned를 깨끗하게 비교.

| arm (held-out, num_gyms=8) | combined return | **gym-clear-only** | evolutions |
|---|---|---|---|
| oracle | 5.625 | **4.188** | 1.438 |
| infer | 5.625 | **4.188** | 1.438 |
| type_blind | 2.562 | 1.812 | 0.750 |
| probe | 1.625 | 1.062 | 0.562 |

→ gym-clear-only가 진화 인플레(~1.44)를 제거하고 **load-bearing 순서(oracle≥infer ≫ type_blind > probe) 유지**.

| 검증 | 결과 |
|---|---|
| 테스트 | **174 passed**/2 skipped (171→174, +3, 회귀 0) |
| mypy/ruff/build | clean (21 files) |
| PPO `[rl]` smoke | pass (sb3) |
| honesty 가드 | pass |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 EpisodeOutcome + run_episode | ✅ | `test_run_episode_returns_outcome_separating_gyms_and_evolutions` (return == gyms+evolutions) |
| AC2 gym-clear-only 병기 + markdown | ✅ | `test_gym_clear_only_separates...` + `test_gym_clear_metric_is_in_report_markdown` |
| AC3 분리 + 순서 보존 | ✅ | combined>gym-clear(oracle) + oracle≥infer>type_blind>probe |
| AC4 API 무회귀 + smoke | ✅ | `measure_learnability` 시그니처+combined 보존, `arm_mean` combined, PPO smoke pass |
| AC5 스크립트 gym-clear 중심 + --runs N | ✅ | main()이 heldout_gyms로 verdict, `--runs` 다중 PPO seed 평균+range, [rl]비CI 표기 |
| AC6 무회귀+DESIGN+honesty | ✅ | 174 passed, mypy/ruff/build clean, DESIGN §3.1.1 3-caveat, honesty 가드 |

전 AC ✅. acceptance를 *메트릭 분리+정직 보고*로 freeze(성능 아님).

## 변경 파일 상세

**수정**
- `src/critter_gym/learnability.py` (+95) — `EpisodeOutcome`(return/gyms_cleared/evolutions), `run_episode`가 outcome 반환, `_arm_means`(combined+gym 동시), `LearnabilityReport.heldin_gyms`/`heldout_gyms`+`gym_gap`+병기 markdown, `measure_learnability` 양 메트릭. `arm_mean` combined 보존.
- `scripts/learnability.py` (+38, `[rl]`) — gym-clear-only 중심 보고, `--runs N` 다중 PPO seed 평균(±range), 단일run/[rl]비CI 정직 표기. `seed` param.
- `tests/test_learnability.py` (+35) — gym-clear-only 분리/순서/markdown 테스트 3종 + 기존 markdown assert 갱신.
- `DESIGN.md` (§3.1.1) — gym-clear-only 정밀 재측정 + 3 caveat.

## 발견된 이슈 (심각도)

- **(낮음, L1 measurement reviewer 반영)** gym-clear-only는 **천장(num_gyms)** bounded(oracle 4.2/8) → 진화-인플레 대신 강한 arm 간 gap 압축 confound. DESIGN 명시.
- **(낮음, L1 반영)** oracle==infer(이 config는 한 번 보면 추론 자명) → 이 메트릭만으로 추론이 *load-bearing*임을 증명 못 함(추론이 *suffices*, 증명은 scripted gate 몫). DESIGN 명시.
- **(낮음)** 다중 run은 `[rl]`/비CI — 단일run caveat 완화지 제거 아님.

## 흡수처 매핑 (extracted_to)

- **DESIGN.md §3.1.1** — learnability follow-up 문단에 gym-clear-only 정밀 재측정 + 3 caveat 흡수. 별도 evergreen/ADR 신설 없음(측정 정밀화는 기존 모듈 확장).

## 타입 체크 / 빌드 결과

mypy: Success (21) · ruff: passed · build: OK · pytest: 174 passed/2 skipped.
