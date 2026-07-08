---
slug: site-redesign
initiative: null
status: active
started: 2026-07-08
acceptance_freeze: true
task_type: general
mode: standard
domains: [render, rl-env]
scope_paths:
  - scripts/build_site.py
  - src/critter_gym/render.py
  - tests/test_build_site.py
  - tests/test_render.py
  - site/index.html
  - site/index.ko.html
  - site/gameplay.gif
extracted_to: []
supersedes: []
---

# site-redesign — 공개 사이트 디자인 시스템 개편 + en/ko 싱크 + GIF 무한반복

> 작성일: 2026-07-08 | 상태: 계획 | 공개 직후 폴리시 (soft launch 기간)

## 목표

공개된 런치 사이트(`anolysius.github.io/creature-rl-env`)를 세 방향으로 개선:
1. **디자인 시스템 전면 개편** — 디자인 토큰(색·간격·타이포 스케일·radii·surface) 기반,
   라이트/다크 테마, 깔끔한 테이블·stat 타일, **인라인 SVG 차트**(matplotlib PNG 대체 →
   테마 반응·벡터·의존성 감소), 반응형, 은은한 모션. dataviz 스킬 방법론 적용
   (팔레트 validator 실행, 카테고리 고정 순서, 단일축, 텍스트=ink 토큰).
2. **en/ko 싱크** — 현재 키는 57=57로 동일하나 `<title>`이 영문 하드코딩이고, 재설계 시
   한쪽 누락 위험 → **패리티를 테스트로 강제** + title 언어별화 + 신규 카피 양쪽 반영.
3. **게임플레이 GIF 무한반복** — `render.save_gif`에 `loop=0` 추가 (현재 `loop` 미지정 →
   인코더 기본값 의존, 무한반복 미보장).

## 작업 범위

| 파일 | 변경 | 영향 |
|---|---|---|
| `scripts/build_site.py` | 디자인 토큰 CSS + 라이트/다크 + 컴포넌트 재스타일 + 인라인 SVG 차트 2종(band·gap) + title 언어별화 | 순수 렌더 함수 유지(테스트 가능) |
| `src/critter_gym/render.py` | `save_gif(..., loop=0)` — 기본값 0(무한), 기존 호출 무변경 | 제품 코드; 기본 동작 = 무한반복으로 개선 |
| `tests/test_build_site.py` | en/ko 키 패리티 테스트 + SVG 차트 존재·구조 + 다크토큰 존재 + escape 무회귀 | +테스트 |
| `tests/test_render.py` | `save_gif`가 loop=0 전달 검증 (imageio mock) | +테스트 |
| `site/index.html`·`index.ko.html`·`gameplay.gif` | 재빌드 산출물 | 결정론 유지 |

### 차트 설계 (dataviz 방법론)

- **band 차트** (super-effective-move rate: oracle/infer/type_blind/probe) — 카테고리별
  magnitude. 단일 측정(율)이라 **단일 accent 색 막대 + 직접 값 라벨**(범례 불요), 천장→바닥
  순서 보존. 4px 라운드 데이터엔드, baseline 앵커.
- **gap 차트** (baseline별 held-in vs held-out) — 2 시리즈 그룹 막대. **2색 카테고리
  팔레트**(validator 통과분) + 범례 present. 격차가 작을수록 두 막대 근접(핵심 메시지).
- 둘 다 **인라인 SVG**(테마 토큰 참조 → 라이트/다크 자동), matplotlib PNG(`band.png`·
  `gap.png`) 대체. 래스터 자산(gameplay.gif·world 썸네일)은 env 렌더라 유지, 컨테이너만 재스타일.
- 값 출처는 기존 `build_assets`의 실측(baseline 점수·inference_baseline) 그대로 — **하드코딩
  0**, 수치 SSOT 불변.

## Step별 계획

