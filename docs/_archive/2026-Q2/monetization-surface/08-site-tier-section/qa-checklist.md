# QA Checklist — site-tier-section (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-6)

- [ ] AC1 — `render_site`에 "Difficulty tiers" 섹션: **고정 리스트 `("standard","hard")`만** `get_tier()`로 SSOT 렌더(name/knobs/harder_knobs/difficulty_note, 전 값 html.escape, 수치·주장 하드코딩 0). 레지스트리 전역 순회 금지.
- [ ] AC2 — SSOT-일치 테스트(렌더 note ≡ `get_tier(...).difficulty_note`, env_tier에서 읽어 비교) + 내장 티어명 포함 + **누출-방지 실증 테스트**(custom 티어를 실제 `register_tier` 등록 후 렌더해도 미포함).
- [ ] AC3 — 양 언어: ko 페이지 라벨 한국어 + 동일 note, 언어 토글·기존 섹션 불변.
- [ ] AC4 — 정직 캡션: 구매자 흐름 한 줄(티어→sealed 매니페스트→서명 인증서) + "prototype·실판매/hosting=사람 게이트" 양 언어.
- [ ] AC5 — `--no-assets` 재빌드로 `site/index.html`·`index.ko.html` 갱신(자산 무변경), 결정론 유지.
- [ ] AC6 — 회귀 0(전체 스위트, baseline 626 — 기존 site 12 테스트 불변), ruff clean. CHANGELOG 1줄.

## Default DoD

- [ ] 전체 테스트 green, 회귀 0.
- [ ] `ruff check scripts/build_site.py tests/test_build_site.py` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
