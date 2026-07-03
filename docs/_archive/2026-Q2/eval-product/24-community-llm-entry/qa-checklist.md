# QA Checklist — community-llm-entry (G1 freeze)

> G1 통과 시 freeze. G2·L3 가 1:1 대조.

## Acceptance (plan AC 1-5)

- [ ] AC1 — 채점 SSOT: LLM 채점이 `--demo` 와 동일 env/seeds/지표를 **공유 함수로** 사용 (별도 루프 금지), 월드마다 agent `reset()` 훅.
- [ ] AC2 — schema-valid 산출: fake LLM agent end-to-end → `validate_submission()==[]` (실호출 0 테스트).
- [ ] AC3 — 무회귀: `--demo`/`--validate` 동작 불변(공유-함수 승격 외 무변경, 기존 테스트 통과), 전체 스위트 회귀 0 (baseline 690).
- [ ] AC4 — quota 게이트: `--llm` 이 예상 호출수 경고 출력; 실측·제출 커밋 범위밖(사용자 승인) 을 help/docstring/how-to 에 명시.
- [ ] AC5 — 문서: how-to en/ko 에 LLM 엔트리 소절 (명령·비용·self-reported 라벨).

## Default DoD

- [ ] `.venv/bin/python -m pytest -q` green 회귀 0 · `mypy src` 신규 0 · `ruff check .` clean. L3 APPROVED(≥2). CHANGELOG append.
