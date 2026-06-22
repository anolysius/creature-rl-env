---
slug: world-render
initiative: env-core
status: active
started: 2026-06-22
acceptance_freeze: true
milestone: M3
exit_criteria: M3-EC6
task_type: env
mode: standard
domains: [render, rl-env]
scope_paths:
  - src/critter_gym/render.py
  - src/critter_gym/envs/critter_env.py
  - tests/test_render.py
  - tests/test_compliance.py
  - pyproject.toml
extracted_to: []
supersedes: []
---

# world-render (M3-EC6 토대)

> 작성일: 2026-06-22 | 상태: 계획

## 목표

킬러 데모(M3-EC6: "같은 에이전트 → unseen held-out 시드 → 보스 격파 GIF")의 **render 토대**를 만든다.
EC6 는 두 조각 — (1) **월드 상태 → 픽셀 프레임**(견고·검증 가능·재사용), (2) 보스 격파 에이전트 +
GIF 조립(학습 품질 의존, CI 비검증). 본 task 는 **(1) render 레이어**만 — `render` 도메인의 첫 vertical.

**핵심: rgb_array 는 색칠된 numpy 배열이라 새 의존성 0 으로 core 구현**(DESIGN 의 numpy-first·fast 철학과
정합). Gymnasium 표준 `render_mode="rgb_array"` → `env.render()` 가 `(H,W,3) uint8` 프레임 반환. GIF
인코딩(프레임 시퀀스 → .gif)만 `[render]` optional extra(imageio) 뒤로 격리([rl]/[viz] 패턴 계승).

**전진 vs 충족 (M3-EC6 경계 명시)**: 본 task 는 EC6 를 **전진**시키되 **충족하지 않는다** — EC6 의
checkbox 는 `[ ]` 로 남는다(milestones 에 그렇게 기록). 충족은 후속 task **`killer-demo`**(보스 격파
에이전트 학습 + 에피소드 녹화 → GIF 조립; `[rl]`+`[render]`, CI 비검증·학습품질 의존)에서. 본 task 는
그 데모가 호출할 **검증 가능한 render API**(`env.render()` + `save_gif`)를 깔아둔다.

> 본 task 는 **연구자에게 보여줄 데모용 월드 렌더링** — DESIGN 의 "art·juice 최저 우선"과 충돌하지
> 않음: 데모(킬러 GIF)는 채택의 force multiplier 라 명시적 제품 목표(M3-EC6). 단 *게임 미화*가 아니라
> *상태의 충실한 시각화*에 한정(색칠 셀 — 그리드/agent/creature/gym/배틀).

## 선행 조건

- ✅ `CritterEnv` 상태 노출 — `_agent_pos`, `_creatures`(set of tile), `_gym_tiles`(pos→idx),
  `_gym_defeated`(list[bool]), `_mode`("overworld"/"battle"), `grid_size`. (env 코드 확인 완료)
- ✅ Gymnasium API — `metadata["render_modes"]` 현재 `[]`(미지원). `render_mode` 파라미터·`render()` 미구현.
- ✅ `check_env`(test_compliance) 통과 중 — render_modes 추가 후에도 유지해야.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/render.py` | **신규** | 높음 (신규 render 도메인) | `draw_frame`(numpy-only) + `save_gif`(지연 imageio) |
| `src/critter_gym/envs/critter_env.py` | 수정 | 중 (env 계약) | `render_mode` 파라미터 + `metadata["render_modes"]` + `render()` 위임 |
| `tests/test_render.py` | **신규** | 중 | core: 프레임 shape·내용·결정론 / `[render]` smoke: GIF |
| `tests/test_compliance.py` | 수정 | 중 | `skip_render_check=True`→실제 render 검증 (renderer 출하로 더 이상 skip 불가) |
| `pyproject.toml` | 수정 | 낮음 | `[render]` extra = imageio (core/dev 무변) |

### 영향 범위 (import 그래프)

- `render.py` → import numpy 만. **imageio 는 `save_gif` 내부 지연 import**(모듈은 imageio 없이 import).
- `critter_env.py` → `render.draw_frame` import(numpy-only 경로); `render_mode` 미설정(None) 시
  `render()` 는 None(Gymnasium 계약). 기존 step/reset/obs **무변** — 순수 추가.
- 측정 스택(generalization/scoreboard/leaderboard/viz)과 **무관**(render 는 독립 vertical).

## Step별 계획

### Step 1 — `render.py` `draw_frame` (numpy-only) [RED→GREEN]

```python
# 색 상수(RGB): 배경/agent/creature/active-gym/defeated-gym/배틀 틴트
def draw_frame(
    grid_size: int, agent_pos: tuple[int, int],
    creatures: Iterable[tuple[int, int]],
    gym_tiles: Mapping[tuple[int, int], int], gym_defeated: Sequence[bool],
    in_battle: bool = False, cell: int = 16,
) -> np.ndarray:                       # (grid_size*cell, grid_size*cell, 3) uint8
    """월드 상태를 색칠 셀 프레임으로. 결정론(동일 상태→동일 배열)."""
