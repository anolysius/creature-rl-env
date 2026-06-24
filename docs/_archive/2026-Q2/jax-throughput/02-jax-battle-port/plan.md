---
slug: jax-battle-port
initiative: jax-throughput
status: active
started: 2026-06-24
acceptance_freeze: true
mode: standard
domains: [rl-env, perf]
scope_paths:
  - src/critter_gym/jax_battle.py
  - tests/test_jax_battle_parity.py
  - scripts/bench_throughput.py
extracted_to: []
supersedes: []
---

# JAX battle 포트 — 핫패스의 어려운 절반 (battle sub-MDP functional 포트)

> 작성일: 2026-06-24 | 상태: 계획 | 이니셔티브: jax-throughput (M4)

## 목표

`jax-hotpath-foundation`(overworld, parity 0 mismatch·vmap 186×)에 이어 **battle sub-MDP를 functional
JAX로 포트**한다. battle 은 핫패스의 *어려운 절반* — `battle.py`(234줄)는 결정론 3-phase step(비-move
액션 switch/item → move 속도순 해소 → force-switch) + terminal 체크 + commit_mode 변형 + scripted_opponent
(greedy 타입인지)이라 overworld 보다 branchy. 목표는 이 step을 **flat array pytree + `jnp.where`/`lax`로
functional 화**하고 numpy `Battle`과 **parity**(동일 초기 state + 동일 action → 동일 trajectory)를 입증하는 것.
성능 헤드라인이 아니라 *측정 + 정직 feasibility verdict*로 freeze.

전진 EC: **M4-EC1**(핫패스 포팅 — overworld + battle = 핫패스 *대부분*, 단 통합은 후속) + **M4-EC2**(parity).

## 선행 조건

- `jax-hotpath-foundation` 완료(main 머지, PR #40) — `jax_overworld.py` 패턴(state pytree·parity 하네스·
  bench·`[jax]` extra·importorskip)을 재사용. `.venv`에 jax 0.4.30 설치돼 있음.
- battle 사실(코드 정독): starter party = 3 creature(각 1 type·1 move), boss = 1 creature(1 type·1 move).
  damage = `max(1, int(power·atk/def·eff))`, eff = `multi_effectiveness`(defender types 곱). commit_mode =
  switch/force-switch 없음·champion faint=즉시 패배(gym-boss 실제 경로, `CritterGym-commit-v0`).
- TypeChart 는 per-seed effectiveness 표 → jnp 행렬(`eff[move_type, defender_type]`)로 사전계산.

## 작업 범위

### 수정 대상 파일 (영향도 표)
| 파일 | 신규/수정 | 영향도 | 설명 |
|---|---|---|---|
| `src/critter_gym/jax_battle.py` | 신규 | 중상 | battle step 의 functional JAX 포트: flat pytree(`JaxBattleState`: party hp/atk/def/speed + move power·type + creature types, active idx, items, turn, done/winner) + `battle_step(state, action_a, action_b)` + `scripted_opponent`(greedy) + TypeChart→`eff_matrix` 빌더 + numpy `Battle`→state bridge. **commit-mode 챔피언 경로 우선**, 전체 switch/item/force-switch 포함은 pilot 결정. import jax 모듈 내부(코어 numpy-only 보존, `__init__` 미import). |
| `tests/test_jax_battle_parity.py` | 신규 | 중 | parity + jit/vmap 가드(`importorskip("jax")`): numpy `Battle`(commit_mode True/포함 시 False)과 동일 초기 state + 동일 action 시퀀스에서 trajectory 동일(active별 hp·active idx·winner·turn·done). + `scripted_opponent` 선택 동일성. + jit 컴파일 + vmap batch shape. |
| `scripts/bench_throughput.py` | 수정 | 저 | battle step 의 numpy vs jax single/vmap steps/s 행 추가(overworld 와 동일 정직 framing). |

### 영향 범위 (import 그래프)
- `jax_battle.py`는 **신규·격리** — 기존 `battle.py`/`creatures.py`/`types.py`를 수정하지 않음(포트는 별도
  복제, parity 가 등가 보증). family A/B/C/D 런타임·obs·action 무영향, 210 tests 무회귀.
