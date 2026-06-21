# Harness Layer Architecture

> 단계 어휘 (L1·G1·L2·G2·L3) 매핑: [rules/80-task-lifecycle.md](../../../.claude/rules/80-task-lifecycle.md#단계-어휘-stage-vocabulary-ssot)
> 작성일: 2026-04-25 | 버전: v1
> 목적: 단일 `.claude/` 하네스 안에서 **가로(horizontal) × 세로(vertical) 레이어** 모델 정의. 향후 vertical 추가 가이드.
> 관련: [master-plan.md](./master-plan.md), [process-diagram.md](./process-diagram.md)

---

## 계약 명세 vs .claude/context — 역할 분리

본 하네스의 핵심 원칙: **코드 내 계약(contract 테스트 + docstring) 이 SSOT, `.claude/context` 가 하네스 canonical 요약**.

| 영역 | 역할 | 편집자 | 사용자 | 형식 |
|---|---|---|---|---|
| `docs/` 설계 노트 | 메인테이너 원본 reference (위키성) | 메인테이너 | 인간 (자유 편집) | 자유 형식 |
| `.claude/context/` | 하네스 canonical (실제 동작 기반) | 개발자 (sync 시점 통제) | Claude / Skills / Hooks | 영문 slug, frontmatter `domain:` 필수 |
| contract 테스트 + docstring | 계약 SSOT (실행 검증 — **예외**: 본 영역만 실행으로 강제) | 메인테이너 | `pytest`, env 구현체 | Python (실행 가능) |

### 원칙

1. **하네스는 `.claude/context/` 만 참조**. 모든 Skill / agent / hook 가 `.claude/context/` 를 canonical 로 사용
2. **`docs/` 설계 노트는 메인테이너 자유 편집 영역**. 자유 형식 — 작성자 워크플로 우선
3. **drift 동기화는 수동 통제**. 자동 sync X (요약 재작성 비용)
4. **contract 테스트는 SSOT 역할 유지** (실행으로 강제) — 설계 노트와 다른 취급

### 동기화 워크플로

```
[메인테이너] docs/ 의 wrapper 설계 노트 편집
    ↓
[개발자] drift 감지 → 변경 항목 표시
[개발자] .claude/context/modules/framestack.md 갱신 (canonical 요약)
    ↓
[task-loop / 다음 task] 갱신된 canonical 사용
```

### context 정합성

`.claude/context/modules/*.md` 는 **실제 `crittergym/` 모듈 기준**. `docs/` 설계 노트와 차이는 정상:
- 일부 wrapper/utility 는 코드에 있지만 설계 노트 미작성 → 메인테이너 위임 영역

---

## 핵심 원칙 (단일 하네스 + 다중 레이어)

**단일 하네스, 다중 레이어**. 별도 `.claude/` 디렉토리를 만들지 않는다.

- **🔵 Horizontal (process)**: 도메인 무관. 모든 작업의 lifecycle 관리
- **🟢🟡🟠 Vertical (domain)**: 도메인 특화. rl-env·render·agents·perf 등

두 레이어는 **같은 `.claude/{rules,hooks,skills,agents,context,data}/`** 안에 평면 배치되고, **prefix 컨벤션 + `domain:` frontmatter** 로 구분된다.

---

## 왜 단일 하네스?

| 별도 하네스 | 단일 하네스 |
|---|---|
| Claude Code 는 `.claude/` 1개만 로드 → invisible | 모든 자산 자동 발견 |
| 별도 디렉토리 = 단일 레포 의도와 배치 | 레포 단일 진실 |
| process layer 중복 (각 하네스마다 task-*) | process layer 1번 작성, 모든 vertical 재사용 |
| 컨텍스트 비용 폭증 (양쪽 다 로드) | 단일 컨텍스트, on-demand 선택 로드 |
| settings.json·CLAUDE.md 분기 관리 | 1곳에서 통합 관리 |

**결정**: 단일 `.claude/`, prefix + frontmatter 로 레이어 구분.

---

## 레이어 모델

```
                    [ 🔵 Process Layer (horizontal) ]
                    task-start, task-end, task-evaluate,
                    task-verify, task-loop, task-review,
                    @plan-reviewer, @qa-verifier,
                    rules/0X-forbidden, rules/80-task-lifecycle,
                    rules/85-git-policy, hooks/harness-*
                              │
              ┌───────────────┼───────────────┬───────────────┐
              ▼               ▼               ▼               ▼
    [ 🟢 rl-env Vertical ] [ 🟡 render ]   [ 🟠 agents ]    [ 🟣 perf ]
    env/spaces/wrappers   render/viewer    baseline eval    JAX/벡터화
    (현재 ✅)             결정성 가드      (future)         (future)
    계약·결정성 검사
```

### 🔵 Horizontal — Process Layer

**범위**: 작업 lifecycle 자체. 모든 도메인이 공통으로 사용.

**구성**:

| 종류 | 파일 prefix | 책임 |
|---|---|---|
| Skills | `task-*` | task-start/end/evaluate/verify/loop/review |
| Agents | `plan-reviewer`, `qa-verifier` | L1·L3 평가 (도메인 무관) |
| Hooks | `harness-*`, `git-policy-guard`, `agent-worktree-*` | 작업 lifecycle 추적·git 정책·worktree 관리 |
| Rules | `00-*`, `80-*`, `85-*` | 보편 금지 + lifecycle 운용 원칙 + git 정책 |
| Context | `context/lifecycle/` | pass-criteria, process docs |

**`domain: lifecycle`** frontmatter.

**재사용**: 단 한 번 작성하면 env 작업이든, 새 렌더 모드든, 벡터화 패치든 **동일하게 사용**.

### 🟢🟡🟠 Vertical — Domain Layer

**범위**: 특정 도메인 (rl-env, render, agents, perf 등).

**구성**:

| 종류 | 파일 prefix | 책임 |
|---|---|---|
| Skills | `<domain>-*` | 도메인 전용 동작 (`/check-contract`, `/bench-perf` 등) |
| Agents | `<domain>-*` | 도메인 전용 검증 (`@rl-env-auditor`, `@perf-auditor`) — 기본 미동봉, 추가 시 |
| Hooks | `<domain>-*` | 도메인 위반 감지 |
| Rules | `9X-` | 도메인 정책 |
| Context | `context/{modules,contracts,...}` | 도메인 문서 |

**`domain: <name>`** frontmatter.

> **기본 동봉 reviewer**: 이 포트에서 실제 동봉되는 reviewer/auditor 는 `@plan-reviewer` + `@qa-verifier` 두 개뿐. 도메인 auditor (`@rl-env-auditor`, `@perf-auditor` 등) 는 아래 [Vertical 추가 플레이북](#vertical-추가-플레이북) 의 확장점으로 필요 시 추가한다.

---

## 컨벤션

### Prefix 규칙

| Layer | Prefix | 예시 |
|---|---|---|
| 🔵 Process | `task-`, `harness-` | `task-verify`, `harness-task-start-guard.py` |
| 🟢 rl-env | `rl-env-` 또는 `env-` | `env-contract-check.py`, `rl-env-auditor.md` |
| 🟡 render | `render-` | `render-determinism-guard.py` |
| 🟠 agents | `agents-` | `agents-eval-check.py` |
| 🟣 perf | `perf-` | `perf-loop-check.py` |

**예외**: `agents/plan-reviewer.md`, `qa-verifier.md` 같은 **process layer 의 일반명사 agent** 는 prefix 없음 (`task-` 가 어울리지 않음).

### Frontmatter `domain:` 필드 (필수)

모든 신규 skill/agent/hook/rule 파일은 `domain:` 필드를 가진다.

```yaml
---
name: task-evaluate
domain: lifecycle           # 🔵 horizontal
---
```

```yaml
---
name: check-contract
domain: rl-env              # 🟢 vertical
---
```

```yaml
---
name: perf-loop-check
domain: perf                # 🟣 vertical
---
```

`rules/80-task-lifecycle.md` (Phase 4d) 가 frontmatter `domain:` 누락 시 warning 발행.

### Rules Numbering

| 범위 | 영역 |
|---|---|
| `00-09` | 🔵 보편 금지 (forbidden, baseline) |
| `80-89` | 🔵 lifecycle, task workflow |
| `85` | 🔵 git policy (단방향 sink — 옵션) |
| `90-99` | 🟢🟡🟠🟣 vertical (rl-env, render, agents, perf) |

> 이 포트는 도메인 정책 rule 을 모두 `90-99` 범위에 둔다 (rl-env / render / agents / perf 각 1 블록). 새 vertical 도입 시에도 90-99 범위 사용.

---

## 현재 상태 (Phase 3 완료 시점)

### 🔵 Process Layer (Phase 4 에서 구축)

| 자산 | 수량 | 상태 |
|---|---|---|
| Skills (`task-*`) | 6 신규 | ⚪ Phase 4 |
| Agents | 2 (plan-reviewer, qa-verifier) | ⚪ Phase 4a |
| Hooks | harness-task-start-guard, harness-task-intent-nudge, harness-commit-guard, harness-commit-intent-record, task-end-archive-guard, git-policy-guard, agent-worktree-return-handler, agent-worktree-stop-guard | ⚪ Phase 4 |
| Rules (00, 80, 85) | 3 | ⚪ Phase 4d |
| Context | `lifecycle/pass-criteria.md` | ⚪ Phase 4b |

### 🟢 rl-env Vertical

| 자산 | 수량 | 상태 |
|---|---|---|
| Hooks (`env-*`) | env-contract-check, determinism-guard | 🟡 (Phase 3 기초) |
| Rules (9X) | env 계약 정책 | 🟡 |
| Context | `contracts/`, `modules/` | 🟡 |

### 🟡 render Vertical (Phase 4c)

| 자산 | 수량 | 상태 |
|---|---|---|
| Hooks (`render-*`) | render-determinism-guard | ⚪ Phase 4c |
| Rules (9X) | render 계약 | ⚪ Phase 4c |
| Context | `contracts/render.md` (선택) | ⚪ |

### 🟠🟣 Future Verticals (계획 단계)

agents (baseline eval), perf (JAX 벡터화). 미정. 필요 시점에 본 문서의 [Vertical 추가 플레이북](#vertical-추가-플레이북) 참조.

---

## Vertical 추가 플레이북

새 vertical (예: agents, perf) 추가 절차. **도메인 auditor agent 도 이 플레이북의 확장점으로 추가**된다 (기본 동봉은 plan-reviewer + qa-verifier 뿐).

### 사전 검토

1. **기존 vertical 로 흡수 가능한가?** — 예: 간단한 render 결정성 검사는 rl-env vertical 에 추가 가능
2. **process layer 만으로 충분한가?** — task-* skill 만으로 해결되면 별도 vertical 불필요
3. **자체 SSOT 데이터가 필요한가?** — 도메인 전용 JSON·정책이 있어야 vertical 가치

### 단계별 추가

#### 1단계: domain prefix 결정

- 단일 prefix: `render-`, `agents-`, `perf-`
- 서브도메인 dot notation: `agents.baseline`, `agents.eval`

#### 2단계: rules 추가 (90-99 범위)

```markdown
---
id: 92-perf-vectorization
domain: perf
paths:
  - crittergym/envs/**/*.py
  - crittergym/wrappers/**/*.py
priority: 92
---

# Perf Vectorization 정책
- step hot path 에 per-element Python 루프 금지
- 시드/배치 차원 보존
- ...
```

#### 3단계: agents 추가 (선택)

도메인 검증 전담 agent. process layer 의 `task-evaluate` 가 도메인 라우팅으로 호출.
**이것이 reviewer 풀을 확장하는 지점이다** — 추가 전까지 L1/L3 는 plan-reviewer + qa-verifier 만 사용.

```markdown
---
name: perf-auditor
domain: perf
model: sonnet
---

# Perf Auditor
plan 또는 PR 의 hot path 변경을 평가:
1. 벡터화 가능 패턴 위반 (per-element 루프)
2. 배치/시드 차원 보존
3. steps-per-second 회귀 가능성

verdict: APPROVE / SUGGEST / BLOCK
```

#### 4단계: hooks 추가 (선택, 결정적 가드)

```python
#!/usr/bin/env python3
"""perf-loop-check — PostToolUse Edit
- step hot path 내 per-element Python 루프 감지
domain: perf
"""
```

#### 5단계: skills 추가 (선택, 사용자 명시 호출용)

```yaml
---
name: bench-perf
domain: perf
description: steps-per-second 벤치
---
```

#### 6단계: context 추가 (도메인 문서)

```
.claude/context/perf/
├── vectorization.md
└── known-bottlenecks.md
```

#### 7단계: process layer 와 연동

- `task-evaluate` 가 plan 의 영향 경로 (`crittergym/envs/**`) 를 보고 자동으로 `@perf-auditor` 병렬 스폰
- `task-review` 도 동일
- 도메인 라우팅 로직은 `rules/80-task-lifecycle.md` 가 정의

#### 8단계: 검증

- 새 task 진행해 보기 — process layer 가 도메인을 자동 인식하는지
- frontmatter `domain:` 필드 일관성 (rules/80 가 강제)

#### 9단계: 본 문서 갱신

[현재 상태](#현재-상태-phase-3-완료-시점) 표에 vertical 행 추가.

---

## Cross-vertical 상호작용

여러 vertical 이 동시에 적용되는 경우 (예: wrapper 에서 env 계약 + render 결정성 + perf 벡터화 동시 수정).

### 자동 처리 원칙

1. **paths 기반 라우팅**: 각 rule/hook 의 `paths:` 가 매칭되면 자동 활성화. 우선순위는 `priority:` 필드
2. **multi-agent 병렬**: `task-evaluate` 가 영향 경로 분석 → 해당하는 모든 vertical agent 를 **단일 메시지에 병렬** 스폰
3. **verdict aggregator**: 모든 vertical 의 verdict 를 합산. 1+ BLOCK → 전체 BLOCK
4. **충돌 처리**: vertical 간 정책 충돌 시 `priority:` 낮은 쪽이 우선 (00-09 가장 강력)

### 예시

wrapper 에 frame stacking 추가 + render 오버레이 추가 + 벡터화 경로 유지:

```
/task-start "framestack + 디버그 오버레이"
   ↓
/task-evaluate
   ├─ @plan-reviewer (lifecycle) — 기본 동봉
   ├─ @qa-verifier (lifecycle)   — 기본 동봉
   ├─ @rl-env-auditor (paths: crittergym/wrappers/** 매칭) — if added
   ├─ @render-auditor (paths: crittergym/render/** 매칭)   — if added
   └─ @perf-auditor (paths: hot path 매칭)                 — if added
   ↓
verdict aggregator (verdict 합산)
   ↓
DoR / DoD / L3 동일 패턴
```

---

## 결정 기록 (ADR-like)

### 왜 namespace 가 아니라 prefix?

namespace 옵션 (예: `.claude/skills/rl-env/contract/SKILL.md`) 검토했으나:
- Claude Code 의 skill discovery 가 평면 구조 가정 → 깊은 nest 미지원
- 사용자가 `/check-contract` 입력 시 nested 경로 직관성 떨어짐
- prefix 가 grep·정렬·필터링에 친화적

**결정**: 평면 + prefix.

### 왜 별도 settings.json 가 아니라 frontmatter?

vertical 별 settings.json (예: `settings.rl-env.json`, `settings.perf.json`) 검토했으나:
- Claude Code 가 단일 settings.json 만 읽음
- frontmatter 가 in-file annotation 이라 파일과 분리되지 않음
- domain 라우팅 로직은 어차피 코드 (rules/80) 가 처리

**결정**: 단일 settings.json + frontmatter `domain:`.

### 왜 vertical 도 같은 dir?

`.claude/domains/<name>/` 구조 검토했으나:
- discovery 한계 (위 namespace 결정과 동일)
- 한 파일이 여러 vertical 에 걸칠 때 (예: wrapper + render) 위치 모호
- prefix 만으로 충분

**결정**: 평면 + prefix.

### 왜 git 통합은 main trunk 기본 + qa sink 옵션?

이 프로젝트는 solo OSS 라 무거운 sink 브랜치 모델이 과함:
- 기본: `feature/fix/...` → `main` (trunk) 직접 PR
- `qa/*` one-way sink (rules/85) 는 **옵션 패턴** — 다인 협업·릴리스 게이팅이 필요할 때만 활성화
- `git-policy-guard` hook 이 main 직접 작업·잘못된 머지 방향을 가드

**결정**: main trunk 기본, qa sink 옵션.

---

## 운용 가이드

### 매 PR 점검

- 신규 skill/agent/hook/rule 에 `domain:` frontmatter 있는지
- prefix 규칙 준수
- rules numbering 충돌 없는지

### 분기점

- 새 vertical 도입 결정 시 본 문서의 [Vertical 추가 플레이북](#vertical-추가-플레이북) 따름
- vertical 폐기 시: 파일 삭제 + 본 문서 [현재 상태](#현재-상태-phase-3-완료-시점) 갱신

### 메트릭 (Phase 5 운용 시)

- vertical 별 hook trigger 횟수
- vertical 별 agent 토큰 사용량
- cross-vertical 작업 비율 (multi-domain 작업)

---

## 변경 이력

| 일자 | 버전 | 변경 |
|---|---|---|
| 2026-04-25 | v1 | 초안. Phase 3 완료 직후 Phase 4 청사진과 함께 작성 |
