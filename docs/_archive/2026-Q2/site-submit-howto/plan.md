---
slug: site-submit-howto
initiative: null
status: active
started: 2026-07-08
acceptance_freeze: true
task_type: general
mode: standard
domains: [render]
scope_paths:
  - scripts/build_site.py
  - tests/test_build_site.py
  - site/index.html
  - site/index.ko.html
extracted_to: []
supersedes: []
---

# site-submit-howto — 커뮤니티 섹션에 "리더보드 올리는 법" 단계별 + 가이드 링크

> 작성일: 2026-07-08 | 공개 사이트 폴리시 (제출 진입장벽 낮추기)

## 목표

사이트 커뮤니티 섹션에 개념 설명은 있으나 (a) 제출 상세 가이드로 가는 **클릭 링크가
없고** (b) "정확히 어떻게 올리나"의 **단계별 설명이 사이트에 없다**. 방문자가 사이트만
보고 제출 흐름을 이해하도록:

1. **단계별 "How to submit"** — 가이드(`docs/how-to/submit-your-model.md`)의 5분 흐름을
   4스텝으로 압축해 사이트에 직접 렌더 (시험지 받기 → 모델 실행 → JSON 작성·로컬 검증 →
   PR). 초심자용, 각 스텝 한 줄 + 핵심 명령.
2. **가이드/제출 링크** — 사이트에서 GitHub 의 상세 가이드(en/ko)와
   `community/submissions/` 폴더로 가는 클릭 링크.
3. **en/ko 동시** — 키 패리티 유지(테스트 강제), ko 는 ko 가이드로 링크.

디자인은 site-redesign 의 토큰/컴포넌트 재사용(카드·번호 스텝). 수치·정직 라벨 무변경.

## 작업 범위

| 파일 | 변경 | 영향 |
|---|---|---|
| `scripts/build_site.py` | `_COPY` en/ko 에 howto 스텝·가이드 링크 키 추가 + 커뮤니티 섹션에 스텝 블록·링크 렌더 | 순수 렌더 함수, 값 무변경 |
| `tests/test_build_site.py` | howto 스텝·가이드 링크 존재(en/ko) + 키 패리티(기존 테스트가 커버) | +테스트 |
| `site/index.html`·`index.ko.html` | 재빌드 산출물 | 결정론 유지 |

## Step별 계획

1. **Red**: test — 커뮤니티 섹션에 (a) 스텝 4개 마커 (b) submit-your-model 가이드 링크
   (en→.md / ko→.ko.md) (c) community/submissions 링크, en/ko 양쪽.
2. **Green**: build_site.py copy 키 + `_community_html`(또는 섹션)에 스텝·링크 렌더.
3. **재빌드 + 시각 검증**: 브라우저로 en/ko 커뮤니티 섹션 확인 (링크 클릭 가능·스텝 가독).
4. 문서/CHANGELOG (task-end).

커밋 단위: 단일 커밋 (단독 PR — 사이트라 CI+pages 자동 검증).

## 검증 방법

- `.venv/bin/python -m pytest tests/test_build_site.py -q` + 전체 회귀 0
- `ruff check .`
- 링크 URL 유효성 (GitHub blob 경로 형식) + 브라우저 실측

## 리스크

| 리스크 | 대응 |
|---|---|
| 가이드 링크가 깨진 경로 | GitHub `blob/main/docs/how-to/...` 정확 경로 + 브라우저 클릭 확인 |
| en/ko 스텝 누락 불일치 | 키 패리티 테스트(기존)가 CI 강제 |
| 결정론 깨짐 | 타임스탬프·랜덤 없음 유지 |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (단계별 설명)**: 커뮤니티 섹션에 4스텝 "how to submit" 이 en/ko 양쪽 렌더 —
  시험지 받기·모델 실행·JSON+검증·PR. **테스트**: `render_site` 출력에 4개 스텝 마커
  (예: `<ol class="steps">` 내 `<li>` 4개) + 핵심 토큰(`season_seeds`/`--validate`/`PR`)
  존재를 en·ko 각각 assert.
- **AC2 (가이드 링크)**: 사이트에서 상세 가이드로 가는 클릭 링크. **테스트**: 렌더
  출력에 `href` 로 en→`.../blob/main/docs/how-to/submit-your-model.md`, ko→
  `submit-your-model.ko.md`, 그리고 `.../community/submissions` 문자열이 각 언어 페이지에
  존재를 assert (링크 라이브 200 은 브라우저 실측 AC4 에서).
- **AC3 (en/ko 패리티·무회귀)**: `_COPY` en/ko 키 동일(기존 패리티 테스트 통과), 전체
  테스트 회귀 0(baseline 706), ruff clean, 재빌드 결정론, html.escape 유지.
- **AC4 (시각 검증)**: 브라우저로 en·ko 커뮤니티 섹션 실측 — 스텝 가독·링크 클릭 동작
  (GitHub 가이드 200). 결과를 report.md 에 1줄 기록.
