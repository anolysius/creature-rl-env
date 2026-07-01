---
slug: repro-stale-se-ref
initiative: eval-product
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: quick-fix
scope_paths:
  - scripts/reproduce_results.py
extracted_to: []
supersedes: []
---

# reproduce_results 정직 노트의 stale "~50%" 참조 정정 (일관성)

> 작성일: 2026-07-01 | mode: quick-fix

## 목표

`scripts/reproduce_results.py` 의 정직 노트(docstring line 12 + `_print_inference_band` 출력 line
75)가 아직 **"§5: super-effective-move rate ~50%"** 를 "논문의 frontier-LLM read" 로 인용한다.
#20 이 §5 를 **"inconclusive, near the chart-blind floor"** 로 정직 하향했으므로 이 참조는 stale —
자기 재현 스크립트가 논문이 downgrade 한 수치를 인용하는 불일치. `~50%` 특정 수치를 제거하고
"논문의 frontier-LLM read (현재 inconclusive/near-floor)" 로 정정. 노트의 취지("LLM read 는 유료·
평가자 로컬·본 스크립트 미재현")는 유효 — 숫자만 정정.

## mode: quick-fix (manual override) 근거

`scripts/**` 는 path-criticality 상 critical 이라 auto-detect 는 standard 이나, 본 변경은 **순수
주석/출력 문자열(로직·수치 출력·테스트 영향 0)** 이라 회귀 위험이 없다(§F.4 manual override —
auto-detect false-positive 보정). `git diff` 로 comment-only 임을 검증. 단일 reviewer(qa-verifier).

## Acceptance Criteria (G1 freeze)

1. **[정합]** reproduce_results.py 의 정직 노트(docstring + 출력)가 stale "~50%" 대신 §5 의 현재 상태
   (inconclusive/near-floor 또는 수치 미명시)를 반영. paper §5 와 불일치 0.
2. **[무회귀]** comment/문자열-only(로직·수치 출력·테스트 무변경). pytest 525 유지. ruff clean.
   `git diff` 가 print/docstring 문자열 외 변경 없음을 보임.
