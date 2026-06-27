---
slug: claude-cli-provider
initiative: eval-product
status: active
started: 2026-06-27
acceptance_freeze: true
domains: [rl-env]
mode: standard
task_type: general
scope_paths:
  - src/critter_gym/eval_harness.py
  - src/critter_gym/llm_eval.py
  - scripts/llm_eval_run.py
  - tests/test_eval_harness.py
  - tests/test_llm_eval.py
extracted_to: []
supersedes: []
---

# Claude-CLI(구독) provider + score_agent 이중-실행 제거 (eval-product #4)

> 작성일: 2026-06-27 | 상태: 계획

## 목표

(1) **구독으로 돌리기**: 실측을 Anthropic API(과금) 대신 로컬 `claude` CLI(Claude Code, 구독 인증)로 —
신규 `llm_eval.claude_cli_complete`(print 모드 `claude -p` 셸아웃; 중립 cwd로 repo CLAUDE.md 미로드).
러너에 `--provider {anthropic, claude-cli}`. (2) **비용 절반**: `eval_harness.score_agent`가 submission을
*두 번* 돌리는 버그(메인 채점 1회 + `_caught_rate` 재실행 1회 = LLM 콜 2배) 제거 — 한 에피소드서 gyms/caught/
evolved를 **한 번에** 읽는 단일 패스로. (probe서 30콜 예상→실제 60콜 확인됨.)

## 선행 조건

- #1 `eval_harness`(`score_agent`/`_caught_rate`/`Scorecard`), #2 `llm_eval`(`LLMAgent`), #3 `SealedEvalSet.max_steps`+`llm_eval_run.py`.
- `score_agent`: `run_episode`(gyms/evolutions) + 별도 `_caught_rate`(caught 재실행). env `info["subgoals"]`={caught,gyms_defeated,evolved} 한 번에 읽기 가능.
- 로컬 `claude` CLI(2.1.x) `-p` print 모드 확인됨(~7s/call, 세션 인증=구독 사용).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/eval_harness.py` | `score_agent` 단일-패스화(`_play_once` 신규로 gyms/caught/evolved 한 번에; `_caught_rate` 제거·`run_episode` 미사용 import 정리). **메트릭 수치 동일**(같은 env 상태원) | 중 | 콜 절반. 기존 metric byte-equivalent(테스트 유지) |
| `src/critter_gym/llm_eval.py` | `claude_cli_complete(binary='claude', ...)` 신규 — `claude -p` 셸아웃, 중립 cwd, 미설치 시 FileNotFoundError | 저 | provider-agnostic 유지 |
| `scripts/llm_eval_run.py` | `--provider {anthropic, claude-cli}`(기본 anthropic). claude-cli=구독, API 키 불요 | 저 | --model은 anthropic에만 적용 명시 |
| `tests/test_eval_harness.py` | 단일-패스 테스트(call-counting agent → act() 콜 == 1패스, 2배 아님) + 기존 metric 무회귀 | 저(test) | |
| `tests/test_llm_eval.py` | `claude_cli_complete` 존재·bogus binary→FileNotFoundError | 저(test) | 실제 CLI는 CI서 안 부름 |

### 영향 범위

- `score_agent` 메트릭은 동일 env 상태(gyms_defeated/caught/evolved)서 산출 → **수치 byte-equivalent**, 기존
  #1/#2 테스트(oracle>random·rate∈[0,1]·end-to-end) 유지. `_play_once`는 신규 헬퍼. claude_cli는 신규 옵션.

## Step별 계획
> 커밋 경계: lifecycle 끝 1 커밋.
1. **(red)** 테스트: (a) eval_harness — 콜 카운팅 stub agent로 `score_agent` 호출 시 agent.act() 총 콜이
   **단일 패스**(seeds×에피소드길이 1배, ≈2배 아님)임을 검증. (b) llm_eval — `claude_cli_complete` 존재 +
   존재하지 않는 binary로 FileNotFoundError.
2. **(green)** `eval_harness`: `_play_once(factory, policy, seed)->(gyms, caught_flag, evolved_flag)` 단일
   에피소드(terminal info["subgoals"] 읽기). `score_agent`가 submission·reference arm 모두 `_play_once` 사용
   (한 번씩). `_caught_rate` 제거, `run_episode` import 정리.
3. **(green)** `llm_eval.claude_cli_complete` + `llm_eval_run.py --provider`.
4. **(verify)** mypy·ruff·pytest(단일패스+기존 무회귀)·build clean.

## 검증 방법
- pytest: 단일-패스 테스트 + 기존 463 무회귀(메트릭 동일). mypy/ruff/build clean. (실제 claude CLI run=별도.)
- score_agent가 submission을 seed당 1회만 호출함을 콜 카운트로 입증. claude_cli provider 구조 검증(미설치 에러).

## 리스크
- **R1 메트릭 변동**: 단일-패스로 바꾸며 수치가 달라지면 기존 결과 불일치. **완화**: 동일 env 상태원
  (info["subgoals"]=sum(_gym_defeated)/_caught/_evolved)에서 산출 → byte-equivalent. 기존 테스트가 가드.
- **R2 claude CLI 가정**: print 모드·인증·출력 형식. **완화**: 확인됨(2.1.x `-p`→clean text). 미설치 시
  FileNotFoundError. parse_action이 free-text 강건.
- **R3 구독 ToS/rate**: 자동 다수 호출이 구독 약관/한도 이슈. **완화**: docstring에 "구독은 대화형 용도·
  rate limit 있음·소규모 probe 권장" 명시. 측정 규모는 사용자 결정.

## Acceptance Criteria (G1 통과 시 freeze)
- **AC1 (단일 패스/콜 절반)**: `score_agent`가 submission을 **seed당 1 에피소드만** 실행(이전 2배 제거).
  콜-카운팅 stub agent(act() 호출 수 기록)로 `score_agent(stub, SealedEvalSet(n_worlds=2, max_steps=N))`의
  총 act() 콜 == 1패스(≈2·N 이하, 이전 2배 ~4·N 아님)임을 신규 테스트로 검증. gyms/caught/evolved/
  frac_of_oracle 메트릭 **수치 동일**(동일 env 상태원): 구체적으로 `tests/test_eval_harness.py`의
  `test_score_agent_oracle_beats_random_and_rates_bounded`/`_obs_only_interface`와 `tests/test_llm_eval.py`의
  `test_llm_agent_scores_end_to_end_on_sealed_set`가 그대로 PASS.
- **AC2 (claude-cli provider)**: `llm_eval.claude_cli_complete(binary='claude')` — `claude -p` 셸아웃(중립
  cwd로 repo CLAUDE.md 미로드), 구독 인증 사용(API 키 불요). binary 미존재 시 명확 `FileNotFoundError`.
  docstring에 "구독=대화형 용도·rate limit·소규모 probe 권장·느림(~s/call)" 명시.
- **AC3 (러너 provider 옵션)**: `llm_eval_run.py --provider {anthropic, claude-cli}`(기본 anthropic).
  claude-cli=구독·키 불요. `--model`은 anthropic에만 적용 명시. ruff clean.
- **AC4 (회귀 0 + 정직)**: 기존 src 메트릭 byte-equivalent. **passing 테스트 수 463(#3 기준) 유지/증가**
  (신규 단일패스+claude_cli 테스트만큼만 증가), 2 skip. `mypy(30)`·`ruff`·`build` clean. 정직 경계
  (구독 ToS/rate·CLI 느림 ~s/call) docstring 명시.
- **AC5 (task-end 산출)**: INITIATIVE #4 행 + CHANGELOG. G1 freeze 시점 미작성.
