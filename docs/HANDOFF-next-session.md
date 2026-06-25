# 인수인계서 — CritterGym (세션 이후: M4 JAX 4-task 완주 + 변별 분해능)

> 다음 세션용. 직전 세션(2026-06-24~25)이 **bounded-YOLO**로 4 task를 전부 main 머지: M4 JAX 데모·config화·non-commit 배틀
> + (A) 변별 분해능. 이 문서 = *무엇이 끝났고 / 정직한 부분 결과 / 다음 최대 leverage*. SSOT: `DESIGN.md`(§3.1.1·§4),
> `docs/explanation/jax-throughput.md`(M4 narrative), `docs/explanation/competitive-analysis.md`(갭 register),
> `docs/_active/{jax-throughput,difficulty-scaling}/INITIATIVE.md`, `docs/CHANGELOG.md`, `CLAUDE.md`(규율).

---

## 0. 오프닝 프롬프트 (새 세션에 붙여넣기)

> CritterGym 작업을 이어서 한다. 먼저 `docs/HANDOFF-next-session.md`, `docs/explanation/jax-throughput.md`,
> `DESIGN.md` §3.1.1+§4, `docs/explanation/competitive-analysis.md`, `docs/_active/jax-throughput/INITIATIVE.md` +
> `docs/_active/difficulty-scaling/INITIATIVE.md`, `docs/CHANGELOG.md` 상단을 읽어라. 직전 세션이 bounded-YOLO로
> **4 task 머지**(PR #45·#46·#47·#48): JAX 실학습 데모·변별 분해능(동적 범위)·jax_env config화(고-gym 재포트)·
> non-commit full battle 포트 — **전부 parity 0 mismatch / 사전약정 규칙 / 정직 보고**. 방침: **공개는 맨 마지막**,
> 기능 준비+비교우위 먼저. 하네스 규율(매 task `/task-start`→L1(opus×2+qa)→**freeze 전 pilot**→G1→TDD→L3 APPROVED→
> task-end, main 직접금지 feature→PR). **"X 증명/회복/전이한다"류 acceptance는 freeze 전 pilot 검증, 성능 아니라
> 측정+정직 보고로 freeze, pilot이 falsify하면 정직 reframe**(이번에 difficulty 메커닉 1회 falsify→reframe). 정직성 > 헤드라인.

---

## 1. 현재 상태 (한 줄)

M0·M1·M2 ✅, M3 부분(공개만 미실행), **M4(JAX) 대폭 전진** — family A commit-mode가 overworld+battle+full-episode env
+ **실학습(A2C)** + **config-driven(고-gym)** + non-commit full battle까지 전부 JAX(parity 0). **328 tests**(2 skip),
numpy-only core + `[rl]`/`[viz]`/`[render]`/`[jax]` extra. main HEAD = `2e9c776`. 활성 이니셔티브 3:
`jax-throughput`(M4, task 1–6 done), `difficulty-scaling`((A), task 1–2 done), `env-core`(M0–M3 done).

## 2. 직전 세션이 한 것 (4 task, 전부 main 머지)

| PR | task | 정직한 결과 |
|---|---|---|
| #45 | `jax-rl-demo` | JAX-native A2C 실학습 1회 — CPU ~2초, 곡선 상승(ep_return ~1.8→~10), **~170× vs sb3**, held-out gap≈0. 사전약정 R1 규칙으로 분기 (a) 확정. A2C-lite·CPU·single-run=신호. |
| #46 | `difficulty-dynamic-range` | (A) *hard* 쪽 = 변별 **분해능↑**. **pilot이 원래 메커닉(스타터 다양화) falsify**(토너먼트 구조상 무력·winnability 정상·변별 이미 +1/gym) → reframe·새 slug. 확실한 레버=gym 수. spread +1.3(3)→+4.9(8) 단조↑, gap≈0 유지. `region.min_gyms` opt-in(byte-identical 무회귀). **"PPO 못 푸는 hard-benchmark"는 명시적 범위 밖**. |
| #47 | `jax-difficulty-report`(R5) | jax_env **config화**(`JaxEnvConfig`+`make_jax_env`, module-level fns=default 보존 byte-identical). 고-gym(8) parity 0 mismatch + 고-gym 학습 **~63× vs sb3**. jax_train config-aware(`difficulty_env_spec`, obs_dim 동적). |
| #48 | `jax-battle-full` | non-commit full battle(party+switch+item+force-switch+party-wipe) JAX 포트(`jax_battle_full.py`, branch-free). parity 0 mismatch(배터리+40 random seed) / vmap **452×**. 한계효용 정직(commit이 gym-boss load-bearing·full-env 통합 별도). |

## 3. ⚠ 정직한 결론 (과대 금지)

**M4 (JAX) — family A commit-mode 거의 완성:**
- overworld·commit-battle·full-episode env·**실학습 A2C**·**config-driven(고-gym)**·**non-commit full battle** 전부
  functional JAX + parity **0 mismatch**(재현성 북극성 #3 보존). "속도 실재"가 벤치 숫자 → *학습 데모*로 마감.
- **미포함**: family B/C/D·**non-commit full-env 통합**(battle만 standalone 포트, jax_env는 commit-only)·**tuned PPO**(현재 A2C-lite)·**GPU 측정**(M4-EC3, .venv는 CPU). 속도 이득=vmap 한정(단일 jit는 손해).

**(A) "hard-and-gap≈0" — gap robust + 변별 *분해능* 확보, 절대 난이도는 미해결:**
- gap≈0은 multi-run robust(#43) + 동적 범위로 변별 분해능↑(#46, oracle−blind spread 2→5). 학습 정책(PPO/A2C)은
  oracle보다 한참 낮음(headroom 큼).
- **미해결**: "PPO/frontier가 oracle에 못 닿는" **절대 hard-benchmark**(다중타입 보스·부분관측·전략 깊이) = 큰 연구,
  별도 이니셔티브급. 명시적 범위 밖으로 남김.

## 4. 다음 후보 (택1, 사람 결정 — 갭 register 기준)

1. **non-commit full-env 통합** — `jax_battle_full`을 jax_env에 분기(현 commit-only). M4 배틀 완전성을 full-env까지.
   중간 크기, 확실(parity 게이트).
2. **다른 family 통합** — forage/duel/muster를 jax_env에(현 family A only). M4 폭 + (B) 연결. 중간.
3. **tuned PPO** — A2C-lite를 제대로 된 PPO로(jax_train), 고-gym서 학습이 oracle에 얼마나 닿나 측정. (A) headroom 탐색.
4. **더 깊은 hard-benchmark** — "PPO 못 푸는" 변별. **큰 연구**(별도 이니셔티브). 절대 난이도.
5. **GPU 벤치(`vectorized-bench`)** — M4-EC3(≥10M GPU). **GPU 환경 필요**(현 .venv CPU) → 환경 갖춰질 때.
6. **(맨 마지막) 공개** — arXiv(EC4)+OSS/Hub(EC5)+데모 GIF(EC6). 사람 게이트.

> 개인 의견: 1·2는 확실·중간(M4 완성도/폭). 3은 (A) 학습 한계 탐색에 직접적. 4는 가장 가치 크나 큰 연구. 5는 환경 제약.

## 5. 코드 포인터 (이번 세션 산출 — 전부 main, `[jax]`/`[rl]` extra)

- `src/critter_gym/jax_env.py` — `JaxEnvConfig` + `make_jax_env(cfg)` factory(static-shape 클로저); module-level fns=default-config 인스턴스 보존.
- `src/critter_gym/jax_train.py` — JAX-native A2C(region bank + lax.scan + 손수 Adam) + `EnvSpec`/`default_env_spec`/`difficulty_env_spec`(config-aware) + `learning_verdict`(사전약정 R1) + `evaluate`.
- `src/critter_gym/jax_battle_full.py` — non-commit full battle(party/switch/item/force-switch/party-wipe, branch-free) + bridge.
- `scripts/jax_rl_demo.py` — `--difficulty`(고-gym) 학습 데모; `scripts/difficulty_generalization.py` — `--resolution`(scripted 분해능)·`--range-gap`(학습 gap).
- 테스트(importorskip, CI numpy-only): `test_jax_{parity,battle_parity,env_parity,train,difficulty_parity,battle_full_parity}.py` + `test_difficulty_dynamic_range.py`.

## 6. 하네스 메모 (이번 세션 학습)

- **freeze 전 pilot이 핵심**: #46서 pilot이 "스타터 다양화" 메커닉을 falsify(토너먼트 구조) → 헛수고·과대주장 차단·정직 reframe. parity 포트(#47·#48)마다 pilot이 0 mismatch를 freeze 전 입증.
- **l3-reviewer-maxturns 재발(이번 3회)** — plan-reviewer가 소스 조사 중 verdict 없이 종료. **SendMessage로 "추가 조사 없이 verdict만"** 회수하면 깨끗(전부 APPROVE 회수). 항구 수정 대기(retro 큐).
- **commit guard + 번호형 인가** — bounded-YOLO 표준 권한 부여로 진행. `.claude/projects/`(repo-로컬 stray)는 매 커밋 `git reset .claude/projects/`로 제외.
- **archive 이동**: 신규 plan/report untracked면 `git mv` 대신 일반 `mv`.
- **bounded-YOLO 운영**: 루틴 게이트(G1·verify·L3·task-end·commit·PR·머지) 자동 진행, 정지 조건(pilot falsify·reframe·공개[사람 게이트]·no-progress)만 멈춤. 엄밀성(pilot·사전약정·L3·parity)은 그대로.

## 7. 정직성 문화 (계승 필수)

매 task acceptance를 *성능*이 아니라 *측정+정직 보고*로 freeze. parity 0 mismatch로 가짜 속도 차단, 속도 이득=vmap 한정
명시, 학습=신호(tuned 아님)·범위 밖(hard-benchmark·full-env·GPU·tuned PPO) 정직 라벨. **사전약정 결정규칙**(데이터 보기 전
고정: R1 학습/분해능/parity 게이트)으로 p-hacking 차단, **pilot이 전제 검증**(falsify시 reframe), 다층 검증(pilot+parity+
adversarial L3). 헤드라인보다 정직성 — moat 층3(trust) 재료.

## 8. 사용자 메모 (계승)

사용자는 수학/RL 깊은 배경 아니나 **전략·정직성·방향 판단으로 지휘**. **매 task 시작·끝에 수식 없는 고등학생용 한 문단
요약(뭘/왜/비유/결과)**을 표·용어와 *별도로* 동반. bounded-YOLO 선호(루틴 자동·정지조건만 확인). 메모리 SSOT:
`~/.claude/projects/.../memory/`(`plain-language-task-summaries`·`user-non-math-background`).
