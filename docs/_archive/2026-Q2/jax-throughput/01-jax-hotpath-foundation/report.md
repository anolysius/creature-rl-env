---
slug: jax-hotpath-foundation
initiative: jax-throughput
status: completed
ended: 2026-06-24
extracted_to:
  - docs/explanation/jax-throughput.md
  - docs/explanation/competitive-analysis.md
  - DESIGN.md
changelog_entry: docs/CHANGELOG.md
---

# JAX 핫패스 포트 — 토대 + de-risk (overworld 슬라이스) · 결과 보고서

M4(Throughput/JAX) 착수. (B) 전이 이니셔티브 종결 후 피벗. env step 이 Python dict/mutable 상태라 직접
jit 불가 → **overworld step(battle 제외)만 functional JAX 로 포트**해 "jit 가능한가 + vmap 으로 빨라지는가"를
최소비용 de-risk 하고 정직한 feasibility verdict 를 산출.

## 요약 (수치 표)

| 지표 | 값 | 비고 |
|---|---|---|
| jit 컴파일 | ✅ family A·B | `test_jit_compiles` |
| parity (numpy↔JAX) | ✅ **0 mismatch** | 실제 `CritterEnv`/`ForageEnv` overworld 전이 대비, 8 케이스 + vmap + invariant |
| numpy overworld | ~410k steps/s | baseline (단일 머신, single run) |
| jax single (jit) | ~55k steps/s | **0.13× = numpy 보다 느림** (단일은 dispatch 오버헤드) |
| jax vmap b=1024 | ~26.5M steps/s | 65× numpy |
| jax vmap b=4096 | ~55.8M steps/s | 136× numpy |
| jax vmap b=16384 | ~76.5M steps/s | **186× numpy** |
| 테스트 | 199 → **210** (+11, skip 2) | 회귀 0 |
| mypy / ruff / build | clean (23 files) | — |

## 계획 대비 실적 (✅/⚠️/❌)

- ✅ **AC1** `src/critter_gym/jax_overworld.py` — overworld step(move+catch/contact-collect+battle 진입 flag)
  functional JAX 포트, family A·B, `jax.jit` 컴파일 성공.
- ✅ **AC2** `tests/test_jax_parity.py` — 동일 seed+action → 실제 numpy env 와 trajectory(agent_pos·caught·
  reward·battle진입 step) 동일, 0 mismatch. `importorskip("jax")` CI 격리.
