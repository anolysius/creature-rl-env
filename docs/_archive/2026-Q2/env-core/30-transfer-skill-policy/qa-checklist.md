# QA Checklist — transfer-skill-policy (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ "전이하는 학습 정책" 이니셔티브(moat 층2/M5)의 **(a')** — #28이 좁힌 "남은 유일한 직접 경로".
> ⚠ 정직성 불변식: 성공 = **개선 효과 측정 + 정직 보고**이지 **"held-in 올렸다"가 아니다**. 양성=confound 제거경로 / 음성=env 본질 어려움, 둘 다 valid.
> 메모: AC7 "timing"=wall-clock(compute feasibility, R3와 동일 의미).

## Acceptance Criteria (frozen at G1)

- [x] **AC1** — `train_and_transfer`에 정책/obs 개선 노브(obs 정규화 + `net_arch`↑) 추가 + bare baseline 보존
  (on/off 인자/플래그 선택).
- [x] **AC2** — baseline vs 개선의 **widened held-in 대조 측정·보고**(#26 2.94·#28 widened 기준). 정직 framing
  (오름=confound 제거경로 / 안오름=env 본질 어려움·레버 부족). ±std + caveat, 날조 0.
- [x] **AC3** — (held-in 올랐을 때) 개선 설정 multi-run LOO **gap을 #28과 같은 축**으로 재측정. 효과 없으면
  "held-in 미상승으로 gap 재측정 불요" 정직 기록(조건부).
- [x] **AC4** — `[rl]` smoke(importorskip) 개선설정 무회귀 + **결정론**(seed 고정·eval 시 정규화 동결),
  core numpy-only 유지.
- [x] **AC5** — 기존 테스트 무회귀(194 유지/증가) + mypy/ruff/build clean.
- [x] **AC6** — DESIGN §3.1.1 정직 갱신(held-in 개선 효과 양성/음성) + M5/층2 매핑 + CHANGELOG 1줄.
- [x] **AC7** — (freeze 전) pilot: (i) 개선설정 held-in 방향(obs 정규화 효과) (ii) timing(wall-clock)
  (iii) 결정론 (iv) 어느 결과든 정직 보고 가능 확인. falsify 시 조정·reframe(새 slug 불요).

## L1 이력
- round 1: plan-reviewer **APPROVE**(5축) / qa-verifier **APPROVE**(3축, AC7 timing 미세 명확화 메모) → **APPROVED**.

## 정직성 불변식
#25(pilot falsify→reframe)·#26(음성도 신호)·#27(caveat 명시)·#28(사전약정+compute 한계 입증) 계승.
결과값이 아니라 개선 효과 측정+정직 보고로 freeze. held-in 안 오르면 "env 본질 어려움"의 정직 음성.
