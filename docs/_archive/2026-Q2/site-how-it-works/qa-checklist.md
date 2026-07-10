# QA Checklist — site-how-it-works (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-5)

- [ ] AC1 — `site/how-it-works(.ko).html` 신규: 승리 조건(상성 4배 스윙)·숨은 상성표(암기 불가)·카운터 복잡도(탐색 작음/비용 구조)·안티-grinding 룰 표·"재는 것/안 재는 것" 포함. **측정 주장 0**(엔진 상수만 인용 — LLM 곡선 등 게재는 사람 게이트로 배제).
- [ ] AC2 — 랜딩 추가분 3개(재는것/안재는것 박스+링크·범례 잡기 명확화 1줄·데모 캡션 링크), 기존 **수치 포함 줄 변경 hunk 0**.
- [ ] AC3 — en/ko 패리티(신규 copy 키 집합 동일) + 딥페이지 상호 언어 토글.
- [ ] AC4 — 신규 테스트가 렌더·패리티·상호 링크·정직 문자열·수치 불변·**엔진 상수 code-sync**(SUPER_EFFECTIVE/NOT_VERY_EFFECTIVE 실값 대조)를 커버, 기존 테스트 무변경. 785 무회귀, ruff clean.
- [ ] AC5 — 재빌드 완료(4 html), HTML 구조/브라우저 검사로 en/ko 딥페이지 확인.

## Default DoD

- [ ] 전체 테스트 green, 회귀 0. `ruff check .` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
