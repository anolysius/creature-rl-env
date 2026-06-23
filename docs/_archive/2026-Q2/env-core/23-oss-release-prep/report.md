---
slug: oss-release-prep
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - LICENSE
  - README.md
  - CONTRIBUTING.md
changelog_entry: docs/CHANGELOG.md (env-core, 2026-06-23)
---

# OSS 릴리스 준비 (M3-EC5) — 결과 보고서

## 요약

활성 M3의 미충족 **EC5(OSS 공개)** 전진 — 오픈소스 릴리스 **로컬 산출물** 준비. MIT `LICENSE` 파일 신규
(pyproject 이미 MIT 선언) + stale README("Phase 0 — Nothing built yet") → 실제 빌드 상태로 재작성 +
`CONTRIBUTING.md` 신규.

**범위 경계(정직)**: **실제 외부 발행**(Prime Intellect Hub 리스팅, GitHub repo public 전환)은 계정·사람
판단이 필요한 외부 행위 = **사용자 게이트**(M3-EC6 killer-demo 선례). 본 task는 *릴리스 산출물 준비*까지.
EC5 "충족"은 사람이 외부 발행 후 결재 — README "Release status"에 명시.

| 검증 | 결과 |
|---|---|
| LICENSE | 표준 MIT 전문 + copyright, pyproject `license={text="MIT"}` 정합 |
| README | install/quickstart(env id 6종)/positioning/측정 요약(논문 링크)/재현/citation; "Phase 0" 제거 |
| 수치 정확성 | held-in 40%/held-out 45%, ~266k, gate ≥0.20/≥0.10, C +3.9 vs +0.2 — 논문과 verbatim 일치(L3 코드/논문 대조) |
| 무회귀 | 제품 코드·테스트 무변경(181 passed 불변), broken-link 0 |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 LICENSE+pyproject 정합 | ✅ | 표준 MIT + "CritterGym contributors", license={text="MIT"} 일치 |
| AC2 README 실제 상태 | ✅ | install(4 extra)/quickstart(env id 6종)/positioning/측정/재현/citation, Phase 0 제거 |
| AC3 수치 일치(verbatim) + (A)/(B) | ✅ | 논문/DESIGN 대조(L3 APPROVE), (A) 측정/(B) 토대지 증명 아님 |
| AC4 외부 발행=사람 게이트 | ✅ | "Release status"에 Hub/public 미수행=maintainer 행위 명시, EC5 자동충족 주장 0 |
| AC5 CONTRIBUTING + broken-link 0 | ✅ | dev 셋업·4 체크·정직성·lifecycle, 링크 전부 유효 |
| AC6 무회귀 + M3-EC5 전진 | ✅ | 루트 메타 파일만 변경, 181 passed 불변, EC5 준비(외부 발행 사람 게이트) |

전 AC ✅. acceptance를 *릴리스 산출물 준비 + 정직 표기*로 freeze.

## 변경 파일 상세

**신규**
- `LICENSE` — 표준 MIT 전문 + "Copyright (c) 2026 CritterGym contributors"(사용자가 법적 주체로 교체 가능).
- `CONTRIBUTING.md` — dev 셋업(.venv/[dev]/ruff/mypy/pytest/build) + 정직성 규율(signal/CI-vs-run/scope) + task lifecycle.

**갱신**
- `README.md` — stale Phase 0 → 실제 상태: 한 줄 소개·install·quickstart(env id 6종 표, family A–D)·"What it measures"(A 측정/B 토대, 논문 링크)·정직 positioning(Pokémon=메타포)·재현(seed split)·citation·**Release status(외부 발행=사람 게이트)**·license.

## 발견된 이슈 (심각도)

- **(낮음, L3 accuracy reviewer 노트 반영)** env 표에 family A 라벨 누락 → `CritterGym-v0`에 "family A baseline" 추가.
- **(정직 표기)** EC5는 *준비*까지 — 외부 발행(Hub/public)은 사람 게이트. milestones M3-EC5는 사람 발행+결재 후 `[x]`.

## 흡수처 매핑 (extracted_to)

- `LICENSE`/`README.md`/`CONTRIBUTING.md` — 공개 표면 evergreen 산출물. 정직 scope는 DESIGN §3.1.1 + 논문 SSOT 준수.

## 타입 체크 / 빌드 결과

루트 메타 파일만 변경 — 제품 코드 무변경. pytest 181 passed/2 skipped 불변. broken-link 0. LICENSE↔pyproject 정합.
