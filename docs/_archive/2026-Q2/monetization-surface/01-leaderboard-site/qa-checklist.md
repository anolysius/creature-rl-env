# QA Checklist — leaderboard-site (G1 freeze)

## Acceptance Criteria

- [x] **AC1 [hard]** ✅ `render_site` — 4 테스트: entry 포함(rank/name/held-out)·결정론·moat+정직 문구(held-out/contamination/RLVR/prototype/in-process/killer_demo.gif)·`html.escape`(`<script>`→`&lt;script&gt;`). PASS.
- [x] **AC2 [tooling]** ✅ `scripts/build_site.py` main() 실행 → `site/index.html`(3.8KB) + `killer_demo.gif` 복사 + 프리뷰 안내. 무료 baseline(random/scripted) 실측 랭크. stdlib만(프레임워크/네트워크 0). PPO/recurrent는 [rl] 없으면 제외(문구 명시). **브라우저 시각 확인**(로컬 http 프리뷰: 표·GIF·moat·정직 캡션 렌더).
- [x] **AC3 [honesty]** ✅ 페이지 "Honest scope"(prototype·in-process·수치 출처·"Publishing this page is a human decision") + docstring 동일 명시.
- [x] **AC4 [regression]** ✅ pytest **529 passed**(525+4), 2 skipped, 회귀 0. ruff clean. 기존 스크립트·채점 무변경.

## Default pass-criteria

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5).
- [ ] L3 (task-review) APPROVED (task-end 선결).
