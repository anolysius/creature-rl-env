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

| 2 | `llm-eval-adapter` | ✅ done (→ `_archive/2026-Q2/eval-product/02-llm-eval-adapter/`) | **오염 방지 agentic-LLM 평가 어댑터** — 신규 `critter_gym.llm_eval`(core·numpy): `render_obs`(obs→LLM 텍스트·결정론) + `parse_action`(free-text→action·숫자/키워드/fallback/클램프·항상 [0,n)) + `LLMAgent`(provider-agnostic `complete` 주입 → #1 `Agent` Protocol 만족 → #1 `score_agent`[봉인 set] 채점) + `anthropic_complete`(옵션 lazy-import·`claude-opus-4-8`·claude-api 준수). demo: stub-LLM을 봉인 set서 end-to-end 채점. **정직 경계**: 어댑터=메커니즘이지 실측 LLM 능력 결과 아님(stub 검증·실측=API key+비용 별도 run)·프로토타입. 450→461(+11, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. |

| 3 | `llm-eval-run` | ✅ done (→ `_archive/2026-Q2/eval-product/03-llm-eval-run/`) | **실제 LLM 비용-제한 sealed-eval 러너** — "프런티어 LLM이 우리 봉인 환경서 몇 % of oracle?" 실측 도구. `SealedEvalSet`에 `max_steps` 노브(기본 200 byte-identical·비용 상한) + 신규 `scripts/llm_eval_run.py`(model/worlds/max-steps + 비용 경고 + frac_of_oracle 출력). #2 `LLMAgent`+`anthropic_complete`로 `claude-opus-4-8` 등을 #1 봉인 set서 `score_agent`. **실행=사용자 로컬**(키=사용자·채팅 금지·SDK env). 정직 경계(작은 probe·step 상한·proxy oracle·단일 run). 461→463(+2, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. |

| 4 | `claude-cli-provider` | ✅ done (→ `_archive/2026-Q2/eval-product/04-claude-cli-provider/`) | **구독(claude CLI) provider + score_agent 콜 절반** — (1) `llm_eval.claude_cli_complete`(`claude -p`·중립 cwd·구독 인증·API 키 불요) + 러너 `--provider {anthropic, claude-cli}`. (2) `score_agent` 이중-실행(`_caught_rate` 재실행) 제거 → `_play_once`로 seed당 1 패스(콜 절반), 메트릭 byte-equivalent. 463→465(+2, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. 후속: 구독으로 적정 호라이즌 실측. |

| 5 | `stateful-llm-agent` | ✅ done (→ `_archive/2026-Q2/eval-product/05-stateful-llm-agent/`) | **기억 가진 LLM agent(스텝 간 history+윈도잉) — 공정한 재측정 도구** — 신규 `llm_eval.StatefulLLMAgent`(에피소드 내 (obs digest, action) 슬라이딩 윈도우[기본 8] 누적 → 프롬프트에 prepend; `reset()`로 월드 경계서 clear) + `eval_harness.Agent` Protocol에 **선택적 `reset()` 훅**(`score_agent`가 duck-typing으로 에피소드마다 호출 → **월드 간 기억 격리**) + 러너 `--stateful --window K`. 무기억 `LLMAgent`는 floor(부분관측서 메모리 load-bearing — recurrent-baseline과 일관)하므로 *기억을 줬을 때* "프런티어 LLM이 봉인 환경서 몇 % of oracle"을 공정하게 잴 수 있는 토대. **정직 경계**: 메커니즘이지 측정 결과 아님(CI=stub); 실측 probe=사용자 로컬(구독 CLI/API); 결과 reframe 금지·"과금 0" 주장 금지. 무상태 경로 **byte-identical**(reset 없는 submission 분기 skip). 465→474(+9, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. 후속: 적정 호라이즌 stateful probe 실측. |

(이후: 적정 호라이즌 실측 run으로 "프런티어 LLM N% of oracle" 기록 / 서버측 봉인 인프라·다중 config·hosted 서비스 — 사람/전략 게이트)

## 정직성 문화 (계승)
프로토타입 = *기능 토대 데모*이지 hosted 제품·고객·매출이 아님(명시). 봉인="in-process 컨벤션"(실제 제품은
서버측 secret seed + 제출 샌드박스 필요). 단일 머신·numpy·단일 config. RLVR 검증 채점만(날조 0).