- `__init__` 미import = 코어 numpy-only 보존. bench 수정은 소비자(회귀 표면 0). `[jax]` extra 이미 존재.

## Step별 계획

1. **pilot (freeze 전, 필수)** — battle step 의 *commit-mode 챔피언 슬라이스*(1 champion vs 1 boss, move-vs-
   move, damage+eff, faint→terminal)를 functional JAX 프로토타입. 검증: (i) `jax.jit` 컴파일, (ii) numpy
   `Battle(commit_mode=True)`와 trajectory parity(소규모 수동 대조), (iii) 전체 switch/item/force-switch까지
   functional 화 비용 가늠 → **AC7 분기 결정**: (a) 전체 battle / (b) commit-only + full 후속분리 / (c) reframe.
   pilot 이 (i)/(ii) falsify 시 정직 reframe(goalpost 이동 금지).
2. **state 설계** — `JaxBattleState` pytree: party_a/b stat 배열(hp·max_hp·atk·def·speed, shape [party_size]),
   move power·type 배열, creature type one-hot/idx(multi-type 위해), active_a/b idx, items_a/b, turn, done, winner.
   고정 party size(A=3, B=1; 또는 공통 MAX_PARTY 패딩 + alive mask).
3. **functional step** — `battle_step`: phase1(item/switch — commit-mode면 skip), phase2(move 속도순 — 두
   mover를 speed로 정렬: `lax.cond`/where로 A-우선/B-우선 분기 후 순차 damage 적용), phase3(force-switch —
   commit-mode skip), terminal(commit: active faint=loss / non-commit: party_wiped). damage = `max(1, floor(
   power·atk/def·eff))` — int 산술 정확 일치 주의(numpy `int()` truncation = jnp floor-toward-zero, 양수라 동일).
4. **scripted_opponent** — greedy 타입인지 move 선택 functional 포트(boss 1 move라 자명하나 일반화 위해).
5. **parity 테스트** — numpy `Battle`과 동일 초기 state(starter vs gym_boss, 여러 seed/타입)+동일 action
   시퀀스에서 trajectory 동일. eff 행렬·속도 타이·faint 타이밍·max_turns truncation 경계 포함.
6. **bench + verdict** — battle step numpy vs jax vmap steps/s. feasibility verdict 박제(jit/parity/speedup/
   남은 부분[switch·item 포함 여부]/후속 권고).

**커밋 단위 경계**: (c1) `jax_battle.py` state+step / (c2) scripted_opponent + parity 테스트 / (c3) bench 확장 +
verdict·report(task-end).

## Freeze 전 pilot 결과 (2026-06-24, scratchpad throwaway)

commit-mode 챔피언 배틀(1 champion vs 1 boss, move-vs-move, eff damage, faint→terminal)을 functional JAX
프로토타입해 AC7 분기 결정. 실측:
- **(i) jit = OK.**
- **(ii) parity = OK** — fixed 차트 45 config(3 champion × 15 type) + vary 차트 24 config(8 seed × 3 champion),
  **0 mismatch**(champ_hp·boss_hp·winner·turn·done 전부 일치).
- **(iii) throughput (CPU)** — numpy 112k/s · **jax vmap 253M(b=1024)/230M(b=8192) steps/s = ~2252×**
  (battle step은 순수 산술이라 overworld보다도 벡터화 효율 높음).
- **pilot이 parity 버그 1건을 freeze 전에 포착**: numpy `Creature.take_damage`가 hp를 `max(0,·)`로 클램프하는데
  초안 JAX는 음수 hp 허용(-22) → winner/turn/done은 일치하나 hp 기록 불일치. **`jnp.maximum(0., ·)` 클램프로
  교정 → 0 mismatch.** (구현 시 take_damage/heal 클램프 정확 미러링 필수.)
- **판정 = AC7 분기 (b)**: commit-mode 챔피언 경로(gym-boss 실제 경로) 완벽 검증 → **이 task로 포트**, 전체
  switch/item/force-switch/multi-creature non-commit battle 은 **후속 `jax-battle-full`로 분리**(scope balloon
  방지·정직 라벨). reframe 불필요.

