# Initiative: env-core

> CritterGym 제품 코어 (Gymnasium env) 의 단계적 구축. DESIGN.md §6 로드맵 Phase 1~ 를 담는 멀티-task 묶음.
>
> **마일스톤 SSOT**: [roadmap.md](../../explanation/roadmap.md) (왜) · [milestones.md](../../reference/milestones.md) (사실).
> **활성 마일스톤: M1** (고정월드 full subgoal chain). 매 task 는 활성 M 의 미충족 EC 에서 내려온다.

## 목표
DESIGN.md 스펙을 실제 동작하는 Gymnasium 환경으로 구현한다. "dumbest-possible playable env"
(10×10, catch-only) 에서 시작해 full subgoal chain + procedural generation + train/test seed split
까지 성장시킨다.

## 북극성 (CLAUDE.md north-star 종속)
1. 모든 기능은 *에이전트 능력 측정* 에 복무 — 게임 재미 아님.
2. 리워드는 verifiable (RLVR) — boolean subgoal.
3. procgen + train/test seed split 비협상.
4. fast / vectorizable.
5. seeded·pinned reproducibility.

## Task 목록
| # | slug | 상태 | 한 줄 |
|---|---|---|---|
| 1 | `scaffolding` | ✅ done (→ `_archive/2026-Q2/env-core/01-scaffolding/`) | 패키지 레이아웃 + 툴체인 + 최소 catch-only env |
| 2 | `env-validation` | ✅ done (→ `_archive/2026-Q2/env-core/02-env-validation/`) | check_env + 베이스라인 spread + held-out 일반화 + throughput 가드 |

(이후 task 는 /task-start 로 append)

## 다음 task
활성 마일스톤 **M1** 의 미충족 exit criterion 에서 내려온다 — 구성 task 목록·EC 는
[milestones.md](../../reference/milestones.md) §M1 참조 (중복 유지 금지, SSOT 단일화).
권장 시작점: `battle-system` (M1-EC1, 진화·보스의 선행).
