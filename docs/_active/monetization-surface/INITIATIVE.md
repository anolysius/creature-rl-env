# Initiative: monetization-surface (M5 — 수익화 표면 prototype)

> **moat 엔진(eval-product)은 검증됨 → 이제 *판매 표면* prototype.** eval-product 이니셔티브가 오염·
> 암기·게이밍 불가 sealed eval 의 *기능 토대*를 짓고 validity 를 경화했다(#15–#21). 본 이니셔티브는
> 그 위에 **팔 수 있는 제품의 기술 artifact 를 prototype 하고 테스트**한다.
>
> **불변식(정직 게이트)**: prototype = *기술 artifact* 자율. **실제 판매·가격·고객·hosting·공개 배포
> = 사람 게이트**(DESIGN §8 · CLAUDE.md). 예: 정적 사이트를 빌드+로컬 프리뷰까지 자율, GitHub Pages
> *공개 토글*은 사람.

## 왜 지금

- 사용자 결정(2026-07-01): "판매용 제품 한두 개 prototype 해서 테스트해보자." moat 엔진이 검증된
  지점(#20 이 eval 의 un-gameable 작동을 실증)에서 *판매 표면*을 구체화할 때.
- **마일스톤**: M5(수익화 표면). 활성 M3 의 남은 EC(arXiv 초안=사실상 완료·사람 제출 / OSS 공개=사람
  게이트)보다 앞서 가는 것 — 사용자 명시 override.

## 제품 후보 (사용자 선택)

1. **비공개 held-out eval 세트 (판매 패키징)** — M5-EC1. `SealedEvalSet`+`verify_sealed` 위 buyer/
   seller 패키징 + 서명된 오염-불가 인증서. moat 직결.
2. **커스텀/고난도 env 티어** — M5-EC2. 기존 knobs·env_family 위 "더 어려운/다른 장르" 티어.
3. **리더보드 웹사이트 (정적, git 호스팅)** — M5-EC3 / 런치 자산. `leaderboard.py` JSON → 정적 HTML
   (프레임워크 0) + 킬러데모 GIF + moat 설명. *첫 task*.

## 정직성 문화 (계승)

prototype = *기능 데모*이지 hosted 제품·매출 아님. 공개 배포·고객·가격·GTM = 사람. 정직성 > 헤드라인.

## Task 목록
| # | slug | 상태 | 한 줄 |
|---|---|---|---|
| 2 | `leaderboard-site-polish` | ✅ done (→ `_archive/2026-Q2/monetization-surface/02-leaderboard-site-polish/`) | **사이트 폴리시 — 게임플레이·학습 시각화·CSS·한국어** — 게임플레이 GIF(scripted 에이전트가 held-out 세계 보스 격파, 128×128·42fr) + 일반화 격차 플롯(matplotlib) + 순수 CSS 애니메이션(그라데이션·페이드인·hover) + 한국어 버전(index.ko.html+토글). `build_assets`(score_baselines 1회·boss_defeated seed·lazy guard). 정직(양 언어): GIF=scripted·공개=사람. 브라우저 en/ko 확인. 4→8 테스트, 529→**535**, L3 2/2 APPROVE. |
| 1 | `leaderboard-site` | ✅ done (→ `_archive/2026-Q2/monetization-surface/01-leaderboard-site/`) | **정적 리더보드 웹사이트** — `scripts/build_site.py`: `render_site(leaderboard)` 순수 함수가 `leaderboard.py` 결과를 프레임워크-0 단일 HTML(랭크 표 + 킬러데모 GIF + moat 설명 + 정직 캡션, 전 값 html.escape)로. main() 무료 baseline 실측 → `site/index.html`+gif 복사. 브라우저 시각 확인. 정직 게이트: 빌드+프리뷰=자율/공개 배포=사람. 4 테스트, 525→**529**, L3 2/2 APPROVE. |
