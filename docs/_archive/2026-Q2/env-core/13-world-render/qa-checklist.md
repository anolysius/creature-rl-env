# QA Checklist — world-render (G1 freeze) · M3-EC6 토대

> G1 통과 시 freeze (2026-06-22). task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (프레임 렌더): `render.py` `draw_frame` → `(grid*cell, grid*cell, 3) uint8` (agent·creature·active/defeated gym·배틀 틴트 구분), numpy-only
- [x] AC2 (결정론): `reset(seed=고정)` 후 render 2회 byte-identical
- [x] AC3 (env 통합): `CritterEnv` `render_mode="rgb_array"` (`metadata`+`render()`); None→None; obs/step/reset 무변
- [x] AC4 (check_env render 검증): `test_compliance.py` `skip_render_check` 제거, `check_env(CritterEnv(render_mode="rgb_array"))` 통과
- [x] AC5 (numpy-only 격리): `render.py` top-level imageio 미import(지연); `save_gif` `[render]` 뒤; import 순수성 테스트
- [x] AC6 (`[render]` smoke): `importorskip("imageio")` 가 `save_gif` .gif 생성(비어있지 않음) 검증(core skip); `imageio` `[render]` extra 추가
- [x] AC7 (툴체인+무회귀): `mypy src`∧`ruff check .`∧`pytest -q`∧`python -m build` 통과; 기존 102 tests 회귀 0
