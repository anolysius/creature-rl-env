# Harness Phase 4: Task 라이프사이클 통합 — 계획

> 단계 어휘 (L1·G1·L2·G2·L3) 매핑: [.claude/rules/80-task-lifecycle.md](../../../.claude/rules/80-task-lifecycle.md#단계-어휘-stage-vocabulary-ssot)
> 작성일: 2026-04-25 | 상태: 계획
> 청사진: [./process-diagram.md](./process-diagram.md) — RFC + ATDD + Multi-Reviewer PR
> 선행: 하네스 기반 설치 (`.claude/` tracked)

---

## 목표

다이어그램의 **3 loop (L1·L2·L3) + 2 gate (DoR·DoD)** 를 결정적 슬래시 커맨드 체인으로 구현. **horizontal layer** (도메인 무관) 라 CritterGym 의 어떤 vertical (rl-env / render / agents / perf) 에도 재사용된다.

## 배경 — Phase 4 가 풀어야 할 갭

| 현재 (기반 설치 시점) | 다이어그램이 요구하는 것 | 갭 |
|---|---|---|
| `commands/task-{start,end}.md` 단순 명령 | Skill 로 격상 + frontmatter `domain: lifecycle` | Skill 변환 필요 |
| 단일 agent 호출 | L1·L3 의 ≥2 agent 병렬 합의 | verdict aggregator 신규 |
| reviewer agent 미비 | `@plan-reviewer` + `@qa-verifier` 신규 필요 | agents 신규 |
| pass criteria 정의 없음 | G1 통과 시점에 acceptance 확정 | `pass-criteria.md` + qa-checklist 자동 생성 |
| TDD 명시 없음 | L2 의 Red-Green-Refactor 강제 | `tdd-guard` + `task-loop` 협업 |
| 운용 원칙 미강제 | 단방향·병렬·acceptance 사전·iteration cap·no-progress | `rules/80-task-lifecycle.md` |

---

## 작업 범위

### 신규 산출물

| 종류 | 파일 | 단계 |
|---|---|---|
| Skill | `.claude/skills/task-start/SKILL.md` | 4a |
| Skill | `.claude/skills/task-end/SKILL.md` | 4a |
| Skill | `.claude/skills/task-evaluate/SKILL.md` | 4a |
| Skill | `.claude/skills/task-verify/SKILL.md` + `scripts/run-tdd.py` | 4b |
| Skill | `.claude/skills/task-loop/SKILL.md` | 4b |
| Skill | `.claude/skills/task-review/SKILL.md` | 4d |
| Agent | `.claude/agents/plan-reviewer.md` | 4a |
| Agent | `.claude/agents/qa-verifier.md` | 4a |
| Rule | `.claude/rules/80-task-lifecycle.md` | 4d |
| Context | `.claude/context/lifecycle/pass-criteria.md` | 4b |

### 수정 산출물

| 파일 | 변경 |
|---|---|
| `CLAUDE.md` | "## Task Lifecycle" 섹션 활성화 (다이어그램 reference) |
| `.claude/commands/task-{start,end}.md` | Skill 로 redirect 또는 삭제 |

### 영향 범위

- **모든 향후 작업**: `/task-start` 부터 `/task-end` 까지 결정적 흐름 강제
- **agent 비용**: 매 작업당 최소 4 agent 호출 (L1 2 + L3 2). Haiku 격리로 비용 제어
- **모든 vertical**: Phase 4 산출물은 `domain: lifecycle` — rl-env/render/agents/perf 등 모든 vertical 이 그대로 사용

---

## Step 별 상세

### Phase 4a — Lifecycle 기반 (1일)

#### Step 4a.1: task-start, task-end → Skill 변환 (반나절)

**목표**: `commands/` 의 두 파일을 `skills/` 로 격상. frontmatter 추가.

**실행**:
```bash
mkdir -p .claude/skills/task-start .claude/skills/task-end
# task-start
cp .claude/commands/task-start.md .claude/skills/task-start/SKILL.md
# task-end
cp .claude/commands/task-end.md .claude/skills/task-end/SKILL.md
```

**frontmatter 추가**:
```yaml
---
name: task-start
description: |
  새 작업의 PRD/계획 문서를 생성한다. 사용자가 "작업 시작",
  "계획 작성", "PRD 만들기", "/task-start" 호출 시 트리거.
argument-hint: "[작업 제목]"
context: inline
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
domain: lifecycle
---
```

`task-end` 도 동일 패턴 (`description` 키워드: "리포트", "작업 완료", "QA 체크리스트").

**기존 `commands/task-{start,end}.md` 처리**:
- 옵션 A: stub 으로 redirect (`이 명령은 /task-start Skill 로 이주됨` 안내)
- 옵션 B: 삭제 (Skill 만으로 동작)
- → **A 권장** (사용자 muscle memory 보존)

**검증**: 새 세션에서 `/task-start "테스트"` 호출 → plan.md 생성 확인.

#### Step 4a.2: `agents/plan-reviewer.md` 신규 (1시간) 🆕

```markdown
---
name: plan-reviewer
description: |
  계획서(plan.md) 의 품질을 평가한다. L1 계획 정련 loop 에서
  /task-evaluate 가 병렬 스폰. 메인 컨텍스트 보호 위해 격리 실행.
model: sonnet
domain: lifecycle
---

# Plan Reviewer

# 평가 축
1. **범위 명확성**: 작업 대상 파일·범위가 명시됐나
2. **영향도 분석**: 직접·간접 영향이 식별됐나
3. **리스크 식별**: 주요 리스크 + 대응이 있나
4. **검증 방법**: lint/type-check/test/determinism 등 검증 계획이 구체적인가
5. **산출물 명시**: 코드·문서·커밋 단위가 명확한가

# 출력 형식 (verdict)
다음 중 하나로 응답:
- `APPROVE` — 모든 축 충족
- `SUGGEST: <축>: <개선안>` — 통과 가능하지만 보완 권장
- `BLOCK: <축>: <필수 보완>` — 통과 불가, 반드시 수정 필요

# 호출 패턴
@plan-reviewer "{plan.md 경로}"
```

#### Step 4a.3: `agents/qa-verifier.md` 신규 (1시간) 🆕

```markdown
---
name: qa-verifier
description: |
  DoD/DoR 검증 전담. plan.md ↔ 결과 (코드·report) 정합성을
  격리 컨텍스트에서 검증. 메인에 verdict 만 반환.
model: haiku
domain: lifecycle
---

# QA Verifier

격리 컨텍스트에서 plan vs 결과 비교. 사용처:
- L1 끝: plan 의 acceptance criteria 가 SMART 한지
- G2 (DoD): 모든 acceptance 가 통과됐는지
- L3: PR diff 가 plan 의 범위를 벗어나지 않는지

verdict: APPROVE / SUGGEST / BLOCK
```

#### Step 4a.4: `skills/task-evaluate/` 신규 (1시간) 🆕 — L1 진입점

```yaml
---
name: task-evaluate
description: |
  계획서를 ≥2 agent 병렬 호출로 평가하고 verdict 를 종합한다.
  /task-start 직후 자동 호출 또는 사용자 명시 호출.
argument-hint: "[plan-path] (optional, 기본=docs/_active/**/plan.md 최신)"
allowed-tools: Bash, Read, Agent
domain: lifecycle
---

# Task Evaluate (L1)

## 동작
1. plan.md 식별 (인자 또는 최신)
2. **paths 라우팅 알고리즘** (Step 4a.4 핵심)
3. **병렬 스폰** (단일 메시지에 N Agent tool)
4. **verdict aggregator** 로 종합 → Decision
5. iteration log 기록 (no-progress 감지)

## Paths 라우팅 알고리즘

```python
def route_evaluators(plan: PlanMd) -> list[Agent]:
    agents = ["@plan-reviewer"]  # lifecycle 무조건 포함
    declared = plan.frontmatter.get("domains", [])      # 명시적 선언
    scope_paths = plan.frontmatter.get("scope_paths", [])

    # 1) 명시 도메인 → 해당 vertical 의 *-auditor (있으면)
    for d in declared:
        agent = f"@{d.split('.')[0]}-auditor"           # rl-env, render, agents, perf
        if agent_exists(agent):
            agents.append(agent)

    # 2) scope_paths 기반 보완 (rules paths 매칭)
    for path in scope_paths:
        for rule in load_rules():
            if path_match(rule.frontmatter.paths, path):
                agent = f"@{rule.frontmatter.domain}-auditor"
                if agent_exists(agent) and agent not in agents:
                    agents.append(agent)

    return dedupe(agents)
```

→ 기본 구성은 `@plan-reviewer` + `@qa-verifier`. vertical 전용 `@<domain>-auditor` 를 추가하면 자동 라우팅된다 (확장 지점).

## Verdict Aggregator

```python
def aggregate(verdicts: list[Verdict]) -> Decision:
    if all(v.kind == "APPROVE" for v in verdicts):
        return Decision.APPROVED      # → L1 종료, G1 진입

    blocks = [v for v in verdicts if v.kind == "BLOCK"]
    if blocks:
        if is_repeat_block(blocks):                 # 동일 BLOCK 2회 (rules/80)
            return Decision.NO_PROGRESS_ESCALATE    # 즉시 사용자
        return Decision.BLOCKED(blocks)             # 보완 요청 → L1 재진입

    suggests = [v for v in verdicts if v.kind == "SUGGEST"]
    return Decision.SUGGEST_CUTOFF(suggests)        # 사용자 컷오프 가능
```

## Selective Re-evaluation (재진입 시)

L1 재진입 시 **변경된 부분만 재평가** — 비용 절감:
- 1차 BLOCK 한 agent 만 재호출 (다른 agent 는 이전 verdict 캐시)
- plan 의 변경 라인이 다른 vertical 영향 없으면 그쪽 agent 도 skip
```

#### Step 4a.5: 통합 동작 확인 (30분)

- 더미 plan: `/tmp/test-plan.md`
- `/task-evaluate /tmp/test-plan.md` 호출 → 병렬 verdict 확인
- L1 loop 5회 이내 종료 가능성 검증

**4a 완료 기준**:
- [ ] `/task-start`, `/task-end` Skill 동작
- [ ] `@plan-reviewer`, `@qa-verifier` 스폰 가능
- [ ] `/task-evaluate` 가 ≥2 agent 병렬 + aggregator 정상
- [ ] 모든 산출물 `domain: lifecycle` frontmatter

---

### Phase 4b — TDD 검증 루프 (1일)

#### Step 4b.1: `pass-criteria.md` 설계 + qa-checklist 자동 합산 (1.5시간)

`.claude/context/lifecycle/pass-criteria.md`:

```markdown
---
name: Pass Criteria
description: G2 DoD 통과 기준. /task-verify 가 참조.
domain: lifecycle
---

# Default Passes

| ID | 명령 / 검사 | 통과 조건 |
|---|---|---|
| `lint` | `ruff check src tests` | exit 0 |
| `type_check` | `ruff` / `mypy` (설정 시) | exit 0 |
| `unit_tests` | `pytest` (해당 모듈) | 모두 pass |
| `determinism` | seed 고정 reset/step 재현 검사 | 동일 seed → 동일 trajectory |
| `obs_space_stable` | observation/action space 스키마 검사 | 기존 checkpoint 와 호환 |

# Plan Override
plan.md frontmatter 의 `passes:` 가 default 를 override.

```yaml
---
passes:
  - lint
  - unit_tests
  # determinism, obs_space_stable 생략 (문서 작업 등)
custom_passes:
  - id: my_custom_check
    cmd: bash scripts/my-check.sh
---
```

# G1 통과 시점 자동 합산 알고리즘
```python
def auto_generate_qa_checklist(plan: PlanMd, criteria: PassCriteria) -> QaChecklist:
    """G1 통과 즉시 호출. 도메인별 acceptance 자동 합산."""
    acceptance = {}
    for domain in plan.frontmatter.domains:
        # 1) pass-criteria.md 의 도메인 default 추가
        acceptance[domain] = criteria.defaults.get(domain, []).copy()
        # 2) plan.md frontmatter 의 도메인 override 병합
        plan_specific = plan.frontmatter.get("acceptance", {}).get(domain, [])
        acceptance[domain].extend(plan_specific)

    # 3) lifecycle (보편) 추가 — 무조건 포함
    acceptance["lifecycle"] = criteria.defaults.get("lifecycle", [])

    return QaChecklist(
        acceptance=acceptance,
        frozen=True,                           # rules/80 가 freeze 강제
        generated_at=now(),
    )
```

**G1 통과 후 acceptance 추가는 BLOCK** (rules/80). qa-checklist 신규 항목 추가 시도 시 즉시 차단 — scope creep 방지.
```

#### Step 4b.2: `skills/task-verify/` 신규 (반나절) — L2 check + G2

```yaml
---
name: task-verify
description: |
  pass-criteria 기준으로 1회 검증. TDD + 자동수정.
  /task-loop 의 inner step.
argument-hint: "[plan-path] (optional)"
allowed-tools: Bash, Read, Edit, Agent
domain: lifecycle
---
```

**SKILL.md 동작**:
1. plan.md + qa-checklist.md 수집
2. pass-criteria 분류:
   - TDD 그룹 (lint, unit_tests)
   - 환경 정합 그룹 (determinism, obs_space_stable)
   - Manual 그룹 (사용자 확인 필요)
3. 실행:
   - TDD: `scripts/run-tdd.py` → pytest wrapper
   - 환경 정합: seed 고정 재현 + space 스키마 diff
4. 자동수정 (whitelist):
   - 사소한 lint autofix (`ruff --fix`)
   - unused import 제거
   - 그 외 → 사용자 승인
5. report 갱신 + iteration log

#### Step 4b.3: `skills/task-loop/` 신규 (1시간) — L2-outer

```yaml
---
name: task-loop
description: |
  /task-verify 자율 N회 반복. L2-outer macro loop.
allowed-tools: Bash, Read, Edit, Agent
domain: lifecycle
---
```

**종료 조건**:
- `all_passed` — 모든 acceptance pass
- `max_iterations=5` — 컷오프 (사용자 에스컬레이션)
- `no_progress` — 동일 fail 2회 연속 (즉시 사용자에게)
- `critical_blocker` — lint/type-check 실패는 즉시 중단

#### Step 4b.4: tdd-guard 와 task-loop 협업 (1시간)

기존 `.claude/tdd-guard/data/test.json` 를 task-loop 가 읽고, 매 iteration 마다:
1. tdd-guard verdict 확인 (test 가 먼저 작성됐나)
2. 실패 시 `BLOCK: tdd-guard violation` → Red 단계로 회귀

#### Step 4b.5: G2 게이트 명세화 (30분)

`/task-verify` 결과 `pass` → G2 자동 통과. `partial`/`fail` → L2 재진입. `max_iterations` → 사용자.

**4b 완료 기준**:
- [ ] `/task-verify` 1회 호출 시 pass-criteria 전수 검증
- [ ] `/task-loop` 4종 종료 조건 동작
- [ ] tdd-guard 협업 검증
- [ ] G2 통과 자동 판정

---

### Phase 4c — vertical hook 통합 (0.5일)

#### Step 4c.1: vertical 검증 hook 통합 (점진적)

각 vertical (rl-env/render/agents/perf) 이 결정론적 검증을 추가할 때, regex/AST/glob 기반은 hook 으로만 구현하고 (rules/80 §C), 의미 판단이 필요한 경우만 `@<domain>-auditor` agent 로 격상한다. hook 은 `pass-criteria.md` 의 도메인 default 로 등록되어 `/task-verify` 가 자동 호출한다.

#### Step 4c.2: pass-criteria 통합

새 vertical default 를 `pass-criteria.md` 에 추가하면 해당 도메인 plan 의 acceptance 합산에 자동 반영된다.

**4c 완료 기준**:
- [ ] vertical hook (있을 경우) 차단/피드백 동작
- [ ] 해당 rule + path 매칭
- [ ] pass-criteria 에 통합

---

### Phase 4d — Multi-reviewer L3 + rules/80 (0.5일)

#### Step 4d.1: `skills/task-review/` 신규 (1시간) — L3 진입점

```yaml
---
name: task-review
description: |
  G2 통과 후 L3 코드 리뷰. ≥2 reviewer 병렬 합의.
allowed-tools: Bash, Read, Agent
domain: lifecycle
---
```

**aggregator**:
- 모두 `APPROVE` → L3 종료
- 1+ BLOCK → 회귀 개선 후 재진입
- SUGGEST → 사용자 컷오프 가능

#### Step 4d.2: `rules/80-task-lifecycle.md` 신규 (1시간) — 운용 원칙 강제

```markdown
---
id: 80-task-lifecycle
domain: lifecycle
paths:
  - "**/*"
priority: 80
related:
  - skills/task-evaluate/SKILL.md
  - skills/task-verify/SKILL.md
  - skills/task-review/SKILL.md
  - context/lifecycle/pass-criteria.md
---

# Lifecycle 운용 원칙

## A. 흐름 제어
1. **단방향 전진**: G1·G2 통과 후 plan 수정 시 새 task slug 강제
2. **병렬 평가**: L1·L3 의 ≥2 agent 호출은 단일 메시지에 묶음 (순차 호출 BLOCK)
3. **acceptance 사전 정의**: G1 통과 후 qa-checklist 신규 항목 추가는 BLOCK
4. **iteration cap**: L1 ≤ 사용자 컷, L2-outer ≤ 5, L3 ≤ 사용자 컷
5. **no-progress 감지**: 동일 fail 2회 연속 → 사용자 에스컬레이션
6. **plan 누락 경고**: 큰 변경(N≥5 파일) plan 없으면 SUGGEST

## B. 도메인 거버넌스
7. **domain frontmatter 필수**: 모든 skill/agent/hook/rule 의 `domain:` 필드 강제. 누락 BLOCK
8. **Cross-vertical 우선순위**: rules `priority:` 낮은 쪽이 강함. 충돌 시 task-evaluate 가 사용자 알림 우선

## C. Hook 우선 원칙 (토큰 절감)
9. **Deterministic = Hook**: regex/AST/glob 기반 검증은 hook 으로만. agent 호출 시 BLOCK
   - 예: import 위반 감지 → hook / 매핑 조회 → skill
   - 의미 판단 (env state machine, reward invariant) → agent 허용

## D. 비용 임계값 (자동 알림)
| 신호 | 임계값 | 조치 |
|---|---|---|
| 단일 작업 토큰 | 200k+ | 작업 분할 권고 |
| 단일 단계 agent 호출 | 10+ | paths 라우팅 검토 |
| L2-outer iteration | 5회 | 자동 에스컬레이션 |
| no-progress | 동일 fail 2회 | 즉시 사용자 |
```

#### Step 4d.3: CLAUDE.md Task Lifecycle 섹션 활성화 (30분)

```markdown
## Task Lifecycle
다이어그램: `docs/harness/explanation/process-diagram.md`

표준 흐름:
1. `/task-start "<제목>"` — plan.md
2. `/task-evaluate` — L1 평가 (≥2 agent 병렬) → DoR
3. (G1) — qa-checklist 자동 생성, acceptance 확정
4. TDD 구현 (`/task-loop` 자율, max 5)
5. `/task-verify` — L2 종료 검증 (G2)
6. `/task-review` — L3 (≥2 reviewer 병렬)
7. `/task-end` — report.md
8. 커밋 + 푸쉬
```

#### Step 4d.4: 풀 사이클 E2E (1시간)

더미 작업: "예시 wrapper 에 옵션 인자 추가"
1. `/task-start` → plan
2. `/task-evaluate` → L1 통과 → G1
3. `/task-loop` → L2 자율
4. `/task-verify` → G2
5. `/task-review` → L3 통과
6. `/task-end` → report
7. 커밋 시뮬레이션

→ 모든 게이트·loop 통과 확인.

**4d 완료 기준**:
- [ ] `/task-review` ≥2 reviewer 합의 동작
- [ ] `rules/80` lifecycle 위반 시 warning
- [ ] CLAUDE.md Task Lifecycle 섹션 + 다이어그램 reference
- [ ] 풀 사이클 1회 통과

---

## 검증 방법

### 자동 검증
- 전체 Skill 목록에 `task-*` 6종 표시
- 전체 Agent 목록에 `plan-reviewer`, `qa-verifier` 표시
- `rules_loader` 가 rules/80 정상 로드

### 수동 검증
- 풀 사이클 E2E (4d.4) 통과
- multi-agent 병렬 호출 시 verdict aggregator 정상
- iteration cap 동작 (max 5 도달 시 사용자 에스컬레이션)
- frontmatter `domain:` 누락 파일 시 rules/80 warning

---

## 리스크

| 리스크 | 대응 |
|---|---|
| 토큰 비용 폭증 (4 agent × 매 작업) | Haiku 격리 (qa-verifier), Sonnet 만 plan-reviewer, max_iterations 컷 |
| 자동수정 의도 외 변경 | whitelist (lint autofix, unused import) 만 |
| 교착 (같은 fail 반복) | no_progress 감지 → 즉시 사용자 |
| L1 evaluator false positive | aggregator 가 SUGGEST 만일 때 사용자 컷오프 허용 |
| domain frontmatter 누락 → 잘못된 agent 호출 | rules/80 가 frontmatter 강제 검증 |
| Phase 4 자체가 큰 작업 | **Phase 4 도 본 프로세스로 진행**: `/task-start "Phase 4"` → 본 plan.md → L1 평가 → ... |

---

## 다음 단계

Phase 4a 부터 순차:
1. `/task-start "Phase 4a: Lifecycle 기반"` (사용자 호출)
2. 본 plan 의 4a step 들을 새 plan.md 로 분기
3. L1 평가 (단, plan-reviewer 가 아직 없으므로 첫 사이클은 사용자 manual review)
4. 4a 구현 → `@plan-reviewer` 스폰 가능해지면 4b 부터 본 프로세스 적용
5. **bootstrap 모순 해결**: Phase 4a 완료 후부터 본 프로세스가 자기 자신에 적용됨 (자기 부트스트래핑)
</content>
</invoke>
