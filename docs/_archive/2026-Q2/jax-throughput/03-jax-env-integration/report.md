---
slug: jax-env-integration
initiative: jax-throughput
status: completed
ended: 2026-06-24
extracted_to:
  - docs/explanation/jax-throughput.md
  - docs/explanation/competitive-analysis.md
changelog_entry: docs/CHANGELOG.md
---

# JAX env 통합 — 벡터화 full-episode env step · 결과 보고서

`jax_overworld` + `jax_battle`(commit-mode)를 **하나의 벡터화 full-episode env step**으로 합성. RL 루프가
JAX 엔진을 실제 소비 가능한 surface 산출. numpy `CritterEnv(commit_battles=True)`(family A)와 full parity.

## 요약 (수치 표)

| 지표 | 값 | 비고 |
|---|---|---|
| jit 컴파일 | ✅ | `test_jit_compiles` |
| full parity (numpy↔JAX) | ✅ **0 mismatch** | 실제 `CritterEnv(commit_battles=True)` 대비, **obs 13키 전체(local_patch 포함) + reward + terminated + truncated** |
| parity 커버리지 | random + gym-clearing 정책, fixed + vary 차트 | 종료(전 gym 격파)·evolution·battle 진입/종료 exercise |
| numpy full env | ~130k steps/s | baseline |
| jax vmap b=1024 | ~4.4M steps/s | 34× numpy |
| jax vmap b=4096 | ~9.0M steps/s | **73× numpy**(pilot) |
| 테스트 | 263 → **281** (+18, skip 2) | 회귀 0 |
| mypy / ruff / build | clean (25 files) | — |

## 계획 대비 실적 (✅/⚠️/❌)

- ✅ **AC1** `src/critter_gym/jax_env.py` — `jax_env_step(state, action) → (state, obs, reward, term, trunc)`,
  overworld + commit-battle `lax.cond` mode dispatch, `jax.jit` 컴파일.
- ✅ **AC2** `tests/test_jax_env_parity.py` — 실제 numpy `CritterEnv(commit_battles=True)`와 full-episode
  trajectory 동일(**obs 13키 전체 + reward + terminated + truncated**), fixed + vary, random + gym-clearing
  정책. `importorskip` CI 격리.
- ✅ **AC3** `vmap` batched full-episode rollout 동작(leading batch dim 보존) — RL 루프 소비 형태.
- ✅ **AC4** `scripts/bench_throughput.py` — full env numpy vs jax vmap 행 추가, 정직 framing.
- ✅ **AC5** 회귀 0 — 281 passed(263 무변경 + 18 신규), 기존 numpy env/`jax_overworld`/`jax_battle` 무변경
  (합성은 복제), mypy/ruff/build clean, 코어 numpy-only.
- ✅ **AC6** feasibility verdict 박제 (아래).
- ✅ **AC7** pilot 분기 **(a) 완성** — full obs(local_patch 포함) parity 달성. (b 후속 분리 불필요.)
- ✅ **AC8** 툴체인 green.

## ⭐ Feasibility verdict (AC6)

1. **(i) jit = OK.** full-episode 합성이 `lax.cond` 2단(mode dispatch + commit-window cycle/fight)으로 깔끔히
   functional 화. 가변 길이 battle도 "한 env step = overworld 1 또는 battle 1턴" 모델로 자연 수용.
2. **(ii) full parity = OK.** 실제 `CritterEnv(commit_battles=True)` 대비 **obs 13키 전체(local_patch egocentric
   포함) + reward + terminated + truncated** 0 mismatch — random + gym-clearing 정책, fixed + vary 차트.
   pilot 미검증이던 local_patch 까지 달성 = **분기 (a) 완성**. 재현성(북극성 #3) 보존.
3. **(iii) speedup = 양성(vmap), 슬라이스보다 낮음.** numpy 130k/s → jax vmap **34×(b=1024) / 73×(b=4096)**.
   full-episode 은 per-env 제어흐름 발산(어떤 env는 battle, 어떤 env는 overworld)으로 슬라이스(overworld 186×·
   battle 1047×)보다 배율 낮음 — *정직 보고*. 그래도 large win, RL 루프가 이 surface 를 소비.
4. **(iv) 포트 범위.** family A(critter) commit-mode, full obs. **미포함**: family B/C/D, non-commit full
   battle(switch/item/multi-creature, = `jax-battle-full`).
5. **(v) 후속 권고.** 핫패스가 실사용 surface 로 묶임 → **`vectorized-bench`**(M4-EC3 GPU 측정; CPU vmap 은
   슬라이스에서 이미 ≥10M) 또는 **`jax-battle-full`**(non-commit 완전성) 또는 RL 학습 루프 데모(JAX 엔진 실소비).

## 정직성 — pilot + L3 가 함께 버그 3건 포착

- **pilot(freeze 전) 2건**: ① jnp 테이블 인덱싱(traced idx) ② **battle 중 NOOP/SWITCH 시 champion 미공격**
  (numpy item99/switch-ignored = wasted turn; 초안은 항상 champion 공격 가정).
- **구현 중 1건(잠재)**: 가변 gym 수 — pilot 은 고정 3으로 운 좋게 통과(random rollout 이 전 gym 격파 안 함).
  `gym_active` 마스크로 정직 수정 + 결정론 종료 테스트 추가.
- **L3 reviewer 1건**: `truncated` 의미 — numpy 는 `steps≥max_steps` 를 terminated 와 **독립** 계산(둘 다 True
  가능: 마지막 gym 을 정확히 max_steps 째 격파). 초안은 `(~terminated) & …` 로 억제 → 희귀 edge parity 갭.
  numpy 정확 미러링으로 수정 + 경계 edge 테스트 추가. **다층 검증(pilot + multi-config parity + adversarial
  L3)이 단일 검증이 놓친 edge 를 잡은 사례.**

## 정직 caveat

- CPU·single run — *방향*, GPU 미측정. full-episode vmap 배율(34–73×)은 슬라이스보다 낮음(제어흐름 발산).
- family A commit-mode 만 — B/C/D·non-commit full battle 미포함.
- 이니셔티브 R5: 난이도(A) 작업이 env 메커닉 바꾸면 재포트 — DESIGN §4 가 M4 를 "spec 안정 후"로 게이트.

## 변경 파일 상세

| 파일 | 신규/수정 | 내용 |
|---|---|---|
| `src/critter_gym/jax_env.py` | 신규 | `JaxEnvState` pytree + `jax_env_step`(lax.cond mode dispatch, overworld/battle branch) + `jax_reset`(numpy Region bridge, gym_active 패딩) + `encode_obs`(13키, local_patch egocentric pad+dynamic_slice) + `make_env_step`(jit). __init__ 미import = 코어 numpy-only. |
| `tests/test_jax_env_parity.py` | 신규 | `importorskip` + 실제 `CritterEnv(commit)` 대비 full-episode parity(random + gym-clearing, fixed + vary) + 종료 마스크 + truncated 독립성 edge + jit + vmap = 18 테스트. |
| `scripts/bench_throughput.py` | 수정 | full env numpy vs jax vmap 행 추가, 정직 framing. |

## 흡수처 매핑 (extracted_to)
- `docs/explanation/jax-throughput.md` — §4 현황에 env 통합 반영, §5 에서 후속(vectorized-bench/jax-battle-full).
- `docs/explanation/competitive-analysis.md` — 갭 register "competitively fast" 행에 통합 진척 반영.

## 타입 체크 / 빌드 결과
mypy src: Success(25) · ruff: All checks passed · build OK · pytest: 281 passed, 2 skipped.
