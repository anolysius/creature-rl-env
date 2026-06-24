# QA Checklist — transfer-budget-recovery (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ "전이하는 학습 정책"(moat 층2/M5)의 **예산 lever 끝보기** — #31이 보류한 probe(더 큰 예산) 실행.
> ⚠ 정직성 불변식: 성공 = **예산 효과 측정 + (회복 시) gap 재측정 + 정직 보고**이지 **"회복했다"가 아니다**.
>   RECOVERY(confound 제거경로+gap 재측정) / PLATEAU(예산도 한계=비싼 경로 필요) 둘 다 valid·결정적.

## Acceptance Criteria (frozen at G1)

- [x] **AC1** — baseline-net(용량 배제) **예산 사다리**(≥1개 250k 초과 점, 예 400k·500k) `--budgets` multi-run
  측정·출력 + #26(2.94)/#28(2.07)/#31(250k 2.44) 기준선 병기(같은 held-in metric).
- [x] **AC2** — **사전약정 결정규칙**(#31 임계 2.5 계승, goalpost 이동 금지): muster fold held-in mean —
  RECOVERY(≥2.5 ∧ 2.44 상회) / PLATEAU(250k 정체) / APPROACHING(>2.44,<2.5). ±run-std + caveat, 날조 0.
- [x] **AC3** — **(RECOVERY 시에만)** 회복 예산 `loo_multirun`으로 **full-LOO confound-reduced gap을 #28 같은 축**
  재측정·보고. 아니면 "held-in 미회복 → gap 재측정 **불요** + 예산 lever 한계" 정직 기록(조건부, 실제 skip).
- [x] **AC4** — `[rl]` smoke(importorskip) `--budgets` 사다리 무회귀 + 결정론(seed 고정), core numpy-only 유지.
- [x] **AC5** — 기존 테스트 무회귀(196 유지/증가) + mypy/ruff/build clean.
- [x] **AC6** — DESIGN §3.1.1 정직 갱신(RECOVERY/PLATEAU + 회복 시 gap) + `genre-generalization.md` 갱신
  + M5/층2 + CHANGELOG 1줄.
- [x] **AC7** — (freeze 전) pilot: (i) 500k held-in 방향(2.5 향함/정체) (ii) timing(전체 추정 현실성)
  (iii) 결정론 (iv) 어느 결과든 정직 보고 가능. 비현실/falsify 시 조정·reframe(새 slug 불요).

## L1 이력
- round 1: plan-reviewer **APPROVE**(5축, genre-generalization.md scope 누락 관찰→흡수) / qa-verifier **APPROVE**(3축) → **APPROVED**.

## 정직성 불변식
#25~#31 계승. 사전약정 임계 2.5(#31 동일, goalpost 이동 금지)로 사후 편향 차단. 결과값이 아니라 효과 측정+정직 보고로 freeze.
PLATEAU면 예산 lever도 한계 = (B) 완전 회복엔 비싼/다른 접근 필요(결정적 음성). RECOVERY면 조건부 신호지 일반 주장 아님.
