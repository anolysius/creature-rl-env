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
| 7 | `sealed-difficulty-levers` | ✅ done (→ `_archive/2026-Q2/monetization-surface/07-sealed-difficulty-levers/`) | **정직성 갭 수리 (M5-EC1/EC2 경화)** — #5 가 남긴 부채: `SealedEvalSet` 이 patch_radius/num_gyms 를 못 담아 sealed 가 티어에 덜 충실. 3 코어 수정: `eval_harness`(SealedEvalSet +두 레버 param+factory, 기본값=CritterEnv 기본→byte-identical), `eval_package`(seed_commitment 바인딩 + EvalManifest 공개 노출), `env_tier`(_SEALED_DROPPED=num_creatures만). 정직: 내장 hard(값=기본)는 이미 충실—효과는 custom 티어; 과대표현 금지. 3 reference 갱신. 6 테스트, 592→**598**, L3 2/2 APPROVE. |
| 6 | `tier-eval-bundle` | ✅ done (→ `_archive/2026-Q2/monetization-surface/06-tier-eval-bundle/`) | **판매-표면 통합 캡스톤 (M5-EC1+EC2)** — `src/critter_gym/eval_marketplace.py`(신규·조합-전용): #4(서명 인증서)+#5(난이도 티어)를 buyer 흐름으로 — `TierOffer`+`build_tier_offer`/`publish_catalog`, `SellerListing`(단일 진실원), `issue_tier_certificate`(오염 위임)+`verify_offer_certificate`(커밋먼트 바인딩), `bundle_honesty`(두 층 note). 계약: 바인딩=resolved knob+seed(티어 label 아님)→seed confound 격리 검증. 정직 두 층 유실 0. 데모 `scripts/tier_eval_bundle_demo.py`. 14 테스트, 578→**592**, L3 2/2 APPROVE. evergreen `docs/reference/tier-eval-bundle.md`. |
| 5 | `custom-env-api` | ✅ done (→ `_archive/2026-Q2/monetization-surface/05-custom-env-api/`) | **커스텀/고난도 env 티어 API (M5-EC2)** — `src/critter_gym/env_tier.py`(신규·additive): `TierSpec`(직렬화+difficulty note) + `validate_tier_spec`(가드) + curated `standard`/`hard` 프리셋 레지스트리 + `make_tier_env`/`tier_env_factory`(override 재검증) + sealed tie-in `sealed_config`/`build_sealed`(SealedEvalSet 지원 서브셋; num_gyms/patch_radius/num_creatures 드롭·문서화). 정직: hard=실측(PPO ~11–16% of oracle) + "SOTA/recurrent=OPEN" 명시. eval_package 미import. 데모 `scripts/list_env_tiers.py`. 22 테스트, 539→**561**, L3 2/2 APPROVE(build_sealed 가드-우회 BLOCK→수정→APPROVE). evergreen `docs/reference/env-tiers.md`. |
| 4 | `private-evalset-package` | ✅ done (→ `_archive/2026-Q2/monetization-surface/04-private-evalset-package/`) | **비공개 held-out eval 판매 패키지 (M5-EC1)** — `src/critter_gym/eval_package.py`(신규·additive): HMAC-SHA256 서명 코어(canonical SSOT) + `seed_commitment`(rug-pull 가드·no-leak) + 서명된 `EvalManifest`(비밀 미노출·buyer 자가점검) + 서명된 `SignedCertificate`(오염 제출 `ok=False` 미채점·부정도 서명유효·매니페스트 커밋먼트 바인딩). L1 SUGGEST 반영=매니페스트도 서명. E2E 데모 `scripts/package_sealed_eval.py`. 정직 3중 명시(HMAC=prototype·실제=비대칭/서버측=사람). stdlib-only 의존성 0. 17 테스트, 539→**556**, ruff/mypy clean, L3 2/2 APPROVE. evergreen `docs/reference/sealed-eval-packaging.md`. |
| 3 | `site-research-visuals` | ✅ done (→ `_archive/2026-Q2/monetization-surface/03-site-research-visuals/`) | **연구-설명 시각화 — 격자 범례·SE-rate band·held-out 썸네일** — 게임플레이 GIF만으론 연구가 안 보여 3가지 추가(양 언어): 격자 색 범례(render.py 팔레트 SSOT), SE-rate 추론 band 차트(oracle 100%/infer 90%/type_blind 27%/probe 0%; 유료 LLM 수치는 차트에 하드코딩 0=캡션만), held-out 세계 썸네일 3장. lazy+guard. 브라우저 en 확인. 4 테스트, 535→**539**, L3 2/2 APPROVE. #2와 동일 브랜치/PR. |
| 2 | `leaderboard-site-polish` | ✅ done (→ `_archive/2026-Q2/monetization-surface/02-leaderboard-site-polish/`) | **사이트 폴리시 — 게임플레이·학습 시각화·CSS·한국어** — 게임플레이 GIF(scripted 에이전트가 held-out 세계 보스 격파, 128×128·42fr) + 일반화 격차 플롯(matplotlib) + 순수 CSS 애니메이션(그라데이션·페이드인·hover) + 한국어 버전(index.ko.html+토글). `build_assets`(score_baselines 1회·boss_defeated seed·lazy guard). 정직(양 언어): GIF=scripted·공개=사람. 브라우저 en/ko 확인. 4→8 테스트, 529→**535**, L3 2/2 APPROVE. |
| 1 | `leaderboard-site` | ✅ done (→ `_archive/2026-Q2/monetization-surface/01-leaderboard-site/`) | **정적 리더보드 웹사이트** — `scripts/build_site.py`: `render_site(leaderboard)` 순수 함수가 `leaderboard.py` 결과를 프레임워크-0 단일 HTML(랭크 표 + 킬러데모 GIF + moat 설명 + 정직 캡션, 전 값 html.escape)로. main() 무료 baseline 실측 → `site/index.html`+gif 복사. 브라우저 시각 확인. 정직 게이트: 빌드+프리뷰=자율/공개 배포=사람. 4 테스트, 525→**529**, L3 2/2 APPROVE. |
