# QA Checklist — claude-cli-provider (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 동결.
> ⚠ eval-product #4 — 구독(claude CLI) provider + score_agent 콜 절반(이중-실행 제거).

## Acceptance Criteria (frozen at G1)

- [x] **AC1 (단일 패스/콜 절반)** ✅ — `score_agent`가 `_play_once`로 seed당 1 에피소드(gyms/caught/evolved
  한 번에). `test_score_agent_single_pass_no_double_run`(콜≤n_worlds×cap) PASS. 메트릭 byte-equivalent —
  `test_score_agent_oracle_beats_random_and_rates_bounded`·`_obs_only_interface`·`test_llm_agent_scores_end_to_end_on_sealed_set` 그대로 PASS.
- [x] **AC2 (claude-cli provider)** ✅ — `claude_cli_complete(binary='claude')`: `claude -p` 셸아웃·중립
  tempdir cwd·구독 인증(키 불요). bogus binary→`FileNotFoundError` 테스트 PASS. docstring에 구독 ToS·
  rate limit·소규모 probe·느림 명시.
- [x] **AC3 (러너 --provider)** ✅ — `--provider {anthropic, claude-cli}`(기본 anthropic). claude-cli=구독·
  키 불요. `--model` anthropic만 적용 명시. ruff clean.
- [x] **AC4 (회귀 0 + 정직)** ✅ — 메트릭 byte-equivalent. 463→**465 passed**(+2), 2 skip. mypy(30)/ruff/build
  clean. 구독 ToS/rate·CLI 느림 docstring.
- [x] **AC5 (task-end 산출)** ✅ — INITIATIVE #4 + CHANGELOG = task-end.

## L1 이력
- round 1: plan-reviewer **APPROVE** / qa-verifier **BLOCK**(AC1/AC4 범위 모호) → BLOCKED.
- round 2 (selective): AC1에 테스트 케이스 ID·콜 수치, AC4에 463/mypy30 명시 → qa-verifier **APPROVE**. APPROVED.

## 정직성 불변식
이중-실행 제거는 메트릭 byte-equivalent(동일 env 상태원)이지 측정값 변경 아님 — 기존 테스트가 가드.
구독 provider는 ToS상 대화형 용도·rate limit 있음 명시(소규모 probe 권장). 과대 0.
