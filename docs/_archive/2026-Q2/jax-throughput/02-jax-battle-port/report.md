---
slug: jax-battle-port
initiative: jax-throughput
status: completed
ended: 2026-06-24
extracted_to:
  - docs/explanation/jax-throughput.md
  - docs/explanation/competitive-analysis.md
changelog_entry: docs/CHANGELOG.md
---

# JAX battle 포트 — commit-mode 챔피언 (핫패스의 어려운 절반) · 결과 보고서

`jax-hotpath-foundation`(overworld)에 이어 battle sub-MDP를 functional JAX로 포트. battle 은 핫패스의
*어려운 절반*(branchy 3-phase step). **commit-mode 챔피언 경로**(gym-boss 실제 경로)를 포트하고 numpy
`Battle`과 parity 입증. 성능 헤드라인이 아니라 측정 + 정직 feasibility verdict.

## 요약 (수치 표)

| 지표 | 값 | 비고 |
|---|---|---|
| jit 컴파일 | ✅ | `test_jit_compiles_and_terminates` |
| parity (numpy↔JAX) | ✅ **0 mismatch** | 실제 `Battle(commit_mode=True)` 대비, fixed 45 + vary 24 config |
| numpy battle | ~112k steps/s | baseline |
| jax vmap b=1024 | ~117M steps/s | **1047× numpy** |
| jax vmap (pilot, b≤8192) | ~230–253M steps/s | 2000×+ (순수 산술이라 overworld보다 벡터화 효율↑) |
| 테스트 | 210 → **263** (+53, skip 2) | 회귀 0 |
| mypy / ruff / build | clean (24 files) | — |

## 계획 대비 실적 (✅/⚠️/❌)

- ✅ **AC1** `src/critter_gym/jax_battle.py` — commit-mode 챔피언 battle step(move-vs-move + eff damage +
  faint→terminal) functional JAX 포트, `jax.jit` 컴파일.
- ✅ **AC2** `tests/test_jax_battle_parity.py` — 실제 numpy `Battle(commit_mode=True)`와 trajectory(champ_hp·
  boss_hp·winner·turn·done) 동일, fixed 45 + vary 24 config 0 mismatch. `importorskip` CI 격리.
- ✅ **AC3** 산술 정확 일치 — damage `max(1, floor(power·atk/def·eff))` + **hp 클램프 `max(0,·)`**(take_damage
  미러링) + 속도 타이(A 우선) + 빠른 쪽 KO 시 느린 쪽 move 스킵 + commit terminal(champ faint→B승, 동시→B승) +
  max_turns truncation. parity 가 가드.
- ✅ **AC4** `scripts/bench_throughput.py` — battle numpy vs jax vmap 행 추가, 정직 framing 유지.
- ✅ **AC5** 회귀 0 — 263 passed(210 무변경 + 53 신규), 기존 `battle.py`/`creatures.py`/`types.py` 무변경
  (포트는 격리 복제), mypy/ruff/build clean, 코어 numpy-only.
- ✅ **AC6** feasibility verdict 박제 (아래).
- ✅ **AC7** pilot 분기 **(b)** 확정 → commit-mode 포트 + full(switch/item/multi-creature)은 후속 `jax-battle-full`.
- ✅ **AC8** 툴체인 green.

## ⭐ Feasibility verdict (AC6)

1. **(i) jit = OK.** 3-phase commit-mode turn 이 `jax.lax.cond`(속도순 분기) + `jnp.where`(faint 스킵·terminal)로
   깔끔히 functional 화. battle 이 overworld 보다 branchy하나 commit-mode 는 switch/force-switch 가 없어 tractable.
2. **(ii) parity = OK.** 실제 `Battle(commit_mode=True)` 대비 0 mismatch(fixed 45 + vary 24). **pilot 이 hp
   음수 버그를 freeze 전 포착** — numpy `take_damage`의 `max(0,·)` 클램프 누락 → `jnp.maximum(0.,·)`로 교정.
   결정론·재현성(북극성 #3) 보존.
3. **(iii) speedup = 강한 양성(vmap 한정).** numpy 112k/s → jax vmap **117M/s(b=1024)=1047×**(pilot 은 더 큰
   batch 서 2000×+). battle step 은 순수 산술이라 overworld(186×)보다 벡터화 효율 더 높음. *정직 framing 유지*:
   이득은 vmap, 단일 env 는 손해.
4. **(iv) 포트 범위 = commit-mode 챔피언.** full non-commit battle(3-creature party + SWITCH + ITEM +
   force-switch + party-wipe terminal)은 **후속 `jax-battle-full`**. commit-mode 는 env 의 gym-boss 실제 경로
   (`CritterGym-commit-v0`, reasoning-load-bearing/learnability)라 load-bearing path 를 커버.
5. **(v) 후속 권고.** overworld + commit-battle 로 핫패스 *대부분* 포트됨 → 다음은 **`jax-env-integration`**
   (batched/vectorized Gymnasium surface 로 RL 루프가 실제 소비) 또는 `jax-battle-full`(완전성). 그 후
   `vectorized-bench`(M4-EC3 GPU).

## 정직 caveat

- CPU·single run — *방향*, GPU 미측정(범위 밖). 단일 jit battle 은 numpy 보다 느림(이득은 vmap).
- **full non-commit battle 미포트** — switch/item/multi-creature 는 후속. 핫패스 포트는 여전히 *부분*(단,
  overworld + commit-battle = env load-bearing path 대부분).
- hp float32 + `max(0,·)` 클램프 = numpy int 산술과 정확 일치(parity 입증). x64 off 무해.
- 이니셔티브 R5: 난이도(A) 작업이 battle 경제(보스 stat·reward) 바꾸면 재포트 — DESIGN §4 가 M4 를 "spec
  안정 후"로 게이트.

## 변경 파일 상세

| 파일 | 신규/수정 | 내용 |
|---|---|---|
| `src/critter_gym/jax_battle.py` | 신규 | `ChampionBattleState`/`ChampionBattleParams` pytree + `champion_battle_step`(lax.cond 속도순 + where 클램프/terminal) + `eff_matrix`/`params_from_creatures`/`initial_state` numpy bridge + `make_battle_step`(jit). __init__ 미import = 코어 numpy-only. |
| `tests/test_jax_battle_parity.py` | 신규 | `importorskip` + 실제 `Battle(commit_mode=True)` 대비 parity(fixed 45 + vary 24) + jit + idempotent + vmap = 53 테스트. |
| `scripts/bench_throughput.py` | 수정 | battle numpy baseline + jax vmap 행 추가, 정직 framing. |
| `src/critter_gym/jax_overworld.py` | 수정(1줄) | 직전 task 의 latent UP037 lint 수정(따옴표 친 반환 annotation 제거). AC8 whole-repo ruff clean 위함. *(프로세스 학습: 직전 task 가 mypy 수정 후 ruff 재실행 누락으로 lint 오류 머지 — 본 task 가 정직 정정.)* |

## 흡수처 매핑 (extracted_to)

- `docs/explanation/jax-throughput.md` — battle 포트 결과를 thread narrative §4(현황)에 반영, §5(open questions)
  에서 `jax-battle-full` 자리매김.
- `docs/explanation/competitive-analysis.md` — 갭 register "competitively fast" 행에 battle 포트 진척 반영.

## 타입 체크 / 빌드 결과
mypy src: Success(24) · ruff: All checks passed · build OK · pytest: 263 passed, 2 skipped.
