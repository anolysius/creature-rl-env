# QA Checklist — duel-fewshot-adapt (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ "전이하는 학습 정책"(moat 층2/M5)의 국소화된 frontier(cross-배틀시스템=duel). #32 follow-up.
> ⚠ 정직성 불변식: 성공 = **제로샷 불가 메커니즘 입증 + few-shot 적응 곡선 측정 + 정직 보고**이지 **"전이 풀었다"가 아니다**.
>   제로샷≠few-shot 구분. ADAPTS/SLOW/NO 모두 valid·결정적.

## Acceptance Criteria (frozen at G1)

- [x] **AC1** — `test_charge_degenerate_in_train_families`(numpy-only, 결정론): train family(critter/forage/muster)
  seed=0 reset 후 `nav_toward_gyms` 200 step 롤아웃 매 step charge==0; 대조 duel 롤아웃 max charge>0.
  헬퍼 `charge_trace(family,seed,steps)`. "degenerate obs → 제로샷 불가" 명시.
- [x] **AC2** — `fewshot_adapt_curve(...)` + `test_fewshot_adapt_curve_smoke`(importorskip,tiny): base{train} 정책을
  held-out duel서 adapt budget 사다리(0 포함) fine-tune, duel held-out 점수 run-간 mean±std. 단언:
  (a) 곡선 길이==len(adapt_budgets) (b) 모든 점 finite (c) 0-adapt==zero-shot(이후 baseline).
- [x] **AC3** — 사전약정 결정규칙(이번 run z₀=0-adapt 제로샷·σ₀ 기준, 하드코딩 숫자 아님): ADAPTS(≤50k>z₀+σ₀ 유의
  상회)/SLOW(100k에야)/NO(최대도 안). ±std + caveat(제로샷≠few-shot, held-out eval seed≠adapt seed, 단일 config). 날조 0.
- [x] **AC4** — `[rl]` smoke(importorskip) few-shot 곡선 무회귀 + degenerate 가드 결정론. core CI numpy-only 유지.
- [x] **AC5** — 기존 테스트 무회귀(197 유지/증가) + mypy/ruff/build clean.
- [x] **AC6** — DESIGN §3.1.1 + `genre-generalization.md` 정직 갱신(제로샷 불가 메커니즘 + few-shot 결과) + M5/층2 + CHANGELOG.
- [x] **AC7** — (freeze 전) pilot: (i) duel 적응 점수 방향(0.93 위로?) (ii) timing (iii) 결정론 (iv) 어느 결과든 정직 보고. falsify 시 reframe.

## L1 이력
- round 1: plan-reviewer **APPROVE**(5축, degenerate 가드 seed/step 명세 SUGGEST→AC1 흡수) / qa-verifier **BLOCK**(AC1~3 정량 테스트 스펙·판정기준·구현위치 누락) → BLOCKED.
- 보완: AC1 `test_charge_degenerate_in_train_families`(seed=0·200 step·charge_trace) / AC2 `test_fewshot_adapt_curve_smoke`+SMART 단언 / AC3 z₀+σ₀ 사전약정 / 구현위치 scripts 한정·env 무변경 명시.
- round 2(selective, qa-verifier 재호출): qa-verifier **APPROVE**(3개 지적 해소) → **APPROVED**.

## 정직성 불변식
#25~#32 계승. 제로샷 불가는 메커니즘으로 *입증*(charge degenerate), few-shot은 별도 metric(제로샷과 구분).
사전약정 z₀+σ₀로 사후 편향 차단. 결과값이 아니라 메커니즘 입증+곡선 측정+정직 보고로 freeze.
