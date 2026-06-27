---
slug: stateful-llm-agent
initiative: eval-product
status: active
started: 2026-06-27
acceptance_freeze: true
domains: [agents]
task_type: env
mode: standard
scope_paths:
  - src/critter_gym/llm_eval.py
  - src/critter_gym/eval_harness.py
  - tests/test_llm_eval.py
  - tests/test_eval_harness.py
  - scripts/llm_eval_run.py
extracted_to: []
supersedes: []
---

# stateful LLMAgent — 스텝 간 기억 + 컨텍스트 윈도잉

> 작성일: 2026-06-27 | 상태: 계획 | 이니셔티브: eval-product (M5)

## 목표

현 `LLMAgent`는 매 스텝 **현재 관측만** 프롬프트에 넣는 무기억(stateless) agent다
(`llm_eval.py:138` — `prompt = system + render_obs(obs)`, 과거 0). 부분관측(국소 5×5 시야)에서
무기억 agent는 본 지도를 즉시 잊어 floor한다 — 이는 우리가 이미 입증한 *memory load-bearing*
([[recurrent-baseline]])과 일관된 결과이지, "프런티어 LLM도 못 푼다"는 난이도 verdict가 **아니다**.

본 task는 **기억을 가진** `StatefulLLMAgent`를 추가한다: 한 에피소드 안에서 (관측 요약, 취한 행동)을
누적해 매 프롬프트에 끼워 넣고, 컨텍스트 한도를 막기 위해 슬라이딩 윈도우로 최근 K스텝만 유지한다.
그러면 봉인 set 위에서 "**기억을 줬을 때** 프런티어 LLM이 우리 환경서 몇 % of oracle인가"라는 *공정한*
숫자를 측정할 수 있다.

**M5-EC1 기여**: 비공개 held-out eval의 가치는 "un-gameable한 agentic-LLM 능력 측정"인데, 그 측정이
공정하려면 agent에게 부분관측을 다룰 최소 장치(기억)를 줘야 한다. 본 task는 그 *측정 도구의 공정성*을
올린다. (EC1 자체 완료가 아니라 기능 토대 — hosted 인프라·고객·공개는 사람 게이트.)

## 선행 조건

- #1 `eval_harness`(SealedEvalSet/score_agent/Agent Protocol), #2 `llm_eval`(LLMAgent/render_obs/
  parse_action/provider), #3 `llm_eval_run.py`, #4 `claude_cli_complete` — 전부 done (archive).
