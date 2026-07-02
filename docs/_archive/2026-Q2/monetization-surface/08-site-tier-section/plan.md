---
slug: site-tier-section
initiative: monetization-surface
status: active
started: 2026-07-02
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - scripts/build_site.py
  - tests/test_build_site.py
  - site/index.html
  - site/index.ko.html
extracted_to: []
supersedes: []
mode: standard
task_type: general
---

# 사이트 난이도-티어 섹션 — env_tier SSOT 연결 (monetization-surface #8)

> 작성일: 2026-07-02 | 상태: 계획 | 추진 EC: **M5-EC2/EC3 연결** — 판매-표면(티어 API·마켓플레이스)과
> 런치 자산(리더보드 사이트)을 잇는다.

## 목표

리더보드 사이트에 **"Difficulty tiers" 섹션**을 추가한다 — #5(env_tier)의 curated 티어 레지스트리를
**SSOT 로 직접 렌더**(사이트에 수치 하드코딩 0, #3 의 render.py 팔레트 SSOT 패턴과 동일 규율):
티어별 knob(grid/steps/view/gyms)·`harder_knobs`·`difficulty_note`(측정 사실+open 명시가 코드에
이미 담김)를 표로 보여주고, 구매자 흐름(티어 선택→sealed 매니페스트→서명 인증서) 한 줄 소개 +
**정직 캡션**(prototype·실판매/hosting=사람 게이트)을 단다. 양 언어(en/ko).

현재 빈틈: 사이트는 grid10 리더보드·band 만 보여주고, 이번 세션에 만든 **판매-표면(티어·마켓플레이스)
이 사이트에 전혀 안 보인다**. 구매자가 "무엇을 파는지"를 사이트에서 못 본다.

**정직성(이니셔티브 불변식)**: 난이도 서술은 `difficulty_note` SSOT 그대로(측정 한정+"SOTA/recurrent
OPEN" 포함 — 사이트가 코드보다 세게 주장 불가). 빌드+로컬 프리뷰=자율, **공개 배포=사람**. 수치
하드코딩 0.

## 선행 조건

- `env_tier.tier_names()`/`get_tier()` — TierSpec(name/knobs/harder_knobs/difficulty_note). main 존재.
- `build_site.py` — `render_site(lang)`/`_COPY` en·ko dict/섹션 골격/`html.escape` 규율(#1–#3).
- 커밋 자산 재사용: `--no-assets` 재빌드(gif/png 재생성 불필요 — 이번 변경은 HTML 만).
- 기존 12 site 테스트(baseline 626 중) 회귀 0 유지.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 종류 | 영향도 | 변경 요지 |
|---|---|---|---|
| `scripts/build_site.py` | 수정 | 낮음 | `_tiers_html()` 헬퍼 + tiers 섹션 + `_COPY` en/ko 키 추가. 기존 섹션 불변 |
| `tests/test_build_site.py` | 수정(추가만) | 낮음 | SSOT-일치·escape·ko·비하드코딩 테스트 |
| `site/index.html`·`index.ko.html` | 재생성 | 낮음 | `--no-assets` 재빌드 산출물 |

### 영향 범위

- `build_site.py` 가 `critter_gym.env_tier` 를 신규 import(SSOT). 렌더 순수성·결정론 유지(타임스탬프 0).
- 기존 섹션/자산/채점 무변경.

## Step별 계획

**Step 1 (Red→Green): tiers 섹션 렌더**
- `_tiers_html(c)` — **고정 리스트 `("standard", "hard")` 만** `get_tier()` 로 렌더(L1 BLOCK 반영:
  `tier_names()` 전역 순회 금지 — `test_env_tier.py` 가 같은 pytest 프로세스에서 custom 티어를
  전역 `_TIERS` 에 등록하므로 레지스트리 순회는 누출 경로). 티어별 행: name / grid·steps·
  view(=2·patch_radius+1)·gyms / harder_knobs(또는 baseline 라벨) / `difficulty_note`
  (**html.escape, SSOT 그대로**).
- `_COPY` en/ko 에 `tiers_h`/`tiers_p`(구매자 흐름 한 줄: 티어 선택→sealed 매니페스트→서명
  오염-불가 인증서)/`tiers_honest`(prototype·custom 티어 가능·실판매/hosting=사람 게이트) 추가.
  difficulty_note 는 코드 SSOT 영어 원문 그대로(팔레트 SSOT 패턴) — ko 페이지엔 라벨만 한국어.
- `render_site` 에 섹션 1개 추가(기존 섹션 뒤, 결정론·escape 유지).
- 테스트: (i) 렌더가 `get_tier(name).difficulty_note` 와 **문자열 일치**(SSOT — note 를 테스트에
  하드코딩하지 않고 env_tier 에서 읽어 비교) (ii) 내장 2종 이름 포함 (iii) **누출 방지**: 테스트가
  custom 티어를 `register_tier` 로 실제 등록한 **후** 렌더해도 그 티어가 산출물에 없음(L1 SUGGEST
  반영 — 고정-리스트 완화의 실증) (iv) ko 페이지 라벨 한국어+note 동일 (v) 정직 캡션(사람 게이트)
  존재 (vi) 기존 12 테스트 불변.

**Step 2: 재빌드 + 로컬 확인**
- `python scripts/build_site.py --no-assets` → `site/index.html`·`index.ko.html` 재생성(자산 재사용).
- 브라우저 시각 확인 시도(#1–#3 관례). 불가 시 정직히 report 에 명시하고 HTML 구조 검사로 대체.

## 검증 방법

- `.venv/bin/python -m pytest tests/test_build_site.py -q` — 기존 12 + 신규 all green.
- 전체 스위트 회귀 0(baseline 626). `ruff check`.
- `--no-assets` 재빌드 무오류 + 산출 HTML 에 tiers 섹션.

## 리스크

| 리스크 | 완화 |
|---|---|
| 사이트가 코드보다 센 난이도 주장(하드코딩) | note 를 SSOT 그대로 렌더 + SSOT-일치 테스트(하드코딩 회귀 방지). |
| 등록 티어 오염(테스트가 custom 티어 등록 시 사이트에 새어듦) | `_tiers_html` 은 **내장 2종("standard","hard")만** 명시 렌더(레지스트리 전체가 아니라 — 테스트 중 등록된 custom 티어가 산출물에 새는 것 방지). |
| 기존 사이트 회귀 | 섹션 1개 추가만, 기존 12 테스트 불변 확인. |
| 공개 배포 오해 | 정직 캡션 + 빌드/프리뷰=자율·배포=사람 유지(#1 관례). |

## Acceptance Criteria (G1 통과 시 freeze)

1. `render_site` 에 "Difficulty tiers" 섹션 — 내장 `standard`/`hard` 를 `env_tier` **SSOT 로 렌더**
   (name/knobs/harder_knobs/difficulty_note, 전 값 html.escape, 수치·주장 하드코딩 0).
2. **SSOT-일치 테스트**: 렌더된 note ≡ `get_tier(...).difficulty_note`(env_tier 에서 읽어 비교),
   내장 티어명 포함. **누출-방지 실증 테스트**: custom 티어를 실제 `register_tier` 등록 후 렌더해도
   미포함(고정-리스트 `("standard","hard")` 렌더가 보장 — 레지스트리 전역 순회 금지).
3. 양 언어: ko 페이지 라벨 한국어 + 동일 note, 언어 토글·기존 섹션 불변.
4. **정직 캡션**: 구매자 흐름 한 줄 + "prototype·실판매/hosting=사람 게이트" 양 언어.
5. `--no-assets` 재빌드로 `site/index.html`·`index.ko.html` 갱신(자산 무변경), 결정론 유지.
6. 회귀 0(전체 스위트, baseline 626 — 기존 site 12 테스트 불변), ruff clean. CHANGELOG 1줄.
