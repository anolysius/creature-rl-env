---
slug: sota-headroom
initiative: hard-benchmark
status: completed
ended: 2026-07-08
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# SOTA-headroom 재측정 — 결과 보고서 (정직 VACUOUS: 값싼 capacity 레버 실패)

## 요약 (수치 표)

#3 (memory-headroom)이 recurrent PPO(GRU **h128**)를 `hard_env_spec`(grid16)에서 oracle의 43%로
측정하며 남긴 capacity confound("hard인가, agent를 덜 키웠나?")를 치려 했다. 같은 config에서
recurrent PPO를 **capacity+budget으로 키워**(h128→h256→h384, 300→600 iters) 재측정.

| 항목 | 결과 |
|---|---|
| 테스트 | **746 → 758** (+12 헬퍼 단위테스트, 회귀 0) |
| lint/type | ruff clean, mypy 신규 함수 clean (render.py:82=baseline) |
| oracle (winnable) | 5.00 (winnable=True), 0.75·oracle = 3.75, type_blind 2.44 |
| **tiny GRU h128 (=#3)** | **2.12 ± 0.09 = 42% of oracle** — #3의 43% 재현 (재현성 검증) |
| wide GRU h256 (600 it) | 1.56 ± 0.62 = 31% ← **더 나빠짐** |
| wider GRU h384 (600 it) | 0.83 ± 0.75 = 17% ← **더 나빠짐** |
| best non-tiny (h256) | 1.56 **< tiny 2.12** → **non_vacuous=False** |
| **사전약정 verdict** | **(!) VACUOUS — best scaled가 tiny를 못 이김(underfit) → verdict 보류** |

**정직 결론**: **값싼 capacity 레버(GRU width↑)는 이 budget에서 더 강한 agent를 만들지 못했다 —
넓힐수록 오히려 나빠졌다(underfit).** 그래서 사전약정한 **non-vacuity guard가 발동해 거짓 "robust"
판정을 막았다**(guard의 정확한 작동 = 이 task의 핵심 산출). "더 강한 agent에도 hard인가"는 **답하지
못했다** — 더 강한 agent를 실제로 만드는 데 실패했기 때문. **#3의 headroom(capacity confound)은 이
sweep으로 닫히지도 강화되지도 않았고, SOTA-hardness는 OPEN으로 남는다.** 단 부수 소득: #3의 h128=42%가
독립 재현됨. 메타 교훈: CPU·small batch(48)·중간 budget에선 순수 width 확대가 최적화 난이도에 눌려
underfit — 진짜 더 강한 agent는 더 나은 최적화(더 큰 batch·budget·LR·GPU)가 필요하지 파라미터 수가
아니다. borderline 아님(opt-bound 2.18 ≪ 3.75)이라 5-run 확충 불요.

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 classify_scaled_headroom 순수함수 | ✅ | headroom.py 신규(best-non-tiny + classify_headroom 위임 + non_vacuous/exceeds), 기존 무변경 |
| AC2 5-branch 단위테스트 | ✅ | test_sota_headroom.py 12 케이스(robust/closes/exceeds/vacuous/inconclusive + tiny-제외 + 경계 raise) |
| AC3 무회귀 + ruff/mypy | ✅ | 746→758(+12), ruff clean, mypy 신규 clean |
| AC4 --quick smoke | ✅ | recurrent PPO sweep·oracle winnable·#3 대비·branch 출력, 판정 전 규칙 출력 |
| AC5 본측정 완주 + 사전약정 그대로 | ✅ | full budget 3-run 완주, **VACUOUS를 그대로 보고**(유리하게 재해석 안 함), 정직 라벨 |

## 변경 파일 상세

**수정**
- `src/critter_gym/headroom.py` (+~60): 신규 순수 함수 `classify_scaled_headroom` + `ScaledHeadroomVerdict`
  NamedTuple. best-non-tiny 선택 → `classify_headroom` 위임 → non_vacuous(best>tiny)·exceeds(best>oracle)
  플래그. 기존 `classify_headroom`/`classify_depth` 무변경. numpy-only(CI, jax 불요).

**신규**
- `scripts/sota_headroom.py` (+~135): hard_env_spec에서 recurrent PPO capacity+budget sweep →
  `classify_scaled_headroom` → 5-branch 출력 + sweep 전체·#3 대비·honest NOTE.
- `tests/test_sota_headroom.py` (+~110): 헬퍼 12 단위테스트.

## 발견된 이슈 (심각도)

- **[중/메타-발견] 순수 width 확대가 CPU 고정 budget에서 underfit**: h256·h384가 h128보다 나쁨
  (2.12→1.56→0.83). recurrent PPO의 hidden-replay가 width²라 최적화가 더 어려워지는데 budget·batch가
  못 따라감. **버그 아님** — "capacity confound를 값싸게 못 닫는다"는 정직한 측정. non-vacuity guard가
  이걸 잡아 verdict 보류 → 거짓 robust 방지.
- **[낮음/baseline] mypy render.py:82**: imageio overload, baseline pre-existing(본 변경 무관).

## 흡수처 매핑 (extracted_to)

**흡수 없음(빈 배열)** — evergreen 4-질문:
1. 새 설계 narrative? **No** — 기존 headroom 측정의 파생.
2. 새 절차/runbook? **No** — script docstring self-contained.
3. 새 명세/표? **No** — 결과 VACUOUS(측정 미완), reference 굳힐 단계 아님.
4. 새 ADR? **No** — 아키텍처 결정 변경 없음(순수 헬퍼 additive).

INITIATIVE.md에 1행. **후속 방향**(사람 결정): 진짜 더 강한 agent = 더 큰 batch·budget·LR 튜닝
또는 GPU(값싼 width 아님), 혹은 더 깊은 arch(stacked GRU — 별개 heavy task). VACUOUS는 "SOTA에도
hard" 질문을 여전히 OPEN으로 남김.

## 타입 체크 / 빌드 결과

- `pytest`: 758 passed, 0 regression.
- `ruff check .`: All checks passed.
- `mypy src`: 신규 함수 clean; render.py:82 1건 pre-existing(무관).
