# QA Checklist — stateful-llm-agent (G1 freeze 대상)

> 생성: 2026-06-27 (task-evaluate APPROVED 후) | freeze: pending → G1 통과 시 확정

## Acceptance Criteria (plan §AC, 사전약정 결정규칙)

- [x] AC1: `StatefulLLMAgent`가 `Agent` Protocol(`act(obs)->int`)을 만족하고 `score_agent`로 채점됨.
- [x] AC2: history가 한 에피소드 안에서 누적되고 `window=K` 상한이 강제됨(K 초과 시 가장 오래된 것 drop).
- [x] AC3: `reset()`가 에피소드(seed)마다 호출되어 월드 간 기억 격리(B의 prompt에 A 흔적 0) — 테스트로 증명.
- [x] AC4: 무회귀 — 기존 `LLMAgent`(무상태)+reset 없는 submission의 `score_agent` 수치 byte-identical, 기존 465 tests green.
- [x] AC5: `llm_eval_run.py --stateful --window K` 동작, 미지정 시 현 무상태 경로 불변.
- [x] AC6: mypy·ruff·unittest·build clean. 정직 경계(도구≠결과, probe=사용자 로컬, 과금 주장 금지) docstring/report 명시.

## 표준 DoD (pass-criteria 기본)

- [x] mypy src clean (30 files)
- [x] ruff check . clean
- [x] `pytest` green 474 passed / 2 skip (회귀 0; pytest는 .venv)
- [x] `python -m build` clean
- [x] CHANGELOG 1 entry (standard narrative)
- [ ] 단일 커밋 (Step 1~5 응집) — 사용자 commit 단계
