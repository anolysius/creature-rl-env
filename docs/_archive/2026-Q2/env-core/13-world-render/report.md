---
slug: world-render
initiative: env-core
status: done
started: 2026-06-22
ended: 2026-06-22
mode: standard
result: passed
milestone: M3
exit_criteria: [M3-EC6]   # 전진(토대) — EC6 자체는 미충족(killer-demo 후속)
extracted_to:
  - docs/reference/milestones.md       # M3-EC6 토대 메모 (checkbox 미충족 유지)
changelog_entry: docs/CHANGELOG.md
---

# Report — world-render (월드 상태 → 픽셀 프레임) · M3-EC6 토대 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약

킬러 데모(M3-EC6)의 **render 토대** — `render` 도메인 첫 vertical. 월드 상태를 색칠 셀 프레임으로
그리는 **numpy-only** `critter_gym.render.draw_frame` + `CritterEnv` 의 Gymnasium 표준
`render_mode="rgb_array"` 통합. **rgb_array 는 색칠 배열이라 새 의존성 0 으로 core 구현**(DESIGN
numpy-first 정합); GIF 인코딩(`save_gif`)만 `[render]` extra(imageio) 뒤로 지연 import 격리.
**EC6 를 전진시키되 충족하지 않음** — checkbox `[ ]` 유지, 보스격파 에이전트+GIF 조립은 후속
`killer-demo`. Acceptance **7/7**, **113 passed/2 skipped**(102→113, 회귀 0), check_env 가 이제
rgb_array render 를 실제 검증(skip 제거).

## 계획 대비 실적

| AC | 내용 | 결과 |
|---|---|---|
| AC1 | `draw_frame` → `(grid*cell,grid*cell,3) uint8` (agent·creature·active/defeated gym·배틀 틴트), numpy-only | ✅ |
| AC2 | 결정론 (고정 시드 byte-identical + 입력 순서 무관) | ✅ |
| AC3 | `CritterEnv` `render_mode="rgb_array"` (metadata+render()); None→None; obs/step/reset 무변 | ✅ |
| AC4 | check_env render 실제 검증 (`skip_render_check` 제거) | ✅ |
| AC5 | numpy-only 격리 (render.py top-level imageio 미import; `save_gif` `[render]` 뒤) | ✅ |
| AC6 | `[render]` smoke (`importorskip` GIF 생성, core skip) + `imageio` extra | ✅ |
| AC7 | mypy/ruff/pytest/build 통과 + 기존 102 무회귀 | ✅ |

## 변경 파일 상세

| 파일 | 종류 | 내용 |
|---|---|---|
| `src/critter_gym/render.py` | 신규 | `draw_frame`(numpy-only, 배경→creature→gym→agent 그리기 순서로 순서 무관 결정론) + `save_gif`(지연 imageio) |
| `src/critter_gym/envs/critter_env.py` | 수정 | `render_mode` 파라미터 + `metadata["render_modes"]=["rgb_array"]`/`render_fps` + read-only `render()` (obs/step/reset 무변) |
| `tests/test_compliance.py` | 수정 | `skip_render_check=True` 제거 → `check_env(CritterEnv(render_mode="rgb_array"))` (render 실제 검증) |
| `tests/test_render.py` | 신규 | 12건 — 프레임 계약·내용·결정론(고정시드+순서무관)·env통합·import순수성 + `[render]` smoke |
| `pyproject.toml` | 수정 | `[render]` extra=imageio; mypy override 에 `imageio.*` |

## 설계 결정

- **rgb_array = numpy-only** — 색칠 셀 배열이라 matplotlib/pygame 불요. core 가 직접 프레임 생성,
  연구자 친화 Gymnasium 표준 인터페이스(`env.render()`).
- **read-only render** — `render()` 가 에피소드 상태를 변형하지 않아 rollout/측정 무결성 보존
  (벤치마크에 영향 0). `render_mode` 는 step/obs/reward 에 미관여.
- **순서 무관 결정론** — 그리기 순서(배경→creature→gym→agent on top)로 `_creatures`(set) 반복
  순서에 무관하게 byte-identical (L3 SUGGEST 흡수: 셔플 입력 테스트로 가드).
- **전진 vs 충족** — EC6 토대만; 보스격파 에이전트 학습+GIF 조립(학습품질·CI비검증)은 후속.

## L3 리뷰 + 흡수

L3 ≥2 reviewer **APPROVED**. 비차단 SUGGEST 1건(draw_frame 순서독립성이 docstring 주장뿐 →
테스트 부재) 즉시 흡수 — 셔플된 creatures/gym_tiles 입력의 frame byte-identical 테스트 추가.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 내용 |
|---|---|
| `docs/reference/milestones.md` | M3-EC6 토대 메모(`world-render` render API ✅); EC6 checkbox 는 미충족 유지(killer-demo 후속) |

## 툴체인 결과

- `pytest` → **113 passed, 2 skipped**(`[rl]`+`[render]` smoke; 102→113, 회귀 0)
- `ruff check .` → clean · `mypy src` → Success (15 files) · `python -m build` → OK
- `check_env(CritterEnv(render_mode="rgb_array"))` fixed+procgen 통과(rgb_array 실제 검증), frame (H,W,3) uint8
