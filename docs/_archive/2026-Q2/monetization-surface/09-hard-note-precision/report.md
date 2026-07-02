---
slug: hard-note-precision
initiative: monetization-surface
status: completed
ended: 2026-07-02
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# hard 티어 difficulty_note 정밀화 — 결과 보고서

## 요약

| 항목 | 값 |
|---|---|
| 성격 | 정직성-정밀화(텍스트-only, knob 무변경) — #8 report [SSOT 관찰] 후속 |
| 테스트 | 630 → 630 (강화 테스트 포함 회귀 0) |
| lint/type | ruff clean · mypy Success |
| L3 | **2/2 APPROVE** (수치·stale 수리 코드 대조 확인) |

## 계획 대비 실적

| AC | 결과 |
|---|---|
| AC1 note 3요소 | ✅ ff ~11–16% 유지 + "related, deeper grid16 config(5gym·420step): rec ~32–43% of oracle(천장 미달)" + "이 정확한 config 의 recurrent·SOTA-class = OPEN, SOTA-hard 주장 금지". knob 무변경. |
| AC2 테스트 | ✅ 기존 토큰 유지 + "recurrent"/"related" 검증 추가. #100 SSOT-일치 자동 정합(site 테스트가 원문 비교). |
| AC3 파급 | ✅ env-tiers.md(인트로+표)·list_env_tiers.py(정직 docstring/print) 정합, site 재빌드(각 html note 문자열만 치환, 자산 무변경). |
| AC4 회귀 | ✅ 630 passed, ruff/mypy clean. CHANGELOG 1줄(본 task-end). |

## 추가 발견·수리 (scope 내)

- **`list_env_tiers.py` 의 2번째 stale**: "sealed 가 patch_radius/num_gyms 를 드롭" — #7(sealed-difficulty-levers)에서 이미 수리된 낡은 서술이 데모 docstring·print·섹션 제목에 잔존 → "carries patch_radius/num_gyms (drops only num_creatures)"로 정정 + `build_sealed` 출력에 두 레버 표시. L3 가 `_SEALED_KNOBS`/`_SEALED_DROPPED` 코드 대조로 정정 정확성 확인.

## 교훈

SSOT 원문 렌더(사이트)는 코드의 낡은 문장이 곧 판매 페이지의 낡은 문장 — 측정이 갱신되면 note 도 함께 갱신하는 규율 필요(이 task 가 그 첫 사례).
