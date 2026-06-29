---
slug: inference-measurement-sync
initiative: eval-product
status: active
started: 2026-06-29
acceptance_freeze: true
domains: [agents]
task_type: general
mode: quick-fix
scope_paths:
  - docs/explanation/competitive-analysis.md
extracted_to: []
supersedes: []
---

# robust inference verdict + 호라이즌 sweep을 competitive-analysis에 정직 반영 (docs quick-fix)

## 목표

(#10 도구로) 측정한 두 결과를 competitive-analysis "monetizable eval" 행에 반영, #9의 "first probe
0.00 (weak)"를 격상:
- **robust verdict**: claude-opus-4-8, inference-gated demonstrator(grid5·types3·boss140/6/18), 40스텝
  **3 runs → inference_score 0.00 ± 0.00 = `at-chart-blind-floor`**(사전약정 분류기, p-hacking 차단).
- **호라이즌 sweep**: max_steps 40/60/120 모두 0.00 → floor가 *예산(생각 시간) 부족*이 아니라 *in-context
  추론 자체* 때문 (호라이즌 3배도 floor 불변).

## Acceptance Criteria

- [ ] AC1: "monetizable eval" 행이 robust verdict(0.00±0.00, 3 runs, at-chart-blind-floor)와 호라이즌
  sweep(40/60/120 모두 0.00 → 추론-bound, 예산-bound 아님)을 반영. "weak first probe" 표현 격상.
- [ ] AC2: 정직 경계 — non-saturated/discriminating 신호이자 강점이지 "LLM 못 함" 헤드라인 아님;
  단일 config·2월드·scripted-oracle proxy·이 difficulty band 한정; hosted/고객/공개 여전히 human-gate.
- [ ] AC3: broken link 0, 표 구조 보존, CHANGELOG 1줄(quick-fix).
