---
slug: site-tier-section
initiative: monetization-surface
status: completed
ended: 2026-07-02
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# 사이트 난이도-티어 섹션 — env_tier SSOT 연결 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 추진 EC | M5-EC2/EC3 연결 (판매-표면 ↔ 런치 자산) |
| 수정 | `build_site.py`(+섹션·_COPY·CSS 2줄) + `test_build_site.py`(+4) + site 2 html 재생성(+36줄 순수 추가) |
| 테스트 | 626 → **630** (+4, 회귀 0 — 기존 site 12 불변) |
| lint | ruff All checks passed |
| L3 리뷰 | **2/2 APPROVE** (plan-reviewer SUGGEST→"프로토타입 buyer flow" 한정어 반영) |
| 시각 확인 | 브라우저 en(get_page_text)+ko(스크린샷) — 티어 표·SSOT 원문·정직 캡션 렌더 확인 |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 결과 | 근거 |
|---|---|---|
| AC1 고정-리스트 SSOT 렌더 | ✅ | `_SITE_TIERS=("standard","hard")` 고정 튜플만 `get_tier()` 렌더(전역 순회 금지), 전 값 html.escape, 하드코딩 0. |
| AC2 SSOT-일치+누출-방지 | ✅ | 렌더 note ≡ `get_tier(...).difficulty_note`(env_tier 에서 읽어 비교); `register_tier("site_leak_probe")` 실제 등록 후 렌더 → 미포함 실증. |
| AC3 양 언어 | ✅ | ko 라벨("난이도 티어" 등)+동일 note 원문, 토글·기존 섹션 불변. |
| AC4 정직 캡션 | ✅ | 구매자 흐름 한 줄("**프로토타입** buyer flow — 시연 artifact, 운영 서비스 아님"; L3 SUGGEST 반영) + "custom=검증만·실판매/가격/hosting=사람" 양 언어. |
| AC5 재빌드 결정론 | ✅ | `--no-assets` 재생성, diff **+36줄 순수 추가**(기존 byte-identical), 2회 빌드 동일, 자산 무변경. |
| AC6 회귀 0+CHANGELOG | ✅ | 630 passed, ruff clean. CHANGELOG 1줄(본 task-end). |

## 변경 상세

- `build_site.py`: `_SITE_TIERS` 고정 리스트(주석에 이유 — 테스트가 전역 레지스트리에 custom 등록하므로 순회는 누출 경로) + `_tiers_html`(SSOT·escape) + `_COPY` en/ko `tiers_*` 7키 + 섹션 1개 + `.table-wrap`/`.note-cell` CSS.
- `test_build_site.py` +4: SSOT-일치 / 누출-방지 실증 / ko / 정직 캡션.
- `site/index.html`·`index.ko.html`: 재생성(티어 섹션만 추가).

## 발견된 이슈

- **[L1 BLOCK→해소] 누출 경로** — 초안의 "레지스트리 전체 순회"는 같은 pytest 프로세스에서 테스트가 등록한 custom 티어가 판매 페이지에 새어드는 실제 버그 경로였음. 고정 리스트+실증 테스트로 차단(L1 리뷰가 잡음 — 리뷰 가치 실증).
- **[L3 SUGGEST→반영] 정직성 한 겹** — buyer-flow 문장이 운영 서비스처럼 읽힘 → "프로토타입(시연 artifact, 운영 서비스 아님)" 한정어 인라인 추가(양 언어).
- **[SSOT 관찰]** hard 티어 note 의 "SOTA/recurrent OPEN"은 이 티어 config(grid16·3gym·300step) 기준으로 정확 — hard-benchmark #3/#5 의 recurrent 측정은 다른 config(grid16·5gym·420step). env_tier note 갱신 여부는 별도 판단(스코프 밖, 페이지는 코드 원문 렌더가 설계).

## 흡수처 매핑

evergreen 신규 추출 없음(섹션은 기존 사이트 자산; 티어 API 문서는 `docs/reference/env-tiers.md` 에 이미 존재). `extracted_to: []`.
