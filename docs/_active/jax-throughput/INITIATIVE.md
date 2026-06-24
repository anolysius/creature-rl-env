# Initiative: jax-throughput

> CritterGym 핫패스의 **JAX 포트** — 속도=채택 게이트(Craftax 교훈). DESIGN.md §4 throughput 목표
> + milestones.md **M4** (Throughput/JAX) 를 담는 멀티-task 묶음.
>
> **마일스톤 SSOT**: [roadmap.md](../../explanation/roadmap.md) (왜) · [milestones.md](../../reference/milestones.md) (사실).
> **활성 마일스톤: M4** (override — (B) 이니셔티브가 M5 enabler 를 M3 release EC 보다 먼저 했던 것과 동일한
> "functional-readiness-first" 선례. 공개[M3-EC4/EC5]는 맨 마지막, 기능 준비+비교우위가 먼저).

## 왜 지금 / 왜 JAX

- **속도 = 채택 게이트**. peer(Procgen/Craftax/XLand)는 JAX-GPU 로 ≫1M steps/s. 우리는 numpy CPU
  (~266k steps/s/core, M1-EC4). 측정이 아무리 영리해도 throughput 열위면 연구자가 안 씀 (competitive-analysis 갭 register #1줄).
- **force-multiplier**. 직전 (B) 7 task 전부 numpy run(50k~500k×multi-run = 5~40분)이 병목이었음.
  JAX vmap 포트는 후속 RL 실험(난이도 스케일·family 확장·multi-run learnability)을 10~100× 싸게 만듦.
- **deterministic·정직보고 쉬움**. throughput 은 측정값이 명확 — (B)에서 길게 겪은 "noisy-RL 결론" 함정이 적음.

## 핵심 리스크 (이니셔티브 전체)

env step 이 Python dict(`self._creatures` 위치-키 set/dict, `self._gym_tiles`)·mutable numpy 상태·Python
제어흐름 중심이라 **직접 jit 불가**. JAX 포트는 flat state pytree + `lax.cond`/`jnp.where` 기반 **functional
재작성**이 필요 — 큰 작업. 따라서 한 번에 포트하지 않고 **de-risk staging**: overworld 슬라이스 → battle → 통합.

## 목표 (M4 EC)
- **EC1**: 핫패스 JAX 포팅 (spec 안정 후 — DESIGN §4)
- **EC2**: numpy ↔ JAX **parity** (동일 seed → 동일 trajectory)
- **EC3**: ≥10M steps/s GPU (DESIGN §4 목표; vmap 배치)

## 북극성 (CLAUDE.md 종속)
1. 모든 기능은 *능력 측정* 복무 — 게임 재미 아님.
2. 리워드 verifiable(RLVR) — JAX 포트도 동일 boolean subgoal 보존.
3. procgen + train/test seed split 비협상 — JAX 포트가 seed→trajectory 재현성 깨면 안 됨 (parity 가 가드).
4. fast / vectorizable — 본 이니셔티브의 존재 이유.
5. seeded·pinned reproducibility.

## Task 목록
| # | slug | 상태 | 한 줄 |
|---|---|---|---|
| 1 | `jax-hotpath-foundation` | ✅ done (→ `_archive/2026-Q2/jax-throughput/01-jax-hotpath-foundation/`) | M4 착수 de-risk: overworld 슬라이스(battle 제외) functional JAX 포트 + numpy↔JAX **parity 0 mismatch** + throughput 벤치. **실측**(CPU·single run): jit OK(family A·B)/jax single 0.13×(더 느림)/**jax vmap 186×(76.5M steps/s, b=16384)** = M4-EC3 ≥10M GPU 목표 CPU서 7.6× 초과. **정직 framing: 이득은 vmap 벡터화 한정**. **feasibility verdict=양성→`jax-battle-port`**. battle 미포트=M4-EC1 *토대*(부분). 199→210(+11, 회귀 0), mypy(23)/ruff/build clean. DESIGN §4 + 신규 jax-throughput.md + competitive-analysis 갱신 |

(이후 task 는 /task-start 로 append — 예정: `jax-battle-port`, `jax-env-integration`, `vectorized-bench`)

## 다음 task
**task 1 종결 — feasibility verdict 양성**(jit OK + parity 0 + vmap 186×). 핵심 미지수 2개(jit 가능성·vmap
speedup) 모두 양성 입증 → M4 포트가 실재함.
- **다음(권장) = `jax-battle-port`** — battle sub-MDP(`battle.py` 234줄: 턴순서·타입표·스위치·commit-window·
  scripted 상대)를 functional JAX(`lax.cond`/`lax.scan` + 고정길이 파티 배열)로 포트 + parity 확장. 핫패스의
  *어려운 절반*. overworld 가 깐 패턴(state pytree·parity 하네스·bench) 위에 빌드.
- 이후: `jax-env-integration`(batched Gymnasium VectorEnv surface — RL 루프가 실제 소비) → `vectorized-bench`
  (M4-EC3 GPU 측정; CPU vmap 은 이미 ≥10M 통과).
- **spec-stability watch**: 난이도 스케일(A) 작업이 env 메커닉 바꾸면 포트 재작업(R4). DESIGN §4 가 M4 를 "spec
  안정 후"로 게이트 — battle 포트 전 메커닉 변경 계획 있으면 순서 재검토.

**caveat (freeze 시 박제)**: 난이도 스케일 작업이 후에 env 메커닉(스타터·보스·reward 경제)을 바꾸면 JAX 포트
재작업 필요. 본 task 는 *안정된 overworld 코어*만 포트해 이 위험을 최소화하나 0 은 아님.
