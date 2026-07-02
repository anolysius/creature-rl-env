---
slug: community-leaderboard
initiative: monetization-surface
status: completed
ended: 2026-07-02
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# 커뮤니티 리더보드 — 시즌제 공개 시험지 + 자가-신고 경쟁 — 결과 보고서

## 요약

| 항목 | 값 |
|---|---|
| 추진 EC | **M5-EC3**(공개 리더보드 운영)의 기술 artifact — 사용자 지시 기능 |
| 신규 | `community.py` + 테스트 16 + `community_submit.py` + 예시 제출(실측) + 가이드 en/ko |
| 수정 | `build_site.py`(Community 섹션) + site 재생성 |
| 테스트 | 630 → **650** (+20, 회귀 0) |
| lint/type | ruff clean · mypy Success |
| L3 | **2/2 APPROVE** (가드 산술·bool-오염 차단·정직 강제 코드 확인) |

## 계획 대비 실적

| AC | 결과 |
|---|---|
| AC1 시즌+스키마 | ✅ `season_seeds` 4성질(공개 영역·sealed 1.1M 분리·시즌 서로소·default 블록 분리 — `heldout_seeds(1000)` 경계 테스트) + 가드 4종. `validate_submission` 필수필드·타입(bool→int/float 오염 차단)·season·spec-일치·sanity·**`self_reported: true` 강제**. |
| AC2 랭킹 | ✅ 통과분만 (season, -score, model) 정렬, 불합격 (파일, 오류) 보고. |
| AC3 CLI+예시 | ✅ `--validate` exit 0/1(CI용), `--demo` 가 season 1 16 세계 **실측**(scripted baseline 0.750) → 합격 JSON 커밋. |
| AC4 사이트 섹션 | ✅ 시즌별 표·정직 라벨 3종(self-reported·sealed 퍼널·"open when announced") en/ko·빈-상태·전 값 escape·하위호환(default ()). 재빌드. **브라우저 탭 고착 → ko HTML 구조 검사로 대체 확인**(섹션·표·예시 0.750·라벨 — 정직 기록). |
| AC5 가이드 | ✅ `submit-your-model.md`+`.ko.md` — 5분 흐름·honor-system 규칙·시즌 개념·LLM 러너 참조·sealed 안내. |
| AC6 회귀+게이트 | ✅ 650 passed, ruff/mypy clean, CHANGELOG 1줄. **사람 게이트 미포함 명시**(접수 공지·Pages 공개·시즌 개시·Hub 등록). |

## 설계 결정 기록

- **시즌 유도 공개**: `1.0M + season×1000` — 비밀 없음, 누구나 시험지 재현. 절차생성=시즌 무한 재발급(고정 벤치마크 불가) → 재미+오염 완화가 같은 메커니즘.
- **정직성 구조화**: 스키마가 `self_reported: true`를 강제 — 공개 트랙은 "검증된 척"이 구조적으로 불가. 사이트 라벨 상시 + sealed 퍼널.
- **지표 비혼동**: 커뮤니티 지표=순수 gym-clears(시즌 블록). 메인 보드(return 기반·다른 seed)와 **직접 비교 불가**를 docstring·사이트 문구에 명시.

## 발견된 이슈

- **[기록] 브라우저 확인 부분 대체** — 크롬 탭이 로딩 고착(확장 이슈)돼 ko 페이지의 시각 스크린샷 대신 HTML 구조 검사로 확인. 이전 task(#8)에서 동일 페이지 시각 확인 완료 이력 + 렌더 테스트 8종 green 으로 보완.
- **[정직성 개선(구현 중)]** 초안 docstring 의 "메인 보드와 comparable by construction" 주장이 지표 차이(gym-clears vs return)로 부정확 → 비교 불가 명시로 정정.

## 사람 게이트 (열려면 park 님 결정)

1. 사이트 공개(GitHub Pages) 2. "제출 접수 개시" 공지(+ CI 에 `--validate` 연결) 3. 시즌 1 공식 개시 선언 4. Prime Intellect Hub 등록(M5-EC3 완결).
