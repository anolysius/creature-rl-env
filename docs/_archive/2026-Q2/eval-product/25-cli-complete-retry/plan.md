---
slug: cli-complete-retry
initiative: eval-product
status: active
started: 2026-07-06
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/llm_eval.py
  - src/critter_gym/community.py
  - scripts/community_submit.py
  - tests/test_llm_eval.py
  - tests/test_community.py
extracted_to: []
supersedes: []
---

# cli-complete-retry — LLM 런 강건화 (timeout 재시도 + 월드별 진행 로그)

> 작성일: 2026-07-06 | 상태: 계획 | 마일스톤: M5-EC3 (커뮤니티 실측의 실패 원인 수리)

## 목표

Fable 5 커뮤니티 실측(8월드, ~1600호출)이 **CLI 호출 1건의 120s stall** 로 전체 사망
(`TimeoutExpired` 전파, 부분 진행 소실). 원인 = `claude_cli_complete` 에 재시도 없음 +
장기 런의 진행 가시성 0 (버퍼링으로 로그 공백). 두 결함을 최소·additive 로 수리:

1. **재시도**: `claude_cli_complete(..., retries=2)` — `TimeoutExpired` 시 fresh
   subprocess 로 최대 N회 재시도, 소진 시에만 raise. **측정 편향 없음** (같은 obs 로
   같은 호출을 다시 시도할 뿐 — 실패를 기본 액션으로 대체하는 침묵 폴백은 금지).
2. **진행 가시성**: `score_submission_on_season(..., on_world=None)` 콜백 (additive,
   기본 None=무변경) + `--llm` 이 월드별 진행(clears 누적)을 flush 출력.

## 영향도 (호출부)

| 대상 | 등급 | 근거 |
|---|---|---|
| `claude_cli_complete` (llm_eval.py) | 낮음 | 호출부 = `llm_eval_run.py`·`community_submit.py` 2곳뿐; `retries` 키워드 기본값 2, **정상 호출 경로는 코드·동작 동일**(재시도는 `TimeoutExpired` 예외 분기에서만) |
| `score_submission_on_season` (community.py) | 낮음 | 호출부 = `--demo`·`--llm`·테스트; `on_world` 기본 None → 기존 호출 byte-identical |
| `community_submit.py` | 낮음 | `--llm` 출력 라인 추가만 |

리스크: (1) **런타임 증가** — 재시도는 stall(120s timeout) 시에만 발동, 최악 호출당
3×120s=6분이지만 정상 호출 무영향; 런은 백그라운드 실행이라 wall-clock budget 상한과
충돌 없음(진행 로그가 stall 가시화). (2) **재시도=동등성** — CLI print 모드는 호출마다
독립 프로세스(세션 상태 없음, cwd=tempdir)라 fresh subprocess 재시도는 같은 prompt 의
동일 재호출 — 응답 분산은 LLM 자체 확률성으로 측정 프레임 안에 이미 포함.

## Acceptance Criteria (G1 freeze)

- **AC1 (재시도)**: `claude_cli_complete(retries=2)` (기본값 2 = **총 시도 최대 3회**:
  최초 1 + 재시도 2) — `TimeoutExpired` 발생 시에만 fresh subprocess 재시도, 성공값
  반환; 3회 전부 timeout 이면 `TimeoutExpired` raise — subprocess 모킹 테스트
  (2회 timeout→3번째 성공: 결과 반환+호출수 정확히 3 / 3회 전부 timeout: raise+호출수
  정확히 3). 실패를 기본 액션으로 바꾸는 침묵 폴백 0.
- **AC2 (진행 콜백)**: `score_submission_on_season(on_world=None)` — 월드마다
  `on_world(world_index:int(0-base), seed:int, clears:int)` 호출 테스트 (n_worlds=3 →
  정확히 3회, 인자 값 검증); 기본 None 은 기존과 byte-identical.
- **AC3 (무회귀)**: 기존 전체 테스트 회귀 0 (baseline 695), `--demo`/`--validate`/
  `llm_eval_run.py` 경로 무변경 (기본 인자 동작 동일 — 재시도는 timeout 예외 시에만).
- **AC4 (스크립트 진행 출력)**: `--llm` 이 월드마다 **stdout** 에 정확한 형식
  `  [k/n] seed=<seed> clears=<c>` (k=1-base) 를 `flush=True` 로 출력 — capsys 또는
  콜백 조립 테스트로 형식 검증.
