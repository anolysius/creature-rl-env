---
name: task-start
description: |
  새 작업의 PRD/계획 문서를 생성하고 L1 평가 진입점을 제공한다.
  사용자가 "작업 시작", "계획 작성", "PRD 만들기", "/task-start" 호출 시 트리거.
  생성된 plan 은 docs/_active/[<initiative>/]<task-slug>/plan.md 에 저장 (Diátaxis 구조, ADR-0014).
argument-hint: "[작업 제목] [--initiative=<name>]"
context: inline
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
domain: lifecycle
---

# Task Start (L1 — 📋 계획 평가, Loop 1: Plan Evaluation 진입점)

새 작업의 plan.md 를 생성한다. 본 Skill 은 작업 lifecycle 의 첫 진입점 (다이어그램 단계 1).

## 입력

```
/task-start <작업 제목> [--initiative=<name>]
```

예시:
```
/task-start "TDD 검증 루프" --initiative=env-core
/task-start "리워드 함수 리팩토링"
/task-start "렌더링 버그 수정"
```

- `--initiative` 지정 시 → `docs/_active/<initiative>/<slug>/` (멀티 task 이니셔티브 안)
- 미지정 시 → `docs/_active/<slug>/` (단발 task)

인자가 없으면 사용자에게 작업 제목을 질문.

## 문서 경로 (Diátaxis 구조 — ADR-0014)

```
docs/
├── _active/                              ← 진행 중 task (prefix 없음)
│   ├── <initiative>/<slug>/plan.md       ← 이니셔티브 안
│   │   └── report.md                     ← /task-end 시 생성
│   └── <slug>/plan.md                    ← 단발 task
├── _archive/{YYYY-Q}/<initiative>/NN-<slug>/  ← /task-end 가 자동 이동 (NN- prefix 자동)
├── explanation/                          ← 살아있는 설계 narrative (왜)
├── how-to/                               ← 살아있는 절차·가이드 (어떻게)
└── reference/                            ← 살아있는 표·체크리스트 (사실)
```

## 이니셔티브 결정 가이드 (자동 제안 가능)

기존 진행 중 이니셔티브 (`docs/_active/*/INITIATIVE.md` 가 있는 폴더) 를 먼저 스캔. 작업 제목이 매칭되면 그 이니셔티브 제안:

- "harness", "lifecycle" → `harness`
- "env", "observation", "action space", "reward" → `env-core`
- "render", "visualization" → `render`

매칭 없거나 1회 task 면 단발 (이니셔티브 없음).

## 수행 절차

### 1. 컨텍스트 수집

- 사용자 작업 설명
- 해당 이니셔티브의 `INITIATIVE.md` (지정 시 필수 참조) — `docs/_active/<initiative>/INITIATIVE.md` 또는 `docs/_archive/{YYYY-Q}/<initiative>/INITIATIVE.md`
- 관련 evergreen 참고: `docs/{domain}/{explanation,how-to,reference}/`
- 관련 소스 코드 미리 탐색
- `git status` 현재 브랜치 상태
- **하네스 컨텍스트 자동 로드**: `docs/harness/{process-diagram, layer-architecture, cross-vertical-scenarios, task-lifecycle}.md`

### 2. plan 작성

`docs/_active/[<initiative>/]<task-slug>/plan.md` 생성. **frontmatter 필수**:

```yaml
---
slug: {task-slug}
initiative: {name|null}                    # null = 단발
status: active
started: YYYY-MM-DD
acceptance_freeze: pending                 # G1 통과 시 true
domains: [rl-env, render, agents, ...]      # cross-vertical 자동 감지
scope_paths:
  - src/critter_gym/envs/**
  - tests/test_env.py
extracted_to: []                           # /task-end 시 채움
supersedes: []
---
```

이어지는 본문 템플릿:

```markdown
# {작업 제목}

> 작성일: YYYY-MM-DD | 상태: 계획

## 목표
## 선행 조건
## 작업 범위
### 수정 대상 파일 (영향도 표)
### 영향 범위 (import 그래프)
## Step별 계획
## 검증 방법
## 리스크
## Acceptance Criteria (G1 통과 시 freeze)
```

### 2.5. task type 감지

plan 작성 후 `task_type` 자동 감지:

```bash
python3 .claude/skills/task-start/scripts/detect-task-type.py docs/_active/[<initiative>/]<slug>/plan.md
```

출력 (stdout JSON): `{"task_type": "harness|env|general", "matched_pattern": "..."}`.