```

- 셀 단위로 사각형 색칠: 배경 → creature → gym(defeated=회색/active=색) → agent(최상위).
- `in_battle` 시 테두리/틴트 오버레이(배틀 가시화). cell px 스케일.

### Step 2 — `CritterEnv` render 통합 [GREEN]

- `__init__(..., render_mode: str | None = None)` 추가; `metadata["render_modes"] = ["rgb_array"]`.
- `render()` — `render_mode == "rgb_array"` 시 `draw_frame(self.grid_size, tuple(self._agent_pos),
  self._creatures, self._gym_tiles, self._gym_defeated, in_battle=self._mode=="battle")` 반환;
  None 모드면 None. obs/step/reset 무변.

### Step 3 — `render.py` `save_gif` (지연 imageio, `[render]`) [GREEN]

```python
def save_gif(frames: Sequence[np.ndarray], path: str, fps: int = 5) -> str:
    """프레임 시퀀스를 .gif 로 — imageio 지연 import(없으면 ImportError)."""
```

### Step 4 — 테스트 + `pyproject` [RED→GREEN]

- **core(numpy-only)**: `draw_frame` 가 `(grid*cell, grid*cell, 3) uint8` 반환; agent 셀이 agent 색;
  creature/gym 셀 존재; defeated gym ≠ active gym 색; `in_battle=True` 가 프레임을 바꿈; **결정론**
  (`reset(seed=고정)` 후 `render()` 2회 byte-identical — unseeded reset 아님).
  `CritterEnv(render_mode="rgb_array").render()` 가 유효 프레임; render_mode=None → None.
- **`test_compliance.py` 전환**: `check_env(CritterEnv(), skip_render_check=True)` →
  `check_env(CritterEnv(render_mode="rgb_array"))`(skip 제거) 로 **check_env 가 rgb_array render 를
  실제 호출·검증**. renderer 를 출하했으므로 skip 은 더 이상 정당하지 않음. 같은 변경에 묶어 무회귀 보장.
- **`[render]` smoke**(`importorskip("imageio")`): `save_gif` 가 ≥2 프레임을 .gif(비어있지 않음)로 저장.
- `pyproject.toml`: `[render]` extra = `["imageio>=2.31"]`.

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build`.
- 수동(데모): `env.render()` 프레임을 모아 `save_gif`(+`[render]`)로 GIF 생성 — EC6 후속 데모의 토대.
- 기존 102 tests 무회귀 + `check_env`(fixed+procgen, rgb_array) 통과.

## 리스크

| 리스크 | 완화 |
|---|---|
| render_modes 추가로 `check_env` 가 render 호출·검증 실패 | `draw_frame` 가 Gymnasium rgb_array 계약((H,W,3) uint8) 충족 + 명시 테스트 |
| imageio 의존이 core 오염 | 지연 import + `[render]` extra 격리 + import 순수성(render.py top-level imageio 미import) |
| 배틀 모드 렌더가 과복잡(미화 유혹) | v1 은 상태 충실 최소(틴트/테두리) — 배틀 장면 연출은 scope 밖 |
| "게임 art" 로 scope 확대 | 색칠 셀만(상태 시각화), 스프라이트·애니·사운드 없음 — DESIGN art-최저 정합 |
| 기존 env 계약(step/obs) 회귀 | render 는 순수 추가(read-only 상태 접근); obs/step/reset 무변 + 102 tests 가드 |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/render.py` `draw_frame` 가 월드 상태를 **`(grid*cell, grid*cell, 3) uint8`**
   프레임으로 렌더(agent·creature·active/defeated gym·배틀 틴트 구분), **numpy-only**.
2. **결정론** — `reset(seed=고정)` 후 동일 상태 → 동일 프레임 배열(byte-identical, 고정 시드 측정).
3. `CritterEnv` 가 `render_mode="rgb_array"` 지원 — `metadata["render_modes"]=["rgb_array"]`,
   `render()` 가 유효 프레임 반환; `render_mode=None` 이면 None. obs/step/reset **무변**.
4. **`check_env` 가 render 를 실제 검증** — `test_compliance.py` 의 `skip_render_check=True` 제거,
   `check_env(CritterEnv(render_mode="rgb_array"))` 로 rgb_array 경로를 호출·검증하며 통과(무회귀).
5. **numpy-only 격리** — `render.py` top-level 에 imageio 미import(지연); `save_gif` 가 `[render]`
   extra(imageio) 뒤. import 순수성 테스트.
6. **`[render]` smoke** — `importorskip("imageio")` 가 `save_gif` 의 .gif 생성(비어있지 않음) 검증
   (core CI skip). `imageio` 가 `[render]` extra 에 추가됨.
7. `mypy src` · `ruff check .` · `pytest -q` · `python -m build` 통과 + 기존 102 tests 무회귀.
