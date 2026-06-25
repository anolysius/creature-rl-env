# 인수인계서 — CritterGym (세션 이후: 4/4 family + v1.0.0-rc 패키징 + 절대난이도 진단 + 메모리 load-bearing)

> 다음 세션용. 직전 세션이 **bounded-YOLO 자율 런**으로 5 PR 머지: #55 duel(C) 포트(**4/4 family 벡터화**) ·
> #56 v1.0.0-rc 패키징 · #58 headroom 강한-baseline 진단(Q1) · #59 **메모리 load-bearing 입증**(Q1 정직 보정) ·
> #57 직전 핸드오프. 이 문서 = *무엇이 끝났고 / 정직한 결과 / 다음(권장: recurrent PPO)*. SSOT: `DESIGN.md`
> (§3.1.1·§4), `docs/explanation/jax-throughput.md`, `docs/explanation/competitive-analysis.md`,
> `docs/_active/{jax-throughput,difficulty-scaling,hard-benchmark}/INITIATIVE.md`, `docs/CHANGELOG.md`,
> `README.md`, `docs/paper/critter-gym.md`, `CLAUDE.md`(규율), 메모리(`autonomous-v1-mandate`·
> `plain-language-task-summaries`·`user-non-math-background`).

---

## 0. 오프닝 프롬프트 (새 세션에 붙여넣기)

