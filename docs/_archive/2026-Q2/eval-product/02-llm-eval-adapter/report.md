---
slug: llm-eval-adapter
initiative: eval-product
status: completed
ended: 2026-06-26
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md   # eval-product #2 행
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# Agentic-LLM eval adapter — 결과 보고서 (eval-product #2)

## 요약

eval-product의 가장 유망한 갈래(오염 방지 *agentic-LLM* 평가)를 #1 봉인 하니스 위에 어댑터로 실현.
신규 `critter_gym.llm_eval`(순수 numpy, core·CI 테스트 가능):
- **`render_obs`** — env obs → LLM이 읽는 텍스트(position·in_battle·gyms·party/enemy·5×5 ascii 로컬뷰·
  문맥별 action 범례). 결정론.
- **`parse_action`** — LLM free-text → action(숫자/키워드/쓰레기→fallback5/범위 클램프, 항상 [0,n)).
- **`LLMAgent`** — provider-agnostic `complete(prompt)->reply` 주입 → #1 `Agent` Protocol(`act(obs)->int`)
  만족 → #1 `score_agent`(봉인 set)로 그대로 채점.
- **`anthropic_complete`** — 옵션 Anthropic hookup(lazy-import, `claude-opus-4-8`, claude-api 준수).

**demo**(16 sealed worlds): render_obs 출력 + stub-LLM 에이전트를 봉인 set서 `score_agent` 채점 end-to-end.
"오염 안 되는 agentic-LLM 능력 시험"의 메커니즘을 코드로 입증(stub은 dumb→0.00 gyms; 메커니즘이 요지).

## 계획 대비 실적

| AC | 상태 | 결과 |
|---|---|---|
| AC1 텍스트 렌더 | ✅ | render_obs 결정론+필드, 2+1 테스트 |
| AC2 강건 파싱 | ✅ | 숫자/키워드/fallback/클램프, 5 테스트, 항상 [0,n) |
| AC3 제출 통합 | ✅ | LLMAgent=Agent(isinstance), stub→score_agent→Scorecard end-to-end, anthropic 옵션 |
| AC4 회귀0/정직경계 | ✅ | 기존 src 무변경, 450→461(+11), mypy30/ruff/build clean, 정직 경계 명시 |
| AC5 task-end 산출 | ✅ | INITIATIVE #2 + CHANGELOG |

## 변경 파일 상세

**신규**:
- `src/critter_gym/llm_eval.py` — `render_obs`/`parse_action`/`LLMAgent`/`anthropic_complete`/`DEFAULT_SYSTEM`.
  eval_harness/env import만(무변경). 순수 numpy(core·CI 테스트); anthropic은 lazy-import 옵션.
- `tests/test_llm_eval.py` — 11 테스트(render 결정론·필드·numpy scalar / parse 5종 / LLMAgent Protocol·
  end-to-end score / anthropic lazy-import).
- `scripts/llm_eval_demo.py` — stub-LLM을 봉인 set서 채점 + render_obs 예시 출력 + Anthropic hookup 주석.

## 발견된 이슈

- **(정직 경계)** 어댑터=메커니즘이지 *실측 LLM 능력 결과 아님*. CI/테스트/demo는 결정론 stub(무-API).
  실측은 API key+비용 별도 run. docstring/demo에 명시.
- **(claude-api 준수)** Anthropic hookup은 `claude-opus-4-8`·thinking 생략·lazy-import(repo 의존성 추가 0).
  mypy `import-not-found`는 inline `# type: ignore`로 처리(pyproject ignore 목록은 scope 밖).

## 흡수처 매핑

- `docs/_active/eval-product/INITIATIVE.md` #2 행 — agentic-LLM 어댑터(오염 방지 LLM 평가) narrative.
- ADR 가치 없음(#1 하니스 + 텍스트 어댑터, 새 아키텍처 결정 아님).

## 타입 체크 / 빌드 결과

- `mypy src`: 30 files clean. `ruff check .`: passed. `build`: 1.0.0rc1 OK. `pytest`: 461 passed, 2 skipped.

## 후속 (initiative, 사람/비용 게이트)

- **실측 LLM 평가 run**(API key+비용·사람) — `anthropic_complete`로 실제 모델을 봉인 set서 채점.
- 서버측 봉인 인프라·다중 config·hosted eval-as-a-service. 고객·공개는 사람 게이트.