- ✅ **AC3** `scripts/bench_throughput.py` — numpy+jax single+jax vmap steps/s 정직 출력("이득은 vmap, single 은
  느림" framing + "direction, not a headline" 명시).
- ✅ **AC4** `pyproject.toml` `[jax]` extra (jax<0.4.31 = py3.9 마지막 라인) + mypy override. 코어 numpy-only 유지.
- ✅ **AC5** 회귀 0 — 210 passed(199 무변경 + 11 신규), 기존 `CritterEnv`/`ForageEnv` 무변경(포트는 격리 복제),
  mypy/ruff/build clean.
- ✅ **AC6** feasibility verdict 박제 (아래 §feasibility verdict).
- ✅ **AC7** pilot 분기 **(a)** 확정 (jit OK ∧ parity 맞음) → 본 scope 진행, reframe 불필요.
- ✅ **AC8** 툴체인 green (ruff ∧ mypy src ∧ pytest ∧ build).

## ⭐ Feasibility verdict (AC6 — 본 task 의 핵심 산출)

1. **(i) jit = OK.** overworld 전이가 flat array pytree(`OverworldState`) + `jnp.where`/`.at[].set` 로 깔끔히
   functional 화됨. family 분기(A=CATCH action / B=contact)는 static Python bool 로 branch-free 컴파일.
   dict→array 변환이 핵심 작업이었으나 overworld 는 무난(battle 이 진짜 난관 — 후속).
2. **(ii) parity = OK.** 실제 env(자기참조 toy 아님) 대비 0 mismatch. 동일 seed → 동일 trajectory 재현성(북극성 #3)
   유지 입증. procgen 은 numpy 그대로(reset 당 1회, 핫패스 아님), step 만 JAX = 올바른 경계.
3. **(iii) speedup 방향·비율 = 강한 양성, 단 vmap 한정.** CPU 에서 **단일-env jit 은 numpy 보다 느림**(0.13×,
   dispatch 오버헤드). 이득은 **전적으로 vmap 벡터화**: b=1024 65× → b=16384 **186×(76.5M steps/s)**.
   CPU 만으로 M4-EC3 의 ≥10M steps/s "GPU" 목표를 7.6× 초과 — GPU 는 본 task 범위 밖이나 방향 매우 양성.
   **정직 framing(헤드라인 금지)**: "JAX 가 빠르다"가 아니라 "JAX 가 *벡터화하면* 빠르다". 단일 env 교체로는 손해.
4. **(iv) battle 포트 난이도 예측 = 중상.** battle(`battle.py` 234줄)은 턴 순서·타입표·스위치·commit-window·
   scripted 상대 등 branchy 상태기계라 overworld 보다 functional 화 비용 큼. `lax.cond`/`lax.scan` + 고정 길이
   파티 배열 필요. 단 overworld 가 패턴(state pytree·parity 하네스·bench)을 깔아둬서 후속이 이 위에 빌드 가능.
5. **(v) 후속 권고 = 양성 → `jax-battle-port`.** verdict (a) 이므로 battle 슬라이스 functional 포트 + parity 확장이
   다음 task. 그 후 `jax-env-integration`(Gymnasium VectorEnv wrapping) + `vectorized-bench`(M4-EC3 GPU 측정).

## 정직 caveat (freeze 시 박제, 유지)

- speedup 은 **단일 머신·single run·CPU** — *방향*이지 튜닝된 벤치 아님. GPU 미측정(범위 밖).
- jax 0.4.30 + py3.9 는 x64 비활성 → int64 가 int32 로 truncate(경고). env 값 범위(pos<grid, caught≤
  num_creatures, steps≤max_steps)에서 무해 → 포트가 **의도적으로 int32** 사용(주석·docstring 명시). x64 필요해지면
  후속에서 enable.
- **battle 미포트** = "핫패스 포트"는 부분적 → M4-EC1 *토대*(완성 아님). overworld 만 vectorized.
- **이니셔티브 리스크 R4**: 난이도 스케일 작업이 후에 env 메커닉(스타터·보스·reward) 바꾸면 포트 재작업 필요.
  본 task 는 안정 overworld 코어만 포트해 최소화하나 0 아님.

## 변경 파일 상세

| 파일 | 신규/수정 | 내용 |
|---|---|---|
| `src/critter_gym/jax_overworld.py` | 신규 | `OverworldState`(pytree) + `overworld_step`(family A/B, branch-free) + `state_from_region`(numpy Region→JAX) + `make_step_fn`(jit). __init__ 미import = 코어 numpy-only 보존. |
| `tests/test_jax_parity.py` | 신규 | `importorskip("jax")` + 실제 env 대비 parity(2 family × 4 seed) + jit + vmap shape + caught invariant = 11 테스트. |
| `scripts/bench_throughput.py` | 신규 | numpy overworld baseline + jax single/vmap, 정직 framing, `--quick`. JAX 행은 ImportError graceful skip. |
| `pyproject.toml` | 수정 | `[jax]` optional extra(jax/jaxlib <0.4.31) + mypy `jax.*`/`jaxlib.*` ignore_missing_imports. 코어 deps 무변경. |

## 흡수처 매핑 (extracted_to)

- `docs/explanation/jax-throughput.md` — **신규** JAX throughput 스레드 living narrative(genre-generalization.md
  와 동형: 왜 JAX·무엇을 측정·어디 섰나). 본 task feasibility verdict 가 시작점.
- `docs/explanation/competitive-analysis.md` — 갭 register "competitively fast" 행 갱신(JAX de-risked).
- `DESIGN.md` §4 — throughput 목표에 실측 CPU vmap 방향(76.5M steps/s, 186×) 기록.

## 타입 체크 / 빌드 결과
mypy src: Success(23 files) · ruff: All checks passed · build: wheel+sdist OK · pytest: 210 passed, 2 skipped.
