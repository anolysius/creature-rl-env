---
slug: stateful-llm-agent
initiative: eval-product
status: completed
ended: 2026-06-27
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md  # task table #5 (archive 이동 시 함께 이동)
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# stateful LLMAgent — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 465 → **474** (+9, 회귀 0), 2 skip |
| mypy | clean (30 files) |
| ruff / build | clean / clean |
| L1 | plan-reviewer SUGGEST(반영) + qa-verifier APPROVE |
| L3 | 2/2 APPROVE |
| 변경 | src 2 · scripts 1 · tests 2 (전부 frozen scope 내) |

## 평이한 한 문단 요약 (수식 없이)

LLM에게 "방금까지 어디를 지나며 무엇을 했는지"를 짧게 기억하게 해주는 새 모드(`StatefulLLMAgent`)를
붙였습니다. 부분만 보이는 우리 환경에서 무기억 LLM은 길을 즉시 잊어 바닥을 치는데, 이건 우리가 이미
증명한 사실(기억이 중요하다)과 같은 현상이지 "LLM이 멍청하다"가 아닙니다. 그래서 **공정하게 다시
재려면** 기억을 줘야 합니다. 가장 중요한 안전장치는 한 시험(월드)이 끝날 때마다 기억을 깨끗이 지워
다음 시험에 새지 않게 하는 `reset()`입니다. 기존 무기억 방식은 한 글자도 안 건드렸습니다.

## 계획 대비 실적

| AC | 결과 | 근거 |
|---|---|---|
| AC1 Protocol+채점 | ✅ | `test_stateful_agent_satisfies_protocol_and_has_reset`, `..._scores_end_to_end_on_sealed_set` |
| AC2 누적+window 상한 | ✅ | `test_stateful_history_accumulates_and_window_is_bounded`, `..._window_zero_is_effectively_memoryless` |
| AC3 reset 월드 격리 | ✅ | `test_score_agent_calls_reset_once_per_episode`(resets==5), `test_stateful_reset_clears_history_and_isolates` |
| AC4 무회귀 byte-identical | ✅ | 465→474, `test_score_agent_stateless_submission_unaffected`, 기존 `test_score_agent_*` green |
| AC5 러너 플래그 | ✅ | `--stateful --window K`, 미지정 시 `LLMAgent`(무상태) 경로 |
| AC6 lint+정직 경계 | ✅ | mypy/ruff/build clean, docstring "memory mechanism, not a measured result / probe=user-run / not reframed" |

## 변경 파일 상세

- **신규 (src/critter_gym/llm_eval.py)**: `StatefulLLMAgent`(history 누적·슬라이딩 윈도우·`reset()`),
  `_obs_summary`(한 줄 digest), `_ACTION_NAMES`. 기존 `LLMAgent`/`render_obs`/`parse_action` 불변.
- **수정 (src/critter_gym/eval_harness.py)**: `Agent` Protocol docstring에 선택적 `reset()` 규약 명시,
  `score_agent`가 `getattr(submission,"reset",None)`로 duck-typing 추출, `_play_once`에 `reset` 키워드
  파라미터 추가 — `env.reset()` 직후 1회 호출. reset 없는 submission은 분기 skip → byte-identical.
- **수정 (scripts/llm_eval_run.py)**: `--stateful` / `--window K` 플래그, stateful 시 토큰↑ 경고 1줄.
- **테스트**: test_llm_eval.py +7 (stateful 누적/window/reset 격리/window=0/invalid/end-to-end),
  test_eval_harness.py +2 (reset 에피소드당 1회 / 무상태 무회귀).

## 발견된 이슈

- 없음 (L3 2/2 APPROVE, 무회귀 0). `window=0`은 무기억과 등가(append 직후 즉시 trim) — 테스트로 고정.

## 정직 경계 (계승)

- 본 task는 **기억 메커니즘**이지 측정 결과가 아니다. CI는 stub `complete`로 검증.
- 실측 probe는 **사용자 로컬 실행**(구독 claude CLI 또는 API, 키=사용자). 나오는 frac_of_oracle은
  그대로 기록 — "프런티어 LLM이 푼다/못 푼다"로 reframe 금지.
- "구독으로 과금 0" 주장 금지 — "API 키 없이 claude CLI 파이프라인이 돈다"까지만.

## 흡수처 매핑

- `extracted_to`: INITIATIVE.md 의 task table #5 행. 별도 ADR/explanation 미생성 — reset 훅 규약의
  SSOT는 `Agent` Protocol docstring(코드 옆), 실행법은 스크립트 docstring + CHANGELOG. cross-task
  의존성 없음(archive invariant 충족).

## 타입 체크 / 빌드 결과

mypy clean(30) · ruff clean · `python -m build` → `critter_gym-1.0.0rc1` wheel+sdist · pytest 474 passed / 2 skipped.
