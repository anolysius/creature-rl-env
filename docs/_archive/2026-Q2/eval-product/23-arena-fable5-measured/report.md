---
slug: arena-fable5-measured
initiative: eval-product
status: completed
ended: 2026-07-02
extracted_to:
  - docs/reference/battle-arena.md
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# arena-fable5-measured — 결과 보고서 (quick-fix minimal)

| 항목 | 값 |
|---|---|
| 실측 | Claude Fable 5 (claude-cli, modelUsage 로 id 확인), battle-memory, 3+2 runs (임계 불변 확충, #3/#5 선례) |
| 결과 | arena SE-rate 48% vs 앵커 40%/40%·oracle 100%; 5-run 합산 **0.132±0.037 → INCONCLUSIVE (종결적** — mean>floor_eps 라 추가 run 으로 판정 변경 불가) |
| 해석 (사전선언 규칙) | **engagement 가설 기각** (전투 보장에도 +8pp) — 오버월드 바닥은 탐색 실패가 아니라 추론 결핍; 단 "완전 floor" 단정도 과장 (약한 일관 above-chance 신호) |
| 변경 | `docs/reference/battle-arena.md` Measured 섹션 + Boundaries 모순 제거 (docs-only 1 file) |
| 검증 | AC1/AC2 충족, L1·L3 qa-verifier APPROVE (quick-fix 단일 리뷰어) |

후속 seed: 논문 §5 에 arena 실측 반영 / LLM 커뮤니티 리더보드 엔트리 wiring (다음 task).
