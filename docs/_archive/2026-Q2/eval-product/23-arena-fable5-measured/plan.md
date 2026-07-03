---
slug: arena-fable5-measured
initiative: eval-product
status: active
started: 2026-07-02
acceptance_freeze: true
task_type: general
mode: quick-fix
domains: [rl-env]
scope_paths:
  - docs/reference/battle-arena.md
extracted_to: []
supersedes: []
---

# arena-fable5-measured — LLM 아레나 실측 결과 기록 (Claude Fable 5, 5-run)

> 작성일: 2026-07-02 | 상태: 계획 | 마일스톤: M3-EC4 (논문 §5 — engagement confound 질문의 실측 답)

## 목표

battle-arena-probe(#22)가 "계측 가능"으로 남겨둔 질문을 사용자 승인 quota 로 실측 완료
(claude-cli = **claude-fable-5**, CLI modelUsage 로 모델 id 확인). 결과를
`docs/reference/battle-arena.md` 에 Measured 섹션으로 정직 기록한다 — 사전약정 프로토콜,
5-run 합산 판정(INCONCLUSIVE, **종결적** — 평균 0.132 > floor 0.10 이라 추가 run 으로
판정 변경 불가), 해석(engagement 가설 기각), 경계 전부 포함.

docs-only (코드 0). 논문 §5 반영은 별도 후속 seed.

## Acceptance Criteria (G1 freeze)

- **AC1**: `docs/reference/battle-arena.md` 에 "Measured" 섹션 — (a) 사전약정 프로토콜
  (명령·runs 3+2 확충 선례·동결 임계), (b) 결과 표 (band 4-arm + Fable 5 48%/42-46 moves),
  (c) 5-run 합산 0.132±0.037 → INCONCLUSIVE + **종결성 논증**(mean>floor_eps ⇒ 추가 run 무의미),
  (d) 사전선언 해석 규칙 적용 (engagement 가설 기각·약한 above-chance 신호·"floor 단정도 부정확"),
  (e) 경계 (1 config·3 worlds·CLI 백엔드·rounded-moment 합산이지만 판정은 rounding 에 강건).
- **AC2**: 기존 문서의 "instrumented, not answered" 문구를 실측 완료 상태로 갱신 (모순 제거).
  CHANGELOG 1줄 (task-end).
