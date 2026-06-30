---
slug: render-obs-tile-codes-2
initiative: eval-product
status: completed
ended: 2026-06-30
extracted_to:
  - docs/explanation/competitive-analysis.md
  - docs/_active/eval-product/INITIATIVE.md   # sequence #14
changelog_entry: docs/CHANGELOG.md (eval-product, #14)
supersedes: [render-obs-tile-codes]
---

# render_obs 타일-코드 버그 수정 (#14 재적용) — 결과 보고서

## 왜 재적용

`render-obs-tile-codes`(#14, PR #81)는 L1/L3 APPROVED 됐으나, #79·#80을 main에 머지한 뒤
main과 충돌했다. #81 브랜치는 #79보다 먼저 분기돼 `BattleMemoryLLMAgent`가 없어, GitHub 웹
충돌 해소가 #79 코드를 날릴 위험이 있었다. 그래서 **#79가 든 새 main 위에 동일 변경을 재적용**해
충돌 0 PR을 만들었다. 신규 리뷰 아님 — #14의 재적용.

## 요약

| 항목 | 값 |
|---|---|
| 테스트 | 512 → **514** (+2, 회귀 0) |
| mypy / ruff | clean |
| 변경 | `llm_eval.py` 렌더러↔env 코드 정합 + 테스트 |
| 무회귀 | scripted byte-identical, #79 `BattleMemoryLLMAgent` 무영향 (전체 그린) |

## 결과 (정직)

- **버그 확정·수정**: env 생물(1)→"#"벽, 체육관(2)→"C"생물로 보이던 LLM 지도를 바로잡음
  (생물→`C`, 체육관→`G`). SSOT import로 드리프트 재발 차단 + 실 env 회귀 테스트.
- **floor는 두 겹이었다**: render fix가 **engagement floor**를 풀었고(LLM이 체육관 진입,
  battle moves 4~13→~60, 비-gated world 100% 클리어), **inference floor는 render fix + #13
  battle-memory 둘 다 적용해도 SE 0%로 유지** = 하네스 artifact 아닌 진짜 능력 신호.
- competitive-analysis "monetizable eval" 행에 정직 반영.

## 정직 경계

단일 run·2 gated world·scripted-oracle proxy·1 모델 제로샷 = 신호이지 verdict 아님.
oracle 100%(풀 수 있음·안 깨짐). "환경을 쉽게"가 아니라 "floor가 진짜인지 검증"한 결과.
