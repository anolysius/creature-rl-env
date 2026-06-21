---
id: 80-task-lifecycle
domain: lifecycle
version: 1.0.0
paths:
  - "**/*"
priority: 80
owner: process-owner
related:
  - skills/task-evaluate/SKILL.md
  - skills/task-verify/SKILL.md
  - skills/task-loop/SKILL.md
  - skills/task-review/SKILL.md
  - context/lifecycle/pass-criteria.md
last_reviewed: 2026-04-26
freeze_until: "2026-05-12"
freeze_reason: "metric collection for v2.0 finalization (harness-stabilization initiative Task 06)"
title: "Task Lifecycle 운용 원칙"
tags:
  - lifecycle
  - process
  - governance
  - cost-control
---

# Task Lifecycle 운용 원칙

본 규칙은 [process-diagram.md](../../docs/harness/explanation/process-diagram.md) 의 9 단계 흐름 + 3 loop (L1·L2·L3) + 2 gate (G1·G2) 를 강제. paths `**/*` (무조건 로드).

## 단계 어휘 (Stage Vocabulary, SSOT)

코드명은 lifecycle 설계 차원에서 사용. 사람-친화 라벨은 사용자 대면 메시지·문서 narrative 에서 사용. 둘 다 같은 단계를 가리킴 — 본 표가 SSOT.

| 코드 | 사람-친화 라벨 | 영어 | 한 줄 의미 | 담당 skill |
|---|---|---|---|---|
| **L1** | 📋 계획 평가 | Loop 1: Plan Evaluation | "이 계획이 충분한가?" — ≥2 agent 가 plan 검토 | `/task-evaluate` |
| **G1** | 🚦 시작 승인 | Gate 1: Definition of Ready | "구현 시작해도 되는가?" — 사용자 confirm + acceptance freeze | (사용자 결정) |
| **L2-outer** | 🔁 반복 검증 | Loop 2 outer: Verify Macro | "max 2회 자동 검증 반복 (default, --max-iter override)" — task-loop 가 task-verify 반복 | `/task-loop` |
| **L2-inner** | 🧪 단일 검증 | Loop 2 inner: Verify Single | "이번 round acceptance 통과?" — 1회 task-verify | `/task-verify` |
| **G2** | ✅ 완료 판정 | Gate 2: Definition of Done | "DoD 모두 통과?" — task-verify 자동 판정 | `/task-verify` |
| **L3** | 👀 리뷰 합의 | Loop 3: Multi-reviewer Review | "여러 reviewer 동의?" — ≥2 reviewer 합의 | `/task-review` |

**사용 규칙**:
- *최초 등장*: 풀 라벨 — 예: `L1 (📋 계획 평가, Loop 1: Plan Evaluation)`
- *이후*: 코드명만 — 예: `L1`
- 사용자 대면 메시지 (skill 응답, error) 는 라벨 우선
- archive 안 historical narrative 는 변경 없음 (의도적 보존)

**작업 단위 어휘 (2계층, ADR-0014)**
- **Initiative** — 멀티 task 묶음. archive 에서 폴더 + INITIATIVE.md narrative
- **Task** — 1 plan + 1 report 단위. `/task-start` ↔ `/task-end` lifecycle atomic unit
- **Phase / Step 어휘 폐기** — Phase 는 Task 와 의미 중복, Step 은 plan/report 의 한 섹션이면 충분 (별도 파일은 사고)
- 단, "Phase 4 strict=0" / "Phase 5 strict=1" 같은 *운용 모드 이름* 은 별개 어휘로 유지

위반 시 strict=0 (Phase 4) 에서는 warning, strict=1 (Phase 5) 에서는 BLOCK.

---

## A. 흐름 제어

### 1. 단방향 전진
- G1·G2 통과 후 plan 수정 시도 시 **새 task slug 강제** — 기존 plan 의 frozen 상태 보호
- 위반 예: G1 통과 후 `phase-4d-...-plan.md` 의 acceptance 추가 → BLOCK + 새 slug 권유
- **lifecycle 순서 강제** (master 9-step): `5. /task-verify → 6. /task-review → 7. /task-end`. `/task-end` (active → archive `git mv`) 이전에 `/task-review` APPROVED 필수. 미수행 시 archive 후 L3 BLOCK 시 역방향 mv 필요 → 단방향 전진 위반. 예외: read-only / docs-only task 는 `/task-verify` skip 가능, 단 `/task-review` 는 skip 금지 (diff 검토 필수)

### 2. 병렬 평가
- L1 (`task-evaluate`) 와 L3 (`task-review`) 의 ≥2 agent 호출은 **단일 메시지에 multiple Agent tool** 묶어야 함
- 순차 호출 시 BLOCK + selective re-evaluation 안내
- 이유: confirmation bias 방지 + wall-clock + 토큰 절감

