---
slug: product-roadmap
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - docs/explanation/**
  - docs/reference/**
  - docs/_active/env-core/INITIATIVE.md
  - CLAUDE.md
extracted_to: []
supersedes: []
---

# product-roadmap — 제품 마일스톤 SSOT 문서

> 작성일: 2026-06-21 | 상태: 계획 | (docs-only)

## 목표
제품 방향의 **첫 SSOT** 를 만든다. 현재 task 가 대화에서 즉흥 생성돼 "휘둘리는" 문제의 근본 원인은
*task 가 올라탈 마일스톤 등뼈가 없어서*다. DESIGN.md §6 의 고수준 4-Phase 로드맵을, **검증 가능한
exit criteria 를 가진 마일스톤 M0–M5** 로 구체화해, 매 `/task-start` 가 *활성 마일스톤의 미충족
exit criterion 에서 내려오도록* 강제하는 backbone 문서를 신설한다.

산출 2종 (Diátaxis):
- `docs/explanation/roadmap.md` — *왜* (마일스톤 순서·근거, 성능/OSS/마케팅 타이밍 판단, 킬러 데모 정의).
- `docs/reference/milestones.md` — *사실* (M별 goal · exit criteria 체크리스트 · 구성 task · DESIGN 매핑 표).

## 선행 조건
- DESIGN.md §6 (제품 로드맵 고수준 SSOT) — 본 문서는 이를 *구체화*하되 모순 금지.
- `docs/harness/explanation/master-plan.md` 는 **하네스** 도입 계획(별개) — 혼동 방지 위해 roadmap.md 에
  "master-plan = 하네스 / roadmap = 제품" 구분 명시.
- M0 의 두 task(`scaffolding`, `env-validation`)는 완료·archive 됨 → M0 를 done 으로 기록.
- docs-only task: rules/80 §A.1 에 따라 `/task-verify`(G2) skip 가능, **`/task-review`(L3) 는 필수**.

## 작업 범위
### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | criticality | 비고 |
|---|---|---|---|
| `docs/explanation/roadmap.md` | 신규 | low | 순서·근거 narrative + 규율 + 킬러 데모 정의 |
| `docs/reference/milestones.md` | 신규 | low | M0–M5 goal·exit criteria·구성 task·DESIGN 매핑 표 |
| `docs/_active/env-core/INITIATIVE.md` | 갱신 | low | 마일스톤 문서 링크 + 활성 M 표시 |

### 영향 범위
- 순수 문서. 코드/import 영향 0. 향후 `task-start` 시 plan 이 본 문서의 M/EC 를 참조(규율).

## Step별 계획
1. **`milestones.md`** (reference) — M0–M5 표:
   - 각 M: `goal` / `exit criteria`(검증 가능 boolean 체크리스트, EC1·EC2…) / `구성 task`(slug) / `DESIGN §` 매핑 / 상태.
   - 합의 골격(아래 "마일스톤 골격" 참조)을 정확히 반영.
2. **`roadmap.md`** (explanation) — narrative:
   - master-plan(하네스) vs roadmap(제품) 구분.
   - 순서 근거: M1 고정월드 먼저(절차생성 전 메커니즘 디버깅 용이), 성능(JAX)은 M4 로 지연(spec 안정 후 — DESIGN §4 단서), OSS/writeup/마케팅은 M3 런치에 묶음.
   - **킬러 데모 정의**: "같은 에이전트 → 한 번도 본 적 없는 held-out 시드(새 맵+새 타입표) → 보스 격파" (포켓몬 레드가 구조적으로 못 보여주는 generalization 장면).
   - **규율 명시**: 매 task 는 frontmatter/plan 에 "어느 M 의 어느 EC 전진" 1줄 기록; 활성 M 안에서만 task 추출; M exit 충족 시 다음 M 게이트.
3. **`INITIATIVE.md` 갱신** — 마일스톤 문서 링크 + "활성 마일스톤: M1" 표기.

## 마일스톤 골격 (G1 freeze 대상 — 본 내용이 milestones.md 의 SSOT)
- **M0 Foundation** (✅ done): 패키지+최소 env+검증. EC: make() 동작, 베이스라인 spread, check_env, throughput 가드. task: scaffolding, env-validation. DESIGN §6 P1.
- **M1 고정월드 full subgoal chain**: 절차생성 없이 단일 월드에서 catch→evolve→체육관 N→최종보스, 턴제 배틀, 고정 타입표. EC: scripted/PPO ≥1 체육관 격파 / info.subgoals 체인 노출 / subgoal별 boolean 리워드 / 에피소드 ≥1k 스텝. task: battle-system, creature-evolution, gym-boss-progression, typechart-fixed. DESIGN §3.4–3.5.
- **M2 procgen + train/test (moat)**: 시드→절차 월드+절차 타입표. EC: held-out 시드가 새 맵+새 타입표 / PPO train-vs-test 갭 측정·리포트 / 시드 누수 0. task: procgen-region, procgen-typechart, generalization-harness. DESIGN §3.1.
- **M3 벤치마크 신뢰성 + 런치**: 베이스라인 4종 + 리더보드 + 측정 viz + writeup + OSS + 킬러 데모. EC: random/scripted/PPO/recurrent 점수표(train+test) / arXiv 초안 / MIT 공개 / 킬러 데모 GIF. task: baseline-suite, metrics-viz, killer-demo, arxiv-draft, oss-release. DESIGN §5–6 P2.
- **M4 Throughput (JAX)**: spec 안정 후 핫패스 포팅. EC: numpy↔JAX parity 테스트 / ≥10M steps/s GPU. task: jax-port, parity-tests, vectorized-bench. DESIGN §4.
- **M5 수익화**: 비공개 held-out eval + 커스텀/고난도 env + Hub 등록. EC: 비공개 eval 재현 가능 / Prime Intellect Hub 등록. task: private-evalset, custom-env-api. DESIGN §8.

## 검증 방법
- docs-only → 자동 테스트 없음. `/task-review`(L3) 에서 reviewer 가 (a) 골격 완전성 (b) DESIGN 모순 여부
  (c) exit criteria 의 검증가능성 (d) 규율 명시를 검토.
- broken link 0 (DESIGN.md / master-plan.md / DESIGN § 참조 정확).

## 리스크
- **마일스톤 분할 입도 논쟁**: 6개가 과/소분할일 수 있음 → 본 task 는 *합의된 골격*을 문서화하는 것이지
  골격 재설계가 아님. 입도 변경은 별도 task.
- **로드맵 노후화**: 문서가 코드와 따로 놀 위험 → 규율(매 task 가 M/EC 참조 + report 가 EC 체크인)로
  살아있게 유지. INITIATIVE.md 가 활성 M 추적.
- **DESIGN 모순**: roadmap 이 DESIGN §6 과 어긋나면 SSOT 충돌 → roadmap 은 DESIGN 을 *구체화*만,
  Phase 매핑을 표에 명시해 상위 SSOT 종속 유지.

## Acceptance Criteria (G1 통과 시 freeze)
- [ ] **AC1**: `docs/reference/milestones.md` 가 M0–M5 각각에 대해 goal / exit criteria(boolean EC 목록) /
  구성 task(slug) / DESIGN § 매핑 / 상태를 가진 표로 존재.
- [ ] **AC2**: M0 가 done(scaffolding+env-validation 완료)으로, 나머지(M1–M5)가 pending 으로 표기.
- [ ] **AC3**: `docs/explanation/roadmap.md` 가 (a) master-plan(하네스)↔roadmap(제품) 구분, (b) 순서 근거
  (M1 고정월드 先, 성능 M4 지연, 런치 M3 묶음), (c) 킬러 데모 정의를 포함.
- [ ] **AC4 (규율 — 문서화)**: roadmap.md 가 "매 `/task-start` 는 어느 M 의 어느 EC 를 전진시키는지
  명시하고 활성 M 안에서만 task 를 추출한다" 규율 **텍스트를 포함**(content 판정 — 문서가 규율을 서술).
- [ ] **AC5**: `INITIATIVE.md` 가 마일스톤 문서를 링크하고 활성 마일스톤(M1)을 표기.
- [ ] **AC6**: DESIGN.md §6 과 모순 없음(각 M 이 DESIGN Phase 에 매핑); 모든 내부 링크 유효(broken link 0).
- [ ] **AC7 (규율 — enforce hook-up)**: `CLAUDE.md` 의 "Task lifecycle" 섹션에 (a) roadmap/milestones
  문서 링크 + (b) "task 는 활성 마일스톤의 미충족 EC 에서 내려온다" 1줄 규율 포인터를 추가 — 규율이
  auto-load 컨텍스트(CLAUDE.md)에 박혀 다음 세션에도 실제로 적용됨(qa-verifier L1 BLOCK 흡수:
  문서 서술(AC4)만으로는 orphan → CLAUDE.md hook-up 으로 enforce 보장). **본 task scope 의 enforce 는
  CLAUDE.md 포인터까지**; rules/80 자체 개정(하네스 도메인)은 별도 task.
