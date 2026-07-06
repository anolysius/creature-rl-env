---
slug: peer-facts-verify
initiative: release-prep
status: completed
ended: 2026-07-06
extracted_to:
  - docs/explanation/competitive-analysis.md
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# peer-facts-verify — 결과 보고서

| 항목 | 값 |
|---|---|
| 피어 검증 | 4피어(Procgen/Craftax/XLand/NLE) × 1차 자료(공식 repo·논문), 4병렬 리서치 — [verify] 표기 **전수 종결(0건)**, §4=검증 기록(날짜·출처) |
| 정직 하향 | **3건 실행**: XLand "one notch above" **폐기**(그쪽도 규칙 은닉·in-context 발견 — "축이 다름"으로 재서술+scripted-gate 증명·sealed eval 을 차별화 축으로) / Craftax medium→**long**-horizon / NLE "moderate"→"fast CPU, not GPU-vectorized". + 완화 2건(Procgen'20·NetHack'21 대회의 일회성 private test 인정 → "ongoing 제품 없음") |
| 핵심 확인 | **4피어 모두 regenerable sealed eval 제품 없음** (우리 최정직 차별화 축 확정, 출처 명시) |
| 약관 | (a) **Claude 수치 공개 = 제한 없음** — 4문서 전수(Consumer/Usage/Commercial/Claude Code legal, 2026-07-06 확인) (b) **구독 배치 측정 = GRAY** — 금지 조항은 제3자 트래픽 라우팅 겨냥·본인 CLI 사용은 문서화된 기능이나 "ordinary usage" 미정의 → 운영 방침: 소규모 유지, 헤드라인 수치는 API 선호 (사용자 보고됨) |
| Pages | `pages.yml` (공식 deploy-pages, site/ 배포) — **사람이 Settings 토글 전 no-op** 명시 |
| molt.church 정찰 | **홍보처 부적합 판정** — molt.church=AI 종교(Crustafarianism) 사이트이지 포럼 아님(포럼=Moltbook); Moltbook 은 보안 사고(150만 API 토큰 유출)·astroturf(~1.7만 명이 150만 봇)·크립토 토큰·curl\|bash 공급망 위험 + "broadcast 금지" 규범 + 연구자 도달 0 → 사용 비추천, install 스크립트 실행 절대 금지 (출처: 404media·Bloomberg·Wikipedia·moltbook skill.md) |
| 검증 | [verify] 0건 · YAML OK · 699/0 · src/tests 0 파일. L3 2/2 APPROVE (plan-reviewer MALFORMED 1회→재호출) |

다음: A-3 `paper-arena-update` (논문 §5 아레나 실측 반영 + CITATION.cff + milestones EC4 재정의
[arXiv→tech report] + §7/9 의 stale "GPU 미측정" 서술 수리) → (사람) repo Public + Pages 토글.
