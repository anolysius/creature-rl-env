# QA Checklist — render-obs-tile-codes (G1 frozen 2026-06-29)

- [x] **AC1** 회귀 테스트가 env `_PATCH_CREATURE`/`_PATCH_GYM` 상수를 import해 `render_obs`
      글리프/살라언스가 그 코드와 일치함을 단언(SSOT 대조, 수정 전 실패) + 실 env obs 렌더 단언.
- [x] **AC2** `_TILE_GLYPHS`·범례·살라언스 코드(gym/creature)·center 분기가 env 코드에 맞게 수정.
- [x] **AC3** 버그를 인코딩했던 기존 합성 테스트가 올바른 env 코드로 갱신.
- [x] **AC4** scripted `score_agent` 수치 byte-identical(렌더러 미사용 — 무회귀).
- [x] **AC5** 전체 스위트 그린(회귀 0) + `mypy src` / `ruff check .` clean.
- [x] **AC6** 정직 경계: 렌더러↔env 정합 수정이며 "floor가 풀린다"는 재측정으로 확인할 후속 가설.

## Default DoD
- [x] 회귀 0 (512 기준 그린 유지)
- [x] mypy/ruff clean
- [x] CHANGELOG 1줄
- [x] L3 APPROVED (plan-reviewer APPROVE + qa-verifier 검증증거로 BLOCK 해소; SUGGEST 3 반영)
