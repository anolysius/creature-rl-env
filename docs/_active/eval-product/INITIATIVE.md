# Initiative: eval-product (M5 — 비공개 재생성 eval 제품)

> **moat 층1→제품화.** CritterGym의 핵심 자산 = **매 평가마다 한 번도 본 적 없는 세계 + 숨은 규칙표를
> 재생성하고, 보상이 verifiable(RLVR)** → eval이 **오염·암기·게이밍 불가능**(DESIGN §9 층1 속성). 공개 env는
> 무료(신뢰·채택), **돈 되는 희소재 = 고객이 못 보는/못 외우는 held-out**(DESIGN §8 수익, M5).
>
> **마일스톤 SSOT**: roadmap.md · milestones.md (M5). **이 이니셔티브 = 기능적 moat의 유일 후보**(사용자와
> moat 논의 결론). **공개·고객·가격·GTM은 사람 게이트** — 본 이니셔티브는 *기능 토대*만 자율로 만든다.

## 왜 지금

- moat 판정(2026-06): 속도(M4)·난이도(hard-benchmark)는 *테이블 스테이크스*(복제 가능)이지 해자 아님.
  **방어 가능 해자 = 채택(층3, 사람) + 비공개 eval 제품(M5, 미착수)** 둘뿐. 후자의 *기능 토대*는 자율 가능.
- 시장 통증: **벤치마크 오염/포화**(contamination·leakage)가 지금 AI 평가의 #1 통증. 우리 재생성+RLVR
  속성이 *바로 그 답* — "외울 수도 오염될 수도 없는 eval".

## 핵심 메커니즘 (왜 moat)

- env seed→world 결정론 + held-out 구역(seed ≥ `TEST_SEED_OFFSET`=1,000,000, train < 1M).
- 평가자가 held-out 구역의 **비공개 블록**(secret offset)에서 신선한 세계를 생성 → 제출 agent를 거기서 채점.
- **오염 가드**: 제출자가 선언한 train seed가 eval 블록과 겹치면(또는 train 구역 밖이면) 검출 → "테스트로
  학습 못 함"이 *검증 가능*. 고정 벤치마크(언젠가 다 유출)가 못 주는 신뢰 = 파는 희소재.

## 북극성 (CLAUDE.md 종속)
1. 능력 *측정* 복무. 2. RLVR(boolean subgoal) 채점만 — hand-tuned 점수 금지. 3. procgen+seed split 비협상
(held-out 재생성·결정론·누수 0이 제품의 근간). 4. fast/vectorizable. 5. seeded·pinned. **정직성 > 헤드라인**
(프로토타입을 "제품 완성"으로 과대 금지 — 인프라/고객/공개는 사람).

## Task 목록
| # | slug | 상태 | 한 줄 |
|---|---|---|---|
| 1 | `sealed-eval-harness` | ✅ done (→ `_archive/2026-Q2/eval-product/01-sealed-eval-harness/`) | **봉인 held-out + agent 제출 → RLVR 검증 채점 프로토타입** — 신규 `critter_gym.eval_harness`(core·numpy): `SealedEvalSet`(secret master_seed→held-out 비공개 블록·재생성) + `verify_sealed`(오염 가드: train∩eval=∅ ∧ train<1M, leak 검출) + `score_agent`(verifiable subgoal-only 채점) + `Agent` Protocol. **demo**: oracle 1.88(100%)/type_blind 0.94(50%)/random 0.38(20%) of-oracle + leak 시도 overlap16 검출·거부 → **moat 메커니즘 end-to-end 입증**. **정직 경계**: 프로토타입·in-process 봉인·단일 머신·hosted 제품/고객/매출/공개 아님. 442→450(+8, 회귀0), mypy29/ruff/build clean. L3 2/2 APPROVE. |

(이후: held-out 봉인 인프라 강화·다중 config·agentic-LLM 어댑터·hosted 서비스 — 일부는 사람/전략 게이트)

## 정직성 문화 (계승)
프로토타입 = *기능 토대 데모*이지 hosted 제품·고객·매출이 아님(명시). 봉인="in-process 컨벤션"(실제 제품은
서버측 secret seed + 제출 샌드박스 필요). 단일 머신·numpy·단일 config. RLVR 검증 채점만(날조 0).
