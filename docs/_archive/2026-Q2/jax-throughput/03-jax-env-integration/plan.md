---
slug: jax-env-integration
initiative: jax-throughput
status: active
started: 2026-06-24
acceptance_freeze: true
mode: standard
domains: [rl-env, perf]
scope_paths:
  - src/critter_gym/jax_env.py
  - tests/test_jax_env_parity.py
  - scripts/bench_throughput.py
extracted_to: []
supersedes: []
---

# JAX env 통합 — 벡터화된 full-episode env step (overworld + commit-battle 합성)

> 작성일: 2026-06-24 | 상태: 계획 | 이니셔티브: jax-throughput (M4)

## 목표

`jax_overworld`(overworld, parity 0·vmap 186×) + `jax_battle`(commit-mode 챔피언, parity 0·vmap 1047×)를
**하나의 벡터화된 full-episode env step**으로 합성한다. 지금까지는 슬라이스 step 만 있었고 RL 루프가 쓸 수 없었음.
이 task 는 **`(state, action) → (state, obs, reward, terminated, truncated)` 단일 functional step** 을 만들어
`vmap` 으로 수천 env 를 동시에 굴릴 수 있게 하고, numpy `CritterEnv(commit_battles=True)` 와 **parity** 를
입증한다. 성능 헤드라인이 아니라 측정 + 정직 feasibility verdict.

전진 EC: **M4-EC1**(핫패스 포팅 — 통합 env step = 슬라이스를 실사용 surface 로) + **M4-EC2**(parity).
이게 되면 RL 학습 루프가 JAX 엔진을 실제 소비(벤치 넘어 가치).

## 선행 조건

