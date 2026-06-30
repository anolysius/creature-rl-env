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
| 13 | `agentic-battle-memory` | ✅ done (→ `_archive/2026-Q2/eval-product/13-agentic-battle-memory/`) | **전투-결과를 기억하는 agentic 메모리 — "얇은 어댑터" confound 제거** — #11 floor(inference_score 0.00=`at-chart-blind-floor`)가 *능력 verdict*인지 *측정 아티팩트*인지 가르는 토대. confound 정체: `StatefulLLMAgent`(#5)의 `_obs_summary`가 위치+gyms만 담아 "무브→데미지" 효과성 신호를 구조적으로 버림 ↔ `DEFAULT_SYSTEM`(#7)은 "적 hp 낙폭 관찰·기억하라" 지시 = 지시↔메커니즘 불일치. 신규 `BattleMemoryLLMAgent(StatefulLLMAgent)`: 연속 in-battle obs diff → 직전 공격무브의 enemy_hp 낙폭을 `{enemy_type:{move:최신데미지}}`(단일값 덮어쓰기, ≤num_types×4 bounded)로 귀속 → 프롬프트에 **원시 관찰 사실**로 surface(정답-무브 추천 없음=측정 무결성). `reset()` 격리, 러너 `--battle-memory`. 귀속 견고성: 스칼라 스냅샷(별칭 버그 차단)+단일보스 불변식(교체 오귀속 도달불가). 무회귀: 기존 어댑터 무변경, scripted arm byte-identical. 실 env sanity(`{2:{1:10}}`). 502→**512**(+10, 회귀0), mypy31/ruff/build clean. L3 2/2 APPROVE(SUGGEST 5건 반영). **정직 경계**: 메커니즘이지 측정 결과 아님; 실측은 사용자 로컬; 어댑터 두껍게=후속 측정 공정화일 뿐 floor 아티팩트 증명 아님; attrition·표본 confound 잔존→reframe 금지. 후속(사용자): `--battle-memory --runs N` 재측정. |
| 1 | `sealed-eval-harness` | ✅ done (→ `_archive/2026-Q2/eval-product/01-sealed-eval-harness/`) | **봉인 held-out + agent 제출 → RLVR 검증 채점 프로토타입** — 신규 `critter_gym.eval_harness`(core·numpy): `SealedEvalSet`(secret master_seed→held-out 비공개 블록·재생성) + `verify_sealed`(오염 가드: train∩eval=∅ ∧ train<1M, leak 검출) + `score_agent`(verifiable subgoal-only 채점) + `Agent` Protocol. **demo**: oracle 1.88(100%)/type_blind 0.94(50%)/random 0.38(20%) of-oracle + leak 시도 overlap16 검출·거부 → **moat 메커니즘 end-to-end 입증**. **정직 경계**: 프로토타입·in-process 봉인·단일 머신·hosted 제품/고객/매출/공개 아님. 442→450(+8, 회귀0), mypy29/ruff/build clean. L3 2/2 APPROVE. |