**예외 — quick-fix mode** (§F.1):
- plan frontmatter `mode: quick-fix` 시 단일 reviewer (qa-verifier) 만 호출 허용
- aggregate-verdicts.py 가 mode 값 읽어 ≥2 reviewer 강제 검증을 quick-fix 에선 우회
- 이 예외는 quick-fix 의 entry condition (1-3 file + criticality=low) 이 회귀 위험 작은 영역 한정이라 정합

### 3. acceptance 사전 정의 (G1 freeze)
- G1 통과 시점에 `qa-checklist.md` 가 자동 생성됨 (pass-criteria.md 의 default + plan acceptance 합산)
- **G1 통과 후 acceptance 신규 추가는 BLOCK** — scope creep 방지
- 추가가 필요하면 새 task slug

### 4. iteration cap
| Loop | 한도 |
|---|---|
| L1 (`task-evaluate`) | 사용자 컷오프 (소프트) |
| L2-outer (`task-loop`) | **2 (default, --max-iter override)** — heavy mode 8 |
| L3 (`task-review`) | 사용자 컷오프 (소프트) |

**L2 cap 2 근거** (harness-token-efficiency, 2026-05-04):
- 실측: task-loop 5 iter 도달 사례 1건 (single-context edge case), 일반 task 는 2 iter 이내 수렴
- 5 iter 가 진짜 필요한 task 는 `--max-iter 5` (또는 heavy mode default 8) 명시 호출 — escape hatch
- 2 iter 안에 안 풀리는 case 는 사람 개입이 6번째 iter 보다 비용 효율적
- 직전 1 iter 와 plan.md 재read 회피 (hand-off) 로 추가 절감
- worst case ~30-60k token/task 절감

### 5. no-progress 감지
- 동일 fail 2회 연속 → **즉시 사용자 에스컬레이션**
- L1: `aggregate-verdicts.py` 의 `is_repeat_block()` 자동 감지
- L2: `task-loop` 의 iteration log 비교
- L3: `task-review` 의 iteration log 비교

### 6. plan 누락 경고
- 큰 변경(N≥5 파일) 시 plan 없으면 **SUGGEST: plan 작성 권유**
- `git diff --name-only HEAD` 로 변경 수 감지

### 6.1. 기능 요청 선제 제안 (메인 에이전트 행동 유도)
- **트리거 의도**: 사용자 발화가 다음 중 하나에 해당하면 구현 시작 전 선제 질의
  - (a) 새 기능·컴포넌트·페이지 신설 의도
  - (b) 다파일 영향 리팩터·마이그·일괄 치환 의도
  - (c) 도메인 모델·API·라우팅 변경 의도
- **예시 발화** (exhaustive 아님): "X 추가해줘", "Y 만들어줘", "Z 페이지 조립", "리팩터해줘", "일괄 치환"
- **질의 형식**: "하네스 동작을 위해 `/task-start` 부터 갈까요?" + 1줄 근거 (예: "N≥5 파일 영향 예상")
- **자동 skip**: 한 줄 수정·오타·주석·질의응답·코드 탐색
- **명시 skip**: 사용자가 "skip" / "그냥 해" / "작은 거야" 등 명시 거부
- **판단 기준**: 모호하면 *질의하는 쪽으로 fallback* — false-positive 가 false-negative 보다 안전 (plan 한 번 더 묻는 비용 << acceptance freeze 누락 비용)

**hook 강제 (harness-bypass-guard, 2026-06-16 — soft→deterministic 격상)**: §C.9 "deterministic = Hook" 원칙대로 본 선제 제안을 2계층 hook 으로 강제. soft 행동 지시만으로는 긴 컨텍스트에서 묻히거나 행동 유도형 발화에 우회되기 때문.
- **L1 넛지** ([`harness-task-intent-nudge.py`](../hooks/harness-task-intent-nudge.py), UserPromptSubmit): 발화가 기능 요청((a)/(b)/(c)) 의도 + 진행 중 frozen task 부재 시 "구현 전 `/task-start`" reminder 를 additionalContext 로 주입 (recency 로 lost-in-the-middle 보완). 비차단.
- **L2 게이트** ([`harness-task-start-guard.py`](../hooks/harness-task-start-guard.py), PreToolUse Write\|Edit): 제품 소스(`src/**`·`tests/**`)에 **frozen plan(acceptance_freeze:true ∧ scope_paths 커버) 없이** 변경 시 **BLOCK**. 자동 통과: 비대상 경로(`.claude/**`·`docs/**` — plan 작성 자체는 chicken-egg 없음) / trivial edit(단일라인 ∧ ≤120 비공백자) / frozen plan 커버. OVERRIDE `HARNESS_SKIP_HARNESS=1` (rules/85 선례). 공유 판정 lib [`_lib/active_plan_scope.py`](../hooks/_lib/active_plan_scope.py).

