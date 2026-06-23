# QA Checklist — genre-transfer-policy (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ "전이하는 학습 정책" 이니셔티브(moat 층2/M5)의 **층2 핵심 측정**. 선행=task26 obs-harmonization(PR #32).
> ⚠ 정직성 불변식: 성공 = **측정 + 정직 보고**이지 **"gap을 줄였다"가 아니다**. 양성=신호, 음성="(B) 미해결".

## Acceptance Criteria (frozen at G1)

- [x] **AC1** — widened-train LOO 전이(각 family held-out, 나머지 train, duel 포함 가능) 측정·출력.
  **비교 축 = 전이 gap = `held_in_mean − held_out_family_mean`(리턴 단위, 기존 `TransferReport.gap`과
  동일 metric)**; widened fold gap을 #26 baseline(train{A,B}→D, gap=+2.56)과 같은 metric으로 한 표 대조.
- [x] **AC2** — 실측을 ±std + 단일run/저예산/N caveat와 함께 정직 보고(코드 근거, 날조 0). 양성=신호(증명 아님),
  음성="(B) widened로도 전이 어렵다".
- [x] **AC3** — `[rl]` smoke(importorskip)로 widened-train LOO + 4 family(duel 포함) fold 구성 무회귀.
  core CI numpy-only 유지.
- [x] **AC4** — 기존 테스트 무회귀(192 유지/증가) + mypy/ruff/build clean.
- [x] **AC5** — DESIGN §3.1.1 정직 갱신(이 task 결과 반영) + 마일스톤 매핑(M5/층2).
- [x] **AC6** — CHANGELOG 1줄 append.
- [x] **AC7** — (freeze 전) pilot로 실험 동작 + 정직 framing 확인. 가정 falsify 시 reframe(freeze 전이라 새 slug 불요).

## L1 이력
- round 1: plan-reviewer **SUGGEST**(DESIGN.md scope_paths 누락) / qa-verifier **BLOCK**(AC1 baseline 축 미명시) → BLOCKED.
- 보완: AC1 비교 축 = 전이 gap(held_in−held_out, TransferReport.gap 동일 metric) 명시 + scope_paths에 DESIGN.md 추가.
- round 2(selective, qa-verifier 재호출): qa-verifier **APPROVE**(BLOCK 해소) → **APPROVED** (no-progress 없음).

## 정직성 불변식
난이도 task #25(pilot falsify→reframe)·genre transfer #26(+2.56 음성도 정직 신호) 선례 계승. 결과값이 아니라
측정+정직보고로 freeze. peer/우리 수치 구분, ±std·caveat 의무.
