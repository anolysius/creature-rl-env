# QA Checklist — transfer-capacity-budget (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ "전이하는 학습 정책" 이니셔티브(moat 층2/M5)의 **cheap/expensive 경계 종결** task.
> ⚠ 정직성 불변식: 성공 = **동시 스케일 효과 측정 + 정직 보고**이지 **"held-in 올렸다"가 아니다**.
>   회복(confound 제거경로) / 미회복(값싼 경로 3개 다 실패 = 경계 종결) 둘 다 valid·결정적.

## Acceptance Criteria (frozen at G1)

- [x] **AC1** — 용량(net_arch)×예산(timesteps) 조합 widened held-in multi-run 측정·출력 + **#26(2.94)·
  #28 budget-only(~2.07)·#30 net-only(1.15) 천장 같은 표 기준선**(같은 held-in/gap metric).
- [x] **AC2** — **사전약정 결정규칙**: muster fold run-간 held-in — 회복(≥2.5 ∧ 천장 상회) / 부분(>2.07,<2.5)
  / 경계 종결(≤2.07 within std). 결과 어디든 ±run-std + caveat, 날조 0.
- [x] **AC3** — (held-in 회복 시) 동시-스케일 multi-run LOO **gap을 #28과 같은 축** 재측정. 못하면
  "held-in 미회복 → gap 재측정 **불요** + **cheap/expensive 경계 종결**" 정직 기록(조건부, 실제로 skip).
- [x] **AC4** — `[rl]` smoke(importorskip) sweep/대조 무회귀 + 결정론(seed 고정), core numpy-only 유지.
- [x] **AC5** — 기존 테스트 무회귀(195 유지/증가) + mypy/ruff/build clean.
- [x] **AC6** — DESIGN §3.1.1 정직 갱신(회복/경계 종결) + `genre-generalization.md` "남은 비싼 경로" 갱신
  + M5/층2 + CHANGELOG 1줄.
- [x] **AC7** — (freeze 전) pilot: (i) big-net×high-budget held-in 방향(천장 상회 여부) (ii) timing(전체
  추정 현실성) (iii) 결정론 (iv) 어느 결과든 정직 보고 가능. 비현실/falsify 시 조정·reframe(새 slug 불요).

## L1 이력
- round 1: plan-reviewer **APPROVE**(5축) / qa-verifier **APPROVE**(3축, AC3 조건부 실제 skip 신뢰 메모) → **APPROVED**.

## 정직성 불변식
#25~#30 계승. 사전약정 천장(#28 2.07)·임계(2.5)로 사후 편향 차단. 결과값이 아니라 효과 측정+정직 보고로 freeze.
미회복이면 (B)의 generalist-mediocrity는 구조적 = cheap/expensive 경계 종결의 결정적 음성(valid 결과).
