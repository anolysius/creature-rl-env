# QA Checklist — readme-ko-parity (G1 freeze)

## Acceptance (plan AC 1-4)

- [ ] AC1 — README.ko.md가 영문 12섹션 전부 커버, 영문에 없는 수치 주장 0(특히 "GPU 수억 steps/s" 제거), 정직 캐비앗 전부 번역 유지.
- [ ] AC2 — README.md Release status stale 수정(공개 완료 반영, 남은 게이트 유지) + 양쪽에 라이브 사이트·how-it-works 링크(언어 대응).
- [ ] AC3 — 상대 링크 전부 유효(`ls` 확인) + 신규 외부 URL HTTP 200(`curl -sI`).
- [ ] AC4 — 코드/테스트 무변경 sanity(791 green 재확인), CHANGELOG 1줄.

## Default DoD

- [ ] L3 리뷰 APPROVED (docs-only여도 diff 검토 필수).
- [ ] CHANGELOG.md 1줄 append.