### 12. Archive 참조 invariant (ADR-0014 후속, hook 강제)
- evergreen (`docs/<domain>/{explanation,how-to,reference}/` + `.claude/{skills,agents,rules,context}/` + 루트 README/CLAUDE.md) 안 markdown 의 link 가 `_archive/` 또는 `_active/` 안 파일을 가리키면 **PostToolUse 경고**
- 정당한 cross-task 의존성은 evergreen 으로 흡수돼 있어야 함 (ADR-0014 흡수 규율)
- 화이트리스트: `<!-- archive-ref-allow -->` marker 직전 줄
- 위반 시 차단 메시지 출력 (enforced by a project-specific PostToolUse hook, if configured; Phase 5 strict 격상 시 BLOCK)

---

## B. 도메인 거버넌스

### 7. domain frontmatter 필수
- 모든 신규 skill / agent / hook / rule 의 `domain:` 필드 강제 (plan.md `domains:` 는 free-form — 본 규칙 적용 X)
- 누락 시 BLOCK
- 적용 도메인:
  - `lifecycle` — process layer (horizontal)
  - `qa` — 검증·결과 정합성 등 read-only 검수 (horizontal)
  - `rl-env`, `render` — vertical (현재)
  - `agents`, `perf` — future verticals

### 8. Cross-vertical 우선순위
- rules `priority:` 낮은 쪽이 강함
- 예: 가상의 `05-foundational` (priority 5) > `80-task-lifecycle` (80) > `85-git-policy` (85)
- 충돌 시 task-evaluate 가 사용자 알림 우선

---

## C. Hook 우선 원칙 (토큰 절감)

### 9. Deterministic = Hook (Agent BLOCK)
- regex / AST / glob / fnmatch 기반 검증은 **무조건 hook**
- agent 호출 시 BLOCK
- 예시:
  - "금지 import 패턴 감지" → hook (regex)
  - "설정 값 조회" → skill (rules_loader CLI)
  - "이 reward 함수가 env step 계약을 위반?" → agent (의미 판단 OK)

### 10. Skill 우선 (가능하면 Bash + Python)
- on-demand 작업은 skill (deterministic 처리, LLM 미호출 비용 0)
- agent 는 의미 판단·맥락 이해 필요한 경우만

### 11. Verdict-only 응답 강제
- agent 출력은 `APPROVE` / `SUGGEST: <축>: <한줄>` / `BLOCK: <축>: <한줄>` 만
- 자유 형식 본문 금지 → aggregator MALFORMED_VERDICT 로그 후 skip

---

## D. 비용 임계값 (자동 알림)

| 신호 | 임계값 | 조치 |
|---|---|---|
| 단일 작업 토큰 | **200k+** | 작업 분할 권고 (사용자 알림) |
| 단일 단계 agent 호출 | **10+** | paths 라우팅 검토 (false routing 의심) |
| L1 iteration | 사용자 컷 권고 (소프트) | 사용자 알림 |
| **L2-outer MAX_ITERATIONS_REACHED** (default cap 2, heavy 8 — 도달 시 cap 초과 의미) | 자동 에스컬레이션 | 사용자 |
| L3 iteration | 사용자 컷 권고 (소프트) | 사용자 알림 |
| **no-progress** (동일 fail 2회) | 즉시 사용자 | 즉시 사용자 |

**메트릭 수집** (Phase 5 운용 시 매 Stop 시 출력 — enforced by a project-specific Stop hook, if configured):

```yaml
session_metrics:
  total_tokens: int
  agent_calls: { vertical 별 }
  hook_fires: { vertical 별 }
  iterations: { L1, L2-outer, L3 }
  no_progress_count: int
  threshold_violations: { tokens_200k_plus, agent_10_plus, L2_max_5 }
```

---

## E. Agent isolation 워크트리 회수 규율

### 13. isolation: worktree 사용 시 main 회수 책임 (2026-04-28)

`Agent` tool 의 `isolation: "worktree"` 옵션 또는 agent frontmatter `isolation: worktree` 사용 시, 해당 agent 는 격리 워크트리 (`.claude/worktrees/agent-<hex>/`) 에서 작동한다. 변경이 있으면 path/branch/changed-files 가 tool result 로 반환됨 (Anthropic 의도된 워크플로).

**규율**:
- **main 에이전트는 같은 turn 내에서 회수 결정 필수** — (1) 회수 (변경 가져오기) / (2) 폐기 / (3) 명시 보존 중 하나
- 다음 user prompt 처리 전 미해결 시 누수로 간주
- 본 규율은 자연스러운 디스플린이지 Agent tool 의 기능을 제약하지 않음

**자동 강제 메커니즘**:
1. PostToolUse hook [`agent-worktree-return-handler.py`](../hooks/agent-worktree-return-handler.py) — Agent tool result 에 `.claude/worktrees/agent-*` 패턴 매칭 시 stderr 가시화 (path / branch / changes / 3옵션)
2. Stop hook [`agent-worktree-stop-guard.py`](../hooks/agent-worktree-stop-guard.py) — 잔존 격리 워크트리 발견 시 exit 2 로 세션 종료 차단
3. agent system prompt 디스플린 — `isolation: worktree` 사용하는 agent 정의에 commit-or-report 디스플린 명시 (예: an isolation:worktree agent)