1. **Red**: test_build_site.py(en/ko 패리티·SVG 차트 마커·다크토큰·escape) + test_render.py(loop=0).
2. **Green(GIF)**: render.py `loop=0`.
3. **Green(디자인)**: build_site.py 토큰·테마·컴포넌트·인라인 SVG 차트·title 언어별화.
4. **재빌드**: `python scripts/build_site.py` → site/*.html + gameplay.gif 갱신.
5. **시각 검증**: 브라우저로 en/ko·라이트/다크 실제 렌더 확인 (label 충돌·오버플로·차트 기하).
6. 문서/CHANGELOG (task-end).

커밋 단위: 단일 커밋 (단독 PR — 공개 사이트라 PR CI+Pages 배포 자동 검증).

## 검증 방법

- `.venv/bin/python -m pytest -q` (전체, baseline 699 + 신규, 회귀 0)
- `mypy src` · `ruff check .`
- 팔레트 validator (dataviz `scripts/validate_palette.js`) — 차트 색 CVD/대비 통과
- 브라우저 실측 (en·ko × 라이트·다크)

## 리스크

| 리스크 | 대응 |
|---|---|
| matplotlib PNG 제거가 기존 build_assets/테스트 깨뜨림 | 인라인 SVG로 대체하되 `_build_band_png`/gap 경로는 안전 제거·테스트 동반 수정; world 썸네일은 유지 |
| 인라인 SVG에 값 하드코딩(수치 SSOT 위반) | 값은 build_assets 실측을 SVG 좌표로 변환만; "band.png 미참조" + 수치 출처 테스트 |
| en/ko 재설계 중 한쪽 누락 | 키 패리티 테스트가 CI에서 강제 (신규 카피는 양쪽 필수) |
| 다크테마 색이 CVD/대비 실패 | validator를 라이트·다크 각 surface로 실행, 통과분만 채택 |
| 결정론 깨짐(재빌드마다 diff) | 타임스탬프·랜덤 없음 유지; gap/band는 실측 고정 seed |
| CI Pages 배포 실패 / 크로스브라우저 | PR CI(build_site 테스트)로 산출 검증 후 머지; 인라인 SVG·CSS는 표준 기능만(외부 폰트/JS 없음); 머지 후 pages 워크플로 실측 확인 |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (디자인 시스템)**: build_site 출력에 디자인 토큰(CSS custom properties: 색·간격·타이포)
  + **라이트/다크 테마 양쪽**(`prefers-color-scheme` + 토큰) + 컴포넌트(카드·테이블·stat 타일)
  일관 스타일. 테스트로 토큰/다크 블록 존재 확인 + 브라우저 시각 검증.
- **AC2 (인라인 SVG 차트)**: band·gap 차트가 **인라인 SVG**(matplotlib PNG 미참조 —
  `band.png`/`gap.png` `<img>` 0건)로 렌더, 값은 build_assets 실측 유래(하드코딩 0),
  텍스트=ink 토큰·카테고리 고정순서·단일축·팔레트 validator 통과.
- **AC3 (en/ko 싱크)**: `_COPY` en/ko 키 집합 **동일**(테스트 강제) + `<title>` 언어별
  렌더 + 신규 카피 양쪽 존재. ko 페이지 정보량 = en 페이지.
- **AC4 (GIF 무한반복)**: `save_gif` 기본 `loop=0`(무한) — imageio mock 테스트로 `loop=0`
  전달 검증 + 재빌드된 `gameplay.gif`가 무한반복(GIF NETSCAPE loop). 기존 호출 무변경.
- **AC5 (무회귀·결정론)**: 전체 테스트 green(699+신규, 회귀 0), `mypy`/`ruff` clean,
  재빌드 결정론(타임스탬프·랜덤 없음), 전 값 `html.escape` 유지.
- **AC6 (시각 검증)**: en·ko × 라이트·다크 4조합 브라우저 실측 — label 충돌·오버플로 0,
  차트 정상, GIF 무한반복 육안 확인. report에 기록.
