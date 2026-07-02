# QA Checklist — site-research-visuals (G1 freeze)

> L1: qa-verifier APPROVE / plan-reviewer 2회 stall(인프라 실패, verdict 아님) → qa-verifier APPROVE + 사용자 진행 지시로 G1.

## Acceptance Criteria

- [x] **AC1 [hard]** ✅ render_site(en/ko): 범례(render.py 팔레트 `_AGENT`/`_CREATURE`/`_GYM_ACTIVE`… → `rgb(r,g,b)` 스와치 + en/ko 라벨 5종) + band `<img src=band.png>` + 썸네일 `world_1..3.png`. 4 신규 테스트(palette·korean·band+썸네일 참조·정직 캡션) + 기존 8 불변. 브라우저 en 시각 확인(색 정합).
- [x] **AC2 [assets]** ✅ build_assets: `_build_band_png`(inference_baseline demonstrator → matplotlib bar, oracle 100%/infer 90%/type_blind 27%/probe 0%, LLM 하드코딩 0) + `_build_world_thumbnails`(heldout_seeds(3) reset 프레임 → imageio, 128×128×3). lazy+guard. 실빌드: band.png(546×327)+world_1..3.png.
- [x] **AC3 [honesty]** ✅ band 캡션(en/ko): "free scripted band(reproducible)·frontier LLM=별도 유료 probe·near chart-blind floor inconclusive·**차트에 미표시**". legend=render.py 팔레트 직접 import(SSOT). "14%" 페이지에 0. 공개=사람 게이트 유지.
- [x] **AC4 [regression]** ✅ pytest **539 passed**(535+4), 0 실패. ruff clean. 기존 스크립트·채점 무변경.

## Default pass-criteria

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5).
- [ ] L3 (task-review) APPROVED (task-end 선결).
