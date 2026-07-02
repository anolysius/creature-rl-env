# QA Checklist — community-leaderboard (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-6)

- [ ] AC1 — `community.py`: `season_seeds` 4성질(공개 영역 내·sealed(≥1.1M) 분리·시즌 서로소·default 블록 분리 — `heldout_seeds(1000)` 서로소 경계 테스트 포함) + 범위 가드 ValueError. `validate_submission`(필수필드·타입·season·spec-일치·점수 sanity, `self_reported: true` 강제) 오류 리스트 반환.
- [ ] AC2 — `load_submissions`: 검증 통과분만 heldout_mean 내림차순 랭킹, 불합격 skip(경로 보고).
- [ ] AC3 — `community_submit.py`: `--validate`(exit 0/1, CI용) + `--demo`(scripted baseline season 1 실측 → 합격 JSON). 예시 제출 1건 커밋 + `--validate` 합격.
- [ ] AC4 — 사이트 Community 섹션: 시즌별 표 + 정직 라벨(self-reported·honor-system·sealed 퍼널·"submissions open when announced") en/ko + 빈-상태 우아 + 전 값 escape. 재빌드+브라우저 확인.
- [ ] AC5 — `submit-your-model.md` + `.ko.md`: 5분 흐름·honor-system 규칙·시즌 개념·LLM 러너 참조.
- [ ] AC6 — 회귀 0(baseline 630, 기존 site 테스트 불변), ruff/mypy clean. CHANGELOG 1줄. 사람 게이트(접수 공지·Pages·시즌 개시·Hub) 미포함 명시.

## Default DoD

- [ ] 전체 테스트 green, 회귀 0. L3 APPROVED(≥2). CHANGELOG append.