> CritterGym 작업을 이어서 한다. 먼저 `docs/HANDOFF-next-session.md`, `docs/explanation/jax-throughput.md`
> (특히 마지막 두 Update: headroom-baseline-strength·recurrent-baseline), `docs/explanation/competitive-analysis.md`
> gap register, `DESIGN.md` §3.1.1+§4, `docs/_active/{difficulty-scaling,hard-benchmark}/INITIATIVE.md`,
> `docs/CHANGELOG.md` 상단, `src/critter_gym/jax_train.py`(특히 파일 끝 recurrent GRU A2C 섹션 + `train_ppo`),
> `scripts/recurrent_baseline.py`, `scripts/ppo_baseline.py` 를 읽어라. main HEAD=`f85cfeb`, **423 tests
> green**(2 skip), 버전 **1.0.0rc1**.
>
> [직전 세션 요약] 5 PR 머지. (1) #55 duel(C) JAX 통합=**4/4 family(A/B/C/D) 벡터화**(parity 0). (2) #56
> v1.0.0-rc 패키징(README/paper 헤드라인 통합 + `scripts/reproduce_results.py` 1-command 재현 + 버전
> 1.0.0rc1; 공개는 사람 게이트). (3) #58 headroom-baseline-strength(Q1): 강한 feedforward(width/depth/budget
> 스윕) baseline에도 oracle headroom **robust**(best 41%/25% of oracle plateau; depth·budget 무효=병목은
> capacity/compute 아님) — **단 robust=feedforward 한정 명시**. (4) #59 recurrent-baseline(hard-benchmark #1):
> 부분관측(5×5 view)서 **메모리 load-bearing 입증**(feedforward A2C 18% vs recurrent GRU A2C 46% of oracle,
> +0.79 robust; recurrent가 더 좁은데도 2.5× → 이득=memory) → **Q1 정직 보정**(headroom 상당부분이 no-memory
> 한계, recurrence가 18%→46% 회복). 전부 사전약정 규칙·freeze 전 pilot·정직 보고·L3 2/2 APPROVE.
>
> [이번 세션 권장 미션] **recurrent PPO** (hard-benchmark #2) — #59가 *A2C 내* 메모리 효과만 보였으므로,
> Q1(PPO)과 **동일 조건**에서 recurrent PPO vs feedforward PPO로 "recurrence가 PPO headroom을 닫는가"를
> 깨끗이 확정. **고난도 구현**(sequence-preserving minibatch: 시간축 셔플 불가 → 시퀀스 보존 minibatch +
> hidden replay). **correctness 먼저 입증**(망가진 recurrent PPO=misleading 결과; 통제 task로 검증 후 신뢰).
> 대안: 더 깊은 hard-benchmark(메모리 부담↑: 긴 호라이즌·다중타입 보스). 또는 GPU 측정(M4-EC3, 하드웨어 필요).
>
> [방침] 하네스 규율 100%(매 task `/task-start`→L1[plan-reviewer+qa 병렬 단일 메시지]→**freeze 전 pilot**→
> G1 freeze→TDD/G2[mypy·ruff·pytest·build]→L3 APPROVED[2 reviewer]→`/task-end`→commit→PR→merge). main 직접
> 금지=feature→PR→merge. **freeze 대상은 결과가 아니라 사전약정 결정규칙**(p-hacking 차단). parity 포트는
> 0 mismatch 비협상. 연구성 task는 pilot이 전제 검증(falsify시 정직 reframe), non-vacuity 가드로 공허한 결과
> 차단, **정직 경계 명시**(robust=무엇 한정·proxy·seed·CPU). **공개(OSS·arXiv·태그 push)는 끝까지 사람 게이트**.
> 매 task 시작·끝 수식 없는 한 문단 요약. `.claude/projects/`는 매 커밋 `git reset .claude/projects/`로 제외.
> L3 reviewer가 verdict 없이 maxturns 종료하면 **SendMessage로 "추가 조사 없이 verdict만"** 회수.

---

## 1. 현재 상태 (한 줄)

M0·M1·M2 ✅, M3 대부분(EC4 arXiv·EC5 OSS=사람 게이트), **M4 거의**(4/4 family·tuned PPO·robust headroom·
1-command 재현·버전 1.0.0rc1; **GPU EC3만 남음=하드웨어**), **(A) 난이도**: headroom robust-to-feedforward +
**메모리 load-bearing(부분관측)**. **423 tests**(2 skip). main HEAD=`f85cfeb`. 활성 이니셔티브: `jax-throughput`
(1–11 done), `difficulty-scaling`(1–4 done), **`hard-benchmark`(신규; #1 recurrent-baseline done)**.

## 2. 직전 세션 5 PR (전부 main 머지)

| PR | task | 정직한 결과 |
|---|---|---|
| #55 | `jax-duel-integration` | duel(C) type-agnostic RPS 배틀을 jax_env 통합(동시 데미지·raw 데미지·charge obs). numpy `DuelEnv` 대비 **parity 0**. **4/4 family 벡터화**. vmap 40–83×. |
| #56 | `v1-results-packaging` | README/paper에 헤드라인 통합(JAX 27–1047×·4 family / PPO 21–28% of oracle) + `reproduce_results.py` 1-command 재현 + 버전 **1.0.0rc1**. 공개=사람 게이트 명시. src 무변경. |
| #58 | `headroom-baseline-strength` (Q1) | 강한 feedforward(width/depth/budget) baseline에도 oracle headroom **robust**(best 41%/25% plateau; **depth·budget 무효**=병목 capacity/compute 아님). **단 robust=feedforward 한정**(recurrent 미배제 명시). |
| #59 | `recurrent-baseline` (hard-benchmark #1) | 부분관측(5×5 view)서 **메모리 load-bearing**: feedforward A2C 18% vs recurrent GRU A2C 46% of oracle(+0.79 robust; recurrent가 더 좁은데도 2.5×=memory 효과). **Q1 정직 보정**: headroom 상당부분 no-memory 한계, recurrence가 18%→46% 회복(단 46%서 잔존). |

## 3. ⚠ 정직한 결론 (과대 금지)

- **M4**: 4/4 family + 양 배틀경제 + tuned PPO 벡터화·parity 0. **vmap 한정·CPU·GPU(EC3) 미측정**(유일 잔여).
- **(A) 절대 난이도 = "메모리 요구 부분관측 과제"로 특성화**: headroom이 강한 *feedforward* 스케일링엔 robust
  (capacity/compute 병목 아님)지만, **recurrence(메모리)가 부분관측 headroom 크게 회복(18%→46%)** → "절대적으로
  hard"가 아니라 "메모리 agent가 절반 회복하나 oracle 미도달(잔존 headroom)". env가 메모리 agent를 **변별**
  (벤치마크 virtue). **미해결**: recurrent *PPO*(Q1 깨끗 연결)·더 강한 메모리 부담·SOTA agent.
- **헤드라인 자산**: (1) competitively fast(4 family·재현 가능) (2) **메모리-요구 부분관측 변별 벤치마크**(neat).

## 4. 다음 세션 — 갈래 (권장순)

1. **recurrent PPO** (hard-benchmark #2, **권장**): Q1(PPO)과 동일 조건서 recurrent PPO vs feedforward PPO →
   "recurrence가 PPO headroom 닫는가" 깨끗 확정. **고난도**(sequence-preserving minibatch + hidden replay;
   A2C는 full-rollout이라 쉬웠지만 PPO는 minibatch 셔플이 recurrence 깸). **correctness 먼저**(통제 task 검증).
   현 `jax_train`의 recurrent A2C(`train_recurrent`/`make_recurrent_rollout`/`recurrent_a2c_loss`)가 GRU 셀·
   rollout·eval 재료 제공.
2. **더 깊은 hard-benchmark**: 메모리 부담↑(긴 호라이즌·다중타입 보스·부분관측 강화)로 "메모리 agent에도 hard".
   단 spec 변경=JAX 재포트. scout가 grid16(큰 지도)=A2C 학습불가 inconclusive 확인(grid10/5×5가 sweet spot).
3. **GPU 측정**(M4-EC3, `vectorized-bench`): ≥10M steps/s **GPU**. 현 .venv는 CPU jax → **하드웨어 필요**(사람).
4. **공개**(M3-EC4/EC5): OSS 리스팅·arXiv 제출·`git tag v1.0.0` push = **사람 게이트**. competitive-analysis
   peer-fact `[verify]` 항목(Procgen/Craftax/XLand 수치·라이선스)은 공개 전 1차 출처 확인 필요.

## 5. 코드 포인터 (이번 세션 산출, 전부 main)

- `src/critter_gym/jax_env.py` — `_FAM_DUEL` + `duel_battle_branch` + charge obs(family-aware). 4/4 family.
- `src/critter_gym/jax_train.py` — feedforward `init_params`/`apply_policy`(**depth 노브** 추가, depth=1
  byte-identical)/`train`/`train_ppo`(`PPOConfig.depth`)/`evaluate_gym_clears` + **recurrent GRU A2C**(파일 끝:
  `gru_init_params`/`gru_step`/`recurrent_policy_value`/`make_recurrent_rollout`/`recurrent_a2c_loss`/
  `train_recurrent`/`evaluate_gym_clears_recurrent`[matched eval]).
- `scripts/` — `reproduce_results.py`(1-command throughput+headroom) · `ppo_baseline.py`(`--strong` capacity×budget
  스윕 best-of) · `recurrent_baseline.py`(부분관측 ff vs rec, 사전약정 memory-load-bearing).
- 테스트(importorskip, CI numpy-only): `test_jax_{...}_parity.py` 4 family + `test_jax_ppo.py`(+depth) +
  `test_jax_recurrent.py`(+4 GRU).

## 6. 하네스 메모 (이번 세션 학습)

- **scout/pilot이 방향 reframe 2회**: "시야 줄이기" falsify(obs_dim 오염·feedforward 안 나빠짐) → 지도-스케일 →
  grid16=A2C 학습불가 → **부분관측 메모리 load-bearing**(grid10/5×5)으로 수렴. **non-vacuity 가드가 내 첫
  가정("제일 깊은 게 제일 강하다") 자동 falsify**(깊은 net이 tiny보다 못함) → best-of-sweep로 정직 재정의.
- **single-run은 노이즈**: recurrent 1-seed 1.44를 3-seed matched로 검증 후에만 보고(프로젝트 "single-run 4회
  교정" 문화 계승). **matched eval**(ff/rec 동일 protocol)로 가짜 effect 차단.
- **archive `git mv`**: untracked task 폴더는 `git mv` 실패 → plain `mv` 후 `git add`.
- **pytest 요약줄 non-tty 억제**: redirect 시 "N passed" 안 보임 → **exit code(0)로 판정**.
- **L3 maxturns**: reviewer가 verdict 없이 종료 → `SendMessage`로 "추가 조사 없이 verdict만" 회수(이번에도 2회).
- **bounded-YOLO 자율 런**: 정지 조건(pilot falsify·결과 reframe·공개[사람]·하드웨어[GPU])만 멈춤. 결과가
  reframe(예: 메모리 load-bearing이 Q1 보정)되면 멈추고 사람 보고 후 방향 확인.

## 7. 정직성 문화 (계승 필수)

매 task acceptance를 *성능* 아닌 *측정+정직 보고*로 freeze. **사전약정 결정규칙(데이터 전 고정)이 freeze 대상**
(결과 아님)으로 p-hacking 차단. parity 0으로 가짜 속도 차단. **연구성 task**: pilot이 전제 검증(falsify시
reframe), non-vacuity 가드(공허한 결과 차단), **정직 경계 명시**(robust=무엇에 한정인가·proxy·seed·CPU·후속).
헤드라인을 보정하는 결과(예: 메모리 load-bearing이 Q1 "robust"를 feedforward 한정으로 좁힘)도 **숨기지 않고
docs에 반영**. 헤드라인보다 정직성 — moat 층3(trust) 재료.

## 8. 사용자 메모 (계승)

사용자는 수학/RL 깊은 배경 아니나 **전략·정직성·방향으로 지휘**. **매 task 시작·끝 수식 없는 한 문단 요약**
(뭘/왜/비유/결과). **자율 mandate**(메모리 `autonomous-v1-mandate`): moat/v1.0.0까지 bounded-YOLO 자율 task
연속+커밋푸시, **공개는 사람 게이트**. **moat 논의 결론**(사용자와): 기능적 moat는 사실상 **M5 비공개 재생성
eval 제품** 하나(미착수); L2 축적·L3 채택은 GTM/연구규모. 절대 난이도(메모리-요구 부분관측)는 그 자체로
*벤치마크 변별력* 자산이나 "방어가능 moat"는 아직(adoption 0). **다음 큰 방향 결정은 사람**.