- `jax-hotpath-foundation` + `jax-battle-port` 완료(main 머지, PR #40·#41). `jax_overworld`/`jax_battle`
  패턴(state pytree·parity 하네스·`make_*_step` jit·importorskip)을 합성.
- env 사실(코드 정독): `CritterEnv.step` 은 `self._mode`("overworld"/"battle")로 dispatch. battle 진입 =
  move 로 미격파 gym 도착 → party 풀힐 + commit_window 열림. commit_window 중 action 4 = 챔피언 cycle(턴
  소모 X), 그 외 = 챔피언 lock 후 전투. 승리 시 gym_defeated[idx]=True + 챔피언 gain_level + 조건부 evolve.
  종료 = 전 gym 격파 / truncation = steps≥max_steps. obs = 13키 dict(agent_pos·local_patch 5×5·caught·
  gyms_defeated·evolved·in_battle·player/enemy hp·type·level·charge 2키[0-mask]).
- **commit_battles=True** 경로(jax_battle 가 이미 커버). family A(critter) 우선.

## 작업 범위

### 수정 대상 파일 (영향도 표)
| 파일 | 신규/수정 | 영향도 | 설명 |
|---|---|---|---|
| `src/critter_gym/jax_env.py` | 신규 | 상 | 통합 벡터화 env: `JaxEnvState`(overworld state + battle sub-state + mode flag + commit_window + party hp/level/evolve + gym_defeated mask + steps) + `jax_env_step(state, action) → (state, obs, reward, term, trunc)` (`lax.cond` mode dispatch) + `jax_reset(region)`(numpy procgen→state bridge) + `encode_obs(state)`(13키 → flat/dict array, HARMONIZED 호환). import jax 모듈 내부(코어 numpy-only, `__init__` 미import). |
| `tests/test_jax_env_parity.py` | 신규 | 중상 | parity + jit/vmap(`importorskip`): numpy `CritterEnv(commit_battles=True)`와 동일 seed + 동일 action 시퀀스에서 **full-episode trajectory 동일**(obs 키별 + reward + terminated + truncated). 여러 seed(fixed+vary). + jit + vmap batch. |
| `scripts/bench_throughput.py` | 수정 | 저 | full env step numpy vs jax single/vmap steps/s 행 추가(정직 framing). |

### 영향 범위 (import 그래프)
- `jax_env.py`는 **신규·격리** — `jax_overworld`/`jax_battle` 를 합성하되 기존 numpy env(`critter_env.py` 등)
  무수정(포트는 복제, parity 가 등가 보증). 263 tests 무회귀. `__init__` 미import = 코어 numpy-only.

## Step별 계획

1. **pilot (freeze 전, 필수)** — 통합 env step 의 *합성 핵심*(mode dispatch + battle 진입[party heal·
   commit_window]/종료[gym_defeated·evolve] + 종료/truncation)을 functional JAX 프로토타입. 검증: (i) jit,
   (ii) numpy `CritterEnv(commit_battles=True)` 와 full-episode parity(obs 스칼라·reward·term·trunc), (iii)
   가장 fiddly 한 조각(local_patch 5×5 egocentric 인코딩·evolution stat 변경)의 비용. **AC7 분기 결정**:
   (a) obs 전체(local_patch 포함) + evolution 포함 full parity / (b) 스칼라 obs + reward/term parity OK,
   local_patch 또는 evolution 무거우면 *문서화된 후속 분리* / (c) 합성 자체 난항 → reframe.
   pilot 이 (i)/(ii) falsify 시 정직 reframe(goalpost 이동 금지).
2. **state 설계** — `JaxEnvState`: overworld(agent_pos·creature_mask·gym 위치) + gym_defeated mask + party
   (3 creature hp·level·evolved·stat) + battle sub-state(active champion idx·boss hp·turn) + mode flag +
   commit_window flag + steps + done/reward 누적. 고정 크기(party 3·gym ≤ max_gyms).
3. **functional step** — `jax_env_step`: `lax.cond(mode==overworld, ow_branch, battle_branch)`.
   ow_branch = `jax_overworld` 로직 + battle 진입 시 party heal·boss 생성·commit_window. battle_branch =
   commit_window cycle 또는 `jax_battle` step + 승리 시 gym_defeated·gain_level·evolve·mode→overworld.
   terminated = 전 gym 격파, truncated = steps≥max_steps.
4. **obs 인코더** — `encode_obs`: 13키. local_patch 는 agent 중심 (2r+1)² gather(creature/gym mask
   egocentric, `dynamic_slice` + 패딩). battle 시 player/enemy hp·type·level.
5. **parity 테스트** — numpy `CritterEnv(commit_battles=True)` 와 full-episode(여러 seed, fixed+vary) obs
   키별 + reward + term + trunc 동일. greedy/랜덤 정책 고정 시퀀스.
6. **bench + verdict** — full env step numpy vs jax vmap steps/s. feasibility verdict 박제(jit/parity 범위/
   speedup/남은 부분/후속 권고).

**커밋 단위 경계**: (c1) `jax_env.py` state+step+reset / (c2) obs 인코더 + parity 테스트 / (c3) bench +
verdict·report(task-end).

## Freeze 전 pilot 결과 (2026-06-24, scratchpad throwaway)

통합 env step(overworld + commit-battle mode dispatch + battle 진입[heal·commit_window]/종료[gym_defeated·
evolution] + 종료/truncation)을 functional JAX 프로토타입해 핵심 risk R1(합성)을 검증. 실측:
- **(i) jit = OK.**
- **(ii) full-episode parity = OK** — vary 차트 12 episode, **0 mismatch**(reward + terminated + truncated +
  스칼라 obs: agent_pos·caught·gyms_defeated·evolved·in_battle·player/enemy hp·type·level). **evolution 포함**
  (챔피언이 gym1 승리 후 진화한 stat 으로 gym2 전투 — parity 유지).
- **(iii) throughput (CPU)** — numpy 125k/s · **jax vmap 9.0M/s(b=4096) = 73×**(b=1024 52×). full-episode 은
  mode dispatch + per-env 제어흐름 발산으로 슬라이스(overworld 186×·battle 1047×)보다 배율 낮으나 여전히 강함.
- **pilot 이 composition 버그 2건 freeze 전 포착**: ① jnp 테이블 인덱싱(traced idx → numpy 배열 인덱싱 불가,
  jnp 변환) ② **battle 중 NOOP(5)/SWITCH(4) 액션 시 champion 미공격**(numpy 는 action 5=item99 wasted·4=
  commit-mode switch ignored → champion 공격 안 하고 boss 만 타격; 초안은 항상 champion 공격 가정). `action<4`
  게이트로 교정 → 0 mismatch.
- **판정 = AC7 분기 (a) 목표**: composition + evolution + 스칼라 obs + reward + term/trunc parity 완벽 입증
  (R1 해결). **local_patch(5×5 egocentric)만 pilot 미포함** = 유일한 미검증 조각 → 구현 시 full obs(local_patch
  포함) 목표, 동적 슬라이스 parity 가 무거우면 **(b)로 local_patch 후속 분리**(정직 라벨). reframe(c) 불필요.

## 검증 방법

- `pytest -q` — 263 무회귀 + 신규 env parity(jax 환경) green. CI(numpy-only) `importorskip` skip.
- `mypy src` / `ruff check .` / `python -m build` clean.
- parity = full-episode trajectory(obs 키별·reward·term·trunc) 동일. fixed + vary seed.
- bench 수동 — full env step numpy vs jax(vmap) steps/s 기록(단일 측정=헤드라인 아님).

## 리스크

- **R1 (핵심)**: mode dispatch + battle 진입/종료의 상태 전이가 `lax.cond` 로 합성하기 복잡(가변 길이 battle,
   commit_window, evolution stat 변경) → pilot 으로 freeze 전 검증, 과대 시 scope 축소(AC7 b).
- **R2**: local_patch egocentric 인코딩(동적 슬라이스+패딩)이 numpy 와 정확 일치 어려움 → parity 가드, 무거우면
   후속 분리.
- **R3**: evolution(승리 시 stat 변경)이 parity 에 필요 — 포함 vs 후속 은 pilot 결정.
- **R4**: family A(critter)만. forage/duel/muster 통합은 후속(jax_overworld 가 A/B 커버하나 full env 는 A 우선).
- **R5 (이니셔티브)**: 난이도(A) 작업이 env 메커닉 바꾸면 재포트 — DESIGN §4 가 M4 를 "spec 안정 후"로 게이트.

## Acceptance Criteria (G1 통과 시 freeze)

> 원칙: 성능 아닌 **측정 + 정직 feasibility verdict**로 freeze. pilot 이 가정 falsify 시 정직 reframe.
> 사전약정 결정규칙(AC7)으로 사후 편향 차단.

- **AC1**: `src/critter_gym/jax_env.py` 신규 — 통합 env step `(state, action) → (state, obs, reward, term,
  trunc)` 이 overworld + commit-battle 을 `lax.cond` mode dispatch 로 합성하고 `jax.jit` 컴파일 성공.
  (불가 판명 시 그 사실 입증=충족.)
- **AC2**: `tests/test_jax_env_parity.py` — numpy `CritterEnv(commit_battles=True)`와 동일 seed + 동일
  action 시퀀스에서 **full-episode trajectory 동일**(parity 범위는 AC7 분기로 확정: 최소 reward·terminated·
  truncated·스칼라 obs). fixed + vary seed. `importorskip("jax")` CI numpy-only 보존.
- **AC3**: `vmap` 으로 batched full-episode rollout 이 동작(leading batch dim 보존) — RL 루프 소비 가능 형태.
- **AC4**: `scripts/bench_throughput.py` 에 full env step numpy vs jax single/vmap steps/s 행 추가, 정직
  framing(이득=vmap) 유지.
- **AC5**: 회귀 0 — 기존 263 tests green(jax 미설치 CI 포함), mypy/ruff/build clean. 기존 numpy env 무변경
  (포트는 격리 복제). 코어 numpy-only.
- **AC6**: **feasibility verdict** report 박제 — (i) jit OK/NG (ii) parity 범위·OK/NG (iii) vmap speedup 방향
  (iv) 포트 범위(family A commit-mode; obs/evolution 포함 여부; 미포함분) (v) 후속 권고. speedup 음수도 정직.
- **AC7 (사전약정 결정규칙)**: pilot 이 **분기 (a) 목표 확정** — composition + evolution + 스칼라 obs +
  reward + term/trunc parity 완벽 입증(R1 해결). 구현 시 **full obs(local_patch 포함) 목표**; local_patch
  egocentric 동적 슬라이스 parity 가 무거우면 **(b) local_patch 만 후속 분리**(정직 라벨, 스칼라 obs+reward+
  term parity 는 충족). (c reframe 미발동.) 어느 분기든 정직 보고가 DoD.
- **AC8**: 툴체인 green (ruff ∧ mypy src ∧ pytest ∧ build).
