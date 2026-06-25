---
slug: jax-noncommit-env-integration
initiative: jax-throughput
status: active
started: 2026-06-25
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env, perf]
scope_paths:
  - src/critter_gym/jax_env.py
  - tests/test_jax_noncommit_env_parity.py
  - scripts/bench_throughput.py
extracted_to: []
supersedes: []
---

# non-commit full battle를 jax_env에 통합 (M4 family-A non-commit 경로)

> 작성일: 2026-06-25 | 상태: 계획 | Initiative: jax-throughput (task 7)

## 목표

`jax_battle_full.py`(non-commit full battle: party + SWITCH + force-switch + party-wipe,
이미 standalone parity 0)의 턴 해소 로직을 **`jax_env`의 battle branch에 통합**해, JAX
full-episode env가 numpy `CritterEnv(commit_battles=False)` — 즉 **기본(default) 환경 경로**
(`CritterGym-v0`/`CritterGym-procgen-v0`) — 와 **full parity 0 mismatch**가 되도록 한다.

현재 `jax_env`는 commit-mode(챔피언 1마리, switch 없음)만 미러링한다. 이 task는 같은
factory가 `commit=False`일 때 non-commit full battle을 dispatch하도록 확장한다.

**M4-EC1/EC2 진척**: family A의 *non-commit* 경로(env의 실제 기본값)까지 JAX 벡터화 +
parity. 배틀 엔진 두 경로(commit/non-commit)가 이제 **standalone 포트뿐 아니라 full-env까지**
통합됨.

**Acceptance 성격(§4 교훈)**: 이 task의 acceptance는 *성능*이 아니라 **측정 + 정직 보고**로
freeze. 비협상 게이트 = **parity 0 mismatch**. 속도는 vmap 한정으로 정직 보고.

## 선행 조건

- `jax_env.py` (commit-mode full-episode env, parity 0) — 이미 main에 존재.
- `jax_battle_full.py` (non-commit full battle step, parity 0) — 이미 main에 존재. 이 task는
  그 *로직*을 env state pytree에 맞게 재사용(직접 import는 선택).
- numpy SSOT (**read-only 참조, 미수정** — parity 기준): `CritterEnv(commit_battles=False)`
  (`envs/critter_env.py`: `_step_battle`/`_to_battle_action`/`_maybe_enter_battle`/`_obs`),
  `Battle(commit_mode=False)` (`battle.py`: Phase1/2/3 + `_update_terminal`), `party.gym_boss`.
  이들은 *변경 대상이 아니라* JAX 포트가 byte-mirror해야 할 진실원(scope_paths에 미포함 = 미수정).
