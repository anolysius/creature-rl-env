---
slug: product-roadmap
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
---

# Report — product-roadmap (제품 마일스톤 SSOT)

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약
제품 방향의 **첫 SSOT** 를 신설. DESIGN.md §6 고수준 로드맵을 검증 가능한 exit criteria 를 가진 마일스톤
M0–M5 로 구체화하고, "매 task 는 활성 마일스톤의 미충족 EC 에서 내려온다" 규율을 CLAUDE.md(auto-load)에
박아 즉흥적 task 생성을 구조적으로 차단. docs-only, Acceptance 7/7, broken-link 0.

## 산출물
| 파일 | 내용 |
|---|---|
| `docs/reference/milestones.md` | M0–M5 표 (goal·exit criteria·구성 task·DESIGN 매핑·상태) + 규율 |
| `docs/explanation/roadmap.md` | 순서 근거(M1 고정월드 先 / JAX M4 지연 / 런치 M3 묶음) + 킬러 데모 정의 + master-plan↔roadmap 구분 |
| `docs/_active/env-core/INITIATIVE.md` | 마일스톤 SSOT 링크 + 활성 M1 + "다음 task" 를 milestones.md 로 위임 |
| `CLAUDE.md` | "Product milestones drive task selection" 단락 — 규율 enforce hook-up |

## Acceptance 결과 (G1 freeze ↔ 실측, 1:1)
- ✅ AC1 milestones.md M0–M5 표 (goal/EC/task/DESIGN/상태)
- ✅ AC2 M0 done(scaffolding+env-validation), M1–M5 pending
- ✅ AC3 roadmap.md 3요소 (구분/순서근거/킬러데모)
- ✅ AC4 roadmap.md 규율 텍스트 포함
- ✅ AC5 INITIATIVE.md 마일스톤 링크 + 활성 M1
- ✅ AC6 DESIGN §6 매핑 정합 + broken-link 0 (스크립트 검증)
- ✅ AC7 CLAUDE.md 규율 포인터 + roadmap/milestones 링크 (enforce hook-up)

## 핵심 효과 — 즉흥성 제거
- "다음에 뭐?" → 활성 마일스톤(M1)의 미충족 EC 를 본다 (대화에서 발명 X).
- task plan/report 가 "M{n}-EC{k}" 로 체크인 → 진행도 가시화.
- 성능/viz/OSS 타이밍이 박혀 즉흥 논쟁 제거 (각 M 에 귀속).

## L3 리뷰 반영
- @plan-reviewer SUGGEST(verification): M1-EC5 "held-out" 이 고정월드(procgen 없음) 맥락에서 모호
  → "고정월드 ≥1 boss 격파, 일반화는 M2" 로 정정.
- @plan-reviewer SUGGEST(impact): INITIATIVE.md 옛 "후속 후보" 목록이 milestones.md M1 task 와 불일치
  → "다음 task" 를 milestones.md 로 위임(중복 제거, SSOT 단일화).
- @qa-verifier: APPROVE (AC 7/7 정합).

## 후속
- **활성 = M1.** 다음 task 권장: `battle-system` (M1-EC1) — 진화·보스의 선행.
- (별도 task) rules/80 자체에 규율을 도메인 규칙으로 격상할지 — 현재는 CLAUDE.md 포인터까지가 scope.
