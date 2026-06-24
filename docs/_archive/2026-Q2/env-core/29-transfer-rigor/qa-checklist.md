# QA Checklist — transfer-rigor (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ "전이하는 학습 정책" 이니셔티브(moat 층2/M5). #27 양성 신호의 **generalist-mediocrity·단일run caveat 메우기**.
> ⚠ 정직성 불변식: 성공 = **robust 측정 + 정직 보고**이지 **"신호 확증"이 아니다**. 신호 강화/아티팩트 reframe 둘 다 valid.

## Acceptance Criteria (frozen at G1)

- [x] **AC1** — multi-run LOO(`--runs N`/집계)가 widened 4 family LOO를 여러 seed 반복 → per-fold
  held-in/held-out/gap을 **run-간 mean ± std**로 출력. #27/#26(+2.56)과 같은 gap metric(held_in−held_out).
- [x] **AC2** — 높은 예산(>50k)에서 측정 + held-in이 #27 대비 올랐는지 보고. **사전약정 결정규칙**(사후 편향
  방지): muster fold 기준 — 신호강화(held-in≥2.5 ∧ gap≤+0.5) / 아티팩트 reframe(gap>+1.0) / 불확실(std≥gap).
  임계는 freeze 시 사전등록, 결과가 어디 떨어지든 ±run-std+caveat로 정직 보고(날조 0).
- [x] **AC3** — `[rl]` smoke(importorskip) multi-run(tiny·≥2 run) 무회귀, core numpy-only 유지.
- [x] **AC4** — 기존 테스트 무회귀(193 유지/증가) + mypy/ruff/build clean.
- [x] **AC5** — DESIGN §3.1.1 정직 갱신(신호강화/아티팩트 어느 쪽이든) + M5/층2 매핑.
- [x] **AC6** — CHANGELOG 1줄 append.
- [x] **AC7** — (freeze 전) pilot 정량 게이트: (i) timing(전체 추정 현실적), (ii) held-in 예산↑로 오르는 방향,
  (iii) multi-run 집계 + AC2 규칙으로 어느 결과든 정직 보고 가능. 비현실/falsify 시 조정·reframe(새 slug 불요).

## L1 이력
- round 1: plan-reviewer **APPROVE**(5축) / qa-verifier **SUGGEST**(AC7/AC2 사전약정 결정규칙 필요) → SUGGEST_CUTOFF.
- 흡수: AC2에 사전약정 결정규칙(신호강화/아티팩트/불확실 임계) + AC7에 정량 게이트(timing/held-in 방향/집계) 추가.

## 정직성 불변식
#25(pilot falsify→reframe)·#26(+2.56 음성도 신호)·#27(generalist-mediocrity caveat 명시) 계승. 사전약정 임계로
사후 narrative 편향 차단. 결과값이 아니라 robust 측정+정직 보고로 freeze.
