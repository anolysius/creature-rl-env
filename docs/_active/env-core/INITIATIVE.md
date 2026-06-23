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

(이후 task 는 /task-start 로 append)

## 다음 task
활성 마일스톤 **M3** 의 미충족 EC — **EC4 arXiv writeup**(측정 인프라 결과를 글로), **EC5 OSS 공개**
(MIT+Prime Intellect Hub). **EC6 충족**은 코드 task 가 아니라 실제 학습 에이전트의 held-out 보스격파
GIF 산출·결재(`scripts/killer_demo.py` 실행). 구성 task·EC 는 [milestones.md](../../reference/milestones.md) §M3.
측정(EC1·EC2·EC3) + 데모 인프라(EC6 토대·수단) 완료 — 남은 건 글쓰기·공개·실제 데모 산출.