- 465 tests green (2 skip), 1.0.0rc1, main HEAD `82002e2`.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/eval_harness.py` | `Agent` Protocol에 **선택적 `reset()`** 추가 + `score_agent`가 에피소드 시작 시(있으면) 호출 | 중 — Protocol 확장이나 하위호환(reset 없는 agent 그대로) |
| `src/critter_gym/llm_eval.py` | `StatefulLLMAgent`(history 누적 + 윈도잉 + `reset()`) 신설. 기존 `LLMAgent` **불변** | 중 — 신규 클래스, 기존 경로 0 변경 |
| `tests/test_llm_eval.py` | history 누적 / 윈도우 상한 / reset 격리 / parse 견고성 테스트 | 저 |
| `tests/test_eval_harness.py` | `reset()`가 에피소드(seed)마다 호출됨 + reset 없는 agent 무회귀 테스트 | 저 |
| `scripts/llm_eval_run.py` | `--stateful` + `--window K` 플래그 (기본 무상태 = 현 동작 byte-identical) | 저 |

### 영향 범위 (import 그래프)

- `eval_harness` ← `llm_eval`, `scripts/llm_eval_run.py`, `scripts/llm_eval_demo.py`. Protocol에
  **추가만** 하므로(메서드 시그니처 불변) 기존 import·호출부 회귀 없음.
- `score_agent` → `_play_once` → `policy(env, obs)`. stateful agent는 `_as_env_policy`로 감싸지며
  `act(obs)`가 매 스텝 호출되는 경로 그대로. **에피소드 경계에서만** `reset()` 추가.

## Step별 계획

1. **`eval_harness` reset 훅** — `Agent` Protocol에 `def reset(self) -> None: ...`를 **선택적**으로
   문서화(Protocol엔 optional 메서드 명시 어려우니, `score_agent`가 `getattr(agent, "reset", None)`로
   duck-typing 호출). `_play_once`(또는 `_as_env_policy` 경계)에서 `env.reset()` 직후 1회 호출.
   reset 없는 기존 submission은 분기 skip → byte-identical.
2. **`StatefulLLMAgent`** — `__init__(complete, *, system, n_actions, window=8)`. 내부 `_history:
   list[tuple[str,int]]`. `act(obs)`: 윈도우 내 과거 (obs 한 줄 요약 + 취한 행동)을 prompt에 prepend
   → `render_obs(obs)` → `complete` → `parse_action` → history append. `reset()`: history clear.
   윈도우 초과분은 drop(가장 오래된 것부터). 과거 obs는 full render가 아니라 **한 줄 요약**(pos/battle/
   gyms)로 토큰 절감.
3. **테스트** — (a) history가 스텝마다 1씩 늘고 window=K에서 상한 K, (b) `reset()` 후 history 0 +
   다음 prompt에 이전 월드 흔적 없음(월드 격리), (c) stub `complete`가 받은 prompt에 과거 행동이
   들어있음, (d) `reset()` 없는 `LLMAgent`로 `score_agent` 무회귀(기존 수치 동일).
4. **러너 플래그** — `llm_eval_run.py --stateful --window K`. 미지정 시 현 무상태 경로(byte-identical).
   비용 경고 문구에 "stateful은 프롬프트가 길어져 호출당 토큰↑" 한 줄 추가.
5. **정직 문서** — docstring + report에 경계 명시(아래 리스크).

**커밋 단위** (L1 plan-reviewer SUGGEST 반영): Step 1~5를 **단일 커밋** + CHANGELOG 1 entry로 묶는다 —
reset 훅(Step 1)·StatefulLLMAgent(Step 2)·테스트(Step 3)·러너 플래그(Step 4)·docstring(Step 5)은 한
기능("기억 장치")의 응집된 변경이며 부분 머지 시 reset 훅만 있고 사용자 없는 dead-path가 생기기 때문.

## 검증 방법

- `mypy src` · `ruff check .` · `python3 -m unittest discover`(pytest 미설치 — unittest) · `python -m build`.
- 무회귀 게이트: 기존 465 tests green 유지 + `LLMAgent`(무상태) `score_agent` 수치 **byte-identical**.
- **실측 probe는 사용자 로컬 실행**(구독 claude CLI, 키=사용자, 채팅 금지) — 본 task는 *도구*를 ship하고
  CI는 stub `complete`로 검증. 라이브 숫자는 별도 사용자 run.

## 리스크

- **컨텍스트 한도**: window가 크면 프롬프트 폭증 → 기본 작게(8) + 과거는 한 줄 요약. (요약·압축
  고도화는 후속 task.)
- **구독 rate limit·속도**: stateful은 프롬프트가 길어 호출당 더 느림 → probe는 소수 월드×짧은 호라이즌.
- **월드 간 오염**: reset 누락 시 월드 A 기억이 B로 누수 → 측정 무효. Step 1 reset 훅 + Step 3(b)
  격리 테스트로 차단(이 task의 가장 중요한 정합성 게이트).
- **과대 금지**: 본 task는 "기억 장치"이지 측정 결과가 아니다. probe 숫자가 나오든(0%~) 그대로 기록,
  "프런티어 LLM이 푼다/못 푼다"로 reframe 금지. "구독으로 과금 0"도 주장 금지(API 키 없이 CLI 파이프
  라인이 돈다까지만).

## Acceptance Criteria (G1 통과 시 freeze)

*사전약정 결정규칙 — 결과(probe 숫자)가 아니라 메커니즘으로만 판정. p-hacking 차단.*

- [ ] AC1: `StatefulLLMAgent`가 `Agent` Protocol(`act(obs)->int`)을 만족하고 `score_agent`로 채점됨.
- [ ] AC2: history가 한 에피소드 안에서 누적되고 `window=K` 상한이 강제됨(K 초과 시 가장 오래된 것 drop).
- [ ] AC3: `reset()`가 에피소드(seed)마다 호출되어 **월드 간 기억 격리**(B의 prompt에 A 흔적 0) — 테스트로 증명.
- [ ] AC4: **무회귀** — 기존 `LLMAgent`(무상태) + reset 없는 submission의 `score_agent` 수치 byte-identical, 기존 465 tests green.
- [ ] AC5: `llm_eval_run.py --stateful --window K` 동작, 미지정 시 현 무상태 경로 불변.
- [ ] AC6: mypy·ruff·unittest·build clean. 정직 경계(도구≠결과, probe=사용자 로컬, 과금 주장 금지) docstring/report 명시.
