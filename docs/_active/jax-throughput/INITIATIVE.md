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
| 2 | `jax-battle-port` | ✅ done (→ `_archive/2026-Q2/jax-throughput/02-jax-battle-port/`) | 핫패스 어려운 절반 — **commit-mode 챔피언 battle**(gym-boss 실제 경로) functional JAX 포트(`jax_battle.py`: lax.cond 속도순 + where faint/terminal). 실제 `Battle(commit_mode=True)` 대비 **parity 0 mismatch**(fixed 45 + vary 24 config). **실측**: jit OK / numpy 112k/s · **jax vmap 1047×(117M/s, b=1024)**(순수 산술이라 overworld보다 벡터화 효율↑). **freeze 전 pilot이 hp 음수 parity 버그 포착**(take_damage `max(0,·)` 클램프). **AC7 분기 (b)**: commit-mode 포트 + full(switch/item/multi-creature)은 후속 `jax-battle-full`. overworld+commit-battle=핫패스 load-bearing 대부분. 210→263(+53, 회귀 0), mypy(24)/ruff/build clean. + jax_overworld 1줄 lint 정정 |

| 3 | `jax-env-integration` | ✅ done (→ `_archive/2026-Q2/jax-throughput/03-jax-env-integration/`) | **벡터화 full-episode env step** — `jax_overworld`+`jax_battle` 합성(`jax_env.py`: `lax.cond` mode dispatch + `encode_obs` 13키[local_patch egocentric]). 실제 `CritterEnv(commit_battles=True)` 대비 **full parity 0 mismatch**(obs 13키 전체+reward+term+trunc, random+gym-clearing, fixed+vary). **실측**: numpy 130k/s · **jax vmap 34×(b=1024)~73×(b=4096)**(full-episode 발산으로 슬라이스보다 배율↓). **AC7 (a) 완성**(local_patch 포함). **다층 검증 버그 3건 포착**(pilot 2 + 가변gym `gym_active` + **L3 truncated 독립성 갭**). family A commit-mode. RL 루프 실소비 가능 surface. 263→281(+18, 회귀 0), mypy(25)/ruff/build clean |

| 4 | `jax-rl-demo` | ✅ done (→ `_archive/2026-Q2/jax-throughput/04-jax-rl-demo/`) | **JAX-native A2C로 실제 학습 1회 데모** — `jax_train.py`(region bank + `lax.scan` rollout + 손수 Adam, on-device vmap+jit) + `scripts/jax_rl_demo.py`. **freeze 전 pilot이 사전약정 결정규칙(R1 `mean_late−mean_early≥std_late`)으로 분기 (a) 확정.** **실측**(CPU·single run): 학습곡선 **상승**(ep_return ~1.8→~10.0, rise 0.041≫std_late 0.003) / 학습 throughput **~0.66M env-steps/s**(별 run ~1.1M) vs 기존 numpy/sb3 ~3.8k = **~170× FASTER**(on-device vmap) / held-out 1.44 vs held-in 1.00 = **gap≈0**(seed split, (A) no-memorization 일관). **정직 framing**: A2C-lite·CPU·single run·reward/step proxy=신호(tuned PPO 아님), sb3 baseline=기존 단일-env 경로. env/jax_env 무변경(parity 보존). 283→287(+4 importorskip smoke, 회귀 0), mypy(26)/ruff/build clean. jax-throughput.md(§4/§5)+DESIGN §4+competitive-analysis 갱신 |

| 5 | `jax-difficulty-report` (R5) | ✅ done (→ `_archive/2026-Q2/jax-throughput/05-jax-difficulty-report/`) | **jax_env config화** — `difficulty-dynamic-range`의 고-gym(8) 동적 범위를 JAX 벡터화로 재포트. `JaxEnvConfig`+`make_jax_env(cfg)` factory(static-shape 클로저); module-level fns=default-config 인스턴스로 **보존**(기존 import·parity·bench byte-identical). `jax_train` config-aware(`EnvSpec`/`difficulty_env_spec`, obs_dim 동적). **freeze 전 pilot**: 고-gym parity **0 mismatch**(grid6·8gym·patch11×11>grid·num_types12·boss150/16, obs 13키+reward+term+trunc, random+gym-clearing, fixed+held-out) + 기존 parity 3종 무회귀. 고-gym 학습 jit/vmap OK(곡선 상승) / **실측 ~196k env-steps/s vmap vs sb3 ~3.1k = ~63× FASTER**(고-gym 발산으로 default보다 배율↓, 정직). `jax_rl_demo --difficulty`. **정직 범위**: family A commit·고-gym 재포트지 scripted resolution arms(env peek)는 numpy 유지·GPU/tuned PPO 후속. 294→310(+16 importorskip parity, 회귀 0), mypy(26)/ruff/build clean. jax-throughput.md(R5)+DESIGN §4 갱신 |