**escape hatch**: `HARNESS_ALLOW_AGENT_WT_LEAK=1` 환경변수 — 사용자 명시 의도로 격리 워크트리를 보존하려는 경우에만. Stop hook 통과.

**자동 판단 정책 (2026-04-28 추가)**:

Layer 2/3 hook 가 잔존 격리 워크트리 감지 시 deterministic safety classifier ([`_lib/worktree_safety.py`](../hooks/_lib/worktree_safety.py)) 적용. 명백히 안전한 폐기 케이스는 자동 판단 추천, 애매하면 사용자 질의 fallback.

| 분류 | 조건 (모두 충족) | 권장 액션 | hook 출력 라벨 |
|---|---|---|---|
| `AUTO_DISCARD` | commits_ahead=0 + lock 없음 + 모든 변경 파일이 (size 0 ‖ 임시 패턴) + 변경 ≤ 5 | `bash scripts/worktree/clean-agents.sh --force --yes` 즉시 실행 | `[AUTO_DISCARD_SAFE]` |
| `ASK_USER` | 위 미충족 (commits_ahead>0, locked, 의미 파일, >5 파일 등) | 기존 3-옵션 질의 (회수 / 폐기 / 강제 종료) | `[ASK_USER]` |

**임시 파일 패턴** (basename 매칭, [`_lib/worktree_safety.py`](../hooks/_lib/worktree_safety.py) `TEMP_PATTERN` SSOT): `^(tmp|temp|foo|bar)\.\w+$` 또는 확장자 `.tmp`, `.swp`, `.bak`, `.log`, `.pyc`. (`test/sample/debug/synthetic` 은 진짜 prototype 파일명 가능성이 있어 제외.)

**원칙**: 보수적 — 의심스러우면 ASK_USER. memory rule `feedback_no_delete_without_confirm.md` 의 spirit (사용자 작업물 손실 방지) 와 일치 — 0-byte 잔여물·테스트 파일은 작업물 아님 → spirit 위반 없이 자동 폐기 가능.

**보수 옵션**: `HARNESS_WT_AUTO_DISCARD_DISABLE=1` 환경변수 시 자동 분류 비활성 → 모든 케이스 ASK_USER 강제 fallback. 사용자가 분류 룰 자체를 신뢰하지 않을 때 사용.

**회수 도구**:
- `bash scripts/worktree/clean-agents.sh` (dry-run 기본 / `--apply` 안전 모드 / `--force` 강제)

**누수 사례 학습** (2026-04-28): an isolation:worktree agent 가 다수 파일 변경 후 commit 없이 종료 → 격리 워크트리 보존 → 후속 세션에서 사용자 발견. 본 §E.13 + Layer 2/3 hook 가 도입된 직접 동기.

---

## F. Mode Tiering (v1.9, 2026-05-01)

작업 영향도에 따라 lifecycle 절차를 3 mode 로 분기. **모든 mode 에서 CHANGELOG entry 강제** (audit trail minimum floor).

### F.1. 3 mode 정의

| Mode | 적용 조건 | Lifecycle 차이 | CHANGELOG |
|---|---|---|---|
| 🟢 quick-fix | 1-3 file + 모든 path criticality=low | task-start minimal plan / task-evaluate single reviewer (qa-verifier) / task-verify skip 가능 (산출물 존재로 acceptance 자동 충족 시) / task-review single reviewer / task-end minimal entry (ADR/INITIATIVE 갱신 skip 가능) | ✅ 1줄 강제 |
| 🟡 standard | default (mode 부재 또는 위 두 조건 미충족) | 9 step 전부 (현재 정책) | ✅ narrative |
| 🔴 heavy | 50+ file 또는 domains 3+ (multi-vertical) | task-loop max 2→8 (default 2 도 부족 시 escape hatch) / task-evaluate paths routing 의무 / isolation:worktree agent 우선 권유 | ✅ narrative + cross-vertical 영향 표 |

### F.2. 자동 감지

`scripts/detect-task-mode.py` (`.claude/skills/task-start/scripts/`) — deterministic, AST 없음, glob 매칭. 분기 룰:

1. plan frontmatter `mode:` 명시 → 자동 감지 무시 (manual override)
2. 어떤 scope_paths 가 critical 매칭 + file_count >= 50 → heavy
3. 어떤 scope_paths 가 critical 매칭 → standard (file 수 무관, 회귀 위험 우선)
4. file_count >= 50 또는 domains_count >= 3 → heavy
5. file_count <= 3 + 모든 path 가 low 매칭 → quick-fix
6. else → standard (default)

판정 결과는 plan frontmatter `mode:` 에 기록. task-start skill 이 자동 chain.

### F.3. Mode frontmatter SSOT (cross-task interface 계약)

| Key | Value enum | Required | Default |
|---|---|---|---|
| `mode` | `"quick-fix"` / `"standard"` / `"heavy"` | optional | `"standard"` (mode 부재 시) |

