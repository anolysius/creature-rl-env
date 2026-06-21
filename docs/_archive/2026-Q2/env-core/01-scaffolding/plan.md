---
slug: scaffolding
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/**
  - tests/**
  - pyproject.toml
extracted_to: []
supersedes: []
---

# Phase 1 스캐폴딩 — 최소 Gymnasium env + 패키지 레이아웃

> 작성일: 2026-06-21 | 상태: 계획

## 목표
DESIGN.md §6 Phase 1 의 진입점 — **"dumbest-possible playable env"** 를 세운다. 두 가지를 동시에 달성:
1. **패키지/툴체인 스캐폴드**: `src/critter_gym/` 레이아웃 + `pyproject.toml` + ruff/mypy/pytest 를
   설치·동작시켜 하네스의 verify 단계(`run-tdd.py`)가 실제로 돌게 한다.
2. **최소 env**: 10×10 그리드, catch-only 리워드, Gymnasium API 준수, `reset(seed)` 결정론.
   이후 task(subgoal chain·procgen)가 올라설 안정된 골격.

부수 목표 — **HARNESS-PORT-MANIFEST §(c) 구조적 커플링 #1~#4 확정**: 스캐폴드를 `src/critter_gym/` +
ruff/mypy/pytest 로 구성함으로써 하네스가 가정한 레이아웃을 *구성에 의해* 충족시킨다.

## 선행 조건
- Phase 0 산출물(DESIGN.md, 하네스) 존재. 제품 코드는 0줄 — green-field.
- 제품 코드 작성은 G1 통과 후 `feature/*` 브랜치에서 (현재 `main`, rules/85).
- `harness-task-start-guard.py` 가 frozen plan 없이 `src/**`·`tests/**` 편집을 BLOCK → 본 plan 의
  G1 freeze 가 그 게이트를 연다(scope_paths 가 `src/critter_gym/**`·`tests/**` 커버).

## 작업 범위
### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | criticality | 비고 |
|---|---|---|---|
| `pyproject.toml` | 신규 | critical | 패키지 메타 + deps(gymnasium, numpy) + dev-deps(ruff, mypy, pytest) + tool 설정 |
| `src/critter_gym/__init__.py` | 신규 | critical | 패키지 진입 + `register()` 호출 |
| `src/critter_gym/registration.py` | 신규 | critical | `gymnasium.register("CritterGym-v0", ...)` |
| `src/critter_gym/envs/__init__.py` | 신규 | critical | env export |
| `src/critter_gym/envs/critter_env.py` | 신규 | critical | 최소 `gymnasium.Env` — 10×10, catch-only |
| `tests/test_env.py` | 신규 | low | API 준수 + 결정론 + catch 리워드 테스트 |
| `tests/test_registration.py` | 신규 | low | `gymnasium.make` 라운드트립 |
| `.gitignore` | 갱신 | low | `__pycache__`, `*.egg-info`, `build/`, `dist/`, `.venv/` |

### 영향 범위 (import 그래프)
- 신규 패키지 — 기존 import 영향 없음. `critter_gym` → `gymnasium` + `numpy` (신규 deps).
- 하네스 verify 경로: `run-tdd.py` 의 `COMMANDS`(mypy src / ruff check . / pytest -q / python -m build)
  가 본 task 산출물에 처음으로 실제 적용된다(§(c)#2 확정).
- `path-criticality.json` 의 critical glob(`src/critter_gym/{envs,spaces,wrappers}/**`, `registration.py`,
  `pyproject.toml`) 이 실제 파일과 1:1 매칭됨을 확인(§(c)#4 확정).

## Step별 계획
1. **툴체인 결정 고정** — deps: `gymnasium>=0.29`, `numpy`. dev: `ruff`, `mypy`, `pytest`. 빌드
   백엔드는 `hatchling`(또는 setuptools). `pyproject.toml` 에 `[tool.ruff]`/`[tool.mypy]`/`[tool.pytest.ini_options]`
   명시. → §(c)#1(ruff 가 포매터/린터) 확정.
2. **패키지 레이아웃** — `src/critter_gym/` (src-layout) 생성. `[tool.hatch.build]`/`packages` 설정으로
   editable install (`pip install -e .[dev]`) 동작. → §(c)#3(`_TARGET_PREFIXES=("src/",)`) 정합 확인.
3. **최소 env** — `CritterEnv(gymnasium.Env)`:
   - `observation_space`: 구조적(Dict 또는 Box) — agent 위치 + 로컬 패치 + `caught` 카운트(DESIGN §3.2 structured-first).
   - `action_space`: `Discrete` — MOVE{N,S,E,W}, CATCH, NOOP (DESIGN §3.3 의 최소 부분집합).
   - `reset(seed)`: seed 로 10×10 맵 + 창조물 스폰을 결정론적 배치. 같은 seed → 같은 초기 상태.
   - `step(action)`: 이동/캐치 처리. CATCH 가 창조물 칸에서 성공 시 boolean subgoal(`caught += 1`) →
     리워드 +1 (RLVR, dense shaping 금지). `(obs, reward, terminated, truncated, info)` 5-튜플 반환.
     `info["subgoals"]={"caught": n}`.
   - 종료: `caught >= C`(예 C=3) → `terminated=True`. step budget 초과 → `truncated=True`.
4. **등록** — `registration.py` 에서 `register(id="CritterGym-v0", entry_point=...)`. `__init__` import 시 1회.
5. **테스트** — `test_env.py`: (a) `reset(seed=0)` 2회 호출 obs 동일(결정론), (b) `step` 반환 형태/공간
   포함, (c) 창조물 칸에서 CATCH → reward=1 ∧ `info` subgoal 증가, (d) C회 캐치 시 terminated.
   `test_registration.py`: `gymnasium.make("CritterGym-v0")` → env 인스턴스.
6. **green 확인** — `ruff check .` clean, `mypy src` clean, `pytest -q` green, `python -m build` 성공.

## 브랜치 & 커밋 단위 (L1 @plan-reviewer SUGGEST 반영)
- 브랜치: `feature/env-scaffolding` (rules/85 — `main` 직접 작업 금지, G1 통과 후 생성).
- 커밋 단위 (3 묶음, step 그룹별):
  1. `chore: package layout + toolchain` — Step 1·2 (`pyproject.toml`, src-layout, `.gitignore`).
  2. `feat: minimal catch-only CritterEnv + registration` — Step 3·4.
  3. `test: env API/determinism/reward suite` — Step 5·6 (green 확인 포함).
- PR: `feature/env-scaffolding → main` (task-end 이후).

## 검증 방법
- TDD: 각 동작 테스트 먼저(Red) → 구현(Green) → 정리(Refactor). task-loop(L2) 가 반복.
- `python3 .claude/skills/task-verify/scripts/run-tdd.py` 가 mypy/ruff/pytest/build 일괄 실행.
- 결정론은 동일 seed 2회 reset obs 비교로 *검증 가능*하게(RLVR 정신).

## 리스크
- **빌드 백엔드 선택**: hatchling vs setuptools — editable+src-layout 둘 다 지원. hatchling 기본 채택,
  문제 시 setuptools fallback. (저위험, 되돌리기 쉬움)
- **obs space 형태**(Dict vs flat Box): 이후 procgen/party 확장에 영향. v1 은 단순 유지, 확장은 후속 task.
- **mypy strictness**: green-field 라 strict 부담 적음. `disallow_untyped_defs` 부터 점진.
- **하네스 가정 어긋남**: §(c)#2 의 `COMMANDS` 가 우리 레이아웃과 안 맞으면 `run-tdd.py` 수정 필요 —
  본 task 가 src-layout 으로 맞추므로 정합 예상. 어긋나면 Step 6 에서 포착.

## Acceptance Criteria (G1 통과 시 freeze)
- [ ] **AC1 (설치)**: `pip install -e ".[dev]"` 가 깨끗한 venv 에서 성공한다.
- [ ] **AC2 (등록)**: `python -c "import gymnasium, critter_gym; gymnasium.make('CritterGym-v0')"` 가
  에러 없이 env 인스턴스를 만든다.
- [ ] **AC3 (Gymnasium API)**: `reset(seed=k)` 가 `(obs, info)` 를, `step(a)` 가 `(obs, reward,
  terminated, truncated, info)` 5-튜플을 반환하고 obs ∈ `observation_space`.
- [ ] **AC4 (결정론)**: 동일 seed 로 `reset` 2회 → 초기 obs 가 정확히 동일(numpy array_equal).
- [ ] **AC5 (RLVR catch 리워드)**: 창조물 칸에서 CATCH 시 reward=+1 ∧ `info["subgoals"]["caught"]`
  증가. 빈 칸 CATCH 는 reward=0. dense shaping 없음(이동 자체 보상 0).
- [ ] **AC6 (종료 subgoal)**: `caught >= C` 도달 시 `terminated=True`; step budget 초과 시 `truncated=True`.
- [ ] **AC7 (툴체인 green)**: `ruff check .` ∧ `mypy src` ∧ `pytest -q` 모두 통과, `python -m build` 성공.
- [ ] **AC8 (커플링 확정)**: HARNESS-PORT-MANIFEST §(c) #1·#2·#3·#4 가 본 레이아웃과 정합함을
  report.md 에 1줄씩 확인 기록(불일치 시 해당 하네스 파일 수정 포함).
