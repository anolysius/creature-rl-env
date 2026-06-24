# 인수인계서 — CritterGym (세션 이후: M4 JAX 핵심 입증 + (A) gap rigor)

> 다음 세션용. 직전 세션(2026-06-24)이 **(B) 종결 후 JAX 피벗으로 M4 핵심을 입증**(PR #40·#41·#42 머지) +
> **(A) "hard-and-gap≈0"의 gap 쪽을 multi-run rigor로 robust 입증**(PR #43 머지). 이 문서는 *무엇이 끝났고 /
> 무엇이 정직한 부분 결과로 남았고 / 다음에 무엇이 최대 leverage인가*. SSOT: `DESIGN.md`(§3.1.1 honest scope·
> §4 throughput), `docs/explanation/jax-throughput.md`(M4 narrative·신규), `docs/explanation/competitive-
> analysis.md`(갭 register), `docs/_active/{jax-throughput,difficulty-scaling}/INITIATIVE.md`, `docs/CHANGELOG.md`,
> `CLAUDE.md`(규율).

---

## 0. 오프닝 프롬프트 (새 세션에 그대로 붙여넣기)

> CritterGym 작업을 이어서 한다. 먼저 `docs/HANDOFF-next-session.md`, `docs/explanation/jax-throughput.md`(M4
> narrative), `DESIGN.md` §3.1.1+§4, `docs/explanation/competitive-analysis.md`(갭 register), `docs/_active/
> jax-throughput/INITIATIVE.md` + `docs/_active/difficulty-scaling/INITIATIVE.md`, `docs/CHANGELOG.md` 상단을
> 읽어라. 직전 세션이 **(B) 종결 후 M4(JAX 속도)로 피벗해 핵심 입증**: overworld(#40)·commit-battle(#41)·
> full-episode env 통합(#42)을 functional JAX 포트, **전부 numpy parity 0 mismatch + vmap 34~1047×**. 이어
> **(A) gap rigor(#43)**: #24 약한신호를 multi-run+예산↑+사전약정으로 정밀화 → **gap≈0 robust(real-gap 미출현),
> 단 현 knob은 변별력 부족 가능**(질문이 *gap*→*hard*로 이동). **이번 세션 미션 = 남은 leverage 택1**(아래 §4).
> 방침: **공개(OSS/arXiv 제출)는 맨 마지막**, 기능 준비+비교우위 먼저. 하네스 규율 준수(매 task `/task-start`→
> L1(opus reviewer×2 + qa, verdict-first)→**freeze 전 pilot**→G1→TDD→L3 APPROVED→task-end, main 직접금지
> feature→PR). **"X 증명/회복한다"류 acceptance는 freeze 전 pilot 검증 + 성능 아니라 *측정+정직 보고*로 freeze,
> pilot이 falsify하면 정직 reframe.** 사전약정 결정규칙으로 사후 편향 차단, 학습 결론은 multi-run. 정직성 > 헤드라인.

---

## 1. 현재 상태 (한 줄)

M0·M1·M2 ✅, M3 부분(EC1·2·3·6 ✅ / EC4 arXiv 초안·EC5 OSS 준비만, 외부 발행 미실행), **M4(JAX) 핵심 입증**
(family A 벡터화 env, EC1/EC2의 family-A 부분 사실상 달성 / EC3 GPU만 남음). **283 tests**, numpy-only core +
`[rl]`/`[viz]`/`[render]`/`[jax]` extra. main HEAD = `01e96cb`. 활성 이니셔티브 3: `jax-throughput`(M4),
`difficulty-scaling`((A)), `env-core`(M0–M3, 대부분 done).

## 2. 직전 세션이 한 것 (4 task, 전부 main 머지)

| PR | task | 정직한 결과 |
|---|---|---|
| #40 | `jax-hotpath-foundation` | overworld step functional JAX 포트. parity 0 mismatch, vmap **186×**(76.5M steps/s). 단일 jit env는 numpy보다 느림(이득=vmap). |
| #41 | `jax-battle-port` | commit-mode 챔피언 battle 포트(gym-boss 경로). parity 0, vmap **1047×**. pilot이 hp 클램프 버그 포착. |
| #42 | `jax-env-integration` | overworld+battle 합성 **full-episode env**(`jax_env.py`, lax.cond dispatch). **full obs(local_patch 포함) parity 0**, vmap 34~73×. **L3가 truncated parity 갭 포착**(numpy term/trunc 독립). RL 루프 실소비 가능. |
| #43 | `difficulty-gap-rigor` | (A) #24 약한신호 → multi-run rigor. held-in 비floor(1.1~1.5) + 세 점 **gap≈0-signal**(real-gap 미출현). 사전약정 classify_gap(floor=0.3·k=1.0). |

## 3. ⚠ 정직한 결론 (과대 금지)

**M4 (JAX 속도) — 핵심 입증, 부분 완성:**
- family A commit-mode 가 **overworld+battle+full-episode env 전부 functional JAX + vmap 벡터화**, 모든 단계
  numpy parity **0 mismatch**(재현성 북극성 #3 보존). "속도가 실재한다"가 입증됨.
- **미포함**: family B/C/D, **non-commit full battle**(switch/item/multi-creature = `jax-battle-full`), **GPU
  측정**(M4-EC3, CPU vmap은 슬라이스서 이미 ≥10M). 단일 jit는 numpy보다 느림 — 이득은 *vmap 한정*(정직 framing).

**(A) "hard-and-gap≈0" — gap 쪽 robust, hard 쪽 미해결:**
- multi-run(100k, 5run)서 세 난이도 점 모두 `gap≈0-signal`, held-in 비floor(정책 유능) → #24 약한신호의 진짜
  업그레이드. **real-gap 미출현** = 현 knob은 train→test 갭을 안 만듦.
- **caveat**: gap 약한 음수(난이도 비대칭), std가 난이도와 함께 커짐(d2 0.90≈gap 2배 → 작은 gap 정밀 배제 못함),
  held-out~1.9/3 = **현 knob이 능력 변별엔 충분히 어렵지 않을 수 있음**. → 미해결은 *hard*(변별 난이도) 쪽.

전부 박제: `DESIGN.md §3.1.1+§4`, `jax-throughput.md`, `difficulty-scaling/INITIATIVE.md`, archive reports.

## 4. 다음 후보 (택1, 사람 결정 — competitive-analysis 갭 register 기준)

> 개인 의견(직전 세션): 오늘 M4 핵심 + (A) gap 모두 ship. 남은 leverage 후보, 대략 가치순:

1. **변별-난이도 env 재설계 (A의 hard 쪽)** — 학습 정책이 쉽게 못 푸는 구조적 난이도(oracle 천장 해소[스타터
   다양화]+깊은 추론 부하)로 env가 능력을 *변별*하게. (A)를 진짜 "hard-and-gap≈0"으로. **단 env 메커닉 변경 =
   JAX 포트 재작업(jax-throughput R5)**. spec-stability 게이트 — 착수 전 순서 결정 필요(큰 작업).
2. **RL 학습 데모** — JAX env로 실제 PPO류 학습 1회 돌려 "실제로 빠르게 학습됨"까지 입증(벤치 너머 제품 데모).
   CPU jax로도 가능. M4를 데모로 마감. leverage 중간, 비용 낮음.
3. **`jax-battle-full`** — non-commit full battle(party+switch+item+force-switch) 포트. M4 완전성↑. 동적 party
   인덱싱+lax.scan. 한계효용 중간(commit-mode가 이미 load-bearing 경로).
4. **GPU 벤치(`vectorized-bench`)** — M4-EC3(≥10M GPU) 마감. **GPU 환경 필요**(현 .venv는 CPU jax). 환경 갖춰질 때.
5. **다른 family 통합** — forage/duel/muster를 `jax_env`에(현재 family A only).
6. **(맨 마지막) 공개** — arXiv 제출(EC4)+OSS repo-public·Hub(EC5)+데모 GIF(EC6). 전부 사람 게이트.

> 트레이드오프: 1은 가치 크나 큰 작업+JAX 재포트 동반(spec 안정 게이트). 2는 싸고 "속도 실재"를 눈에 보이게. 막히면
> 1·2 중 사람이 택. JAX가 빨라져 이제 (A) 재설계 실험도 싸다(단 RL 루프를 JAX env에 올리는 통합 필요할 수 있음).

## 5. 코드 포인터 (직전 세션 산출 — 전부 main, `[jax]` extra)

- **JAX 포트 스택**(`src/critter_gym/`, import jax 모듈 내부=코어 numpy-only 보존, `__init__` 미import):
  - `jax_overworld.py` — `OverworldState` pytree + `overworld_step`(family A/B, branch-free) + `state_from_region` + `make_step_fn`.
  - `jax_battle.py` — `ChampionBattleState`/`Params` + `champion_battle_step`(commit-mode, lax.cond 속도순) + `params_from_creatures`/`initial_state` + `eff_matrix`.
  - `jax_env.py` — `JaxEnvState` + `jax_env_step`(lax.cond mode dispatch) + `jax_reset`(numpy Region bridge, gym_active 패딩) + `encode_obs`(13키, local_patch egocentric) + `make_env_step`. **family A commit-mode only.**
- **벤치** `scripts/bench_throughput.py` — numpy vs jax single/vmap (overworld·battle·full-env 3 섹션), 정직 framing.
- **parity 테스트**(`importorskip("jax")`, CI numpy-only): `tests/test_jax_parity.py`·`test_jax_battle_parity.py`·`test_jax_env_parity.py`.
- **(A) 난이도** `scripts/difficulty_generalization.py`([rl]) — `classify_gap`(사전약정 floor=0.3·k=1.0, 순수함수 numpy-only) + `train_and_gap_multirun`(std-across-runs) + `--runs N`. 테스트 `tests/test_difficulty_generalization.py`.
- **문서** `docs/explanation/jax-throughput.md`(M4 narrative 신규) + DESIGN §4 + §3.1.1 + competitive-analysis 갭 register.

## 6. 하네스 메모 (직전 세션 학습)

- **freeze 전 pilot이 매 task 버그를 사전 포착** — JAX 포트마다 pilot이 parity 버그를 1~2건씩 잡음(hp 클램프,
  battle중 NOOP/SWITCH champion 미공격, jnp 인덱싱, 가변 gym 수). pilot 없이 freeze했으면 다 놓쳤을 것. **pilot은
  필수**(가정 검증 + 버그 사전 포착 + AC7 분기 결정).
- **다층 검증이 단일 검증 놓친 edge 포착** — #42서 pilot·multi-config parity가 못 잡은 truncated 독립성 갭을
  **adversarial L3 reviewer가 포착**(numpy term/trunc 독립계산=둘다 True 가능). pilot+parity+L3 3층이 값어치.
- **l3-reviewer-maxturns 재발(이번 세션 3회)** — plan-reviewer가 소스 조사 중 verdict 없이 종료. **SendMessage로
  "추가 조사 없이 verdict만" 요청해 회수**하면 깨끗(전부 APPROVE 회수됨). 항구 수정 대기(retro 큐).
- **commit/push guard가 번호형 옵션 선택("1")을 인가로 못 읽음** — 키워드-리터럴 매칭이라 "커밋 키워드" 없으면
  BLOCK. 사용자가 "커밋+PR 올리기" *옵션을 명시 선택*했으면 인가 명확 → `HARNESS_ALLOW_COMMIT=1` override(정직히
  보고). retro 후보: 번호 선택지 인가 인식.
- **archive 이동**: 신규 plan/report untracked면 `git mv` 불가 → 일반 `mv`(가드 PreToolUse Bash라 mv는 통과).
- **`.claude/projects/` (repo-로컬)는 stray** — 메모리 SSOT는 `~/.claude/projects/.../memory/`(글로벌). 커밋서 매번 제외(`git reset .claude/projects/`).
- **실측 run은 background**(run_in_background). sb3 PPO 100k×3×5run=~30분. harness가 추적→완료 시 자동 재호출(폴링 불필요).
- 개발 `.venv`: ruff/mypy/pytest/build + sb3 2.7.1 + sb3-contrib 2.7.1 + **jax 0.4.30(CPU, py3.9 마지막 라인)**. core CI numpy-only(jax/PPO는 importorskip).

## 7. 정직성 문화 (계승 필수)

직전 4 task 공통 — **acceptance를 *성능*이 아니라 *측정+정직 보고*로 freeze**. JAX 포트: parity 0 mismatch를
정직 입증(가짜 속도 아님), 이득은 vmap 한정(단일은 손해)을 헤드라인 금지로 명시, GPU/battle-full 미포함을 *부분*으로
정직 라벨. (A): real-gap 미출현·std 증가·변별력 부족 가능을 caveat로 박제, "gap≈0 입증" 과대 회피. **사전약정
결정규칙(classify_gap 임계 데이터 보기 전 고정)으로 p-hacking 차단, multi-run으로 단일run 노이즈 교정, pilot으로
가정 사전검증, 다층 검증(pilot+parity+adversarial L3)으로 edge 포착.** 헤드라인보다 정직성 — 이게 moat 층3(trust) 재료.

## 8. 사용자 메모 (계승)

사용자는 수학/RL 깊은 배경 아니나 **전략·정직성·방향 판단으로 지휘**. **매 task 시작·끝에 수식 없는 고등학생용 한 문단
요약(뭘/왜/비유/결과)을 표·용어와 *별도로* 동반**할 것. 메모리 SSOT: `~/.claude/projects/.../memory/`
(`plain-language-task-summaries`·`user-non-math-background`, 상호 [[링크]]).