- `[jax]` extra (코어/CI는 numpy-only 유지).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/jax_env.py` | `JaxEnvConfig`에 `commit`/`potions`/`battle_max_turns` 필드 + `JaxEnvState`에 `items`·`battle_turn` 필드 + `make_jax_env`가 `commit=False`일 때 non-commit battle_branch dispatch | **높음** (코어 JAX env) | 기존 commit 경로 byte-identical 보존(default `commit=True`) |
| `tests/test_jax_noncommit_env_parity.py` | 신규 — numpy `CritterEnv(commit_battles=False)` 대비 full-episode parity (importorskip) | 신규 | 비협상 게이트 |
| `scripts/bench_throughput.py` | non-commit full-env 행 추가(정직 framing) | 낮음 | vmap 한정 명시 |

### 영향 범위 (import 그래프)

- `jax_env.py`는 `__init__.py`가 import하지 않음(`[jax]` 뒤) → 코어 CI 무영향.
- 기존 `test_jax_env_parity.py`(commit), `test_jax_difficulty_parity.py`(고-gym commit),
  `test_jax_battle_full_parity.py`(standalone) — **무회귀 필수**(default config byte-identical).
- `JaxEnvState`에 필드 추가 → pytree leaf 증가. 기존 코드는 named access만 → 안전. vmap
  tree_map stack도 안전.

## Step별 계획

**Step 1 (Red — parity 테스트 먼저)**: `tests/test_jax_noncommit_env_parity.py` 작성.
`test_jax_env_parity.py` 구조 재사용하되 `CritterEnv(commit_battles=False)` + non-commit JAX
env(`make_jax_env(JaxEnvConfig(commit=False, ...))`). 비교: 13 obs 키 전체(local_patch 포함) +
reward + terminated + truncated, 매 step. fixed(num_types=3) + vary(num_types=8) 차트, random
policy + gym-clearing policy(switch/force-switch/party-wipe 경로 자극). 처음엔 FAIL(미구현).

**Step 2 (Green — 통합 구현)**:
1. `JaxEnvConfig`에 `commit: bool = True`, `potions: int = 2`, `battle_max_turns: int = 200` 추가.
2. `JaxEnvState`에 `items: jax.Array`(() int32), `battle_turn: jax.Array`(() int32) 추가; `reset`이
   초기화(items=0, battle_turn=0 — 배틀 진입 시 set).
3. `make_jax_env`에서 `commit` 분기:
   - overworld_branch: 배틀 진입 시 commit이면 `commit_window=on_gym`(기존), non-commit이면
     `commit_window=False` + `items=potions`·`battle_turn=0` set(+기존 heal/boss_hp/active=0).
   - battle_branch: commit이면 기존 cycle/fight, non-commit이면 **non-commit 턴**:
     action→(kind,idx) 매핑(`<4`→MOVE idx0, `==4`→SWITCH(next_alive from party_hp),
     `==5`→ITEM(99) 낭비턴) → Phase1 switch(item은 idx99라 항상 낭비) → Phase2 speed-order
     moves(보스 항상 MOVE, faint skip, tie→A) → Phase3 force-switch → party-wipe/boss-dead/
     battle-truncation(battle_turn≥battle_max_turns) 종료 판정. 종료 시: 승(boss dead & ~a_wiped)→
     `gym_defeated[battle_gym]`·active 레벨업·can_evolve시 evolve·reward(+1, evolve시 +1)·
     `mode=overworld`; 패/truncation→reward0·`mode=overworld`.
4. `boss_spd`/`boss_atk`/`boss_def`/`boss_move_power`는 기존 config 재사용(non-commit 보스도 동일
   `gym_boss`).

**Step 3 (검증/벤치)**: jit 컴파일 + vmap 배치 테스트. `bench_throughput.py`에 non-commit
full-env 행(정직 framing: vmap 한정, CPU). 실측 수치 기록.

**Step 4 (문서)**: `jax-throughput.md`(§5 #non-commit-full-env-통합 ✅) + INITIATIVE.md task 7 행 +
DESIGN §4 한 줄.

## 검증 방법

- **freeze 전 pilot (비협상 게이트)**: parity 배터리(fixed+vary, random+gym-clearing, ≥12 seed)를
  freeze 전 실행 → **0 mismatch** 입증. 추가로 ① 보스 항상-MOVE 가정 ② battle-truncation이 env
  truncation 전에 발산하지 않음을 경험적 확인.
  - **pilot 결과 박제 위치**: 본 plan에 `## Pilot 결과 (freeze 전)` 섹션을 append하고(0 mismatch
    수치·검증한 가정 결과), 최종 report.md `## Pilot` + CHANGELOG 1줄에 재기록.
  - **falsify 시 reframe 절차**(AC7): pilot이 미러 불가한 mismatch를 발견하면 → (a) 원인을 plan에
    박제, (b) 범위를 "미러 가능한 부분 + 발산 원인 honest 라벨"로 축소 reframe(새 slug 불요, freeze
    전이므로), (c) 사용자 정지 보고(bounded-YOLO 정지 조건 ①). 헛 freeze 금지.
- TDD: `python -m pytest tests/test_jax_noncommit_env_parity.py -q` (jax 설치 시).
- 무회귀: 전체 328 tests green 유지(commit/difficulty/standalone parity 포함).
- canonical: `mypy src` · `ruff check .` · `pytest -q` · `python -m build`.

## 리스크

| 리스크 | 완화 |
|---|---|
| non-commit 턴 해소가 numpy `Battle.step`과 미세 발산(speed tie·force-switch active·int floor) | `jax_battle_full`이 이미 standalone parity 0 — 그 로직 재사용. pilot이 0 mismatch로 입증. |
| 보스가 항상 MOVE가 아닐 수 있음(scripted_opponent) | pilot이 단일-creature 보스에서 MOVE-only 경험적 확인. 아니면 보스 action도 미러. |
| battle-truncation(turn≥200) 모델링 누락 → env truncation과 발산 | `battle_turn` 카운터 추가로 정확 미러. pilot이 비발산 확인. |
| 승리 레벨업 대상 creature가 force-switch 후 active와 불일치 | numpy는 Phase3(force-switch) 후 active를 레벨업 — JAX도 post-force-switch active 사용(동일 순서). |
| `JaxEnvState` 필드 추가가 commit parity 깨뜨림 | 추가 필드는 commit 로직/obs 미관여; default `commit=True` byte-identical. 무회귀 테스트로 가드. |
| spec drift(난이도 작업이 보스/reward 변경) | config-driven이라 흡수; spec-stability watch 유지. |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `make_jax_env(JaxEnvConfig(commit=False))`가 non-commit full-episode env step을
  생성(overworld + non-commit full battle: SWITCH/force-switch/party-wipe). jit 컴파일.
