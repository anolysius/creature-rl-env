---
slug: leaderboard-site-polish
initiative: monetization-surface
status: completed
ended: 2026-07-01
extracted_to: []
changelog_entry: docs/CHANGELOG.md (monetization-surface 섹션)
---

# 리더보드 사이트 폴리시 — 결과 보고서 (게임플레이·학습 시각화·CSS·한국어)

## 요약

#1 정적 사이트를 **매력적으로** 확장: (1) **게임플레이 애니메이션 GIF**(scripted 에이전트가 처음 보는
held-out 세계를 클리어, 128×128·42프레임), (2) **일반화 격차 플롯**(matplotlib), (3) **순수 CSS
애니메이션**(그라데이션 히어로·페이드인·hover), (4) **한국어 버전**(`index.ko.html` + 언어 토글).
영어·한국어 **브라우저 시각 확인** 완료.

## 계획 대비 실적

- ✅ **AC1** — `render_site(..., lang, demo_cleared)` en/ko 결정론. 8 테스트(entry·결정론 en+ko·
  moat/정직·escape·korean·언어토글·@keyframes CSS·demo 캡션 정직) PASS.
- ✅ **AC2** — `build_assets()` `score_baselines` 1회 → gap.png(567×435) + 리더보드; held-out seed
  순회 `boss_defeated` gameplay.gif(128×128·42fr) 생성(seed 고정). imageio/matplotlib lazy+guard.
  main() → index.html + index.ko.html + 자산. 실빌드 성공("defeats the boss" 캡션=격파 seed 채택).
- ✅ **AC3** — 양 언어 "Honest scope"/"정직한 범위" + docstring: prototype·in-process·GIF=scripted
  baseline(학습/LLM 아님)·수치 출처·공개=사람 게이트.
- ✅ **AC4** — pytest **535 passed**(529 + imageio 설치로 un-skip 2 + 신규 4), 0 실패. ruff clean.
  기존 스크립트·채점 무변경.

## 변경 파일

- `scripts/build_site.py` — render_site(lang·demo_cleared 확장·CSS·i18n copy·언어 토글) + build_assets(
  score_baselines 1회·gap plot·boss_defeated GIF·lazy guard).
- `tests/test_build_site.py` — 4→8 테스트(i18n·CSS·자산·정직 캡션 추가).
- `site/` — index.html·index.ko.html·gameplay.gif·gap.png(신규), killer_demo.gif(삭제·미참조).

## 발견된 이슈

- **[저, 비차단] L3 관찰**: `--no-assets` CLI 경로가 `demo_cleared=True` 를 가정(자산 재생성 안 하므로
  실제 격파 여부 미검증). 커밋된 gameplay.gif 는 실제 boss_defeated 클립이라 현재 참이며, 로컬-프리뷰
  전용 경로. 후속 강화 여지(커밋 자산의 cleared 여부를 sidecar 로 기록). 기본 경로(build_assets)는 정확.
- imageio 설치로 기존 skip 2 테스트가 un-skip(535). extras-gated → 미설치 CI 에선 다시 skip(정상).

## 흡수처 (extracted_to)
- 없음 — 도구·산출물.

## 정직 경계
- 게임플레이 GIF = scripted baseline(학습/LLM 아님) 정직 라벨(양 언어). "보스 격파"는 실제 격파 seed 에서만.
- prototype·in-process·수치=무료 baseline. **공개 배포(GitHub Pages 공개)=사람 게이트**(양 언어 명시).
