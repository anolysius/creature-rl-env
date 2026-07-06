# QA Checklist — cli-complete-retry (G1 freeze)

## Acceptance (plan AC 1-4)

- [ ] AC1 — `claude_cli_complete(retries=2)`: 총 시도 최대 3회(1+2), TimeoutExpired 시에만 재시도, 소진 시 raise. 모킹 테스트 2건(3번째 성공=반환+호출수 3 / 전부 timeout=raise+호출수 3). 침묵 폴백 0.
- [ ] AC2 — `score_submission_on_season(on_world=None)`: 월드마다 `on_world(idx0, seed, clears)`, n_worlds=3→정확히 3회+인자 검증, None=byte-identical.
- [ ] AC3 — 무회귀: baseline 695 회귀 0, 기본 인자 경로 동작 동일.
- [ ] AC4 — `--llm` 월드별 stdout `  [k/n] seed=<seed> clears=<c>` (k=1-base, flush=True) — 형식 테스트.

## Default DoD

- [ ] pytest green 회귀 0 · mypy 신규 0 · ruff clean. L3 APPROVED(≥2). CHANGELOG append.