| 6 | `jax-battle-full` | ✅ done (→ `_archive/2026-Q2/jax-throughput/06-jax-battle-full/`) | **non-commit full battle JAX 포트** — 핫패스 배틀 남은 절반. `jax_battle_full.py`(`FullBattleState`/`FullBattleParams`+`full_battle_step`: party P + SWITCH + ITEM(potion) + 기절 force-switch + party-wipe, branch-free·동적 party gather·argmax next-alive). **freeze 전 pilot parity 0 mismatch**: numpy `Battle(commit_mode=False)`(starter 3 vs boss 1) 대비 배터리(attack/switch/item-heal/force-switch/party-wipe/truncation)+random 40seed(fixed+vary), 매 턴 party_a_hp·active·boss_hp·winner·turn·done 일치. **실측**: numpy 96k/s · **jax vmap 43.5M/s(b=1024)=452×**(순수 산술). **한계효용 정직**: gym-boss 실경로는 commit(이미 포트)·non-commit full-env 통합은 별도 후속. standalone(jax_env 무변경). 310→328(+18 importorskip, 회귀 0), mypy(27)/ruff/build clean. jax-throughput.md(§5 #1)+DESIGN §4 갱신 |

| 7 | `jax-noncommit-env-integration` | ✅ done (→ `_archive/2026-Q2/jax-throughput/07-jax-noncommit-env-integration/`) | **non-commit full battle을 jax_env에 통합** — `jax_battle_full`(standalone, parity0)의 턴 로직을 `jax_env` battle branch에 연결. `make_jax_env(JaxEnvConfig(commit=False))`가 numpy `CritterEnv(commit_battles=False)`(env **기본** 경로 `CritterGym-v0`/`-procgen-v0`)를 미러. action 매핑(`<4`→MOVE·`4`→SWITCH cyclic-next-alive·`5`→wasted ITEM) + Phase1/2/3(force-switch=first-in-order, SWITCH=cyclic — **freeze 전 pilot이 두 순서 차이 포착**) + party-wipe/boss-dead/battle-trunc + 승리시 gym_defeated·레벨·evolve. **parity 0 mismatch**: 13 obs+reward+term+trunc, full 에피소드, fixed+vary, 4 정책(random·gym-clearing·switch-heavy·never-attack[패배 경로]) + **non-vacuity 가드**(force-switch·party-wipe 실자극 증명). **실측**: numpy 139k/s · **jax vmap 5.08M(b=1024)=36× / 8.35M(b=16384)=60×**(commit full-env와 동급). 정직 범위: family A·CPU·single·vmap-only·potion inert(action space 미방출)·GPU/tuned PPO 후속. 328→360(+32 importorskip parity, 회귀 0; default commit=True byte-identical), mypy(27)/ruff/build clean. jax-throughput.md(§4 Update+§5 #1)+DESIGN §4 갱신 |

| 8 | `jax-ppo-tuned` | ✅ done (→ `_archive/2026-Q2/jax-throughput/08-jax-ppo-tuned/`) | **tuned PPO 베이스라인 + oracle-headroom 정량화(KR1)** — `jax_train` A2C-lite를 proper PPO(`train_ppo`: GAE(λ)+value bootstrap+clipped surrogate+adv-norm+K-epoch minibatch, on-device jit+vmap)로. `gae` 순수함수(property: γ1λ1↔MC·λ0↔1-step TD) + `evaluate_gym_clears`(oracle와 동일 gym-clear 지표). A2C `train`/`jax_env` **무변경**(추가 API). `scripts/ppo_baseline.py`가 default+hard config서 held-out PPO vs oracle headroom 보고(사전약정 R1 학습·R2 PPO≥A2C·R3 PPO<0.75×oracle⇒headroom, 데이터 전 고정). **실측**(CPU·single·200iter): default PPO 0.59=oracle 1.84의 **32%**(A2C 0.78), hard PPO 1.06=oracle 7.28의 **15%**(A2C 1.88 거의붕괴)·gap≈0 — **hard-and-learnable**(R3 reframe 미발동). striking: hard서 PPO(1.06)<type_blind(2.03)=capability ladder 선명. 정직: single·작은net·CPU·oracle proxy·multi-run rigor 후속. 360→365(+5: gae property+PPO smoke), mypy(27)/ruff/build clean. jax-throughput.md(PPO Update)+DESIGN §3.1.1+competitive-analysis 갱신 |

| 9 | `jax-family-integration` | ✅ done (→ `_archive/2026-Q2/jax-throughput/09-jax-family-integration/`) | **forage(B)+muster(D) family를 jax_env에 통합(KR2)** — `make_jax_env(JaxEnvConfig(family=…))`가 numpy `ForageEnv`(contact-collect overworld·CATCH inert·gym-enter 상호배제)/`MusterEnv`(CATCH+party 공격 부스트+evolve 리셋)를 미러. **muster 핵심**: 부스트는 attack→battle damage→enemy_hp obs로 흐르고 `evolve()`가 `attack=form.attack`로 리셋(creatures.py:97) → 단순 base+12×caught 아님 → `party_atk_boost` 누적기(catch +12 전멤버/evolve시 해당 멤버 0)로 정확 미러. **parity 0 mismatch**: 13 obs+reward+term+trunc, full 에피소드, fixed+vary, random+gym-clearing+catch-then-gym, 24 tests + **non-vacuity 가드**(catch·evolve 양 경로 자극 증명). 3/4 family(A/B/D=type-matchup 배틀) 벡터화. **duel(C)는 별도 RPS 엔진 포트=후속**. 정직: family A/B/D·non-commit·CPU·vmap-only·GPU/duel 후속. 372→396(+24, 회귀 0; family A byte-identical), mypy(28)/ruff/build clean. jax-throughput.md(family Update)+DESIGN §4 갱신 |

| 10 | `jax-duel-integration` | ✅ done (→ `_archive/2026-Q2/jax-throughput/10-jax-duel-integration/`) | **duel(C) family를 jax_env에 통합(KR2 마무리, 4/4 family)** — type-AGNOSTIC RPS/stamina 배틀(type chart 무용)을 별도 `duel_battle_branch`로 미러. `make_jax_env(JaxEnvConfig(family=duel, commit=False))`가 numpy `DuelEnv(commit_battles=False)`를 미러. duel 고유 3요소: **동시 데미지**(속도순 없음·양쪽 take_damage 무조건→동시기절=loss), **raw stat 데미지**(`floor(atk×(1+charge))`·defense/eff/min1 없음·`_damage` 미사용), **duel 전용 charge obs**(`player_charge`/`enemy_charge` 비-0→encode_obs family-aware, 비-duel byte-identical). overworld=family A CATCH 재사용. `battle_turn`을 duel turn 카운터로 재사용(40-cap stalemate=loss; non-commit branch 미도달이라 안전). **parity 0 mismatch**: 13 obs(charge 2키 포함)+reward+term+trunc, full 에피소드, fixed+vary, 5 정책(random·gym-seeking·charge-exploit·all-GUARD stalemate·**scripted-optimal**[보스 결정론 악용→win·evolve]) + non-vacuity 가드(3 액션·turn-cap loss·evolve 자극). **freeze 전 pilot이 19,200 steps 0 mismatch 입증 + always-attack는 0승**(탱키 보스가 charge-0 공격 out-trade→승리엔 RPS 필요)→scripted-optimal로 win 60·evolve 24. **실측**(CPU·single·vmap-only): numpy 123k/s · **jax vmap 4.96M(b=1024)=40× / 10.15M(b=16384)=83×**. **4/4 family(A/B/C/D) 전부 벡터화 = full breadth**. 정직: CPU·single·vmap-only·GPU(M4-EC3) 후속. 396→415(+19, 회귀 0; family A/B/D byte-identical), mypy(28)/ruff/build clean. jax-throughput.md(duel Update)+DESIGN §4 갱신 |

| 12 | `gpu-bench-colab` | ✅ done (→ `_archive/2026-Q2/jax-throughput/12-gpu-bench-colab/`) | **M4-EC3(≥10M steps/s GPU) enabler + 로컬 Metal 비가용 박제** — GPU 측정은 하드웨어 게이트. **로컬 Apple GPU(M5 Pro·macOS 26.5) 실측**: jax-metal 0.1.0(jax 0.4.26)·0.1.1(jax 0.4.34) 둘 다 METAL device 인식·단순 op OK지만 **fused `lax.scan(vmap(env_step))`서 NSException 크래시**(Metal PJRT 한계, 코드 문제 아님); per-step만 ~23k/s(CPU보다 느림) → **로컬 Apple GPU는 JAX로 EC 측정 불가**. 신규 **`scripts/gpu_bench.py`**(fused-scan throughput, 기존 jax_overworld/jax_env/jax_train 심볼만 import; CPU sanity: overworld vmap **~480M/s**·full-episode **~22M/s** @b1024, vmap≫numpy·전부 유한) + **`scripts/colab_gpu_bench.ipynb`**(무료 Colab/Kaggle T4용 14-cell 노트북: GPU 확인→clone[public+PAT]→`jax[cuda12]`+repo 설치→bench+train throughput→복붙 요약, nbformat valid). 측정 실행=사용자 Google 로그인(게이트). **정직 경계**: notebook은 GPU 부재로 로컬 CPU-sanity까지만 검증·repo 공개전(clone 안내)·EC 달성은 사용자 Colab 회수 후 별도 기록(도구+음성결과 박제이지 EC 달성 아님). src 무변경 → 442 무회귀, mypy(28)/ruff/build clean. jax-throughput.md §5(Metal 비가용+Colab 경로) 갱신. _(commit pending)_ |
| 11 | `v1-results-packaging` | ✅ done (→ `_archive/2026-Q2/jax-throughput/11-v1-results-packaging/`) | **KR3 결과 패키징 / v1.0.0-rc 준비** — 흩어진 강한 결과(JAX vmap 27–1047×·4/4 family parity 0 / tuned PPO 21–28% of oracle robust hard-and-learnable / 재현성)를 front-facing README+paper로 통합 + **1-command 재현**(`scripts/reproduce_results.py [--quick] [--runs N]`: bench_throughput+ppo_baseline 오케스트레이션·수치 라이브·honest framing) + 버전 **0.0.1→1.0.0rc1**. **제품 코어(src) 무변경 — docs/scripts/meta만**. README "What it measures"에 competitively-fast+4-family+hard-and-learnable 헤드라인+Release status(GPU/arXiv/OSS 잔여 게이트=사람). paper §2 갱신+신규 §6 Throughput+§4 PPO headroom subsection+§5/§8/§9+source map. **공개(OSS·arXiv·태그 push)는 사람 게이트 — 직전 정지(AC6)**. 정직: 모든 주장 caveat 동반·라이브 재생성 fabricate 0. 415 무회귀(src 무변경), mypy(28)/ruff clean, build→1.0.0rc1. L3 2/2 APPROVE(정직성 축). Acceptance AC1–AC6 |

(이후 task 는 /task-start 로 append — 예정: `vectorized-bench`[GPU=M4-EC3 마지막 항목], **공개[OSS·arXiv·태그]=사람 게이트**)

## 다음 task
**task 1·2·3·4·5·6·7 종결** — overworld + commit-battle + 통합 env + 실학습 데모 + config화(고-gym) +
non-commit full battle 포트 + **non-commit full-env 통합** 완료(전부 parity 0). 배틀 엔진 두 경로
(commit/non-commit) 모두 *standalone뿐 아니라 full-episode env까지* JAX 벡터화. M4-EC1/EC2 family-A
**commit·non-commit 양 경로 달성**(남은 건 GPU·다른 family·tuned PPO).
- **다음(택1)**:
  - **`vectorized-bench`** — M4-EC3(≥10M steps/s GPU) 측정. CPU vmap 은 슬라이스에서 이미 통과, full-env 는
    36–73×. GPU 환경 필요(현 .venv 는 CPU jax). EC 마무리.
  - **다른 family 통합** — forage/duel/muster 를 `jax_env` 에(현재 family A only). (B) 연결.
  - **tuned PPO** — A2C-lite를 제대로 된 PPO로(jax_train), 고-gym서 학습이 oracle에 얼마나 닿나 측정. (A) headroom.
- **spec-stability watch**: 난이도(A) 작업이 env 메커닉(보스 stat·reward) 바꾸면 포트 재작업(R5). DESIGN §4
  가 M4 를 "spec 안정 후"로 게이트 — 메커닉 변경 계획 있으면 순서 재검토.
- **피벗 고려**: M4 핵심(속도 실재) 입증됨. 갭 register 의 또 다른 축 **난이도 스케일(A)** 로 피벗하거나, M4 를
  GPU/데모로 마감할지 사람 결정 시점.

**caveat (freeze 시 박제)**: 난이도 스케일 작업이 후에 env 메커닉(스타터·보스·reward 경제)을 바꾸면 JAX 포트
재작업 필요. 본 task 는 *안정된 overworld 코어*만 포트해 이 위험을 최소화하나 0 은 아님.