값은 frontmatter 의 string literal. 본 SSOT 의존:
- `detect-task-mode.py` — 판정 결과 출력
- `aggregate-verdicts.py` — quick-fix 시 ≥2 reviewer 강제 우회 (§A.2 예외)
- 모든 task-* skill — mode 별 절차 분기
- 후속 task `harness-prompt-cache-optimization` — mode 별 prompt template

### F.4. Manual override

plan frontmatter `mode:` 명시 시 자동 감지 무시. 사유:
- 자동 감지 false positive/negative 보정
- standard 보다 더 보수적 검증 원할 때 (e.g. quick-fix 자동 결과 → 수동 standard)

### F.5. CHANGELOG 강제 (모든 mode 의 minimum floor)

audit trail 의 최소 보장 — quick-fix mode 도 1줄 entry 의무. mode 별 template:

| Mode | Template |
|---|---|
| quick-fix | `- **YYYY-MM-DD** — \`<slug>\` (quick-fix): <한 줄>. <commit hash>.` |
| standard | 현재 narrative 그대로 |
| heavy | standard + cross-vertical 영향 표 |

### F.6. Path criticality SSOT

`.claude/data/path-criticality.json` (schema 동봉) — critical / low 분류. medium = 위 두 분류 외 default. critical 과 low 둘 다 매칭 시 critical 우선.

### F.7. 정량 효과 (도입 직전 측정 baseline, harness-mode-tiering task)

- task당 평균 cost: standard baseline → quick-fix 적용 task ~70% 절감, heavy 적용 task ~20% 절감
- 전체 평균 토큰 절감 추정: ~25% (week budget 14% → 10-11%)
- 본 효과는 task #13 (`rules80-v2-finalize`, scheduled 2026-05-12) 결산 시 실측 결과로 정정

---

## G. Prompt Cache (v1.10, 2026-05-01)

reviewer / qa-verifier prompt 의 fixed prefix cache hit 으로 호출당 ~30% 절감.
mode tiering (§F) 과 직교 — 모든 mode 에서 적용 가능 (heavy mode 효과 큼 — 더 많은 reviewer 호출).

### G.1. Helper 강제

| Helper | 사용처 | 신규 task 의무 |
|---|---|---|
| `_lib/qa_verifier_prompt.py` | qa-verifier 호출 (L1 / L3) | ✅ 기존 정책 유지 |
| `_lib/reviewer_prompt.py` | plan-reviewer 호출 (L1 / L3) | ✅ harness-prompt-cache-optimization 도입 |

직접 prompt 작성 시 fixed prefix 매번 미세 다름 → cache miss. helper 사용 의무.

### G.2. fixed/variable 분리

```
prompt = fixed_prefix (cache eligible, agent+purpose 별 동일)
       + variable section (이번 task 고유, 매 호출 다름)
```

- **fixed_prefix**: agent role / 평가 축 표준 / verdict 형식 / anti-pattern / 위반 처리. SHARED_GUIDELINES (lifecycle 9-step / aggregator 4 decision / mode tiering / prompt cache / verdict 형식 / MALFORMED 처리 / 모델 격리 / domain frontmatter / hook 우선 / 비용 임계) 가 모든 reviewer 에 prepend.
- **variable**: 이번 task plan / diff / inline 검증 결과 / axes 명시.

axes 한도 (rules/80 §G 강화):
- plan-reviewer: 5
- qa-verifier: 3 (rules/80 §C.10 기존 정책)

### G.3. 정량 기대치

- fixed prefix 1024+ token 임계 충족 시 자동 cache hit (Anthropic prompt caching)
- plan-reviewer L1 fixed prefix: ~1187 tokens (4749 chars)
- qa-verifier fixed prefix: ~1164 tokens (4659 chars)
- 호출당 cached portion ~30% cost 절감 (cached 토큰은 전체 비용의 10% 가격)
- 1 task 당 reviewer 호출 평균 4-6회 → task당 ~10-15% 절감

### G.4. mode 별 분기

| Mode | reviewer 호출 수 (avg) | 본 helper 절감 효과 |
|---|---|---|
| 🟢 quick-fix | 1 (qa-verifier만) | qa_verifier_prompt 활용 — minimal |
| 🟡 standard | 4 (≥2 reviewer × L1+L3 round) | task당 ~10-15% |
| 🔴 heavy | 6-8 (모든 vertical reviewer) | task당 ~15-20% |

### G.5. cache invalidation 주의

agent 정의 (.md system prompt) 변경 시 cache 자동 invalidation. SHARED_GUIDELINES
또는 agent 별 fixed prefix 변경도 동일. 변경은 별도 task (review 강도 ↑) 에서.

---

## H. Gate Summary Card (v1.11, 2026-06-16)

사람이 진행 의사를 결정하는 **hard 게이트** 직전에, "직전 단계에서 무엇을 했는가"를 **컨텍스트 독립적으로** 요약한 카드를 제시하고 그걸 보고 승인하게 한다.

**해결 문제**: 대화 컨텍스트가 길어지면 사람이 *무엇을 승인하는지* 놓친다. 승인 시점에 위 로그를 다시 읽지 않아도 카드 하나로 yes/no 를 닫을 수 있어야 한다.

