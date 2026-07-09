# QA Checklist — demo-gif-purposeful (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-5)

- [ ] AC1 — `baselines.demo_policy` 신규: 우선순위(battle 공격 > 내칸 CATCH > 살아있는 체육관 최단 step > 생물 추적 > sweep) 계약이 테스트로 고정. `greedy_policy`·`random_policy` byte-identical(git diff 함수 본문 hunk 0 직접 확인).
- [ ] AC2 — 기존 스위트 무회귀(763 green, 기존 test_baselines 무변경), ruff/mypy clean.
- [ ] AC3 — `build_site.py`가 GIF 생성에만 demo_policy 사용 — `_free_policies`(랭킹·차트 수치 경로) 무변경, 재빌드 html의 수치 포함 줄 변경 hunk 0(캡션 문구만 diff).
- [ ] AC4 — 재생성 `site/gameplay.gif`에서 체육관 가시 시 최단경로 접근 확인(프레임 검사), boss_defeated 클리어 seed 우선 선택 유지.
- [ ] AC5 — en/ko 캡션에 데모 정책 명시 구절(랭킹 행 오인 방지), en/ko 패리티 유지.

## Default DoD

- [ ] 전체 테스트 green, 회귀 0.
- [ ] `ruff check .` / `mypy src` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
