---
slug: site-redesign
initiative: null
status: completed
ended: 2026-07-08
extracted_to: []
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# site-redesign — 결과 보고서

| 항목 | 값 |
|---|---|
| 디자인 시스템 | CSS 디자인 토큰(--surface/--ink/--series/--radius/--shadow) + **라이트/다크 테마**(prefers-color-scheme + `:root[data-theme]` 수동 토글, vanilla JS localStorage) + 컴포넌트(카드·테이블 uppercase 헤더·tabular 숫자·moat 카드·pill 버튼) |
| 인라인 SVG 차트 | matplotlib PNG 2개(gap.png/band.png) **삭제** → 인라인 SVG 2종. `_gap_svg`(2색 blue/aqua 그룹막대, held-in/held-out) + `_band_svg`(단일 accent, oracle→probe). 값=`leaderboard.entries`·`inference_baseline` **실측**(하드코딩 0), 테마 반응, `<title>` hover, dataviz 팔레트 validator 통과(ΔE 73.6, 라이트/다크 각 surface) |
| en/ko 싱크 | 키 집합 동일(테스트 강제) + `<title>` 언어별화. ko 정보량 = en (브라우저 4조합 확인) |
| GIF 무한반복 | `render.save_gif(loop=0)` 기본 — NETSCAPE loop 마커 확인 |
| 테스트 | 699 → **706**(+7). 3 기존 테스트(PNG 참조) → SVG 검증 갱신. ruff clean·mypy 신규 0 |
| 시각 검증 | en·ko × 라이트·다크 **4조합 브라우저 실측** — 라벨 클리핑 1건 발견·수정(pad_l 확대), 나머지 정상 |
| L1 / L3 | 2/2 APPROVE(SUGGEST 반영) / 2/2 APPROVE(plan-reviewer MALFORMED 1회→재호출) |

계획 대비 AC1–AC6 전부 ✅. 결정론(재빌드 diff 0)·수치 SSOT(실측 유래) 유지.
후속: 머지 → PR CI + pages 워크플로가 배포 실측(soft launch 기간).