### H.1. 적용 범위 (v1)

커밋·푸시를 제외한 hard 게이트 **2곳**:

| 게이트 | 카드 | 생성 주체 |
|---|---|---|
| **G1** (🚦 시작 승인) | G1 카드 — *앞을 봄* | `task-evaluate` Decision.APPROVED 출력 |
| **task-end** (✅ 종료 승인) | 종료 카드 — *뒤를 봄* | `task-end` archive 이동 confirm 직전 |

**v1 범위 밖** (후속 seed):
- escalation 카드 — `no-progress` / `MAX_ITERATIONS_REACHED` / 비용 임계(§D) 시에도 동일 카드. seed: `gate-card-escalation`
- soft cutoff(L1/L3 SUGGEST) 카드
- PostToolUse 헤더 강제 hook (LLM 출력 포맷 강제) — seed: `gate-card-hook-enforce`

### H.2. 5블록 골격 (SSOT)

모든 Gate Summary Card 는 다음 5블록을 **순서대로** 갖는다:

1. **헤더 앵커** — 고정 문자열. 긴 로그에서 검색·스크롤로 즉시 발견.
   - G1: `## 🚦 G1 승인 요청 — "<승인 시 일어나는 일>"`
   - end: `## ✅ task-end 승인 요청 — "<승인 시 일어나는 일>"`
2. **승인 대상 1줄** — "YES 하면 일어나는 일" (헤더의 따옴표 부분과 동치). G1=acceptance freeze + 구현 시작 / end=archive 이동 + CHANGELOG append.
3. **대분류→소분류 표** — `domains`(대분류) × 변경 단위(소분류 한 줄) × 영향. **≤5행**. 상세는 plan.md/report.md 링크로 분리 (카드에 본문 복사 금지).
4. **게이트별 주인공** (가장 중요 블록):
   - G1: 🔒 **freeze 될 Acceptance 체크리스트** (`qa-checklist.md` 의 AC 목록)
   - end: ✅ **Acceptance 결과** — G1 freeze 와 **1:1 대조** (`[x]…✅` / `[ ]…⚠️ 미검증` / `❌ 실패`)
5. **명시 옵션** — 번호형 선택지.
   - G1: `[1] GO (freeze) │ [2] 보완 후 재평가 │ [3] 취소`
   - end: `[1] 종료 │ [2] 보류`

### H.3. 설계 원칙

- **컨텍스트 독립** — 카드 하나로 자기완결. 위 대화를 안 읽어도 의사결정 가능.
- **길이 상한** — 한 화면 이내. 상세는 링크. 표 ≤5행.
- **시작=종료 닫힘** — end 카드의 주인공(acceptance 결과)은 G1 카드의 주인공(freeze 된 acceptance)을 그대로 다시 띄워 대조. "시작 때 약속한 것 = 끝낼 때 확인하는 것".
- **자동 조립 우선** — 카드 골격은 `_lib/gate_summary_card.py` 가 plan frontmatter(`domains`/`scope_paths`) + `qa-checklist.md` 에서 조립. 소분류 한 줄 설명만 사람/LLM 보강.

### H.4. 강제 수준

LLM 출력 포맷이라 hook 로 100% 강제 불가. v1 은 **SKILL.md 스펙 + helper 조립**으로 soft 보장. PostToolUse 헤더 검사 강제는 후속(§H.1 seed).

---

## I. Self-Retro — 하이브리드 자가정화 (v1.12, 2026-06-16)

실수가 발생하면 **개선안(가드 초안)을 자동 포착**해 큐에 적재하고, **게이트(task-end 카드)에서 사람이 결재**해 task seed 로 전환한다.

### I.1. 불변식 (가장 중요)

> **감지·초안 = 자율 / 적용·후속 = 사람 게이트.**

큐의 어떤 제안도 **자동 적용되지 않는다**. 완전 자율 자기수정은 의도적으로 배제 — 자기심판 편향(단일 에이전트가 자기 실수를 자기가 판정), 안전모델(G1/task-end 사람 게이트) 위반, 보안 표면(self-modification) 때문. 메우는 빈틈은 "사람이 우연히 발견해야만 학습된다" 하나뿐.

### I.2. 루프

```
실수 신호(보수적) ─auto─→ 제안 큐(.claude/retro/proposals.md) 에 초안 append
                              ↓
                    task-end 종료 카드 "🔁 제안된 개선" 블록에 pending surface
                              ↓
                    사람 결재: [seed] task 로 / [dismiss] 폐기 / [defer] 보류
                              ↓
                    승인분(seeded)만 후속 task — auto-apply 0
```

### I.3. 감지 신호 (보수적 — "애매하면 안 적음")

메인 에이전트가 다음 **명시 신호** 시 큐에 1줄 append (거짓양성 회피 — 정상 동작을 실수로 오인 금지):

