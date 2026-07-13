# QA Checklist — board-haiku-seed (G1 freeze)

## Acceptance (plan AC 1-4)
- [ ] AC1 — claude_cli_complete(model=...) 계약 테스트(fake binary·quota 0): None=기존 argv 불변, 지정 시 --model 포함. 무회귀+ruff/mypy.
- [ ] AC2 — community_submit --cli-model/--cli-bin 스레딩 + reproduce 기록. fake-binary 카나리아(1w, quota 0)로 전 경로 검증.
- [ ] AC3 — 본측정 완주(season1·8w·BattleMemory w8·Haiku·단일 run) — JSON --validate VALID, 점수 그대로 등재(사후 재측정 0).
- [ ] AC4 — JSON 커밋 + 사이트 재빌드로 보드 haiku 행(en/ko), 카피 무변경.

## 사전약정 (freeze)
- 설정: season1·n_worlds 8·BattleMemory(w8)·model claude-haiku-4-5-20251001·binary ~/.local/bin/claude. **단일 run 그대로**(유리한 run 고르기·사후 재측정 금지, 낮은 점수=변별력 증거). 라벨 "claude-haiku-4.5 (claude-cli)"+reproduce에 cli-model 기록.
- 예산: ≤1,600콜(구독 quota, API 0원), ~1.5-3.5h background.

## Default DoD
- [ ] 전체 테스트 green. ruff/mypy. L3 APPROVED. CHANGELOG 1줄.