- **AC2 (비협상 게이트)**: numpy `CritterEnv(commit_battles=False)` 대비 **parity 0 mismatch** —
  13 obs 키 전체(local_patch 포함) + reward + terminated + truncated, full 에피소드, fixed
  (num_types=3) + vary(num_types=8) 차트, random + gym-clearing 정책(≥12 seed). **freeze 전
  pilot이 입증**.
- **AC3 (무회귀)**: 기존 328 tests green 유지 — commit parity(3)/difficulty parity/standalone
  full-battle parity 포함. default-config(commit=True) **byte-identical**.
- **AC4**: vmap이 non-commit 에피소드 배치 처리; throughput 실측 보고(**vmap 한정·CPU 정직
  framing**, default보다 배율 차이 정직 라벨).
- **AC5**: jit이 non-commit step 컴파일(tracer 통과).
- **AC6 (정직 범위)**: 정직 라벨 — CPU·single run·family A·vmap-only speedup·potion은 env action
  space상 실질 미사용(numpy 미러)·battle-truncation edge 처리 명시. 헤드라인 과대 0.
- **AC7 (사전약정 pilot 결정규칙)**: freeze 전 pilot이 parity 배터리에서 0 mismatch를 입증(데이터
  보기 전 고정된 게이트). pilot이 미러 불가한 mismatch를 발견하면 **정직 reframe**(범위 축소/원인
  박제), 헛 freeze 금지.
- **AC8**: `mypy src`·`ruff check .`·`pytest -q`·`python -m build` clean. 문서(jax-throughput.md +
  INITIATIVE + DESIGN §4) 갱신. CHANGELOG 1줄(standard narrative).

## Pilot 결과 (freeze 전 가정 검증 + parity 게이트)

**가정 검증 (코드 기반, falsify 0)**:
1. **보스 항상-MOVE**: `scripted_opponent`(battle.py:210-223)는 구조적으로 `BattleAction(MOVE, …)`만
   반환 — 보스(1-move `gym_boss`)는 항상 MOVE(0). `jax_battle_full`의 "보스 항상 MOVE" 가정 코드로
   확정. ✓
2. **battle-truncation**: numpy `_update_terminal`이 `turn≥max_turns(200)`서 truncate. 실전 도달
   불가(보스 hp120·min dmg≥1 → 빠른 종료)이나 procgen(max_steps 400 > 200)서 이론적 발산 막기 위해
   `battle_turn` 카운터로 정확 미러. ✓
3. **신규 발견 (parity 0의 핵심)**: Phase1 SWITCH는 **cyclic** next-alive(`_next_alive_player`),
   Phase3 force-switch는 **first-in-order**(`_next_alive`) — 서로 다른 순서. JAX서 각각 cyclic
   loop / `argmax`로 구분 미러. (이 구분을 놓쳤으면 parity 깨졌을 것)

**parity 게이트 (비협상, 0 mismatch)**: 신규 `test_jax_noncommit_env_parity.py` **32 passed** —
numpy `CritterEnv(commit_battles=False)` 대비 13 obs 키+reward+term+trunc, full 에피소드, fixed
(num_types 3)+vary(num_types 8), 4 정책(random·gym-clearing·switch-heavy·never-attack), seed
배터리. **non-vacuity 가드**(`test_force_switch_actually_exercised`)가 배터리가 force-switch +
party-wipe를 실제 자극함을 증명(coverage probe: 9 battle·21 switch·7 win·5 evolve + never-attack
이 force-switch·wipe 도달). 미러 불가 mismatch **0** → reframe 불요.

**실측 (CPU·single run, vmap 한정 정직)**: numpy 139k/s · jax vmap **5.08M/s(b=1024)=36× / 5.65M
(b=4096)=41× / 8.35M(b=16384)=60×**. commit full-env(31×)와 동급 — 동일 overworld·다른 배틀 경제.
