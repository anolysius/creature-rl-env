---
slug: leaderboard-site-polish
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

# 리더보드 사이트 폴리시 — 게임플레이 애니메이션·학습 시각화·CSS·한국어

> 작성일: 2026-07-01 | mode: standard | 마일스톤: M5 런치 자산 (#1 후속)

## 목표

#1 정적 리더보드 사이트를 **매력적으로** 확장한다:

1. **게임플레이 애니메이션** — scripted 에이전트가 *처음 보는 held-out 세계*에서 이동·체육관 진입·
   전투·보스 격파하는 큰 GIF(128×128, ~50 프레임)를 생성·임베드. "에이전트가 어떻게 움직이나" 시각화.
2. **일반화 시각화** — matplotlib 로 generalization-gap(held-in vs held-out) 플롯 PNG 임베드.
   "얼마나 일반화하나(암기 아님)" 시각화. (learning-curve 는 [rl] 학습 필요 → 범위 밖.)
3. **CSS 애니메이션** — 프레임워크 0 순수 CSS: 그라데이션 히어로, 로드 페이드인, 표 행 hover,
   데모 강조. 세련된 레이아웃.
4. **한국어 버전** — `site/index.ko.html` + 언어 토글(EN ↔ 한국어). README.ko 관례 계승.

**정직 게이트(계승)**: 빌드+로컬 프리뷰=자율. **공개 배포=사람 게이트**. GIF 는 *scripted* baseline
플레이(학습/LLM 아님) 로 정직 라벨. 자산 생성엔 `imageio`(GIF)·`matplotlib`(플롯) 필요 — [viz] extra;
없으면 커밋된 자산 재사용(빌드는 계속 동작).

## 선행 조건

- #1 `build_site.py`(`render_site`, main()) — main 안착(#92).
- `demo.record_episode`/`save_demo`(GIF, imageio lazy) + `baselines.greedy_policy`(scripted, obs-only).
- `viz.plot_generalization_gap`(matplotlib) + `scoreboard.score_baselines`(무료 baseline).
- `imageio`(설치됨)·`matplotlib`(있음). `docs/assets/killer_demo.gif`.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/build_site.py` | `render_site(leaderboard, *, generated_note, lang="en", assets=…)` 확장(CSS 애니메이션·i18n copy[en/ko]·언어 토글·게임플레이 GIF+plot `<img>`) + `build_assets()`(scripted held-out GIF + gap PNG 생성, lazy import guard) + main()이 en/ko 2 HTML + 자산 생성/복사 | **중** |
| `tests/test_build_site.py` | 기존 4 테스트 갱신(신규 시그니처) + i18n(ko copy·토글)·CSS·자산 참조 테스트 | 중 |
| `site/**` | `index.html`·`index.ko.html`·게임플레이 `demo.gif`·`gap.png` 생성물 | 저 |

### 영향 범위

- `render_site` 는 여전히 순수(입력→HTML). 자산 생성(`build_assets`)만 imageio/matplotlib lazy 사용.
- 채점·env·기존 스크립트 무변경. 무료 baseline 만.
- 결정론: GIF/plot 는 seed 고정(held-out seed·greedy 결정론·rng seed) → 재현. HTML 은 note 타임스탬프 없음.

## Step별 계획 (TDD)

1. **Red** — `tests/test_build_site.py`:
   - 갱신: `render_site(..., lang="en"/"ko")` 시그니처. en 페이지 영어 copy·ko 페이지 한국어 copy 포함.
   - 언어 토글 링크(index.html↔index.ko.html) 양쪽 존재.
   - CSS 애니메이션 존재(`@keyframes`/`animation:`), 게임플레이 GIF·gap plot `<img>` 참조.
   - 기존 불변: entry 내용·결정론·moat/정직 문구·html.escape.
2. **Green** — `build_site.py`:
   - i18n copy dict(en/ko) + `render_site(lang)` 분기 + 언어 토글 + CSS(@keyframes 페이드인·그라데이션·hover).
   - `build_assets(out)`: **`score_baselines` 1회 → ScoreTable** 확보(플롯·리더보드 공용) → `plot_generalization_gap(table)`→PNG. 게임플레이 GIF 는 held-out seed 후보를 순회하며 greedy `record_episode` → **`recording.boss_defeated` 인 첫 seed 채택**(그래야 "보스 격파" 클레임이 참); 후보 내 미격파면 **정직 라벨로 fallback**("navigates & battles"). lazy import(imageio/matplotlib); 실패 시 skip+경고(커밋 자산 유지).
   - main(): `--lang`(both 기본) → index.html + index.ko.html 작성, 자산 생성(가능 시)/복사.
3. **Refactor** — 템플릿/CSS 정리, docstring 에 정직 게이트·자산 의존([viz]) 명시.

## 검증 방법

- 신규/갱신 테스트 통과(i18n·CSS·자산참조·기존 불변).
- `python scripts/build_site.py` → index.html·index.ko.html·demo.gif·gap.png 생성, **브라우저 시각 확인**
  (애니메이션·게임플레이·플롯·언어 토글·한국어).
- 전체 pytest 회귀 0(529 유지 + 신규). ruff clean.
- 프레임워크/네트워크 의존 0(정적).

## 리스크

| 리스크 | 완화 |
|---|---|
| imageio/matplotlib 부재 환경서 자산 재생성 실패 | `build_assets` lazy import + try/except → skip+경고, 커밋된 자산 재사용(빌드·페이지 정상). 자산은 git 추적. |
| GIF 가 "학습된/LLM 에이전트"로 오인 | scripted baseline 플레이임을 페이지·캡션 정직 라벨. |
| 결정론 깨짐(자산 재생성마다 다름) | held-out seed·greedy 결정론·rng seed 고정 → byte-안정 목표(실패 시 자산은 커밋본 고정). |
| 한국어 번역 품질/누락 | copy dict 로 en↔ko 1:1, 핵심 문구(moat·정직 캡션) 양쪽 동등. reviewer 확인. |
| 공개 배포 과대 | 정직 게이트 문구 유지(양 언어). |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[hard]** `render_site(leaderboard, *, generated_note, lang)` 가 lang="en"/"ko" 로 각 언어 페이지를
   결정론 렌더: entry·moat·정직 캡션(양 언어) + 게임플레이 GIF·generalization plot `<img>` + 언어 토글
   (index.html↔index.ko.html) + `@keyframes` CSS 애니메이션. 값 html.escape. 신규/갱신 테스트.
2. **[assets]** `build_assets()` 가 **`score_baselines` 1회 ScoreTable** 로 generalization-gap PNG
   (matplotlib) + 리더보드를 만들고, held-out seed 를 순회해 **`boss_defeated=True` 인 scripted GIF**
   (record_episode/save_demo)를 생성(seed 고정=재현; 미격파면 정직 라벨 fallback). imageio/matplotlib
   lazy+guard(부재 시 skip, 커밋 자산 유지). main() 이 index.html+index.ko.html+자산을 `site/` 에 출력.
3. **[honesty]** 페이지(양 언어)+docstring: prototype·in-process·GIF=scripted baseline·수치 출처·
   **공개 배포=사람 게이트** 명시.
4. **[regression]** 전체 pytest 회귀 0(529 유지 + 신규). ruff clean. 기존 스크립트·채점 무변경.