| trigger | 의미 |
|---|---|
| `manual-revert` | 수동 원복 (스코프 밖 drift 정정 포함) |
| `hook-block-override` | hook BLOCK 후 OVERRIDE 사용 |
| `user-correction` | 사용자 명시 교정 ("그거 아냐", "다시") |
| `no-progress` | 동일 실패 2회 escalation |

오적재 비용은 낮다 — 큐는 "제안"일 뿐 자동 적용 0, 사람이 dismiss.

### I.4. 큐 + helper

- SSOT: [`.claude/retro/proposals.md`](../retro/proposals.md) — 한 줄/제안 (`status | id | date | trigger | summary | proposal`).
- helper: [`_lib/retro_proposals.py`](../skills/_lib/retro_proposals.py) — `append`(idempotent) / `list_pending` / `set_status`. deterministic.
- 게이트 surface: `gate_summary_card.build_end_card(pending=…)` 가 pending 을 "🔁 제안된 개선" 블록으로 렌더 (pending 0 이면 생략 — 무회귀). `--proposals-file` CLI 로 주입.

### I.5. v1 범위 + 후속

- **v1**: 에이전트 주도 감지(I.3) + 큐(I.4) + task-end 카드 surface + 사람 결재.
- **후속 seed**: `retro-runtime-auto-detect` — PostToolUse/Stop hook 가 실수 신호를 스스로 포착해 append(완전 자동 감지). "무엇이 실수인가" 가 비결정론적이라 거짓양성 위험 → v1 제외. / G1 카드에도 surface(다음 task scope 로 픽업).

---

## 검증 메커니즘

본 규칙은 다음으로 강제됨:

| 검증 | 시점 | 대상 |
|---|---|---|
| `route-evaluators.py` | L1 호출 | declared domains + scope_paths |
| `aggregate-verdicts.py` | L1 / L3 종료 | verdict 형식 + no-progress |
| `task-loop` iteration log | L2 매 round | 종료 조건 (5 Decision) |
| `task-verify` G2 판정 | L2 종료 | acceptance 자동 합산 결과 |
| **rules/80 자체** (project-specific PostToolUse hook, if configured) | 매 PostToolUse (Phase 5 strict) | frontmatter `domain:` 누락, plan 누락 큰 변경 |
| `agent-worktree-return-handler.py` | Agent tool 호출 후 | 격리 워크트리 반환 가시화 (E.13) |
| `agent-worktree-stop-guard.py` | 세션 종료 시 | 잔존 격리 워크트리 시 exit 2 차단 (E.13) |
| `harness-task-intent-nudge.py` | UserPromptSubmit | 기능 요청 의도 + frozen task 부재 시 `/task-start` 넛지 (§A.6.1) |
| `harness-task-start-guard.py` | PreToolUse Write\|Edit | 제품 소스 frozen plan 없이 변경 BLOCK — 하네스 우회 차단 (§A.6.1) |

---

## 참조

- [process-diagram.md](../../docs/harness/explanation/process-diagram.md) — 다이어그램 (3 loop + 2 gate)
- [layer-architecture.md](../../docs/harness/explanation/layer-architecture.md) — horizontal × vertical 모델
- [cross-vertical-scenarios.md](../../docs/harness/explanation/cross-vertical-scenarios.md) — E2E 시나리오 + 토큰 절감 12 전략
- [pass-criteria.md](../context/lifecycle/pass-criteria.md) — G2 DoD 통과 기준 SSOT
- task-* SKILL.md (5종): start / end / evaluate / verify / loop / review

---

## 변경 이력

