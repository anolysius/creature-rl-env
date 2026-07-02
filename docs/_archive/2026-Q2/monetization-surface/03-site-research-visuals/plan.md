---
slug: site-research-visuals
initiative: monetization-surface
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
scope_paths:
  - scripts/build_site.py
  - tests/test_build_site.py
  - site/**
extracted_to: []
supersedes: []
---

# 사이트 연구-설명 시각화 — 격자 legend · SE-rate 추론 band · held-out 썸네일

> 작성일: 2026-07-01 | mode: standard | 마일스톤: M5 런치 자산 (#2 후속, 같은 브랜치)

## 목표

현재 사이트엔 게임플레이 GIF 한 장뿐이라 **정작 연구하는 것(맥락 내 숨은-규칙 추론·오염불가
held-out·추론 변별)이 시각적으로 안 보이고**, 격자 색의 의미도 설명이 없다. 3가지 추가(양 언어):

1. **격자 색 legend** — `render.py` 실 팔레트(agent/creature/gym-active/gym-defeated/empty) 를 색
   스와치 + 라벨로. 게임플레이 GIF 옆에 배치. (새 자산 불필요 — CSS 색상 박스.)
2. **SE-rate 추론 band 차트** — `inference_baseline`(demonstrator sealed) 의 arm 별 super-effective-
   move rate(oracle/infer/type_blind/probe)를 막대 차트(matplotlib)→`site/band.png`. 우리 moat 핵심
   (추론 변별)을 한 장으로. **정직**: scripted band 만(무료·재현); 프런티어 LLM read(~14%)는 별도
   유료 probe 라 차트에 하드코딩 안 함(캡션 텍스트로만 언급).
3. **held-out 세계 썸네일** — 서로 다른 held-out 시드 3개의 reset 프레임(`env.render`)→
   `site/world_1..3.png`. "매번 처음 보는 서로 다른 세계 = 못 외운다" 시각화.

**정직 게이트(계승)**: 빌드+로컬 프리뷰=자율, 공개 배포=사람. band=scripted proxy·config 명시.
자산 생성엔 imageio/matplotlib(lazy+guard; 부재 시 skip·커밋 자산 유지).

## 선행 조건

- #2 `build_site.py`(render_site lang/demo_cleared, build_assets) — 같은 브랜치(feature/leaderboard-
  site-polish) 커밋됨.
- `render.py`(팔레트 상수 `_AGENT`/`_CREATURE`/`_GYM_ACTIVE`/`_GYM_DEFEATED`/bg; `draw_frame`).
- `eval_harness.inference_baseline`(SE-rate arms) + `SealedEvalSet`(demonstrator config).
- `env.render()`(rgb_array) reset 프레임.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/build_site.py` | render_site 에 legend 섹션(색 스와치, render.py 팔레트, en/ko) + band 차트 `<img>` + 썸네일 `<img>` 3장; build_assets 에 band.png(inference_baseline+matplotlib) + world_1..3.png(held-out reset 프레임) 생성(lazy guard); `_COPY` en/ko 추가 문구 | **중** |
| `tests/test_build_site.py` | legend(색/라벨)·band.png·world 썸네일 참조 + en/ko 문구 테스트(기존 8 유지) | 중 |
| `site/**` | band.png · world_1..3.png 신규, index.html/index.ko.html 갱신 | 저 |

### 영향 범위

- render_site 순수 유지. 자산 생성만 imageio/matplotlib lazy. 채점·env·기존 스크립트 무변경.
- 무료 baseline + scripted arm 만. LLM 유료 수치 하드코딩 0.

## Step별 계획 (TDD)

1. **Red** — `tests/test_build_site.py`:
   - legend: 페이지에 5개 색 라벨(en: agent/creature/gym/cleared/empty, ko: 에이전트/생물/체육관/…)
     + render.py 팔레트 RGB(예 `rgb(80,140,230)`) 포함.
   - band.png·world_1.png..world_3.png `<img>` 참조(en+ko).
   - 기존 8 테스트 불변(entry·결정론·moat·escape·korean·토글·CSS·demo 캡션).
2. **Green** — `build_site.py`:
   - render.py 팔레트 import → legend 스와치(inline style `background: rgb(r,g,b)`) + en/ko 라벨.
   - band 차트: `inference_baseline(demonstrator sealed)` → arm se_rate 막대(matplotlib)→band.png.
   - 썸네일: 서로 다른 held-out 시드 3개 `CritterEnv(render_mode=rgb_array).reset(seed)` → `env.render()`
     프레임 → imageio.imwrite world_N.png. lazy guard.
   - render_site: legend·band·썸네일 섹션 추가(en/ko copy). main() 변화 없음(build_assets 확장).
3. **Refactor** — 팔레트 SSOT(render.py) 재사용 확인, docstring 정직 문구.

## 검증 방법

- 신규/기존 테스트 통과.
- `python scripts/build_site.py` → band.png·world_1..3.png 생성 + **브라우저 시각 확인**(legend 색 정합·
  band 차트·썸네일·en/ko).
- 전체 pytest 회귀 0(535 유지 + 신규). ruff clean.

## 리스크

| 리스크 | 완화 |
|---|---|
| legend 색이 실제 렌더와 불일치 | `render.py` 팔레트 상수를 **직접 import**(하드코딩 금지) → SSOT. |
| band 차트에 LLM 유료 수치 하드코딩(비재현·과대) | scripted band(oracle/infer/type_blind/probe)만 플롯; LLM read 는 캡션 텍스트로만(별도 유료 probe 명시). |
| imageio/matplotlib 부재 | lazy+guard(skip·커밋 자산 유지, 빌드 계속). |
| 썸네일이 held-out 진짜 다른 세계인가 | 서로 다른 held-out 시드 사용(TEST_SEED_OFFSET+), 시드 페이지에 표기. |
| config 혼동(band=demonstrator vs 리더보드=default) | band 캡션에 config·"inference-gated demonstrator" 명시. |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[hard]** render_site(en/ko) 가 (a) 격자 색 **legend**(`render.py` 팔레트 RGB + en/ko 라벨 5종)
   (b) SE-rate band 차트 `<img src=band.png>` (c) held-out 썸네일 `<img src=world_1..3.png>` 를 포함.
   결정론·html.escape·기존 8 테스트 불변. 신규 테스트.
2. **[assets]** build_assets 가 `inference_baseline`(demonstrator)→band.png(scripted arm se_rate,
   matplotlib; LLM 하드코딩 0) + 서로 다른 held-out 시드 3개 reset 프레임→world_1..3.png(imageio) 생성.
   lazy+guard(부재 시 skip·커밋 자산 유지).
3. **[honesty]** band 캡션(양 언어): scripted proxy band·demonstrator config·프런티어 LLM read 는 별도
   유료 probe(하드코딩 아님) 명시. legend 는 render.py 팔레트 SSOT. 공개=사람 게이트 유지.
4. **[regression]** 전체 pytest 회귀 0(535 유지 + 신규). ruff clean. 기존 스크립트·채점 무변경.
