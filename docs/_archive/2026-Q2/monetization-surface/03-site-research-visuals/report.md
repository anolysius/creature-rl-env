---
slug: site-research-visuals
initiative: monetization-surface
status: completed
ended: 2026-07-01
extracted_to: []
changelog_entry: docs/CHANGELOG.md (monetization-surface 섹션)
---

# 사이트 연구-설명 시각화 — 결과 보고서 (범례·band 차트·썸네일)

## 요약

사이트가 게임플레이 GIF 한 장뿐이던 것을, **연구를 실제로 보여주는 3가지**로 확장(양 언어):
(1) 격자 색 **범례**(render.py 팔레트 SSOT), (2) **SE-rate 추론 band 차트**(oracle 100%/infer 90%/
type_blind 27%/probe 0% — moat KPI), (3) **held-out 세계 썸네일 3장**(서로 다른 맵 = 못 외움).
브라우저 en 시각 확인(색 정합·차트·썸네일).

## 계획 대비 실적

- ✅ **AC1** — 범례(팔레트 rgb 스와치 + en/ko 라벨) + band.png `<img>` + world_1..3.png `<img>`. 4 신규 테스트 + 기존 8 불변.
- ✅ **AC2** — `_build_band_png`(inference_baseline demonstrator → matplotlib, LLM 하드코딩 0) + `_build_world_thumbnails`(heldout_seeds(3) reset 프레임 → imageio). lazy+guard. 실빌드: band.png(546×327) + world_1..3.png(128²).
- ✅ **AC3** — band 캡션(en/ko): scripted band·demonstrator config·LLM=별도 유료 probe·"차트에 미표시"(페이지에 "14%" 0). 범례=팔레트 SSOT. 공개=사람 게이트.
- ✅ **AC4** — pytest **539 passed**(535+4), 0 실패. ruff clean. 기존 스크립트·채점 무변경.

## 변경 파일
- `scripts/build_site.py` — 팔레트 import + `_legend_html`·`_build_band_png`·`_build_world_thumbnails`·render_site 3 섹션·CSS·en/ko copy.
- `tests/test_build_site.py` — 4 신규(palette·korean·band+썸네일·정직 캡션).
- `site/` — band.png·world_1..3.png(신규), index.html·index.ko.html(갱신).

## 정직 경계
- band 차트 = 무료 scripted band(재현); 프런티어 LLM 수치는 **차트에 하드코딩 0**(캡션 텍스트로만·별도 유료 probe).
- 범례 = render.py 팔레트 직접 import(SSOT·드리프트 0). 공개 배포 = 사람 게이트.

## 후속
- #2와 함께 단일 PR(같은 브랜치 feature/leaderboard-site-polish, 사용자 요청). 다음 monetization 제품: #4 비공개 held-out eval 세트 패키지 / #5 커스텀 env 티어.