| 일자 | 버전 | 변경 |
|---|---|---|
| 2026-04-26 | 1.0.0 | 초안 (Phase 4d Step 4d.2). 4 섹션 (A 흐름 / B 도메인 / C Hook 우선 / D 비용) |
| 2026-04-27 | 1.1.0 | docs/ Diátaxis 재정비 + 2계층 어휘 통일 (ADR-0014). plan 경로 `docs/_active/[<initiative>/]<slug>/plan.md` 로 변경, `/task-end` 가 evergreen 흡수 + CHANGELOG append + active→archive 이동 (NN- prefix 자동) 강제. |
| 2026-04-27 | 1.2.0 | A.7 (frontmatter `domain:` 필수) 와 evergreen broken link 자동 검증 hook 도입 (project-specific PostToolUse hook, if configured). 명시 규칙 ↔ 자동 강제 gap 해소 (ADR-0014 후속). |
| 2026-04-27 | 1.3.0 | (1) L3 qa-verifier prompt 단순화 패턴 명시 (`task-review` SKILL.md "L3 qa-verifier 호출 패턴" 섹션). 명령 실행은 메인이 inline 결과 제공, qa-verifier 는 텍스트 판정만. (2) Archive 참조 invariant (A.12) 자동 강제 (project-specific PostToolUse hook, if configured). evergreen → archive/active link 차단 + `<!-- archive-ref-allow -->` 화이트리스트. |
| 2026-04-27 | 1.4.0 | qa-verifier 채널 강화 — 5단계 cross-cutting fix (L1 + G1 + L2-outer + G2 + L3). (1) `_lib/qa_verifier_prompt.py` helper 도입 — 모든 task-* skill 의 호출 통일. (2) `aggregate-verdicts.py` 3-tier fallback (last-line / multiline / keyword heuristic) — MALFORMED 본문에서 verdict 추출. (3) `@qa-verifier` `tools: [Read]` 강제 (Bash/Grep/Glob 제거) — 옵션 B graceful degradation. (4) system prompt 5 ABSOLUTE OUTPUT RULES 명시. |
| 2026-04-27 | 1.5.0 | A.1 단방향 전진 명세 강화 — master 9-step 순서 (`/task-verify → /task-review → /task-end`) 명시. `/task-end` 는 L3 APPROVED 후에만 호출 (read-only/docs-only 도 `/task-review` skip 금지). archive 이동 후 L3 BLOCK 시 역방향 mv = 위반. `task-end/SKILL.md` 의 step 8 안내에서 "L3 권유 (commit 전)" 라인 제거 + "선결 조건" 섹션 신설. 발견 경로 — visual-regression #01 task 에서 task-review 가 task-end 뒤로 밀린 사례. |
| 2026-04-28 | 1.6.0 | A.6.1 (기능 요청 선제 제안) 추가 — 메인 에이전트가 사용자 발화에서 (a) 신설 / (b) 다파일 리팩터·마이그 / (c) 도메인·API·라우팅 변경 의도 감지 시 구현 시작 전 "`/task-start` 부터 갈까요?" 선제 질의. 의도 중심 + 예시 보조 + fallback=질의 (false-positive 안전 편향). 키워드 enumerate 회피 — LLM 의미 매칭 편향 방지. |
| 2026-04-28 | 1.7.0 | §E (Agent isolation 워크트리 회수 규율) 신설 — E.13. 누수 사례 (isolation:worktree agent 가 다수 파일 변경 후 미커밋 종료) 학습. PostToolUse hook (`agent-worktree-return-handler.py`) + Stop hook (`agent-worktree-stop-guard.py`) 자동 강제. escape hatch `HARNESS_ALLOW_AGENT_WT_LEAK=1`. agent system prompt 디스플린 (isolation:worktree agent) 1차 방어선. |
| 2026-04-28 | 1.8.0 | §E.13 자동 판단 정책 추가 — `_lib/worktree_safety.py` deterministic safety classifier 도입. 명백 안전 케이스 (commits_ahead=0 + lock 없음 + 빈/임시 파일만 + ≤5건) `[AUTO_DISCARD_SAFE]` 라벨로 자동 폐기 추천, 애매 케이스 `[ASK_USER]` 로 기존 3-옵션 질의 fallback. 보수 옵션 `HARNESS_WT_AUTO_DISCARD_DISABLE=1` 환경변수. memory rule `feedback_no_delete_without_confirm.md` 의 spirit 보존 (사용자 작업물 손실 방지) — 0-byte 잔여물은 작업물 아님 → 자동 폐기 허용. L3 SUGGEST-1 흡수 — TEMP_PATTERN narrowing (`test/sample/debug/synthetic` 제외, `tmp/temp/foo/bar` + 확장자만) 으로 진짜 prototype 보호 (`test.py` 800 bytes 같은 케이스 ASK_USER fallback). |
| 2026-06-16 | 1.12.0 | §I (Self-Retro — 하이브리드 자가정화) 신설 — 실수 신호(보수적: manual-revert/hook-block-override/user-correction/no-progress) 감지 시 개선안 초안을 `.claude/retro/proposals.md` 큐에 자동 append, task-end 종료 카드 "🔁 제안된 개선" 블록에 surface, **사람 결재(seed/dismiss/defer)** 후에만 task seed 전환. 불변식 "감지·초안=자율 / 적용=사람 게이트" — 완전 자율 자기수정 배제(자기심판 편향·안전모델·보안). helper `_lib/retro_proposals.py`(append idempotent/list_pending/set_status) + `gate_summary_card` 종료 카드 확장(pending 0 무회귀). v1=에이전트 주도 감지, 후속 seed `retro-runtime-auto-detect`(완전 자동 감지). initiative `harness-stabilization`. |
| 2026-06-16 | 1.11.0 | §H (Gate Summary Card) 신설 — 사람 hard 게이트(G1·task-end) 직전에 "직전 단계 작업 요약 카드" 제시 후 승인. 5블록 골격 SSOT (헤더 앵커 / 승인 대상 1줄 / 대분류→소분류 표 ≤5행 / 게이트별 주인공(G1=freeze될 acceptance, end=acceptance 결과 1:1 대조) / 명시 옵션). `_lib/gate_summary_card.py` 가 plan frontmatter + qa-checklist 에서 자동 조립. v1 범위=G1·task-end 2곳, escalation·hook 강제는 후속 seed. 동기 — 긴 컨텍스트에서 "무엇을 승인하는지" 상실 방지 (initiative `harness-stabilization`). |
