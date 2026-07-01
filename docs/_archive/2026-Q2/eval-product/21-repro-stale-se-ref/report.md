---
slug: repro-stale-se-ref
initiative: eval-product
status: completed
ended: 2026-07-01
extracted_to: []
changelog_entry: docs/CHANGELOG.md (eval-product 섹션)
---

# reproduce_results stale "~50%" 참조 정정 — 결과 보고서 (quick-fix)

## 요약

#20 이 §5 를 "inconclusive, near-floor" 로 하향한 뒤, `scripts/reproduce_results.py` 정직 노트
(docstring + `_print_inference_band` 출력)가 여전히 "§5: ~50%" 를 인용하던 불일치를 정정. 두 문자열
모두 "§5: a robust multi-run probe is inconclusive, near the chart-blind floor" 로 교체.

## 계획 대비 실적
- ✅ **AC1** — 두 정직 노트가 §5 현재 상태 반영, stale "~50%" 제거(grep 0). paper §5 와 일치.
- ✅ **AC2** — comment/string-only(로직·출력·테스트 무변경). pytest **525 유지**. ruff clean. L3 qa-verifier APPROVE.

## 변경 파일
- `scripts/reproduce_results.py` — docstring 1곳 + 출력 2줄, 문자열-only.

## 정직 경계
- mode quick-fix(manual override): scripts/** critical 이나 comment-only=회귀 위험 0(§F.4).
