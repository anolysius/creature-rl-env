---
slug: jax-hotpath-foundation
initiative: jax-throughput
status: active
started: 2026-06-24
acceptance_freeze: true
mode: standard
domains: [rl-env, perf]
scope_paths:
  - src/critter_gym/jax_overworld.py
  - scripts/bench_throughput.py
  - tests/test_jax_parity.py
  - tests/test_throughput.py
  - pyproject.toml
extracted_to: []
supersedes: []
---

# JAX 핫패스 포트 — 토대 + de-risk (overworld 슬라이스)

> 작성일: 2026-06-24 | 상태: 계획 | 이니셔티브: jax-throughput (M4 착수)

## 목표

M4(Throughput/JAX)를 **de-risk staging**으로 착수한다. 전체 포트를 한 번에 하지 않고, 핵심 미지수
두 개 — **(1) env step 이 functional JAX 로 jit 가능한가, (2) vmap 배치로 numpy 대비 유의미하게
빨라지는가** — 를 *가장 단순한 슬라이스(overworld step, battle 제외)*로 최소비용 입증하고, **정직한
feasibility verdict**를 산출한다. 성능 헤드라인이 아니라 *측정 + 정직 feasibility 보고*가 산출물.

전진 EC: **M4-EC1**(핫패스 포팅 — overworld 부분 *토대*, 완성 아님) + **M4-EC2**(numpy↔JAX parity *토대*).
M4-EC3(≥10M steps/s GPU)는 본 task 범위 밖(GPU·full-env 필요) — 단 vmap CPU speedup 비율로 *방향*만 측정.

## 선행 조건

