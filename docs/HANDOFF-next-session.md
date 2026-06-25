# 인수인계서 — CritterGym (세션 이후: 자율 v1.0.0 런 4-task — non-commit·tuned-PPO·headroom-rigor·family폭)

> 다음 세션용. 직전 세션이 **bounded-YOLO 자율 런**으로 4 task를 전부 main 머지: non-commit full-env 통합
> + tuned PPO 베이스라인(KR1) + headroom multi-run rigor(KR1↑) + forage/muster family 통합(KR2 3/4).
> 이 문서 = *무엇이 끝났고 / 정직한 부분 결과 / 다음 미션(duel C 포트 → v1.0.0 패키징)*. SSOT: `DESIGN.md`
> (§3.1.1·§4), `docs/explanation/jax-throughput.md`, `docs/explanation/competitive-analysis.md`,
> `docs/_active/{jax-throughput,difficulty-scaling}/INITIATIVE.md`, `docs/CHANGELOG.md`, `CLAUDE.md`(규율),
> 메모리 `~/.claude/projects/.../memory/`(`autonomous-v1-mandate`·`plain-language-task-summaries`·
> `user-non-math-background`).

---

## 0. 오프닝 프롬프트 (새 세션에 붙여넣기)

> CritterGym 작업을 이어서 한다. 먼저 `docs/HANDOFF-next-session.md`, `docs/explanation/jax-throughput.md`,
> `DESIGN.md` §3.1.1+§4, `docs/explanation/competitive-analysis.md`, `docs/_active/jax-throughput/INITIATIVE.md`
> + `docs/_active/difficulty-scaling/INITIATIVE.md`, `docs/CHANGELOG.md` 상단, `src/critter_gym/envs/duel_env.py`,
> `src/critter_gym/jax_env.py` 를 읽어라. main HEAD=`4be0cce`, **396 tests green**(2 skip).
>
> [직전 세션 요약] bounded-YOLO 자율 런으로 4 PR 머지(#50 non-commit full-env 통합 parity0·vmap 36–60×,
> #51 jax-ppo-tuned: proper PPO[GAE+clip+epochs] + oracle-headroom = 벤치 결과표 실체[KR1], #52
> ppo-headroom-rigor: headroom multi-run robust[default 28%·hard 21% of oracle, hard-and-learnable robust],
> #53 jax-family-integration: forage+muster 통합[KR2 3/4 family, parity0]). 전부 parity 0 / 사전약정 규칙 /
> 정직 보고.
>
> [이번 세션 미션] **KR2 마무리 → KR3 패키징**. (1) **duel(C) JAX 포트** — type-agnostic RPS 배틀 엔진을
> jax_env에 `family=duel`로 통합(numpy `DuelEnv` 대비 parity 0). 이러면 **4/4 family 전부 벡터화** = 강한
> breadth 주장 완성. (2) 그 다음 **KR3 — 결과 패키징/v1.0.0 준비**: 흩어진 강한 결과(JAX 속도 + robust
> headroom + 4 family)를 front-facing README/paper로 통합 + 1-command 재현 벤치 + 버전 1.0.0-rc 준비.
> **공개(OSS 리스팅·arXiv 제출·태그 push)는 끝까지 사람 게이트** — v1.0.0 발행 직전 멈춤.
>
> [방침] 하네스 규율 100% 유지(매 task `/task-start`→L1[plan-reviewer+qa 병렬]→**freeze 전 pilot**→G1
> freeze→TDD/G2[mypy·ruff·pytest·build]→L3 APPROVED[2 reviewer]→`/task-end`). main 직접 금지=feature→PR→
> merge. parity 포트는 **0 mismatch 비협상**. "X 한다"류 acceptance는 freeze 전 pilot으로 검증, 성능 아닌
> *측정+정직 보고*로 freeze, pilot이 falsify하면 정직 reframe. 사전약정 결정규칙(데이터 전 고정)으로
> p-hacking 차단. 정직성 > 헤드라인. 매 task 시작·끝 수식 없는 한 문단 요약 동반. `.claude/projects/`는 매
> 커밋 `git reset .claude/projects/`로 제외.

---

## 1. 현재 상태 (한 줄)

M0·M1·M2 ✅, M3 부분(공개만), **M4 대폭**: family A/B/D(=critter/forage/muster, type-matchup 배틀) 전부
JAX 벡터화 + commit·non-commit 양 배틀 경제 통합 + **tuned PPO 베이스라인 + multi-run-robust oracle
headroom**. **396 tests**(2 skip), numpy-only core + `[rl]`/`[viz]`/`[render]`/`[jax]` extra. main HEAD=
`4be0cce`. 활성 이니셔티브: `jax-throughput`(task 1–9 done), `difficulty-scaling`((A), task 1–3 done),
`env-core`(M0–M3 done).

## 2. 직전 세션 4 task (전부 main 머지)

| PR | task | 정직한 결과 |
|---|---|---|
| #50 | `jax-noncommit-env-integration` | non-commit full battle(party+SWITCH+force-switch+party-wipe)을 jax_env에 통합. numpy `CritterEnv(commit_battles=False)`(env **기본** 경로) 대비 parity 0. vmap 36–60×. pilot이 Phase1 SWITCH(cyclic) vs Phase3 force-switch(first-in-order) 순서 차이 포착. |
| #51 | `jax-ppo-tuned` (KR1) | A2C-lite를 **proper PPO**(GAE(λ)+clip+epochs+adv-norm)로. `evaluate_gym_clears`로 oracle와 동일 지표. 사전약정 R1/R2/R3. **default PPO=oracle 32%·hard 15%, hard-and-learnable**(reframe 미발동). hard서 PPO<type_blind=capability ladder. |
| #52 | `ppo-headroom-rigor` (KR1↑) | headroom을 **multi-run(5) robust**로. 신규 `headroom.py classify_headroom`(numpy-only CI, 사전약정 frac0.75·k1.0). **default 28%·hard 21%, 낙관상한도 임계 한참 밑=robust**. ppo-closes 미발동. |
| #53 | `jax-family-integration` (KR2) | forage(B contact-collect)+muster(D catch→공격부스트, evolve가 부스트 리셋) 통합. parity 0(24 tests)+non-vacuity 가드. **3/4 family 벡터화**. muster 부스트는 `party_atk_boost` 누적기로 미러. |

## 3. ⚠ 정직한 결론 (과대 금지)

- **M4 (JAX)**: family A/B/D + commit·non-commit 배틀 + full-episode env + tuned PPO 전부 벡터화·parity 0.
  **속도 이득=vmap 한정**(단일 jit는 손해)·CPU(GPU 미측정 M4-EC3)·**duel(C) 미포트**(별도 RPS 엔진).
- **(A) hard-and-learnable**: tuned PPO가 oracle의 21–28%만(5-run robust), gap≈0(일반화), hard서
  PPO<type_blind = capability ladder 선명. **헤드라인 자산**. caveat: 작은 net·CPU·200iter(이 예산 기준
  headroom)·oracle=scripted ceiling proxy·5-run(대규모 sweep 아님)·강한 baseline은 후속.

## 4. 이번 세션 미션 상세

### (1) duel(C) JAX 포트 — KR2 마무리 (4/4 family)
numpy SSOT = `src/critter_gym/envs/duel_env.py`(정독 필수). 핵심:
- **type-agnostic RPS 배틀**(type chart 무용). battle action: 0=ATTACK,1=CHARGE,2=GUARD(그 외→GUARD).
- **charge state**: `_pcharge`/`_echarge`(0..`MAX_CHARGE`=2). **obs `player_charge`/`enemy_charge`가 비-0**
  (타 family는 0-mask) → `encode_obs`를 family-aware로(duel은 charge 필드에서 채움; 비-duel은 0=byte-identical).
- **보스 결정론**: `echarge>=1`이면 ATTACK 아니면 CHARGE.
- **해소**: ATTACK = `attack×(1+charge)` 데미지(상대 GUARD면 0), 자기 charge 리셋; CHARGE=charge+1(≤MAX);
  GUARD=무. 단일 active creature(party[0]) vs 단일 보스(스위칭/파티와이프 없음).
- **종료**: 보스 기절 ∨ player active 기절 ∨ `_duel_turns>=_DUEL_TURN_CAP`(=40, 교착=패). 승(보스 기절 &
  player 살아있음)시 gym_defeated·레벨·evolve(+1). 배틀 진입시 풀힐·charge/_duel_turns 리셋.
- **overworld는 family A(CATCH-collect)** — DuelEnv는 `_step_overworld` 미override(critter 재사용).
- **JAX 설계**: `JaxEnvState`에 `player_charge`/`enemy_charge`/`duel_turns` 추가(비-duel 0=byte-identical),
  `_FAM_DUEL=3` battle branch(branch-free where, 4번째 배틀 경제). `make_jax_env(JaxEnvConfig(family=duel,
  commit=False))` vs numpy `DuelEnv(commit_battles=False)` parity 0. **freeze 전 pilot이 RPS 해소·charge·
  교착-cap을 0 mismatch로 입증**(commit 무관 — duel은 자체 _step_battle, Battle.step 미호출).

### (2) KR3 — 결과 패키징 / v1.0.0 준비
- README.md + `docs/paper/critter-gym.md`가 **stale**(JAX 속도·PPO headroom 이전). 새 헤드라인으로 갱신:
  "경쟁력 속도(JAX vmap 36–1047×) + hard-and-learnable(tuned PPO oracle 21–28% robust) + 4 family + 재현성".
- 1-command 재현 벤치(throughput 표 + headroom 표 재생성) + 버전 1.0.0-rc 준비.
- **공개(외부 발행·태그 push)는 사람 게이트** — 직전 멈춤·결재.

## 5. 코드 포인터 (이번 세션 산출, 전부 main)

- `src/critter_gym/jax_env.py` — `JaxEnvConfig`(grid/patch/gyms/boss + `commit`/`potions`/`battle_max_turns`/
  `family`) + `JaxEnvState`(+`items`/`battle_turn`/`party_atk_boost`) + `make_jax_env(cfg)`: overworld family
  분기(critter/forage/muster) + commit fight·noncommit·(미래 duel) battle branch + `encode_obs`(13키).
  duel 추가 = `family` enum에 `_FAM_DUEL`, charge 필드, duel battle branch, encode_obs charge 채움.
- `src/critter_gym/jax_train.py` — A2C `train` + **PPO**(`PPOConfig`/`gae`/`make_ppo_rollout`/`ppo_loss`/
  `train_ppo`/`evaluate_gym_clears`) + `EnvSpec`/`default_env_spec`/`difficulty_env_spec`.
- `src/critter_gym/headroom.py` — `classify_headroom`(numpy-only CI, 사전약정).
- `scripts/ppo_baseline.py` — default+hard PPO vs oracle headroom(`--runs N`). `scripts/bench_throughput.py`
  — overworld/battle/full-env/non-commit-full-env 벤치.
- 테스트(importorskip, CI numpy-only): `test_jax_{parity,battle_parity,env_parity,train,difficulty_parity,
  battle_full_parity,noncommit_env_parity,ppo,family_parity}.py` + `test_headroom.py`(CI 포함).

## 6. 하네스 메모 (이번 세션 학습)

- **freeze 전 pilot이 핵심**: #50 SWITCH 순서차·#53 muster 부스트×evolve 리셋을 freeze 전 입증(헛 freeze 차단).
- **l3-reviewer-maxturns 재발(이번 2회)** — plan-reviewer가 verdict 없이 종료. **SendMessage로 "추가 조사
  없이 verdict만"** 회수하면 깨끗(전부 APPROVE). qa-verifier도 INLINE 있음에도 누락 주장 1회 → 강조 재호출로 해결.
- **bounded-YOLO 자율 런**: 루틴 게이트(G1·verify·L3·task-end·commit·PR·merge) 자동, 정지 조건(pilot
  falsify·reframe·**공개**[사람 게이트]·no-progress 2회)만 멈춤. `HARNESS_ALLOW_COMMIT=1`로 커밋 인가.
- **non-vacuity 가드 패턴**: parity 배터리가 실제로 핵심 경로(force-switch/party-wipe/muster catch+evolve)를
  자극함을 별도 테스트로 증명 → parity가 vacuous 아님 보장.

## 7. 정직성 문화 (계승 필수)

매 task acceptance를 *성능* 아닌 *측정+정직 보고*로 freeze. parity 0으로 가짜 속도 차단, vmap 한정·CPU·
이 예산 한정 명시, oracle=scripted proxy·single/few-run 라벨. 사전약정 결정규칙(데이터 전 고정)으로 p-hacking
차단, pilot이 전제 검증(falsify시 reframe), 다층 검증(pilot+parity/property+non-vacuity 가드+adversarial L3).
헤드라인보다 정직성 — moat 층3(trust) 재료.

## 8. 사용자 메모 (계승)

사용자는 수학/RL 깊은 배경 아니나 **전략·정직성·방향으로 지휘**. **매 task 시작·끝 수식 없는 한 문단 요약**
(뭘/왜/비유/결과)을 표·용어와 *별도로* 동반. **자율 mandate**(메모리 `autonomous-v1-mandate`): v1.0.0/moat까지
bounded-YOLO 자율 task 연속+커밋푸시, **공개는 사람 게이트**. 자율 런 OKR — KR1 ✅(tuned PPO+robust headroom) /
KR2 🟡 3/4(duel C 남음) / KR3 ⬜(패키징·v1.0.0).
