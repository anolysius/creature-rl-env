---
slug: leaderboard-site
initiative: monetization-surface
status: completed
ended: 2026-07-01
extracted_to: []
changelog_entry: docs/CHANGELOG.md (monetization-surface 섹션)
---

# 정적 리더보드 웹사이트 — 결과 보고서 (M5 런치 자산 prototype #1)

## 요약

`leaderboard.py` 결과를 **프레임워크 없는 단일 정적 HTML**로 찍어내는 `scripts/build_site.py` 신설.
페이지 = 랭크 표 + 킬러데모 GIF + moat 설명(held-out seed split·오염 가드·RLVR·un-gameable 추론) +
repo 링크 + 정직 캡션. `site/index.html`(+GIF 복사)로 출력 → GitHub Pages 호스팅 가능. **빌드 +
브라우저 로컬 프리뷰 시각 확인**까지 완료; **공개 배포는 사람 게이트**로 명시.

## 계획 대비 실적

- ✅ **AC1** — `render_site(leaderboard, *, generated_note)` 결정론 유효 HTML(entry·moat·정직·GIF·html.escape). 4 테스트 PASS.
- ✅ **AC2** — main() 무료 baseline(random/scripted) 실측 → `site/index.html`(3.8KB)+gif 복사+프리뷰 안내. stdlib만(프레임워크/네트워크 0). PPO/recurrent [rl] 부재 시 제외. 브라우저 렌더 확인.
- ✅ **AC3** — 페이지 "Honest scope" + docstring: prototype·in-process·수치 출처·"Publishing this page is a human decision".
- ✅ **AC4** — pytest **529 passed**(525+4), 회귀 0, ruff clean, 기존 스크립트·채점 무변경.

## 변경 파일

- `scripts/build_site.py` (신규, +188): `render_site`(순수·testable) + `_rows_html`·`_free_leaderboard`·`_leaderboard_from_json` + main().
- `tests/test_build_site.py` (신규, +67): entry·결정론·moat/정직 문구·escape 4 테스트.
- `site/index.html` (신규, 생성물·결정론) + `site/killer_demo.gif` (복사) — GitHub Pages 호스팅 산출물.

## 흡수처 (extracted_to)

- 없음 — 도구·산출물. 초기 initiative(monetization-surface) narrative 는 INITIATIVE.md.

## 정직 경계

- prototype 런치 페이지이지 hosted 제품 아님. 봉인 = in-process. 수치 = 무료 baseline 실측(LLM 과대 없음).
- 빌드 + 로컬 프리뷰 = 자율. **공개 배포(GitHub Pages 공개 토글) = 사람 게이트**(페이지·docstring 명시).

## 후속 (monetization-surface)
- #2 비공개 held-out eval 세트 (판매 패키징, M5-EC1) / #3 커스텀·고난도 env 티어 (M5-EC2).
- 공개 배포 토글·실제 판매/가격/고객 = 사람 게이트.
