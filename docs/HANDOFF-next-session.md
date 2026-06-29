# 인수인계서 — CritterGym (세션 이후: eval-product moat-KPI 인프라 #5~#12)

> 다음 세션용. 직전 세션이 **bounded-YOLO 자율 런**으로 eval-product 이니셔티브 **#5~#12 (8 PR #70~#77 전부 main 머지)**를
> 완료 — "오염·암기 불가능한 in-context 규칙추론 eval"의 **측정 인프라 + 고객용 KPI + robust화 + 직접 추론 메트릭**.
> 이 문서 = *무엇이 끝났고 / 정직한 측정 결론 / 남은 사람-게이트 갈래*. SSOT: `docs/explanation/competitive-analysis.md`
> (gap register "monetizable eval" 행), `docs/_active/eval-product/INITIATIVE.md`(#1~#12 표),
> `docs/CHANGELOG.md` 상단(eval-product), `src/critter_gym/{eval_harness,llm_eval,inference_rigor}.py` +
> `scripts/llm_eval_run.py`, `CLAUDE.md`(규율), 메모리(`autonomous-v1-mandate`·`auto-mode-blocks-self-merge`·
> `plain-language-task-summaries`·`user-non-math-background`).

---

## 0. 오프닝 프롬프트 (새 세션에 붙여넣기)

> CritterGym 작업을 이어서 한다. 먼저 `docs/HANDOFF-next-session.md`, `docs/explanation/competitive-analysis.md`
> gap register, `docs/_active/eval-product/INITIATIVE.md`(#1~#12), `docs/CHANGELOG.md` 상단,
> `src/critter_gym/{eval_harness,llm_eval,inference_rigor}.py` + `scripts/llm_eval_run.py`, `CLAUDE.md`(규율),
> 메모리(autonomous-v1-mandate·auto-mode-blocks-self-merge·plain-language-task-summaries·user-non-math-background)를
> 읽어라. main HEAD=`88a72f0`, **502 tests green**(2 skip), 버전 **1.0.0rc1**. `.venv`에 pytest/mypy/ruff
> 있음(`python3` 기본엔 없음 — `.venv/bin/python -m pytest`).
>
> [직전 세션 요약 — eval-product #5~#12, 8 PR 머지] "외울·오염 불가능한 in-context 규칙추론 eval"의 기능 토대 완성:
> #5 stateful LLMAgent(에피소드 내 기억+윈도잉+reset, 월드간 격리) · #6 render-obs 가독성(0-mask 오도 제거+G/C
> 살라언스) · #7 battle 가독성(무브=숨은 타입·교체·재시도 안내, 정답은 미노출=추론은 LLM 몫) · #8 **inference_score
> KPI**=(submission−type_blind)/(oracle−type_blind)∈[0,1] + SealedEvalSet grid/boss 노브 · #9 competitive-analysis
> 정직 반영(quick-fix) · #10 **inference_rigor.classify_inference**(사전약정 multi-run 분류기, headroom.py 패턴) +
> 러너 `--runs` · #11 robust 측정 반영(quick-fix) · #12 **inference-telemetry**(super-effective-무브 사용률, env
> read-only, attrition 우회) + 러너 `--telemetry`. 매 task 풀 lifecycle(L1 2/2→G1→TDD→G2→L3 2/2→archive→PR→merge),
> 정직 경계 100%, HARNESS_ALLOW_COMMIT=1 커밋.

---

## 1. 무엇이 끝났나 (이번 세션)

`eval-product` 이니셔티브 = **M5 기능적 moat 유일 후보**("비공개 재생성 eval 제품"). 이번 세션에 *측정 도구 체인*을 완성:

| 산출 | 파일 |
|---|---|
| 봉인 held-out + 오염가드 + RLVR 채점 (이전 #1~#4) | `eval_harness.py` (`SealedEvalSet`/`verify_sealed`/`score_agent`/`Agent`) |
| LLM 어댑터 (render/parse/LLMAgent/provider) | `llm_eval.py` |
| **기억 가진 agent** (#5) | `llm_eval.StatefulLLMAgent` + `eval_harness.Agent.reset()` 훅 |
| **obs/전투 가독성** (#6·#7) | `llm_eval.render_obs`/`DEFAULT_SYSTEM` |
| **inference_score KPI** (#8) | `eval_harness.Scorecard.inference_score` + `SealedEvalSet` grid/boss 노브 |
| **robust 분류기** (#10) | `inference_rigor.classify_inference`(사전약정 0.5/0.1/1.0) + 러너 `--runs N` |
| **직접 추론 telemetry** (#12) | `eval_harness.score_inference_telemetry`(SE-무브율, read-only) + 러너 `--telemetry` |

**한 줄 데모**: `python scripts/llm_eval_run.py --provider claude-cli --stateful --telemetry --grid-size 5
--num-types 3 --boss-hp 140 --boss-atk 6 --boss-def 18 --worlds 2 --max-steps 40 --master-seed 3`
→ 3-arm(oracle/type_blind/LLM) gym-clears + inference_score + SE-무브율.

## 2. 정직한 측정 결론 (★ 과대 reframe 금지 — 인수인계 비협상)

claude-opus-4-8(구독 Claude CLI)을 **inference-gated demonstrator**(grid5·types3·boss140/6/18)에서 측정:

| 신호 | LLM | oracle | type_blind |
|---|---|---|---|
| gym-clears | 0.00 | 3.00 | 0.00 |
| inference_score | **0.00 ± 0.00** (3 runs) → `at-chart-blind-floor` | 1.0 | 0.0 |
| 호라이즌 sweep 40/60/120 | 모두 0.00 (inference-bound, not budget-bound) | — | — |
| 메모리 stateless vs stateful | 둘 다 0.00 (메모리는 레버 아님) | — | — |
| **SE-무브 사용률** (직접 추론) | **0%** (21 moves) | 100% | 0% |

**이게 뜻하는 것**: 이 setup에서 프런티어 LLM이 숨은 상성표를 robust하게 **추론·exploit하지 못한다**(직접 메트릭도 0%).
**이게 뜻하지 *않는* 것**: "프런티어 LLM이 우리 환경을 못 푼다"는 능력 verdict ❌. 다음 confound 때문:
1. **얇은 `claude -p` print-mode 어댑터** — 스텝당 깊은 추론·scratchpad·도구 없음. 진짜 agentic harness면 다를 수 있음.
2. **전투 밸런스가 가혹**(2턴 사망) + `damage=max(1,...)`라 살면 중립 attrition 승 가능 → "추론 필수 + 학습 가능" sweet spot이 *config 노브로 안 잡힘*.
3. 작은 표본(2월드·21 moves·단일 config·scripted-oracle proxy·일부 단일 run).

→ **올바른 프레이밍**: "우리 eval은 *non-saturated·discriminating*(현 프런티어 LLM이 floor) = 측정할 가치 있는 미해결 능력 + headroom" (제품 강점). oracle/type_blind 앵커 대비로만 읽기. (competitive-analysis "monetizable eval" 행에 이대로 박제됨.)

## 3. 핵심 설계 통찰 (다음 세션이 결정할 것)

probe로 **env 전투 모델의 구조적 사실**을 발견: `battle.py:123` `damage=max(1, int(power*atk/def*eff))` — **모든 무브가 ≥1 데미지** →
살아남으면 중립 무브 attrition으로 승. 그래서 "추론 필수(중립론 못 깸)"와 "배울 여지(오래 생존)"가 현 모델에서 **충돌**.
- catch+gym 게임(M1 설계)으론 정상. *순수 in-context 추론 eval*로 쓰려면 전투 모델 손봐야 함.

## 4. 남은 갈래 (전부 사람/전략 게이트 또는 긴 probe)

| 갈래 | 성격 | 비고 |
|---|---|---|
| **전투 모델 재설계** (max(1) 제거 / 보스 회복 / 턴 제한 → "추론 필수+학습 가능") | **사람 게이트** | 벤치마크 *정의* 변경 — JAX parity 재증명·모든 baseline 수치 영향 |
| **진짜 agentic harness** (스텝당 추론/메모/도구) 로 재측정 | 자율 가능 | confound #1 해소 → 깨끗한 능력 숫자 |
| **difficulty curve** (여러 band SE-무브율/inference_score) | 자율(probe 시간↑) | "어느 난이도부터 LLM이 floor 넘나" 곡선 |
| **M5 서버측 봉인 인프라** (secret seed + 제출 샌드박스 + hosted) | **사람/전략** | in-process harness=토대이지 제품 아님 |
| **공개** (OSS 리스팅 / arXiv / git tag push) | **사람 게이트(끝까지)** | moat layer 3 = adoption |
| GPU full-episode 정밀치 | better-HW | minor |

## 5. 규율·환경 메모 (계승)

- **테스트**: `.venv/bin/python -m pytest`(pytest는 .venv에만). mypy/ruff도 `.venv/bin/python -m`. 502 passed/2 skip.
- **커밋**: `HARNESS_ALLOW_COMMIT=1 git commit`(mandate 근거 commit-guard 우회). `.claude/projects/`는 매 커밋 `git reset -q .claude/projects/`로 제외.
- **머지**: 사용자가 자율 위임 시 `gh pr merge` 가능(2026-06-28~). 위임 발화가 직전 컨텍스트에 있어야 self-approval 가드 통과([[auto-mode-blocks-self-merge]]).
- **lifecycle**: main 직접 금지·feature/fix/docs 브랜치→PR→merge. archive `git mv`는 신규 파일이면 실패 → 파일시스템 `mv` + `git add -A`로 우회.
- **정직성 > 헤드라인**: 모든 수치 caveat 동반, "LLM 못 푼다"·"제품 완성"·"과금 0" 류 reframe 금지.
- **실측 probe**: 사용자 로컬 claude CLI(구독). 백그라운드 실행은 `run_in_background` + 완료 알림 대기(`nohup &` 중첩 금지 — detach 혼동).
- 🔔 **남은 사용자 보안 TODO** (이전 핸드오프 계승): Colab GitHub classic 토큰 삭제.

## 변경 이력
- 2026-06-29: eval-product #5~#12 세션으로 전면 갱신(이전 4/4-family/난이도 세션 내용 → archive CHANGELOG·INITIATIVE에 보존).