**감지 룰** (priority 순):
1. `.claude/(hooks|skills|agents|rules)/**` → `harness` (하네스 자산 자체 변경)
2. `(envs|spaces|wrappers)/**` 또는 `registration.py` → `env` (RL 환경 코어 변경)
3. else → `general`

**manual override**: 사용자가 frontmatter 에 `task_type:` 명시 시 자동 감지 무시 + override 안내 stderr.

### 2.6. mode 감지 (rules/80 §F mode tiering, harness-mode-tiering 흡수)

plan 작성 후 `detect-task-mode.py` 호출 — scope_paths + domains + manual override 으로 3 mode 자동 분류:

```bash
python3 .claude/skills/task-start/scripts/detect-task-mode.py docs/_active/[<initiative>/]<slug>/plan.md
```

출력 (stdout JSON): `{"mode": "quick-fix|standard|heavy", "reason": "...", "file_count": N, "domains_count": N, "max_criticality": "...", "manual_override": bool}`.

**3 mode 정의** (rules/80 §F.1):

| Mode | 적용 조건 | Lifecycle 차이 |
|---|---|---|
| 🟢 quick-fix | 1-3 file + 모든 path criticality=low | task-evaluate single reviewer (qa-verifier만) / task-verify skip 가능 / task-review single reviewer / task-end minimal entry |
| 🟡 standard | default | 9 step 전부 |
| 🔴 heavy | 50+ file 또는 domains 3+ | task-loop max 5→8 / task-evaluate paths routing 의무 |

**자동 처리**:
- 판정 결과를 plan frontmatter `mode:` 에 기록 (task-start 가 chain)
- mode 별로 plan template 분기 — quick-fix 는 minimal (목표 + Acceptance 2 섹션), standard 는 현재 7 섹션, heavy 는 standard + cross-vertical 영향 섹션

**Manual override**: 사용자가 frontmatter 에 `mode:` 명시 시 자동 감지 무시 (override). `mode` enum: `"quick-fix"` / `"standard"` / `"heavy"`.

**CHANGELOG 강제**: 모든 mode 에서 audit trail entry 의무 (rules/80 §F.5).

### 3. 작업 시작 안내 + L1 평가 자동 chain

plan 생성 후:
1. 계획서 경로 사용자에게 알림 (한 줄)
2. TodoWrite 로 Step별 작업 항목 등록
3. **L1 평가 자동 호출**: 사용자 추가 prompt 없이 즉시 `/task-evaluate <plan-path>` 를 chain. plan 작성 → 평가까지 한 흐름으로 진행
4. 평가 verdict 수신 후 사용자에게 결과 보고:
   - `APPROVED` → G1 진입 confirm 요청
   - `BLOCKED` / `SUGGEST_CUTOFF` / `NO_PROGRESS_ESCALATE` → 사용자 결정 위임
5. 첫 Step 구현은 G1 통과 (사용자 confirm) 후에만 시작

**chain 의 의도**: 사용자가 두 번 prompt 입력 (`/task-start` + `/task-evaluate`) 하지 않아도 plan 작성과 L1 평가가 한 흐름으로. G1 게이트는 그대로 사용자 confirm 보호 — 자동화는 chain 까지만.

## 중요 원칙

- master-plan.md 와 기존 문서를 참조하여 컨텍스트 풍부하게
- 수정 대상 파일은 실제 코드를 탐색하여 구체적으로 명시
- 영향도는 import 그래프 + 페이지 사용 처 기반 판단
- plan 작성 후 즉시 구현 시작 X. **사용자 확인 (G1) 대기**
- L1 평가는 자동 chain — 단 G1 진입은 사용자 confirm 필수
- frontmatter `domains:` 와 `scope_paths:` 는 task-evaluate 의 paths 라우팅에 사용 — 정확히 작성
- task-evaluate 재진입 (BLOCK 후 plan 보완 → 재평가, Selective Re-evaluation) 은 사용자가 직접 `/task-evaluate` 단독 호출 — chain 은 첫 평가만

## 다이어그램 매핑

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의 **단계 1 계획 작성** + **L1 첫 평가 자동 chain**.
- 첫 호출: plan 작성 → `/task-evaluate` 자동 호출 → verdict 보고 → 사용자 G1 confirm 대기
- 재진입 (BLOCK 후): 사용자가 plan 보완 → `/task-evaluate` 단독 호출 (Selective Re-evaluation)
