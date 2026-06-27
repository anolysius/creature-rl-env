# QA Checklist — llm-eval-adapter (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 동결.
> ⚠ eval-product #2 — 오염 방지 agentic-LLM 평가 어댑터. 성공 = *동작하는 어댑터 메커니즘*이지 실측 LLM 능력 결과 아님.

## Acceptance Criteria (frozen at G1)

- [x] **AC1 (텍스트 렌더)** ✅ — `render_obs` 결정론 + 필드(position·in_battle·gyms·5×5 ascii·action 범례
  0-5·전투 시 enemy) 검증. 2 테스트(`test_render_obs_is_deterministic`/`_includes_core_fields`) + numpy scalar.
- [x] **AC2 (강건 파싱)** ✅ — `parse_action`: 숫자(action N/standalone)·키워드(north~wait)·빈/쓰레기→fallback5·
  범위밖→클램프, 모두 [0,n). 5 테스트(plain number/keywords/garbage/out-of-range/all-in-bounds).
- [x] **AC3 (제출 통합)** ✅ — `LLMAgent` `isinstance(_, Agent)` True + stub complete로 `score_agent`(봉인
  set) → `Scorecard`(n_worlds=4, stub.calls>0) end-to-end. `anthropic_complete` lazy-import 옵션(미설치 시
  ImportError 테스트). demo end-to-end 동작.
- [x] **AC4 (회귀 0, G2)** ✅ — 기존 src 무변경(신규 모듈만). 450→**461 passed**(+11), 2 skip. mypy **30**·
  ruff·build clean. 정직 경계(어댑터=메커니즘·실측 LLM 결과 아님·stub·프로토타입) docstring/demo 명시.
  Anthropic 예시 `claude-opus-4-8`·thinking 생략(claude-api 준수).
- [x] **AC5 (task-end 산출)** ✅ — INITIATIVE #2 + CHANGELOG = task-end 단계.

## L1 이력
- round 1: plan-reviewer **SUGGEST**(다음 task 진입 기준) / qa-verifier **BLOCK**(AC4 INITIATIVE/CHANGELOG가
  freeze 이후 산출물) + SUGGEST(AC1/AC3 구체화) → BLOCKED.
- round 2 (selective): AC4(G2 검증)와 AC5(task-end 산출) 분리 + AC1 필드 구체화 + AC3 #1 타입 참조 →
  qa-verifier **APPROVE**. plan-reviewer SUGGEST 흡수 → APPROVED.

## 정직성 불변식
어댑터=메커니즘(텍스트 렌더+파싱+#1 채점 연결)이지 *실측 LLM 능력 결과 아님*(실측=API key+비용 별도 run).
CI/테스트/demo는 결정론 stub LLM(무-API). Anthropic은 옵션 lazy-import(claude-opus-4-8). 봉인 held-out
(오염 불가)에서의 채점이라 결과가 신뢰됨 — 그 메커니즘을 #1과 합쳐 입증. 과대 0.
