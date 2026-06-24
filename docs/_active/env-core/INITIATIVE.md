# Initiative: env-core

> CritterGym 제품 코어 (Gymnasium env) 의 단계적 구축. DESIGN.md §6 로드맵 Phase 1~ 를 담는 멀티-task 묶음.
>
> **마일스톤 SSOT**: [roadmap.md](../../explanation/roadmap.md) (왜) · [milestones.md](../../reference/milestones.md) (사실).
> **활성 마일스톤: M3** (벤치마크 신뢰성 + 런치). M0·M1·M2 완료. 매 task 는 활성 M 의 미충족 EC 에서 내려온다.

## 목표
DESIGN.md 스펙을 실제 동작하는 Gymnasium 환경으로 구현한다. "dumbest-possible playable env"
(10×10, catch-only) 에서 시작해 full subgoal chain + procedural generation + train/test seed split
까지 성장시킨다.

## 북극성 (CLAUDE.md north-star 종속)
1. 모든 기능은 *에이전트 능력 측정* 에 복무 — 게임 재미 아님.
2. 리워드는 verifiable (RLVR) — boolean subgoal.
3. procgen + train/test seed split 비협상.
4. fast / vectorizable.
5. seeded·pinned reproducibility.

## Task 목록
| # | slug | 상태 | 한 줄 |
|---|---|---|---|
| 1 | `scaffolding` | ✅ done (→ `_archive/2026-Q2/env-core/01-scaffolding/`) | 패키지 레이아웃 + 툴체인 + 최소 catch-only env |
| 2 | `env-validation` | ✅ done (→ `_archive/2026-Q2/env-core/02-env-validation/`) | check_env + 베이스라인 spread + held-out 일반화 + throughput 가드 |
| 3 | `battle-system` | ✅ done (→ `_archive/2026-Q2/env-core/04-battle-system/`) | 턴제 배틀 sub-MDP 엔진 (M1-EC1) |
| 4 | `gym-boss-progression` | ✅ done (→ `_archive/2026-Q2/env-core/05-gym-boss-progression/`) | 배틀=gated checkpoint + env 통합 (M1-EC3/EC4) |
| 5 | `creature-evolution` | ✅ done (→ `_archive/2026-Q2/env-core/06-creature-evolution/`) | 진화 = long-horizon 투자 (M1-EC2) → **M1 완성** |
| 6 | `procgen-region` | ✅ done (→ `_archive/2026-Q2/env-core/07-procgen-region/`) | 시드→절차 region + train/test 분리 (M2-EC1) |
| 7 | `procgen-typechart` | ✅ done (→ `_archive/2026-Q2/env-core/08-procgen-typechart/`) | 시드별 내부정합 타입표, infer-the-meta (M2-EC2/EC3) |
| 8 | `generalization-harness` | ✅ done (→ `_archive/2026-Q2/env-core/09-generalization-harness/`) | train-vs-test 일반화 갭 측정 하네스 (M2-EC4) → **M2 완성** |
| 9 | `baseline-suite` | ✅ done (→ `_archive/2026-Q2/env-core/10-baseline-suite/`) | 베이스라인 4종 train+test 점수표 `critter_gym.scoreboard` (M3-EC1) |
| 10 | `leaderboard` | ✅ done (→ `_archive/2026-Q2/env-core/11-leaderboard/`) | 리더보드 포맷+재현 configs `critter_gym.leaderboard` + 키 개명 (M3-EC2) |
| 11 | `metrics-viz` | ✅ done (→ `_archive/2026-Q2/env-core/12-metrics-viz/`) | 측정 메트릭 플롯 4종 `critter_gym.viz` (matplotlib `[viz]` 격리) (M3-EC3) |
| 12 | `world-render` | ✅ done (→ `_archive/2026-Q2/env-core/13-world-render/`) | 월드 상태→픽셀 프레임 `critter_gym.render` + env rgb_array (M3-EC6 토대) |
| 13 | `killer-demo` | ✅ done (→ `_archive/2026-Q2/env-core/14-killer-demo/`) | 녹화 파이프라인 `critter_gym.demo` + `scripts/killer_demo.py` (M3-EC6 수단; EC6 미충족 유지) |
| 14 | `typechart-depth` | ✅ done-descoped (→ `_archive/2026-Q2/env-core/15-typechart-depth/`) | 타입 풀 3→15 + 보스 재출현 (M3 신뢰성; "추론 load-bearing"은 pilot로 불가 입증→future work) |
| 15 | `reasoning-load-bearing` | ✅ done (→ `_archive/2026-Q2/env-core/16-reasoning-load-bearing/`) | team-commit 보스 경제로 **추론 load-bearing scripted-arm 실증**(Gate0 0.48/Gate1 0.36, `CritterGym-commit-v0`); DESIGN §3.1.1 open problem 해소(학습 *학습*은 follow-up). M1 무회귀 |
| 16 | `learnability-measurement` | ✅ done (→ `_archive/2026-Q2/env-core/17-learnability-measurement/`) | 챔피언-선택 액션 UX(`_commit_window`) + `critter_gym.learnability` 측정 하네스. **PPO 100k 측정: learned ≫ probe/blind, infer 수준 = 양성 learnability 신호**(caveat: 진화합산/N16/단일run). (A) 학습 수준 작동 입증. M1 무회귀 |
| 17 | `genre-generalization-foundation` | ✅ done (→ `_archive/2026-Q2/env-core/18-genre-generalization-foundation/`) | (B) 장르 일반화 **측정 머신 토대**: `env_family`(공유 계약+registry) + `ForageEnv`(family B, contact-collect, same-seed→A≠B) + `genre_generalization`(env-level 갭). 2 패밀리=토대지 장르 주장 아님(gap=신호). family A 무회귀, check_env 4종 |
| 18 | `battle-system-family` | ✅ done (→ `_archive/2026-Q2/env-core/19-battle-system-family/`) | (B) **토대 강화 — 세 번째 family C** `DuelEnv`(`CritterGym-duel-v0`)가 **배틀 시스템 자체 교체**(타입-무관 stamina/commit RPS, family B의 thin 약점 메움). `genre_generalization` 다-family LOO + obs-only 레퍼런스 정책. **측정**: held-out=duel에서 A-튜닝 gap +3.917 ≫ C-적합 +0.167 = **skill-structural 신호**(난이도 아님; family B gap≈0이 못 만든 정책-특정 대조). 3 family도 증명 아닌 토대. family A/B 무회귀(160→171), check_env 5종 |
| 19 | `learnability-precision` | ✅ done (→ `_archive/2026-Q2/env-core/20-learnability-precision/`) | (A) learnability **정밀화** — #17 caveat(격파+진화 합산 착시) 해소. **gym-clear-only 메트릭**(`EpisodeOutcome` 진화 분리) + `--runs N` 다중 PPO seed. 측정: gym-clear oracle/infer 4.19 ≫ type_blind 1.81 > probe 1.06(순서 유지). 정직 caveat 3종(num_gyms 천장/oracle==infer 구분불가/단일config·다중run[rl]) DESIGN 명시. API 무회귀(171→174) |
| 20 | `family-d-muster` | ✅ done (→ `_archive/2026-Q2/env-core/21-family-d-muster/`) | (B) **토대 4-family 확장 — 진행 축** family D `MusterEnv`(`CritterGym-muster-v0`): 수집이 배틀력 좌우(CATCH→파티 공격력↑)+강한 보스 → 먼저 muster해야 승리. `genre_generalization` 4-family LOO + `rush_policy`/`muster_policy`. **측정**(within-family): D muster 1.42≫rush 0.00(load-bearing), A muster≤rush(무용)=skill-structural. raw LOO는 난이도 confound→within-family 대조로 통제(DESIGN 명시). 4 family도 증명 아닌 토대. A/B/C 무회귀(174→181), check_env 6종 |
| 21 | `arxiv-writeup` | ✅ done (→ `_archive/2026-Q2/env-core/22-arxiv-writeup/`) | **M3-EC4 전진(docs-only)** — 측정 자산을 arXiv 논문 초안으로 패키징: `docs/paper/critter-gym.md`(8섹션) + `docs/paper/README.md`(수치↔출처 재현 맵). 모든 수치 코드 근거(날조 0), CI-reproducible vs run-derived 라벨. Pokémon=메타포, (A) 측정/(B) 토대지 증명 아님 명시. L3 코드 대조 검증. 초안 산출(제출은 후속). 제품 코드 무회귀(181) |
| 22 | `oss-release-prep` | ✅ done (→ `_archive/2026-Q2/env-core/23-oss-release-prep/`) | **M3-EC5 전진(준비, docs-only)** — OSS 릴리스 로컬 산출물: MIT `LICENSE` 신규 + stale README→실제 상태 재작성(install·quickstart env id 6종·정직 positioning·측정 요약·citation) + `CONTRIBUTING.md`. 수치 논문 verbatim(L3 대조). **외부 발행(Hub/repo-public)=사람 게이트** 명시(EC5 자동충족 0). 제품 코드 무회귀(181) |
| 23 | `competitive-analysis` | ✅ done (→ `_archive/2026-Q2/env-core/24-competitive-analysis/`) | **공개 전 갭 탐지기(docs-only)** — OSS 벤치마크(Procgen/Craftax/XLand/NetHack) 대비 정직 비교 `docs/explanation/competitive-analysis.md`: capability 매트릭스 + 열위 먼저 트레이드오프 + peer [verify] 라벨 + **갭 register**(못함→필요기능→마일스톤). 결론: 공개 전 난이도 스케일·family 확장+학습정책·JAX가 최대 leverage. DESIGN §9 자기평가 준수. 제품 코드 무회귀(181) |
| 24 | `difficulty-generalization` | ✅ done (→ `_archive/2026-Q2/env-core/25-difficulty-generalization/`) | **(A) hard-and-gap≈0** — 갭 register "난이도" 항목 착수. pilot이 "깨끗한 단조 scripted 사다리" falsify(다차원/cliff/oracle 천장)→**학습정책 gap 실험**으로 reframe. `scripts/difficulty_generalization.py`([rl]): 난이도 점 3종×PPO held-in→held-in/held-out gap. **실측**(40k,N16): 모든 점 gap이 std 안(d2_hard +0.06±1.64) — 학습정책서도 gap≈0 consistent(약한 증거=신호). DESIGN §3.1.1 갱신. numpy-only 유지(181→183) |
| 31 | `transfer-budget-recovery` | ✅ done (→ `_archive/2026-Q2/env-core/32-transfer-budget-recovery/`) | **(B) 예산 RECOVERY + confound-reduced gap — "전이는 메커닉 이웃 안, duel로는 실패"**: #31 보류 probe(더 큰 예산) 실행. `budget_ladder_configs`+`--budgets`(baseline-net). **실측**(5run): 250k 2.44→**400k/500k 2.75**(held-in PLATEAU, 회복임계 2.5 통과=**RECOVERY**; 단일seed pilot 노이즈→multi-run 3번째 교정). RECOVERY라 **full-LOO @400k confound-reduced gap 재측정**: held-out critter −1.08±0.73/forage −1.48±0.51/muster −0.12 **(≤0=전이 OK)** vs **duel +1.73±0.61(robust 실패)**. held-in 회복(2.0~2.75=평범 아님)이라 **generalist-mediocrity 아닌 진짜 전이 실패**. **결론: (B)=real but structurally bounded — 메커닉 이웃(수집+타입상성) 안엔 전이, 진짜 다른 배틀시스템(duel)으론 실패. frontier를 cross-배틀시스템으로 국소화.** caveat: 음수 gap=난이도 비대칭도 반영·held-in 천장 2.75<2.94·단일 config. 196→197(+1 smoke, 회귀 0), mypy(22)/ruff/build clean. DESIGN §3.1.1+genre-generalization.md 갱신 |
| 30 | `transfer-capacity-budget` | ✅ done (→ `_archive/2026-Q2/env-core/31-transfer-capacity-budget/`) | **(B) 용량×예산 동시 스케일 — PARTIAL 회복, 예산이 lever·용량 아님**: #30(net만)·#28(예산만) 사이 안 해본 점. `held_in_sweep`+`SweepRow`+`--sweep`(muster fold multi-run, 천장 표+사전약정 회복임계 2.5). **실측**(5run): baseline-net **150k 2.07±0.62→250k 2.44±0.35**(std 조임)/big-net@250k **1.87±0.39**(robust 하락). **verdict=PARTIAL**(2.44>2.07,<2.5). ① **예산이 held-in 계속 올림→#28 "compute 병목 아님" 부분 정정**(저예산 외삽) ② **용량(큰 net) robust 해로움**=lever는 예산. 가장 긍정적: baseline@250k held-in 2.44·held-out 2.49·**gap −0.05≈0**(held-in 비평범+gap~0 첫 점; 단일 fold/config·큰 std=주장 아님). AC3: held-in<2.5→full-LOO gap 재측정 **보류**. **경계 미종결**(예산 아직 오름·용량 배제). 195→196(+1 smoke, 회귀 0), mypy(22)/ruff/build clean. DESIGN §3.1.1 + genre-generalization.md 갱신 |
| 29 | `transfer-skill-policy` | ✅ done (→ `_archive/2026-Q2/env-core/30-transfer-skill-policy/`) | **(B/a') 정책·obs 개선으로 held-in 끌어올리기 — 정직한 음성**: #28이 좁힌 "정책/obs 개선" 경로 직접 검증. `train_and_transfer`에 `net_arch`/`scale_obs` 노브+`--improved`+`_ScaleObs`(결정론). **pilot이 whole-obs `VecNormalize`=범주형 obs 망쳐 해로움 밝힘→제외**. **실측**(baseline vs improved, 50k×5run): 개선설정이 widened held-in을 **4 fold 전부 못 올리고 낮춤**(muster 1.73→1.15·duel 1.74→1.10·critter 0.86→0.65·forage 0.92→0.68, drop 대부분 std 초과=robust; net256+스케일 50k서 underfit). **정직 음성**: compute(#28)도 이 정책/obs 레버도 held-in을 #26(2.9)로 못 올림 → generalist-mediocrity confound **stubborn 잔존**, (B) 여전히 신호. AC3 조건부 held-in 미상승→gap 재측정 불요. **(B) 스레드 학술 narrative `docs/explanation/genre-generalization.md` 박제**. 194→195(+1 결정론 smoke, 회귀 0), mypy(22)/ruff/build clean. DESIGN §3.1.1 갱신 |
| 28 | `transfer-rigor` | ✅ done (→ `_archive/2026-Q2/env-core/29-transfer-rigor/`) | **(B) widened-train 전이 신호 robust 재측정 — multi-run + 예산↑**: #27 caveat(generalist-mediocrity·단일run) 메우기. `train_and_transfer_loo_multirun`+`--runs N`(run-간 mean±std)+`MultiRunFoldReport`. **사전약정 결정규칙**으로 사후 편향 차단. **실측**(50k·150k×5run, N16): ① gaps가 #26 +2.56보다 robust하게 훨씬 좁음(유지) ② 그러나 대체로 **held-in 하락**(0.9~2.1≪2.94); 예산↑는 held-in 약간만 상승(muster 1.73→2.07,<2.5)→generalist-mediocrity **축소되나 제거 안 됨**(병목=정책/obs) ③ **#27 음수 muster gap robust 아님**(+0.22±0.45/+0.44±0.72,std>gap=불확실; −0.25=노이즈) ④ duel robust 최난(+1.15±0.11). **단일-seed pilot의 "held-in 안 오름"도 노이즈→multi-run이 교정**. **pilot이 (a)예산↑전제 일부 falsify→AC7(ii)/R3 사전등록 분기로 정직 reframe**((a)=수정→발견). 정직 verdict: (B) 여전히 신호, 깨끗한 주장엔 **절대skill↑(정책/obs, compute·seed 아님)** 필요. 193→194(+1 smoke, 회귀 0), mypy(22)/ruff/build clean. DESIGN §3.1.1 갱신 |
| 27 | `genre-transfer-policy` | ✅ done (→ `_archive/2026-Q2/env-core/28-genre-transfer-policy/`) | **(B) 전이하는 학습 정책 — widened-train LOO 전이 측정(moat 층2 핵심)**: obs 조화(#27) 위에서 train 분포 확대(**duel 포함**)로 학습 정책의 unseen family 전이 gap 측정. `train_and_transfer_loo`+`--loo`(4 family LOO, #26과 동일 gap metric). **실측**(PPO 50k, N16, 단일run): unseen-muster gap **+2.56(2-family)→−0.25(3-family, duel 포함)**, 타 fold critter −0.92/forage −1.48/duel +1.08 — gap 0근처/음수로 붕괴=**wider train이 전이 돕는 양성 신호**. ⚠ **정직 caveat**: held-in 절대성능도 2.94→1.1~2.0 하락(generalist 평범화)→좁은/음수 gap은 균일 평범도 반영(증명 아님); 음수 gap=낮은 절대skill+held-out 쉬움 유력. (B) "측정상 미해결(#26)"→"wider train이 gap 좁힘(이 task)"=**신호지 증명 아님**(절대skill↑·multi-run 필요). 192→193(+1 smoke, 회귀 0), core numpy-only 유지, mypy(22)/ruff/build clean. DESIGN §3.1.1 갱신 |
| 26 | `obs-harmonization` | ✅ done (→ `_archive/2026-Q2/env-core/27-obs-harmonization/`) | **(B) 전이 정책 이니셔티브 선행 — 4-family obs 조화(enabler)**: #26이 obs 불일치로 제외하던 **duel(13키)을 포함**해 4 family(A/B/C/D)가 **단일 공유 obs 공간** 노출. `env_family.HARMONIZED_OBS_KEYS`(=`REQUIRED_OBS_KEYS` ∪ charge 2키) SSOT + `MAX_CHARGE_OBS`; base `CritterEnv`가 charge 0-마스킹 노출(비-duel)·`DuelEnv` 실제값 override(중복 space 제거). **freeze 전 pilot로 회귀 단 1건 실측→A안(코어 최소 침습) 확정**. 패딩 **행동 불변** 수치 증명(charge 키 제거 시 액션 동일). `assert_obs_compatible` 4 family 통과 + `_MultiFamilyEnv` 구성 smoke(**4-family 전이 *실험*은 다음 task**, gap 미축소). 마일스톤 override(M5 enabler를 M3 공개보다 먼저). 185→192(+7, 회귀 0), mypy(22)/ruff/build clean. DESIGN §3.1.1 갱신 |
| 25 | `genre-learned-transfer` | ✅ done (→ `_archive/2026-Q2/env-core/26-genre-learned-transfer/`) | **(B) 학습-정책 전이 첫 측정** — 갭 register "family+학습정책" 착수. `scripts/genre_learned_transfer.py`([rl]): train {critter,forage} PPO → held-out family {muster}(obs 동일 family만, duel 제외). **실측**(50k,N16): held-in 2.94±2.02 vs held-out 0.38±0.70, **gap +2.56** — 학습 정책이 unseen family로 전이 안 됨=**"(B) 미해결" 정직 신호**(증명 아님). 닫는 것=M5/층2. DESIGN §3.1.1 갱신. numpy-only 유지(183→185) |

(이후 task 는 /task-start 로 append)

## 다음 task
**현재 진행 중 이니셔티브 = "전이하는 학습 정책"(moat 층2, M5/갭 register 1순위) — 공개 전 기능 준비 우선**
(사람 방침: OSS/arXiv 제출은 맨 마지막). task 26(`obs-harmonization`)으로 **선행(4-family obs 조화) 완료**.
- ✅ **층2 측정(task 27) + robust 재측정(task 28) 완료** — widened-train LOO gap이 #26 +2.56보다 robust하게
  좁음(유지). 그러나 **(b) multi-run + 예산↑가 밝힌 한계**: 좁은 gap은 대체로 **held-in 하락**(generalist-mediocrity)
  탓이고, #27 음수 gap은 run 노이즈(불확실)였음. **(a) 예산↑로는 held-in이 약간만 오름(<2.5) = compute가 병목 아님**.
- ✅ **(a') 정책/obs 개선 검증 완료(task 29) — 정직한 음성**: net256+선택 obs스케일이 widened held-in을 4 fold
  전부 *낮춤*(50k서 underfit), whole-obs VecNormalize는 pilot서 해로움. → **compute(#28)도 단순 정책/obs(#29)도
  generalist-mediocrity confound 제거 못 함** = 값싼 경로 2개 정직하게 닫힘. **학술 narrative 박제:
  [`genre-generalization.md`](../../explanation/genre-generalization.md).**
- ✅ **(i) 용량+예산(task 30, PARTIAL) → 예산 RECOVERY(task 31) 완료**: 예산이 held-in을 **2.75로 회복**(용량은
  배제). 회복 상태 full-LOO에서 **critter/forage/muster 전이 OK(gap≤0), duel만 robust 실패(+1.73)** = generalist-
  mediocrity 아닌 진짜 전이 실패. **(B) 결론 = "real but structurally bounded": 메커닉 이웃 안 전이, cross-배틀시스템
  (duel) 실패.** 박제: [`genre-generalization.md`](../../explanation/genre-generalization.md).
- **다음(국소화된 frontier = cross-배틀시스템 전이)** — duel로 전이하는 정책: (i) **메커닉-범용 표현**(family/task
  embedding=contextual MDP), (ii) **duel-포함 커리큘럼**. 예산으론 안 됐으니(held-in 회복돼도 duel gap +1.73) 표현/
  커리큘럼이 다음. 또는 **(B)를 "structurally bounded 부분 주장"으로 arXiv 패키징하고 난이도·JAX로 피벗**(제품 신뢰성).
- 이후 옵션: 5~6번째 family 추가 / JAX 포트(속도=채택 게이트) / 난이도 ladder env 재설계 / multi-run learnability.
- **맨 마지막(M3 공개)**: arXiv 제출(EC4) + OSS repo-public·Hub(EC5) + 실제 학습 에이전트 데모 GIF(EC6) — 전부 사람 게이트.
  구성 EC 는 [milestones.md](../../reference/milestones.md) §M3.
