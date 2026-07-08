---
slug: site-submit-howto
initiative: null
status: completed
ended: 2026-07-08
extracted_to: []
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# site-submit-howto — 결과 보고서

| 항목 | 값 |
|---|---|
| 단계별 설명 | 커뮤니티 섹션에 "How to get on the board / 리더보드에 올리는 법" **4스텝 카드**(번호 카운터 + 굵은 액션 + 코드 스니펫: `season_seeds(1,16)`·`community_submit.py --demo/--llm`·`--validate`·`community/submissions/`), en/ko 양쪽 |
| 링크 | "전체 단계별 가이드 →" pill(en→`submit-your-model.md`, ko→`.ko.md`) + "제출 폴더 보기 →"(`tree/main/community/submissions`) — **라이브 3개 전부 200 확인** |
| en/ko 싱크 | `_COPY` 신규 키 양쪽 추가, 패리티 테스트 통과 |
| 테스트 | 706 → **708**(+2: 스텝 4개·토큰·링크 href). ruff clean, 결정론 |
| 시각 검증 | 브라우저 실측 — 4 스텝 카드·코드 스니펫·pill/링크 동작, en·ko 정상, 가이드 링크 클릭 200 |
| L1 / L3 | 2/2 APPROVE(AC 구체화 SUGGEST 반영) / 2/2 APPROVE |

계획 대비 AC1–AC4 전부 ✅. 수치·정직 라벨 무변경. 후속: 머지 → pages 자동 배포.
