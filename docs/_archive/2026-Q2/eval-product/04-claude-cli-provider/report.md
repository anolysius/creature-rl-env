---
slug: claude-cli-provider
initiative: eval-product
status: completed
ended: 2026-06-27
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md   # eval-product #4 행
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# Claude-CLI(구독) provider + score_agent 이중-실행 제거 — 결과 보고서 (eval-product #4)

## 요약

(1) **구독으로 실측**: 신규 `llm_eval.claude_cli_complete` — 로컬 `claude` CLI(`claude -p`, 중립 tempdir
cwd)를 LLM 백엔드로 → **Claude Code 구독 인증 사용, API 키/과금 불요**. 러너에 `--provider {anthropic,
claude-cli}`. (2) **콜 절반**: `score_agent`가 submission을 두 번 돌리던 버그(`run_episode` + `_caught_rate`
재실행) 제거 → 신규 `_play_once`로 gyms/caught/evolved를 한 에피소드서 한 번에 → seed당 1 패스.

**메트릭 byte-equivalent**(동일 env 상태원 info["subgoals"]) → 기존 #1/#2 테스트 그대로 PASS. 463→465(+2).

## 계획 대비 실적

| AC | 상태 | 결과 |
|---|---|---|
| AC1 단일 패스/콜 절반 | ✅ | `_play_once` 1패스, 콜-카운팅 테스트 PASS, 기존 metric 테스트 무회귀 |
| AC2 claude-cli provider | ✅ | `claude -p` 셸아웃·중립 cwd·구독·키 불요, bogus binary→FileNotFoundError |
| AC3 러너 --provider | ✅ | {anthropic, claude-cli}, claude-cli=구독, ruff clean |
| AC4 회귀0/정직 | ✅ | 메트릭 byte-equivalent, 463→465(+2), mypy30/ruff/build clean |
| AC5 task-end 산출 | ✅ | INITIATIVE #4 + CHANGELOG |

## 변경 파일 상세

**수정**:
- `src/critter_gym/eval_harness.py` — `score_agent` 단일-패스화: 신규 `_play_once(factory, policy, seed)->
  (gyms, caught, evolved)`(terminal info["subgoals"] 한 번에). `_caught_rate` 제거, `run_episode` import 정리.
  submission·reference arm 모두 `_play_once` 1회. **메트릭 수치 동일**.
- `src/critter_gym/llm_eval.py` — `claude_cli_complete(binary='claude', cwd, timeout)`: `claude -p` 셸아웃·
  중립 tempdir·미설치 FileNotFoundError·구독 ToS/rate/느림 docstring.
- `scripts/llm_eval_run.py` — `--provider {anthropic, claude-cli}`(기본 anthropic). claude-cli 분기.
- `tests/test_eval_harness.py`(+단일패스) · `tests/test_llm_eval.py`(+claude_cli 구조).

## 발견된 이슈

- **(버그 픽스)** `score_agent` 이중-실행(`_caught_rate` 재실행) → LLM 제출 콜 2배였음. 단일-패스로 절반.
  메트릭은 동일 env 상태(info["subgoals"]=sum(_gym_defeated)/_caught/_evolved)서 산출 → byte-equivalent.
- **(구독 정직 경계)** 구독은 대화형 용도·rate limit — 자동 다수 호출은 소규모 probe 권장(docstring). CLI
  ~s/call로 느림 → 큰 run은 API 권장.

## 흡수처 매핑

- `docs/_active/eval-product/INITIATIVE.md` #4 — 구독 provider + 콜 절반.
- ADR 가치 없음.

## 타입 체크 / 빌드 결과

- `mypy src`: 30 files clean. `ruff check .`: passed. `build`: 1.0.0rc1 OK. `pytest`: 465 passed, 2 skipped.

## 후속

- 실측 run(claude-cli 구독, 적정 호라이즌)으로 "프런티어 LLM이 우리 봉인 환경서 N% of oracle" 숫자 회수 →
  난이도 표 기록(별도, 사용자/세션 실행).
