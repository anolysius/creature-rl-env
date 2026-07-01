# QA Checklist — leaderboard-site-polish (G1 freeze)

## Acceptance Criteria

- [x] **AC1 [hard]** ✅ `render_site(..., lang, demo_cleared)` en/ko 결정론 렌더. 8 테스트(entry·결정론[en+ko]·moat/정직·escape·korean[리더보드/프로토타입]·언어토글[index.ko.html↔index.html]·@keyframes CSS·demo 캡션 정직) PASS. **브라우저 시각 확인**(en+ko).
- [x] **AC2 [assets]** ✅ `build_assets()` `score_baselines` 1회 → gap.png(matplotlib, 567×435) + 리더보드; held-out seed 순회 `boss_defeated=True` gameplay.gif(128×128, 42프레임) 생성(seed 고정). lazy+guard(부재 시 skip). main() → index.html + index.ko.html + 자산 `site/`. 실빌드 성공("defeats the boss" 캡션=격파 seed 채택).
- [x] **AC3 [honesty]** ✅ 양 언어 "Honest scope"/"정직한 범위" + docstring: prototype·in-process·GIF=scripted baseline(학습/LLM 아님)·수치 출처·공개=사람 게이트.
- [x] **AC4 [regression]** ✅ pytest **535 passed**(529 + imageio 설치로 un-skip 2 + 신규 4), 0 실패. ruff clean. 기존 스크립트·채점 무변경.

## Default pass-criteria

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5).
- [ ] L3 (task-review) APPROVED (task-end 선결).
