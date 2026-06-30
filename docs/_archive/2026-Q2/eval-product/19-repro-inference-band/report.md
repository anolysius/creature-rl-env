---
slug: repro-inference-band
initiative: eval-product
status: completed
ended: 2026-06-30
extracted_to: []
changelog_entry: docs/CHANGELOG.md (eval-product 섹션)
---

# 논문 §5 inference band 를 one-command 재현에 추가 — 결과 보고서

## 요약

논문의 재현 진입점 `scripts/reproduce_results.py` 가 (1) throughput + (2) oracle headroom 만
재생성하고 **§5 의 eval-product inference band(#16)는 빠져 있던** 것을 정정. (3) eval-product
inference band 섹션 + testable `inference_band(quick)` 헬퍼 추가 → 리뷰어가 §5 의 scripted band
(oracle/infer/type_blind/probe SE-rate)를 한 명령으로 재생성·검증(무료·결정론, LLM 無). 유료 LLM
실측(§5 SE ~50%)은 평가자 로컬이라 미포함을 명시. M3-EC4(arXiv 초안 신뢰성) 전진.

## 계획 대비 실적

- ✅ **AC1** — `inference_band(quick)` 결정론 InferenceBaseline, SE-rate 단조(oracle≥infer≥type_blind≥probe), quick(4)<full(8). 2 테스트.
- ✅ **AC2** — main() "(3) eval-product inference band" 섹션 출력(4-arm SE-rate). 헤더 (1)(2)(3) + docstring 갱신. 기존 (1)(2) shell-out 무변경.
- ✅ **AC3** — 출력에 "scripted band=무료·결정론·재현 / LLM 실측(§5 ~50%)=유료·평가자 로컬·미포함" 명시.
- ✅ **AC4** — pytest **525 passed**(523+2), 회귀 0. mypy/ruff clean. throughput/headroom 무변경.

## 변경 파일

- `scripts/reproduce_results.py` (+~58): `_DEMO_CONFIG`·`_demo_sealed(quick)`·`inference_band(quick)`(inference_baseline 재사용)·`_print_inference_band` + main() (3) 섹션 + 헤더/docstring. (L3 SUGGEST 반영: sealed 1회 생성.)
- `tests/test_reproduce_results.py` (신규, +30): band 단조·결정론·quick<full.

## 발견된 이슈

- **#18 audit trail 누락 복구** — 본 task 작업 중 #18(se-rate-rigor)의 CHANGELOG/INITIATIVE/archive 가 main 에 없음을 발견(#88 커밋이 코드 3파일만 포함 — 차단 후 재커밋 시 staging 사고). 별도 커밋(`722f9e4`)으로 복구. (본 PR 에 동반.)
- L3 SUGGEST(SealedEvalSet 이중 생성) 반영 — 비차단 cosmetic, sealed 1회 생성으로 정리.

## 흡수처 (extracted_to)

- 없음 — 새 evergreen 없음. repro 진입점 확장(기존 도구 재사용). band 정의·정직 경계는 #16 `inference-baseline.md`.

## 정직 경계

- scripted band 만 재현(무료·결정론). LLM 실측(§5 ~50%)은 유료·평가자 로컬·미포함(출력 명시).
- band 의 type_blind floor 는 max_steps 의존(#16 계승) — repro 는 max_steps=40 고정 운용점.

## 타입/빌드
- pytest 525 passed, 2 skipped. ruff clean. mypy src clean(scripts 는 mypy src scope 외).