| 2 | `llm-eval-adapter` | ✅ done (→ `_archive/2026-Q2/eval-product/02-llm-eval-adapter/`) | **오염 방지 agentic-LLM 평가 어댑터** — 신규 `critter_gym.llm_eval`(core·numpy): `render_obs`(obs→LLM 텍스트·결정론) + `parse_action`(free-text→action·숫자/키워드/fallback/클램프·항상 [0,n)) + `LLMAgent`(provider-agnostic `complete` 주입 → #1 `Agent` Protocol 만족 → #1 `score_agent`[봉인 set] 채점) + `anthropic_complete`(옵션 lazy-import·`claude-opus-4-8`·claude-api 준수). demo: stub-LLM을 봉인 set서 end-to-end 채점. **정직 경계**: 어댑터=메커니즘이지 실측 LLM 능력 결과 아님(stub 검증·실측=API key+비용 별도 run)·프로토타입. 450→461(+11, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. |

| 3 | `llm-eval-run` | ✅ done (→ `_archive/2026-Q2/eval-product/03-llm-eval-run/`) | **실제 LLM 비용-제한 sealed-eval 러너** — "프런티어 LLM이 우리 봉인 환경서 몇 % of oracle?" 실측 도구. `SealedEvalSet`에 `max_steps` 노브(기본 200 byte-identical·비용 상한) + 신규 `scripts/llm_eval_run.py`(model/worlds/max-steps + 비용 경고 + frac_of_oracle 출력). #2 `LLMAgent`+`anthropic_complete`로 `claude-opus-4-8` 등을 #1 봉인 set서 `score_agent`. **실행=사용자 로컬**(키=사용자·채팅 금지·SDK env). 정직 경계(작은 probe·step 상한·proxy oracle·단일 run). 461→463(+2, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. |

| 4 | `claude-cli-provider` | ✅ done (→ `_archive/2026-Q2/eval-product/04-claude-cli-provider/`) | **구독(claude CLI) provider + score_agent 콜 절반** — (1) `llm_eval.claude_cli_complete`(`claude -p`·중립 cwd·구독 인증·API 키 불요) + 러너 `--provider {anthropic, claude-cli}`. (2) `score_agent` 이중-실행(`_caught_rate` 재실행) 제거 → `_play_once`로 seed당 1 패스(콜 절반), 메트릭 byte-equivalent. 463→465(+2, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. 후속: 구독으로 적정 호라이즌 실측. |

| 12 | `inference-telemetry` | ✅ done (→ `_archive/2026-Q2/eval-product/12-inference-telemetry/`) | **직접 추론 메트릭 — super-effective 무브 사용률(attrition 우회)** — 전투 `damage=max(1)`라 살면 중립 attrition 승 → gym-clear 기반 KPI가 sweet spot 못 잡음(전투 모델 변경=벤치마크 정의=사람 게이트). 자율안전 대안(사용자 결정): env **read-only**, 전투 move-결정마다 chosen move eff>1.0 비율 측정 = 추론 exploit을 *승리와 분리*해 직접 잼. 신규 `InferenceTelemetry`+`score_inference_telemetry`(`_super_effective_move` read-only, action 4/5 제외, 0-move 가드) + 러너 `--telemetry`(submission+oracle/type_blind 앵커). **변별: oracle SE-rate 61% vs type_blind 7%**. env 무변경 → score_agent byte-identical. 498→502(+4, 회귀0), mypy31/ruff/build clean. L3 2/2 APPROVE. 정직: exploit≠추론 증명·점수 보장 아님. |

| 11 | `inference-measurement-sync` | ✅ done (→ `_archive/2026-Q2/eval-product/11-inference-measurement-sync/`) | (quick-fix) #10 도구로 첫 robust 측정 반영 — claude-opus-4-8, inference-gated demonstrator: 40스텝 3 runs → **inference_score 0.00±0.00 = at-chart-blind-floor**(노이즈 아님) + 호라이즌 sweep 40/60/120 모두 0.00 → floor는 *추론-bound, 예산-bound 아님*. competitive-analysis 정직 갱신. docs-only, L3 APPROVE. |

| 10 | `inference-score-rigor` | ✅ done (→ `_archive/2026-Q2/eval-product/10-inference-score-rigor/`) | **inference_score 측정 robust화 — 사전약정 multi-run 분류기** — #8 첫 KPI(단일 run 0.00)를 노이즈 아닌 robust verdict로 격상. 신규 `inference_rigor.classify_inference`(per-run inference_score들의 mean±std로 3-branch: `m−k·s≥0.5`→**infers** / `m+k·s≤0.1`→**at-chart-blind-floor** / else **inconclusive**; 임계 데이터 전 freeze=p-hacking 차단; numpy-only CI; `headroom.py` 패턴 mirror) + 러너 `--runs N` 집계(N=1 무회귀). 분류기=*도구*(verdict 그대로 기록, 결과 단정 안 함); 실측 N-run LLM은 후속. 집계 검증: oracle×3→infers / type_blind×3→at-floor. 489→498(+9, 회귀0), mypy31/ruff/build clean. L3 2/2 APPROVE. |

| 9 | `eval-product-narrative-sync` | ✅ done (→ `_archive/2026-Q2/eval-product/09-eval-product-narrative-sync/`) | (quick-fix) competitive-analysis "monetizable eval" 행에 #5~#8 측정 토대 + 첫 probe inference_score 0.00(non-saturated 신호, 약한 증거)을 정직 반영. docs-only, L3 qa-verifier APPROVE. |

| 8 | `inference-score-metric` | ✅ done (→ `_archive/2026-Q2/eval-product/08-inference-score-metric/`) | **고객용 moat 지표 — 봉인 eval의 in-context 추론 정량화** — `Scorecard.inference_score = (submission−type_blind)/(oracle−type_blind)` [0,1] 클램프(`0`=규칙 모르는 baseline / `1`=expert; 분모≤0이면 0). probe 여정(#5~7)+scout로 확인한 **oracle 100% vs type_blind 50%** 추론 gap 위 LLM 위치를 단일 KPI로 — 처음 보는 봉인 세계서 숨은 규칙을 in-context 추론해야만 오르므로 **암기·오염·게이밍 불가**(고정 벤치마크가 못 주는 희소재의 정량 증거). + `SealedEvalSet`에 `grid_size`·`boss_hp/atk/def` 노브(기본=CritterEnv 기본 → byte-identical)로 navigable+inference-gated demonstrator config 타깃. 러너에 노브 CLI + 고객용 3-arm+inference_score 출력 + demonstrator preset(grid5·types3·boss140/6/18). **정직 경계**: 지표=특정 band 신호이지 절대 능력치 아님·점수 보장 아님·demonstrator 시연용. 484→489(+5, 회귀0; 기본 byte-identical), mypy30/ruff/build clean. L3 2/2 APPROVE. 후속: demonstrator config 실측으로 첫 inference_score 기록. |

| 7 | `battle-legibility` | ✅ done (→ `_archive/2026-Q2/eval-product/07-battle-legibility/`) | **전투 obs 가독성 — LLM이 숨은 타입표 추론 루프에 진입하게** — #6 후에도 0% floor → existence probe(grid5·types3·1gym)로 **탐색 벽 제거 후에도 보스전 전패**(19전투) 확인. 같은 config 대조: oracle 클리어(3턴)/type_blind 59턴 전패/**LLM=type_blind처럼 move0만 반복·교체/커밋 미사용·2턴 사망·catch 혼동**. 수정: `DEFAULT_SYSTEM`에 전투 전략(무브 0~3=다른 숨은 타입·시도+적 hp 관찰+기억·`spamming move 0 usually loses`·action4 교체·패배 후 재진입) + catch 명확화(C 타일 정확히, gym/빈 타일 무동작); `render_obs` 전투 분기 Tip(무브 다양화·적 hp 관찰·교체). **벤치마크 정직성**: super-effective 정답 미노출 — "시도→관찰→기억" 전략만(추론은 LLM 몫=env가 측정하려는 능력). obs 스키마 무변경. scripted 수치 불변. 480→484(+4, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. 후속: 재측정으로 클리어 여부 확인. |

| 6 | `render-obs-legibility` | ✅ done (→ `_archive/2026-Q2/eval-product/06-render-obs-legibility/`) | **render_obs 가독성 수정 — LLM 오도 제거** — #5 stateful probe가 무상태·stateful 모두 **0% of oracle** floor → 1 에피소드 transcript 진단(seed 1506920)으로 원인이 **render_obs 오도**임을 확정(난이도/파싱 아님): (1) env가 오버월드서 0-마스킹하는 `player_*`를 그대로 "Your creature: hp 0..."로 찍어 LLM이 "생물 없음" 오판(실제론 starter_party 보유) (2) gym(G) 타일을 creature로 착각해 보스전 패배 루프. 수정: `render_obs`가 in_battle 분기(전투 중만 스탯), 오버월드엔 "스타터 파티 보유" 정직 표현 + 시야 G/C 살라언스(방향구)·중앙 gym 진입 플래그 + `DEFAULT_SYSTEM`에 파티·목표·catch 설명. **정직 경계**: obs에 없는 정보(파티 마릿수) 날조 금지(진실 한도만); 렌더 수정≠점수 보장(호라이즌/전투 난이도 잔존). scripted score_agent 수치 불변(렌더↔채점 분리). 474→480(+6, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. 후속: 수정 후 stateful probe 재측정. |

| 5 | `stateful-llm-agent` | ✅ done (→ `_archive/2026-Q2/eval-product/05-stateful-llm-agent/`) | **기억 가진 LLM agent(스텝 간 history+윈도잉) — 공정한 재측정 도구** — 신규 `llm_eval.StatefulLLMAgent`(에피소드 내 (obs digest, action) 슬라이딩 윈도우[기본 8] 누적 → 프롬프트에 prepend; `reset()`로 월드 경계서 clear) + `eval_harness.Agent` Protocol에 **선택적 `reset()` 훅**(`score_agent`가 duck-typing으로 에피소드마다 호출 → **월드 간 기억 격리**) + 러너 `--stateful --window K`. 무기억 `LLMAgent`는 floor(부분관측서 메모리 load-bearing — recurrent-baseline과 일관)하므로 *기억을 줬을 때* "프런티어 LLM이 봉인 환경서 몇 % of oracle"을 공정하게 잴 수 있는 토대. **정직 경계**: 메커니즘이지 측정 결과 아님(CI=stub); 실측 probe=사용자 로컬(구독 CLI/API); 결과 reframe 금지·"과금 0" 주장 금지. 무상태 경로 **byte-identical**(reset 없는 submission 분기 skip). 465→474(+9, 회귀0), mypy30/ruff/build clean. L3 2/2 APPROVE. 후속: 적정 호라이즌 stateful probe 실측. |

(이후: 적정 호라이즌 실측 run으로 "프런티어 LLM N% of oracle" 기록 / 서버측 봉인 인프라·다중 config·hosted 서비스 — 사람/전략 게이트)

## 정직성 문화 (계승)
프로토타입 = *기능 토대 데모*이지 hosted 제품·고객·매출이 아님(명시). 봉인="in-process 컨벤션"(실제 제품은
서버측 secret seed + 제출 샌드박스 필요). 단일 머신·numpy·단일 config. RLVR 검증 채점만(날조 0).
