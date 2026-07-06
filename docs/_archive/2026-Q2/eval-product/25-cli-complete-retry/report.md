---
slug: cli-complete-retry
initiative: eval-product
status: completed
ended: 2026-07-06
extracted_to: []
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# cli-complete-retry — 결과 보고서

| 항목 | 값 |
|---|---|
| 사고 | Fable 5 커뮤니티 실측(8월드 ~1600호출)이 CLI 1건 120s stall 로 TimeoutExpired 전파 → 런 전체 사망, 부분 진행·쿼터 소실 |
| 수리 | `claude_cli_complete(retries=2)` — timeout 시에만 동일 prompt fresh subprocess 재시도(총 최대 3회), 소진 시 raise; **침묵 폴백 0** (측정 비편향 — CLI print 모드는 무상태 독립 프로세스) |
| 가시성 | `score_submission_on_season(on_world=None)` additive 콜백 + `--llm` 월드별 `  [k/n] seed=... clears=...` flush 출력 |
| 테스트 | 695 → **699** (+4: retry 성공/소진 2, 콜백 1, 형식 1), 회귀 0; ruff clean; mypy 신규 0 |
| L1 / L3 | qa BLOCK(AC 구체성)→보완→APPROVE + plan-reviewer SUGGEST 2건(영향도 표·런타임 리스크) 반영 / plan-reviewer MALFORMED 1회→재호출, 최종 **2/2 APPROVE** |

계획 대비: AC1–AC4 전부 ✅. 후속: 재측정(쿼터=사용자 승인) — `--llm` 재실행 시 진행
로그가 월드 단위로 남아 stall/사망 지점도 즉시 가시화.
