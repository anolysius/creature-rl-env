# QA Checklist — killer-demo (G1 freeze) · M3-EC6 (전진)

> G1 통과 시 freeze (2026-06-22). task-verify(G2)·task-end 가 1:1 대조.
> ⚠ 이 task 는 EC6 를 **전진**(데모 수단 ship + 파이프라인 CI 검증)시키되 **완전 충족하지 않음** —
> milestones EC6 체크박스 `[ ]` 유지.

## Acceptance Criteria
- [x] AC1 (녹화 파이프라인): `demo.py` `record_episode` → `EpisodeRecording`(frames+steps+total_reward+gyms_defeated+boss_defeated+seed), numpy-only; render_mode≠rgb_array → ValueError
- [x] AC2 (프레임·결정론): `len(frames)==steps+1`, 각 `(H,W,3) uint8`; 고정 seed+결정론 정책 byte-identical
- [x] AC3 (보스격파 감지=파이프라인 검증, 일반화 아님): scripted 가 seed=3(train)에서 `gyms_defeated≥1`, `boss_defeated==(remaining_gyms==0)`; held-out 일반화 미증명 명시
- [x] AC4 (numpy-only 격리): `demo.py` top-level torch/sb3/imageio 미import; `save_demo`→`render.save_gif`; import 순수성 테스트
- [x] AC5 (`[render]` smoke): `importorskip("imageio")` 가 `save_demo` .gif 생성(비어있지 않음) 검증(core skip)
- [x] AC6 (데모 스크립트): `killer_demo.py` train→held-out 녹화→GIF+격파리포트(PPO deterministic=True); `[rl]`+`[render]` graceful, 산출 GIF=비CI 실행 산물
- [x] AC7 (정직 표기): milestones EC6 `[ ]` 유지(전진≠충족); `[x]`=실제 held-out GIF 확인+별도 결재; report 명시
- [x] AC8 (툴체인+무회귀): `mypy src`∧`ruff check .`∧`pytest -q`∧`python -m build` 통과; 기존 113 tests 회귀 0
