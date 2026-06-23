---
slug: competitive-analysis
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - docs/explanation/competitive-analysis.md
changelog_entry: docs/CHANGELOG.md (env-core, 2026-06-23)
---

# 경쟁 비교 분석 (갭 탐지기) — 결과 보고서

## 요약

공개 전 선결로, OSS RL 벤치마크(Procgen/Craftax/XLand/NetHack) 대비 **정직한 비교 + 갭 탐지기**를 작성
(`docs/explanation/competitive-analysis.md`, docs-only). 사용자 방침(공개는 맨 마지막, 기능 준비+분석 먼저) 지원.

**핵심 산출 = 갭 register**: 우리가 *주장 못 하는 것* → 필요 기능 → 마일스톤 매핑. 가장 큰 leverage =
**난이도 스케일**(toy→hard) + **family 확장 + 학습정책 held-out**(B를 토대→주장), **JAX 포트**(채택 enabler).

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 매트릭스+산문+register+verify-list | ✅ | §1~§5 완비(9축×5열 매트릭스) |
| AC2 정직 열위 명시(전축우위 0) | ✅ | §3 "where we lose, stated first"(속도/성숙·채택/난이도/meta-RL 폭) |
| AC3 우리 수치 논문/DESIGN 일치 | ✅ | (A) property/(B) 토대/numpy ~266k/toy — L3 코드 대조 APPROVE |
| AC4 peer 정성/[verify] + 속도 basis | ✅ | peer 셀 [verify], 266k=CPU/core≠GPU 명시 |
| AC5 갭 register(갭→기능→마일스톤) | ✅ | 6 갭 × (못함/이유/필요기능/unblocks) |
| AC6 docs-only 무회귀 + L3 | ✅ | 코드 무변경(181 불변), broken-link 0, L3 APPROVED |

전 AC ✅. acceptance를 *정직한 비교 + 갭 register*로 freeze(마케팅 아님).

## 변경 파일 상세

**신규(docs-only)**
- `docs/explanation/competitive-analysis.md` — peers / capability 매트릭스 / 정직 트레이드오프(열위 먼저) / peer verify-list / 갭 register(→기능→마일스톤).

## 발견된 이슈 (심각도)

- **(정직 표기)** peer 사실은 학습지식 기반 → 전부 [verify] 라벨(공개 전 1차 출처 검증 필요). 이것 자체가 갭("peer 사실 미검증").
- **(통찰)** 비교가 확인해 줌: 공개 전 **난이도 + genre 폭**을 toy/토대 → hard/주장으로 올려야 함. 사용자 "공개 마지막" 방침 지지.

## 흡수처 매핑 (extracted_to)

- `docs/explanation/competitive-analysis.md` — living 비교 문서(Diátaxis explanation). 논문 비교 섹션·기능 우선순위 입력.

## 타입 체크 / 빌드 결과

docs-only — 제품 코드 무변경. pytest 181 passed/2 skipped 불변. broken-link 0.