## 검증 방법

- `pytest -q` — 210 무회귀 + 신규 battle parity(jax 환경) green. CI(numpy-only) `importorskip` skip.
- `mypy src`(24 모듈 예상) / `ruff check .` / `python -m build` clean.
- damage 산술 일치: numpy `int(x)`(truncation)와 jnp 정수 산술이 양수 도메인서 bit-동일임을 parity 가 가드.
- bench 수동 — battle step numpy vs jax(vmap) steps/s 기록(단일 측정=헤드라인 아님).

## 리스크

- **R1 (핵심)**: 3-phase step 의 속도순 정렬·force-switch·multi-creature switching 이 `lax.cond`/동적
   인덱싱으로 표현하기 번거로움 → pilot 으로 freeze 전 검증, 과대 시 commit-only 로 scope 축소(AC7 b).
- **R2**: int damage 산술 미세 불일치(`int()` vs jnp). 양수 도메인 floor 동일 예상이나 parity 로 *입증*; 불일치 시
   명시적 `jnp.floor`/int32 캐스팅으로 교정.
- **R3**: multi-type eff 곱이 starter/boss 는 단일타입이라 trivial 하나, 일반 creature(1-2 type) 위해 eff
   행렬 곱 경로 유지(vary 모드 호환).
- **R4**: commit_mode True/False 두 경로 — 우선 commit(env gym-boss 경로), non-commit 포함은 pilot 결정.
- **R5 (이니셔티브)**: 난이도(A) 작업이 battle 경제(보스 stat·reward) 바꾸면 재포트 — DESIGN §4 가 M4 를
   "spec 안정 후"로 게이트. freeze 시 박제.

## Acceptance Criteria (G1 통과 시 freeze)

> 원칙: 성능 아닌 **측정 + 정직 feasibility verdict**로 freeze. pilot 이 가정 falsify 시 정직 reframe.
> 사전약정 결정규칙(AC7)으로 사후 편향 차단.

- **AC1**: `src/critter_gym/jax_battle.py` 신규 — battle step(최소 commit-mode 챔피언 경로: move-vs-move +
  eff damage + faint→terminal)의 functional JAX 포트가 `jax.jit` 컴파일 성공. (불가 판명 시 그 사실 *입증*=충족.)
- **AC2**: `tests/test_jax_battle_parity.py` — numpy `Battle`과 동일 초기 state + 동일 action 시퀀스에서
  trajectory(hp·active·winner·turn·done) **동일**. `importorskip("jax")` CI numpy-only 보존.
- **AC3**: damage/eff 산술이 numpy 와 **정확 일치**(int truncation·속도 타이·faint 타이밍·max_turns 경계
  포함) — parity 테스트가 가드.
- **AC4**: `scripts/bench_throughput.py` 에 battle step numpy vs jax single/vmap steps/s 행 추가, 정직
  framing(이득=vmap·single 느림) 유지.
- **AC5**: 회귀 0 — 기존 210 tests green(jax 미설치 CI 포함), mypy/ruff/build clean. 기존 `battle.py`/
  `creatures.py`/`types.py` 무변경(포트는 격리 복제). 코어 numpy-only.
- **AC6**: **feasibility verdict** report 박제 — (i) jit OK/NG (ii) parity OK/NG (iii) vmap speedup 방향
  (iv) 포트 범위(commit-only / full switch·item) 명시 (v) 후속 권고(jax-env-integration). speedup 음수도 정직.
- **AC7 (사전약정 결정규칙)**: pilot 결과로 freeze 분기 — pilot 이 **분기 (b) 확정**(commit-mode 챔피언 경로
  jit+parity 완벽 = 0 mismatch, full 은 별도 chunk) → **commit-mode 포트 + full switch/item/multi-creature
  non-commit battle 은 후속 `jax-battle-full`로 분리**(정직 라벨). (a 전체/c reframe 은 미발동.) 정직 보고가 DoD.
- **AC8**: 툴체인 green (ruff ∧ mypy src ∧ pytest ∧ build).