- (B) 이니셔티브 종결 (#32–39, 전부 main). env 코어 안정 (199 tests).
- M4 milestone override 정합성: (B)가 M5 enabler 를 M3 release EC 보다 먼저 한 선례와 동일
  (functional-readiness-first; 공개는 맨 마지막). INITIATIVE.md 에 박제.
- 개발 `.venv` 에 `jax` (CPU) 설치 필요 — pilot/TDD 실행용. **CI 는 numpy-only 유지**(parity 테스트는
  `importorskip("jax")`, bench script 의 jax 부분은 `[jax]` extra).

## 작업 범위

### 수정 대상 파일 (영향도 표)
| 파일 | 신규/수정 | 영향도 | 설명 |
|---|---|---|---|
| `src/critter_gym/jax_overworld.py` | 신규 | 중 | overworld step 의 functional JAX 포트: flat state pytree(`OverworldState`) + `jit`/`vmap` 가능한 순수함수 `jax_overworld_step`. import jax 는 모듈 내부(코어 import 무영향). family A(action-catch)+B(contact-collect) 분기를 `jnp.where`/`lax.cond`로. **battle 진입은 flag 반환까지만, battle 자체는 미포트(후속 task).** |
| `scripts/bench_throughput.py` | 신규 | 저 | throughput 벤치 하네스: numpy `CritterEnv`/`ForageEnv` overworld-only steps/s 베이스라인 측정 + (jax 있으면) `jax_overworld_step` 단일/vmap(batch) steps/s. 정직 출력(환경·batch·기기 명시). numpy 부분 CI-safe. |
| `tests/test_jax_parity.py` | 신규 | 중 | parity + jittability 가드(`importorskip("jax")`): 동일 seed+동일 action 시퀀스에서 JAX overworld 슬라이스가 numpy overworld 와 **동일 trajectory**(agent_pos·caught·reward·battle-진입 flag) 산출. + `jit` 컴파일 성공 + `vmap` batch 형상 가드. |
| `tests/test_throughput.py` | 수정 | 저 | 기존 floor 가드 유지(무회귀). overworld-only 측정 헬퍼를 bench 와 공유하도록 소폭 정리(선택). 회귀 0. |
| `pyproject.toml` | 수정 | 저 | `[project.optional-dependencies]`에 `jax = ["jax>=0.4"]` extra 추가(rl/viz/render 와 동일 격리 패턴). 코어 deps 무변경(numpy-only 유지). |

### 영향 범위 (import 그래프)
- `jax_overworld.py`는 **신규·격리** — 기존 `CritterEnv`/`ForageEnv` 를 수정하지 않음(포트는 별도 함수로
  복제, parity 가 등가 보증). 따라서 family A/B/C/D 런타임·obs·action 무영향, 199 tests 무회귀.
- `pyproject` extra 추가는 코어 의존성 그래프 무변경 — `pip install critter_gym` 기본 설치 numpy-only.
- bench script 는 소비자(아무도 import 안 함) — 회귀 표면 0.

## Step별 계획

1. **pilot (freeze 전, 필수)** — `.venv`에 jax(CPU) 설치. overworld step 의 *최소 슬라이스*(move+clip,
   family A catch / family B contact-collect, battle 진입 trigger flag)를 functional JAX 로 1-family
   프로토타입. 검증 질문: (i) `jax.jit`이 실제로 컴파일되는가, (ii) numpy overworld 와 동일 seed 에서
   trajectory 가 맞는가(소규모 수동 대조), (iii) vmap(batch=1k) CPU steps/s 가 numpy 대비 어느 방향인가.
   **pilot 이 (i) 또는 (ii)를 falsify 하면 → 정직 reframe**(예: "overworld 도 dict 구조상 functional
   재작성 비용 큼" / "CPU vmap 은 numpy 대비 이득 없음, GPU 필요" 를 verdict 로). goalpost 이동 금지.
2. **state 설계** — `OverworldState`(NamedTuple/pytree): agent_pos(2,), creature_mask(grid,grid) 또는
   creature 좌표 배열+alive mask, caught, gym 위치·defeated mask, steps, rng key. dict→array 변환이
   핵심 작업. seed→state 생성도 JAX(또는 numpy 생성 후 device_put — parity 만 맞으면 됨).
3. **functional step** — `jax_overworld_step(state, action) -> (state, reward, battle_entered)`.
   분기는 `jnp.where`/`lax.select`/`lax.cond`. family A/B 차이(catch action vs contact)는 정적 flag 로
   두 함수 또는 `lax.cond`.
4. **parity 테스트** — numpy overworld(기존 `_step_overworld` 경로를 battle 전까지 구동)와 JAX 슬라이스가
   동일 seed+동일 action 시퀀스(랜덤 policy 고정 rng)에서 trajectory 동일. agent_pos·caught·reward·
   battle-진입 step 일치. (battle 진입 후는 비교 범위 밖 — 슬라이스 경계 명시.)
5. **bench 하네스** — `scripts/bench_throughput.py`: numpy overworld steps/s + jax 단일/vmap steps/s,
   정직 출력. test_throughput.py 무회귀 확인.
6. **verdict 작성** — feasibility 를 report 에 박제: jit OK/NG, parity OK/NG, CPU vmap speedup 비율(방향),
   battle 포트 난이도 예측, 후속 task 권고(양성→jax-battle-port / 음성→reframe).

**커밋 단위 경계** (L1 plan-reviewer SUGGEST 반영): (c1) pyproject `[jax]` extra + bench 하네스 numpy
베이스라인 부분 / (c2) `jax_overworld.py` state+functional step (Step 2–3) / (c3) parity 테스트 + bench
jax 부분 (Step 4–5) / (c4) verdict·report (Step 6, task-end). pilot(Step 1)은 커밋 전 검증이라 별도 산출 없음.

## Freeze 전 pilot 결과 (2026-06-24, scratchpad throwaway)

overworld 슬라이스(move+catch/contact, family A·B, battle 제외)를 functional JAX 로 프로토타입해 AC7
분기를 결정. 실측:
- **(i) jit 컴파일 = OK** (family A·B 둘 다).
- **(ii) parity = OK** — 1200 checks(200 step × 2 family × 3 seed), **0 mismatch**. numpy overworld 와
  trajectory(agent_pos·caught·reward·battle진입 flag) 정확 동치.
- **(iii) throughput (CPU)** — numpy single 187k/s · jax **single(jit) 44k/s = 0.24×**(단일은 dispatch
  오버헤드로 numpy보다 느림) · jax **vmap 13.4M(b=1024) → 17.0M(b=4096) → 19.6M(b=16384) = 71~104×**.
- **판정 = AC7 분기 (a)** (jit OK ∧ parity 맞음) → 본 scope 진행, reframe 불필요.
- **정직 발견 (구현 반영)**: ① JAX 이득은 **전적으로 vmap 벡터화** — 단일-env 는 더 느림(bench·verdict 가
  반드시 이 framing 으로 보고). ② jax 0.4.30 + py3.9 는 x64 비활성 → int64 가 int32 로 truncate(경고);
  env 값 범위(caught≤num_creatures, steps≤max_steps)에선 무해하나 구현 시 **x64 enable 또는 int32+bound
  문서화** 필요. ③ CPU vmap 만으로 19.6M/s = M4-EC3 의 ≥10M GPU 목표를 CPU 에서 이미 초과(GPU 는 본 task
  범위 밖이나 방향 매우 양성).

## 검증 방법

- `pytest -q`(또는 `python -m pytest`) — 199 무회귀 + 신규 parity 테스트(jax 설치 환경) green.
  CI(numpy-only) 에선 parity 테스트 `importorskip` skip, 코어 그대로.
- `mypy src`(22 모듈) / `ruff check .` / `python -m build` clean.
- bench script 수동 실행 — numpy vs jax(vmap) steps/s 수치 기록(report). **단일 측정이라 헤드라인 아님.**
- parity = trajectory 동일성(determinism 테스트 패턴 차용). 수치 동치가 가드.

## 리스크

- **R1 (핵심)**: overworld 도 `_creatures`(set)·`_gym_tiles`(dict) 구조라 functional 재작성이 예상보다
   클 수 있음 → pilot 으로 freeze 전 검증, falsify 시 reframe.
- **R2**: CPU 에서 vmap 이 numpy 대비 이득이 작거나 음수일 수 있음(JAX 이득은 주로 GPU·대배치). →
   verdict 는 *방향*만 주장, "GPU 에서 검증 필요"를 정직 caveat 로. M4-EC3 은 본 task 범위 밖.
- **R3**: jax 설치가 `.venv` 환경에 무겁/플랫폼 이슈(darwin). → CPU-only jax, CI 무영향(importorskip).
- **R4 (이니셔티브)**: 난이도 스케일 작업이 후에 env 메커닉 바꾸면 재포트 필요 → 본 task 는 안정 overworld
   코어만 포트해 최소화하나 0 아님. freeze 시 박제.
- **R5**: battle 미포트라 "핫패스 포트"가 부분적 → EC1 *토대*로 정직 라벨, 완성 아님 명시.

## Acceptance Criteria (G1 통과 시 freeze)

> 원칙: 성능 수치가 아니라 **측정 + 정직 feasibility 보고**로 freeze. pilot 이 가정 falsify 하면 정직 reframe.
> 사전약정 결정규칙으로 사후 편향 차단.

- **AC1**: `src/critter_gym/jax_overworld.py` 신규 — overworld step(move+catch/contact-collect+battle
  진입 flag, battle 제외)의 functional JAX 포트가 family A·B 를 커버하고 `jax.jit` 컴파일 성공.
  (jit 이 불가하면 → AC 충족 = 그 사실을 *입증*하고 verdict 에 정직 박제. 헤드라인 아닌 측정.)
- **AC2**: `tests/test_jax_parity.py` — 동일 seed + 동일 action 시퀀스에서 JAX overworld 슬라이스가
  numpy overworld 와 trajectory(agent_pos·caught·reward·battle-진입 step) **동일**. battle 진입 전까지
  범위 명시. `importorskip("jax")` 로 CI numpy-only 보존.
- **AC3**: `scripts/bench_throughput.py` — numpy overworld steps/s 베이스라인 + (jax 환경) 단일/vmap
  steps/s 를 정직 출력(환경·batch·기기 라벨). 수치는 report 에 기록(단일 측정 = 헤드라인 아님).
- **AC4**: `pyproject.toml` 에 `[jax]` extra 추가, 코어 deps numpy-only 유지. `pip install` 기본은
  numpy-only(무회귀).
- **AC5**: 회귀 0 — 기존 199 tests green(jax 미설치 CI 포함), mypy/ruff/build clean. 기존 `CritterEnv`/
  `ForageEnv` 런타임·obs·action 무변경(포트는 격리 복제).
- **AC6**: **feasibility verdict** report 에 박제 — (i) jit OK/NG (ii) parity OK/NG (iii) CPU vmap
  speedup 방향·비율 (iv) battle 포트 난이도 예측 (v) 후속 권고(양성→jax-battle-port / 음성→reframe).
  사전약정: speedup 측정값이 어떻든 *측정 자체*가 산출물, 음수/이득없음도 정직 결론.
- **AC7 (사전약정 결정규칙)**: pilot 결과로 freeze 분기 — (a) jit OK ∧ parity 맞음 → 본 scope 진행
  / (b) jit 가능하나 parity 미세 불일치 다수 → 슬라이스 더 축소(move-only) 후 진행 / (c) overworld
  functional 재작성이 큰 작업으로 판명 → scope 를 "feasibility 분석 + 최소 move-only 프로토타입 +
  정직 verdict"로 reframe(전체 포트 비용을 정직 보고). 어느 분기든 정직 보고가 DoD.
