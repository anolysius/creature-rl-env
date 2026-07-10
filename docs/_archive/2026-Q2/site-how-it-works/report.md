---
slug: site-how-it-works
initiative: null
status: completed
ended: 2026-07-10
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# 사이트 "시험지 작동 원리" 페이지 — 결과 보고서

## 요약

사용자가 GIF를 보며 던진 질문들(승리 조건·카운터 복잡도·왜 잡기가 전투력에 안 붙나·룰이 제각각
아니냐)이 곧 방문자의 질문 = face-validity 구멍. 사용자 선택 구조(랜딩+딥다이브 1페이지)로 수리.

| 항목 | 결과 |
|---|---|
| 테스트 | **785 → 791** (+6, 기존 무변경, 회귀 0), ruff clean, **src 무변경** |
| 신규 페이지 | `how-it-works(.ko).html` — 승리조건(상성 ×2/×1/×0.5=4× 스윙)·숨은 상성표·카운터 복잡도(탐색 작음/비용구조 표)·안티-grinding 룰 표·재는것/안재는것 |
| 랜딩 추가 | scope 박스+링크·범례 잡기 명확화·캡션 링크 — **기존 줄 변경 0(순수 추가만)** |
| 측정 주장 | **0** — 테스트가 DIAL-VISIBLE/0.68/0.47 부재를 assert(게재=사람 게이트) |
| 상수 code-sync | 배수가 `critter_gym.types` 상수에서 빌드 시점 유도 — drift 시 테스트가 잡음 |
| en/ko | 키 패리티(기존 테스트 자동 커버) + 상호 언어 토글 + back-링크 |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 딥페이지 콘텐츠+측정주장 0 | ✅ | 5개 섹션 전부, mechanics-not-claims 테스트 |
| AC2 랜딩 3추가+수치줄 hunk 0 | ✅ | 삭제/수정 줄 0(순수 추가), "숫자" 4건은 신규줄 `<h2>`·`margin-bottom:0` 무해 문자 |
| AC3 en/ko 패리티+토글 | ✅ | 키 패리티 테스트 + 토글/back-링크 테스트 |
| AC4 신규 테스트+무회귀 | ✅ | 6 테스트(렌더·클레임부재·**상수 code-sync**·상호링크·토글·랜딩 명확화), 791 green |
| AC5 재빌드+확인 | ✅ | 4 html, 사용자에게 en/ko 페이지 전달·확인 |

**L3 처리**: qa-verifier APPROVE. plan-reviewer는 도구 예산 소진으로 콘텐츠-코드 대조 미완 →
SUGGEST(머지 전 직접 대조 권고) 반환. **메인이 직접 대조 수행**: 상성 상수(types.py:23-24
2.0/0.5)·스타터 3마리/기술 1개(party 실행 확인)·승리조건(battle.py party_wiped/max_turns)·매치업
보장(region.py:116 strictly super-effect)·CATCH 무추가(critter_env.py:251-256)·레벨업 승리시만
(critter_env.py:314) — **전 항목 일치**. 추가 정밀화 1건: 매치업 보장 문장에 "(기본 시험지 기준 —
숨은 2차 타입 손잡이는 보장 약화 가능)" 한정어(en/ko) — #7의 secondary-unwinnable 경계 반영,
과대 서술 방지.

## 변경 파일 상세

- `scripts/build_site.py` (+~350): `_COPY` hiw_*/scope_*/lg_catch_note 키(en/ko) +
  `render_how_page()`(자체 컴팩트 CSS — 랜딩 CSS 바이트 불변 의도로 중복 채택, docstring 명시) +
  랜딩 3 삽입 + main 4-html.
- `tests/test_build_site.py` (+61): 6 테스트.
- `site/`: index(.ko) 재빌드(순수 추가) + how-it-works(.ko) 신규. 머지 시 GitHub Pages 자동 서빙.

## 흡수처 매핑

**흡수 없음** — 사이트 카피(설명 텍스트)는 evergreen 문서가 아닌 산출물. 콘텐츠의 근거는 전부
코드/기존 archive에 있음.

## 타입 체크 / 빌드 결과

- `pytest`: 791 passed, 0 regression. `ruff`: clean. mypy: 대상 무변경(src 무변경).
