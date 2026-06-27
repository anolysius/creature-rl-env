---
slug: llm-eval-adapter
initiative: eval-product
status: active
started: 2026-06-26
acceptance_freeze: true
domains: [rl-env]
mode: standard
task_type: general
scope_paths:
  - src/critter_gym/llm_eval.py
  - tests/test_llm_eval.py
  - scripts/llm_eval_demo.py
extracted_to: []
supersedes: []
---

# Agentic-LLM eval adapter — 오염 방지 LLM 에이전트 평가 (eval-product #2)

> 작성일: 2026-06-26 | 상태: 계획

## 목표

eval-product의 가장 유망한 갈래 = **오염 방지 *agentic-LLM* 능력 평가**(시장 통증 #1). #1
`sealed-eval-harness`가 봉인 held-out + RLVR 검증 채점 + 오염 가드를 만들었고, 거기에 **LLM 에이전트를
제출 가능**하게 하는 어댑터를 추가해 "처음 보는 세계에서 숨은 규칙을 추론해 체육관을 깬다 — verifiable
subgoal로 채점, 봉인 held-out이라 외울 수 없다"를 *동작하는 코드*로 만든다.

핵심: env obs를 **텍스트로 렌더**(LLM이 읽음) → LLM이 행동 텍스트 반환 → **action으로 파싱** →
#1의 `score_agent`로 채점. 어댑터는 **provider-agnostic**(완성 함수 `complete: (prompt)->reply` 주입)이라
CI는 **stub LLM**으로 결정론·무-API 테스트, 실제 Anthropic hookup은 옵션(claude-api 레퍼런스 준수).

## 선행 조건

- #1 `eval_harness`: `Agent` Protocol(`act(obs)->int`)·`score_agent`·`SealedEvalSet`. LLMAgent가 Agent를 만족.
- env obs(numpy): agent_pos(2)·local_patch(5×5 tile codes)·in_battle·player/enemy hp/type/level·gyms_defeated·
  caught·evolved·charge. action 6: 0-3=N/S/E/W·4=Catch(overworld)/Switch(battle)·5=Wait/Item(battle 0-3=공격).
- 순수 numpy(core 모듈, CI 테스트 가능). Anthropic hookup은 lazy-import(옵션, repo 의존성 추가 없음).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/llm_eval.py` | 신규 | 중 | `render_obs`/`parse_action`/`LLMAgent`/`anthropic_complete`(옵션). eval_harness/env import만. |
| `tests/test_llm_eval.py` | 신규 | 저(test) | render 결정론·legible / parse 강건성+fallback / LLMAgent가 Agent 만족·stub로 score_agent 통과 |
| `scripts/llm_eval_demo.py` | 신규 | 저(script) | stub-LLM 에이전트를 봉인 set서 채점(오염 방지 agentic eval 시연) + Anthropic hookup 안내(주석) |

### 영향 범위

- 신규 독립 모듈, 기존(eval_harness/env) import만 — 무변경. 전체 테스트 회귀 0.

## 설계 (구현 윤곽)

- `render_obs(obs) -> str`: 읽기 쉬운 텍스트(위치·in_battle·party hp/type/level·enemy[전투 시]·gyms cleared·
  5×5 ascii 로컬뷰·**문맥별 action 범례**). 결정론(같은 obs→같은 문자열).
- `parse_action(reply, n_actions=6) -> int`: reply에서 숫자(0-5) 또는 키워드(north/south/east/west/catch/
  wait/attack/switch) 추출 → action index. 모호/실패 시 **안전 fallback**(5=Wait). 강건(LLM 장황함 허용).
- `LLMAgent(complete, system=DEFAULT_SYSTEM)`: `act(obs)=parse_action(complete(system + render_obs(obs)))`.
  `Agent` Protocol(`act(obs)->int`) 만족 → #1 `score_agent`로 그대로 채점.
- `anthropic_complete(model="claude-opus-4-8", max_tokens=...) -> complete`: **옵션** Anthropic hookup
  (lazy `import anthropic`; `messages.create(model=…, system=…, messages=[user])` → text). claude-api 레퍼런스
  준수(model id·thinking 생략). API key/패키지 없으면 ImportError 안내.

## Step별 계획
> 커밋 경계: lifecycle 끝 1 커밋(관례).
1. **(red)** `tests/test_llm_eval.py`: render 결정론+핵심 필드 포함 / parse 강건성(숫자·키워드·쓰레기→fallback·
   범위 클램프) / LLMAgent(stub complete)가 `isinstance(_, Agent)` 만족 + `score_agent`로 봉인 set 채점되어
   Scorecard 반환.
2. **(green)** `llm_eval.py` 구현(위 설계). eval_harness/env import만.
3. **(green)** `scripts/llm_eval_demo.py`: 결정론 stub-LLM(예: 항상 "WAIT" / 간단 휴리스틱)을 봉인 set서
   `score_agent`로 채점 출력 + Anthropic hookup 사용법 주석(opt-in).
4. **(verify)** mypy(src)·ruff·pytest(신규+기존 무회귀)·build clean.

## 검증 방법
- pytest: 신규 + 기존 전체 green(회귀 0). mypy·ruff·build clean.
- render/parse 결정론·강건성, LLMAgent가 #1 하니스와 합쳐져 end-to-end 채점됨이 코드로 입증.
- demo가 "봉인 held-out서 LLM(stub) 에이전트 채점"을 시연.

## 리스크
- **R1 LLM API 의존**: CI/테스트가 실제 LLM 호출하면 비결정·비용·키 필요. **완화**: 코어 provider-agnostic
  (complete 주입), 테스트·demo는 **stub** 사용. Anthropic은 옵션 lazy-import.
- **R2 parse 취약**: LLM 출력이 다양해 파싱 실패. **완화**: 숫자+키워드+fallback(Wait)+범위 클램프, 강건성
  테스트(쓰레기 입력 포함).
- **R3 과대("LLM eval 완성")**: stub로만 검증하고 실측 LLM 결과 없음. **완화**: "어댑터(메커니즘)이지 실제
  LLM 능력 측정 결과 아님; 실측은 API key+비용 필요한 별도 run" 정직 명시.

## Acceptance Criteria (G1 통과 시 freeze)
- **AC1 (텍스트 렌더)**: `render_obs(obs)`가 결정론(같은 obs→동일 문자열)이고 **구체 필드 포함**:
  `agent_pos`(위치)·`in_battle`·`gyms_defeated`(cleared 수)·5×5 ascii 로컬뷰·문맥별 action 범례(0-5);
  전투 시 enemy hp/type 추가. 테스트로 결정론 + 위 필드 문자열 존재 검증.
- **AC2 (강건 파싱)**: `parse_action(reply, n_actions=6)`가 (a) 숫자 0-5 (b) 방향/행동 키워드(north/south/
  east/west/catch/switch/wait/attack) (c) 쓰레기/빈 입력→안전 fallback(5=Wait) (d) 범위 밖 숫자→클램프.
  모두 정수 ∈ [0, n_actions) 반환. 결정론 테스트.
- **AC3 (제출 통합)**: `LLMAgent`가 **`critter_gym.eval_harness`(#1)의 `Agent` Protocol(`act(obs)->int`,
  runtime_checkable)** 만족(`isinstance(agent, Agent)` True) → stub `complete`로 #1 `score_agent`(봉인
  `SealedEvalSet`) 채점되어 #1 `Scorecard`(NamedTuple) 반환(end-to-end 테스트). Anthropic hookup
  `anthropic_complete`은 옵션(lazy `import anthropic`, 미설치/키 없음 시 명확 에러).
- **AC4 (회귀 0, G2 검증)**: 기존 src 무변경(신규 모듈만), 전체 테스트 무회귀, mypy(29→증가)·ruff·build
  clean. **(정직 경계, 산출물 명시)** llm_eval docstring·demo·report에 "어댑터=메커니즘이지 실측 LLM 능력
  결과 아님(실측=API key+비용 별도 run)·stub 검증·프로토타입" 명시. Anthropic 예시는 claude-api 레퍼런스
  준수(model `claude-opus-4-8`, thinking 생략).
- **AC5 (task-end 산출, audit floor)**: lifecycle 종료 시 `docs/_active/eval-product/INITIATIVE.md` #2 행
  추가 + `docs/CHANGELOG.md` 1줄 append(rules/80 §F.5 모든 mode 강제). (G1 freeze 시점엔 미작성 — task-end
  단계 산출물.)
