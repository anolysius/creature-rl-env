---
slug: readme-ko-parity
initiative: null
status: completed
ended: 2026-07-13
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# 한국어 README 완전 패리티 — 결과 보고서

## 요약

사용자 지적("ko README 부실")에서 출발, 조사 중 **정직성 drift 발견 및 제거**가 핵심 성과.

| 항목 | 결과 |
|---|---|
| README.ko.md | 78줄/6섹션 → **12섹션 완전 번역 패리티**(en 12 == ko 12) |
| **정직성 drift 제거** | ko의 "GPU(T4) 수억 steps/s" 과대주장(영문은 "GPU 미측정" 명시) 제거 — grep "수억/T4" 0 |
| 수치 대조 | ko 수치 토큰 16개 자동 추출 → **영문 존재 missing 0** |
| README.md stale | Release status "공개 미수행" → "Public since July 2026"(사실 부합) + 남은 게이트(GPU·arXiv·태그/허브) 보존 |
| 사이트 링크 | 양쪽에 라이브 사이트+how-it-works 추가(en→.html / ko→.ko.html), 4 URL 전부 HTTP 200 |
| 링크·무회귀 | 상대 링크 11개 대상 전부 존재, 791 green sanity |

한국어 웹사이트는 범위 외 확정 — en/ko 키 패리티가 테스트로 구조 강제(확인됨).

## 계획 대비 실적

AC1(12섹션+수치 drift 0+캐비앗 보존) ✅ · AC2(stale 수정+링크) ✅ · AC3(링크 유효+200) ✅ ·
AC4(791 sanity+CHANGELOG) ✅. L3: qa APPROVE + plan-reviewer(stall→verdict-first) APPROVE —
캐비앗 4곳("CPU·single-run·GPU 미측정"/"baseline not SOTA"/"토대이지 증명 아님"/"포켓몬은
비유")의 행 단위 대응 확인.

## 흡수처 매핑

흡수 없음 — 번역 미러 + stale 정정. ko 하단 "SSOT=영문/코드" 각주 유지.
