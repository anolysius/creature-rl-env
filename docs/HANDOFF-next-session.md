# 인수인계서 — CritterGym (세션 이후: (B) 전이 이니셔티브 종결 — obs조화→전이측정→메커니즘 규명)

> 다음 세션용. 직전 세션(2026-06-23~24)이 **7 task를 정직하게 ship**(PR #32–39, 전부 main 머지)하며
> **(B) "전이하는 학습 정책" 이니셔티브를 정직하게 종결**. 이 문서는 *무엇이 끝났고 / 무엇이 정직한
> 부분 결과로 남았고 / 다음에 무엇을 하면 가장 가치 있는가*. SSOT: `DESIGN.md` §3.1.1(정직 scope),
> `docs/explanation/genre-generalization.md`((B) 학술 narrative — **신규 박제**),
> `docs/explanation/competitive-analysis.md`(갭 register), `docs/_active/env-core/INITIATIVE.md`,
> `docs/CHANGELOG.md`, `CLAUDE.md`(규율).

---

## 0. 오프닝 프롬프트 (새 세션에 그대로 붙여넣기)

> CritterGym 작업을 이어서 한다. 먼저 `docs/HANDOFF-next-session.md`, `docs/explanation/genre-generalization.md`
> ((B) 종결 narrative), `DESIGN.md` §3.1.1, `docs/explanation/competitive-analysis.md`(갭 register),
> `docs/_active/env-core/INITIATIVE.md`, `docs/CHANGELOG.md` 상단을 읽어라. 직전 세션이 **(B) 전이 이니셔티브를
> 7 task(#32–39)로 종결**: obs조화→전이측정→robust화→정책/obs(음성)→예산 RECOVERY→duel 메커니즘 입증+few-shot.
> **(B) 최종 = sharply characterized partial result**: 학습 정책이 *메커닉 이웃(수집+타입상성)은 제로샷 전이*,
> *구조적으로 새 배틀시스템(duel)은 제로샷 원리불가(charge feature가 train서 degenerate)+느린 few-shot(~100k)*.
> **이번 세션 미션 = (B)는 종결됐으니 피벗** — 갭 register의 **난이도 스케일** 또는 **JAX 속도**(공개 전 신뢰성·채택
> 게이트)로 전환 권장. 또는 (B) 더 깊이(메타-RL로 duel few-shot 단축)는 새 아키텍처=큰 작업. 방침: **공개(OSS/arXiv
> 제출)는 맨 마지막**, 기능 준비 + 비교우위가 먼저. 하네스 규율 준수(매 task `/task-start`→L1(opus reviewer×2 +
> qa, verdict-first)→**freeze 전 pilot**→G1→TDD→L3 APPROVED→task-end, main 직접금지 feature→PR). **"X 증명/회복/
> 전이한다"류 acceptance는 freeze 전 pilot 검증 + 성능 아니라 *측정+정직 보고*로 freeze, pilot이 falsify하면 정직
> reframe.** 정직성 > 헤드라인.

---

## 1. 현재 상태 (한 줄)

M0·M1·M2 ✅, M3 부분(EC1·2·3·6 ✅ / EC4 arXiv **초안**·EC5 OSS **준비**만, 외부 발행 미실행). **199 tests**,
numpy-only core + `[rl]`/`[viz]`/`[render]`/`[dev]` extra. **env id 6종**, **family 4종**(A critter/B forage/
C duel/D muster). main HEAD = `352c959`. **(B)/moat 층2 이니셔티브 종결**(M5 enabler를 M3 공개보다 먼저 = 사람 방침).

## 2. 직전 세션이 한 것 (7 task, archive 27~33 = (B) 전이 이니셔티브 전체)

| archive | task | PR | 정직한 결과 |
|---|---|---|---|
| **27** | obs-harmonization | #32 | 4 family 단일 공유 obs(`HARMONIZED_OBS_KEYS`, charge 0-마스킹). duel 포함 가능해짐. enabler |
| **28** | genre-transfer-policy | #34 | widened-train LOO: gap +2.56→~0 양성 *신호*(단일run) |
| **29** | transfer-rigor | #35 | multi-run+예산↑: #27 음수gap=노이즈, "compute 병목 아님"(저예산 외삽), 사전약정 결정규칙 도입 |
| **30** | transfer-skill-policy | #36 | 정책/obs(net256+scale) 음성: held-in 못 올림. whole-obs VecNormalize는 해로움(배제) |
| **31** | transfer-capacity-budget | #37 | 용량×예산: **예산이 lever·용량 아님**. 250k held-in 2.44 PARTIAL |
| **32** | transfer-budget-recovery | #38 | **예산 RECOVERY**(400k held-in 2.75). 회복 상태 full-LOO: 메커닉 이웃 전이 OK·**duel +1.73 실패** |
| **33** | duel-fewshot-adapt | #39 | **제로샷 duel 원리불가 *입증***(charge degenerate)+**few-shot SLOW**(~100k). **(B) 종결** |

## 3. ⚠ (B) 최종 결론 (정직 — 과대 금지)

**(B) = sharply characterized partial result** (open도 solved도 아님):
1. **메커닉 이웃(critter/forage/muster) = 제로샷 전이됨** — 회복된 held-in(~2.75)에서 gap ≤ 0.
2. **구조적으로 새 배틀시스템(duel) = 제로샷 원리불가** — duel RPS가 의존하는 `charge` obs가 train 3 family서
   **항상 0(degenerate)** → gradient 0 → 학습 불가. 테스트로 *입증*(`charge_trace`). **일반 명제**: genre 전이는
   새 메커닉이 train서 degenerate한 obs에 의존하면 제로샷 불가.
3. **duel few-shot = SLOW** — fine-tune ~100k(=base 2/3)에야 0.65→1.45. 거의 새로 배우는 진짜 새 skill.
4. lever 정리: **예산 O**(held-in 회복), **용량(net) X**(underfit), **단순 obs scale X**, **whole-obs VecNormalize 해로움**.

전부 `DESIGN.md §3.1.1` + `docs/explanation/genre-generalization.md`에 박제(arXiv 직결).

## 4. 권장 순서 (갭 register `competitive-analysis.md` §5 — 공개 전 기능)

1. **(권장) 피벗 — 난이도 스케일** — DESIGN §3.1.1 "hard-and-gap≈0" 갭. env가 toy라 gap≈0의 능력예측력 약함.
   난이도 ladder env 재설계(스타터 다양화 등, #25가 드러낸 oracle 천장 해소)로 (A)를 "hard-and-gap≈0"으로.
2. **(권장) 피벗 — JAX 속도** — 속도=채택 게이트(Craftax 교훈). numpy hot-path를 JAX 포트. 큰 작업이나 공개 전 속도 열위 메움.
3. **(B) 더 깊이(옵션, 큰 작업)** — 메타-RL/메커닉-범용 표현으로 duel few-shot을 *빠르게*(현재 SLOW ~100k 단축).
   새 아키텍처 + 새 의존성(sb3-contrib RecurrentPPO 설치돼 있음). 제품 leverage는 1·2가 더 큼.
4. **(맨 마지막) 공개** — OSS repo-public + Prime Intellect Hub + arXiv 제출(전부 사람 게이트).

> 개인 의견(직전 세션): **(B)는 깔끔히 종결됐으니** 1(난이도) 또는 2(JAX)로 피벗하는 게 공개 전 제품 신뢰성·채택에
> 가장 직접적. (B) 더 깊이 파는 건 한계효용 낮음(메커니즘 다 규명됨).

## 5. 코드 포인터 (직전 세션 산출 — 전부 main)

- **전이 실험 스택** `scripts/genre_learned_transfer.py`([rl], CLI 다수):
  - `train_and_transfer(..., net_arch=, scale_obs=)` — 단일 fold 전이(+정책/obs 노브, default off=baseline)
  - `train_and_transfer_loo` / `train_and_transfer_loo_multirun`(run-간 mean±std) — `--loo` / `--runs N`
  - `held_in_sweep` + `budget_ladder_configs` — `--sweep`(용량×예산) / `--budgets`(예산 사다리) + 사전약정 verdict
  - `fewshot_adapt_curve` + `charge_trace` — `--fewshot`(duel 적응 곡선) + 제로샷 불가 메커니즘
  - `HELD_IN_CEILINGS`/`RECOVERY_THRESHOLD`(2.5)/`HARMONIZED`은 env_family에.
- **env_family** `HARMONIZED_OBS_KEYS`(=REQUIRED ∪ charge 2키)/`MAX_CHARGE_OBS`/`CHARGE_OBS_KEYS`. base `CritterEnv`가 charge 0-마스킹, `DuelEnv` override.
- **테스트** `tests/test_genre_learned_transfer.py`(전이 smoke 다수) + `tests/test_obs_harmonization.py`(조화 가드). 전부 [rl] importorskip 또는 numpy-only.
- **문서** `docs/explanation/genre-generalization.md`(**(B) 학술 narrative 신규**) + DESIGN §3.1.1 + competitive-analysis.md(갭 register).

## 6. 하네스 메모 (직전 세션 학습)

- **multi-run이 단일-seed pilot을 *4번* 교정** — pilot 단일 seed가 held-in/gap을 반복 오도(노이즈). 학습 결론은
  반드시 multi-run. pilot은 *방향·timing·feasibility*까지만 신뢰(AC7 정량 게이트로 활용).
- **사전약정(pre-registered) 결정규칙** — "어떤 결과면 신호/아티팩트/불확실/RECOVERY/SLOW"를 freeze 시 못박아 사후
  narrative 편향 차단. qa-verifier가 이걸 SUGGEST/BLOCK으로 요구함(정직성 강화). 임계 goalpost 이동 금지.
- **l3-reviewer-maxturns 재발(이번 세션 3회)** — plan-reviewer가 소스 조사 중 verdict 없이 종료. **SendMessage로
  "verdict만" 요청해 회수**하면 깨끗. retro 큐에 seeded(항구 수정 대기).
- **qa-verifier 조건부 BLOCK 패턴** — 파일 못 보니 "기록됐는지 확인 불가"로 BLOCK하기도 함. **실제 기록 발췌를 inline로
  재호출**하면 APPROVE. (EXTERNAL READ FORBIDDEN이라 inline이 완결돼야 함.)
- **auto-mode가 main 머지 차단** — `gh pr merge`는 *가장 최근 사용자 발화*에 머지 인가가 있어야 통과. "머지해줘" 직후 실행.
- **archive 이동**: 신규 plan/report untracked면 `git mv` 불가 → 일반 `mv`. NN- prefix 다음 = **34**.
- **실측 run은 백그라운드**(run_in_background). 50k~500k×multi-run은 ~5~40분. foreground 2분 한도 주의.
- 개발 `.venv`(ruff/mypy/pytest/build + sb3 2.7.1 + sb3-contrib 2.7.1). core CI numpy-only(PPO `[rl]` 뒤 importorskip).

## 7. 정직성 문화 (계승 필수)

직전 7 task 공통 — **acceptance를 *성능/주장*이 아니라 *측정+정직 보고*로 freeze**. 양성=신호(예산 RECOVERY),
음성=음성(정책/obs 안 올림), 가정 falsify=reframe(제로샷 charge degenerate). 사전약정 임계로 사후 편향 차단,
multi-run으로 단일-seed 노이즈 교정, 메커니즘까지 *입증*. peer 사실 `[verify]`, 우리 수치 코드 근거(날조 0).
**(B)를 "전이 풀었다"로 과대주장하지 않고 "sharply characterized partial result"로 정직 종결한 게 이 프로젝트의
신뢰성 자산이자 moat 층3(trust)의 재료다. 헤드라인보다 정직성.**
