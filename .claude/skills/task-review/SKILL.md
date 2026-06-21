---
name: task-review
description: |
  G2 통과 후 L3 코드 리뷰. ≥2 reviewer 병렬 합의로 회귀·DS·a11y·UX writing 검증.
  task-evaluate 의 verdict aggregator 패턴 재사용 (APPROVED/BLOCKED/SUGGEST_CUTOFF/NO_PROGRESS).
argument-hint: "[plan-path] (optional, 기본=최신 plan + 매칭 report + git diff)"
allowed-tools: Bash, Read, Glob, Grep, Agent
domain: lifecycle
---

# Task Review (L3 — 👀 리뷰 합의, Loop 3: Multi-reviewer Review)

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의 **L3 코드 리뷰 loop** 진입점. G2 통과 후 자동 호출 또는 사용자 명시 호출. **task-evaluate 와 동일한 paths 라우팅 + verdict aggregator** 패턴 재사용 — 코드 중복 최소화.

---

## 입력

```
/task-review                                              # 최신 plan + report + git diff
/task-review docs/_active/<slug>/plan.md     # 명시 경로
```

---

## Reviewer prompt — helper 강제 (rules/80 §G, harness-prompt-cache-optimization)

reviewer (plan-reviewer) 호출 prompt 는 `_lib/reviewer_prompt.py` 의
`build_reviewer_prompt` 함수 사용 의무. fixed prefix + variable 분리 — 매 호출
동일 fixed prefix 가 Anthropic prompt cache hit (1024+ token 임계 충족, 호출당 ~30% 절감).

```python
# CLI
python3 .claude/skills/_lib/reviewer_prompt.py \
  --agent plan-reviewer --purpose L3 \
  --variable '{"plan": "...", "diff_stat": "..."}' \
  --axes "scope" --axes "회귀" --axes "freshness"
```

**금지** (anti-pattern):
- ❌ 자유 prompt 직접 작성 — fixed prefix 매번 미세 다름 → cache miss
- ❌ 가이드/원칙을 매 호출 prompt 에 inline 으로 작성 — helper 의 fixed prefix 활용

qa-verifier 는 별도 helper (`_lib/qa_verifier_prompt.py`) 사용 — 기존 정책 유지.

## Mode 분기 (rules/80 §F mode tiering)

| Mode | reviewers |
|---|---|
| 🟢 quick-fix | `[@qa-verifier]` (single — §A.2 quick-fix 예외) |
| 🟡 standard | review_profile 기준 (code/docs-only/harness-tooling) — 현재 정책 |
| 🔴 heavy | review_profile=code + 모든 매칭 vertical reviewer (존재 시) |

mode 부재 = standard. quick-fix 시 plan-reviewer skip (qa-verifier 단독).

## 동작 (4 step) — task-evaluate 와 대칭 구조

### Step 1: 입력 수집

- plan.md (인자 또는 최신)
- 매칭 report.md (있으면)
- 매칭 qa-checklist.md (G1 freeze 비교)
- `git diff` (변경 파일 + 추가/제거 라인)
- plan frontmatter `mode:` — quick-fix / standard / heavy 분류

### Step 2: paths 라우팅 (route-evaluators 재사용)

**task-evaluate 와 다른 점**: agent 명명 규칙이 `*-auditor` (L1 평가) 가 아닌 `*-reviewer` (L3 리뷰).

```python
def route_reviewers(plan, git_diff):
    reviewers = ["@qa-verifier"]   # lifecycle 무조건 (정합성 검증)

    declared = plan.frontmatter.get("domains", [])
    diff_paths = git_diff.changed_files

    # 명시 도메인 → vertical reviewer (해당 agent 가 실재할 때만 추가)
    for d in declared:
        agent = f"@{d.split('.')[0]}-reviewer"  # 예: @rl-env-reviewer (존재 시)
        if agent_exists(agent) and agent not in reviewers:
            reviewers.append(agent)

    # diff paths 매칭 보완 (실제 변경 영역 기반)
    for path in diff_paths:
        for rule in load_rules():
            if path_match(rule.paths, path):
                agent = f"@{rule.domain}-reviewer"
                if agent_exists(agent) and agent not in reviewers:
                    reviewers.append(agent)

    return dedupe(reviewers)
```

**L1 vs L3 라우팅 차이**:
| 측면 | L1 (task-evaluate) | L3 (task-review) |
|---|---|---|
| 입력 | plan.md frontmatter | plan + git diff (실제 변경) |
| 평가 대상 | 계획 자체 (SMART, scope) | 결과 정합성 (plan ↔ 코드) |
| Agent prefix | `*-auditor` | `*-reviewer` |
| 기본 lifecycle agent | plan-reviewer + qa-verifier | qa-verifier (만 — plan-reviewer 는 계획 평가 전용) |

### Step 2.5: review_profile 분기 (route_reviewers 호출 전)

본 단계는 [`scripts/detect-review-profile.py`](scripts/detect-review-profile.py) 가 결정 (deterministic, AST 없음 — 단순 파일 확장자 + 경로 매칭).

**3 profile**:

| profile | reviewers (≥2 강제, rules/80 A.2) | 적용 조건 | 토큰 절감 |
|---|---|---|---|
| `code` (default) | `@plan-reviewer` (sonnet) + `@qa-verifier` (haiku) | 코드/스타일 ext ≥1 변경 OR fallback | — |
| `docs-only` | `@plan-reviewer` (sonnet, 작은 scope) + `@qa-verifier` (haiku) | docs 분류만 변경 (코드/스타일/harness 0) — 예: ADR / README / pure markdown 변경 | — |
| `harness-tooling` | `@plan-reviewer` (sonnet) + `@qa-verifier` (haiku) | task_type=harness + .py/.sh/.json ≥1 + 코드/스타일 0 | — |

> ℹ️ 모든 profile 의 reviewer 는 `@plan-reviewer` + `@qa-verifier` 두 generic agent (`detect-review-profile.py` 의 `PROFILE_REVIEWERS` SSOT). Python 프로젝트에선 `.py` 변경이 `harness-tooling` (task_type=harness 시) 또는 `code` (default) 로 분기한다. 도메인 전용 reviewer 를 추가하면 `PROFILE_REVIEWERS` 에 매핑해 확장한다.

**plan-reviewer 의 L3 역할**: docs-only profile 에서 plan-reviewer 는 L1 의 "plan SMART 평가" 가 아닌 **"diff vs plan freeze 정합 검증"** 역할. 검증 축:
1. scope_paths 외 변경 검출
2. acceptance freeze 후 추가 항목 검출
3. 의도 외 trim / 추가 검출

agent 정의 (`agents/plan-reviewer.md`) 변경 없음 — task-review 호출 시 prompt 만 L3 의 새 역할로 작성.

**호출 예** (Bash):
```bash
profile_data=$(python3 .claude/skills/task-review/scripts/detect-review-profile.py docs/_active/<slug>/plan.md)
profile=$(echo "$profile_data" | jq -r '.profile')
mapfile -t reviewers < <(echo "$profile_data" | jq -r '.reviewers[]')
```

**Manual override**: plan frontmatter `review_profile:` 명시 시 자동 감지 무시 (rule 1 priority).

**Backward compat**: review_profile 부재 plan → default `code` profile 적용 (현재 정책 유지).

### Step 3: 병렬 스폰 (단일 메시지)

```
[1 message — 병렬]
- Agent(@qa-verifier "{plan} {report} {git-diff-base}")
- Agent(@plan-reviewer "{git-diff}")          # code/harness-tooling profile 의 sonnet 리뷰어
# (vertical reviewer 가 존재하고 라우팅에 매칭되면 같은 메시지에 추가)
```

**rules/80 강제** (Phase 4d):
- 순차 호출 BLOCK
- 단일 메시지 multiple Agent tool 만 허용
- domain frontmatter 누락 agent 호출 BLOCK

### Step 4: Verdict Aggregator (aggregate-verdicts 재사용)

```python
def aggregate(verdicts: list[Verdict]) -> Decision:
    # task-evaluate 와 동일 — code path 재사용
    return Decision.APPROVED | BLOCKED | SUGGEST_CUTOFF | NO_PROGRESS_ESCALATE
```

---

## 사용자 응답 형식

### Decision.APPROVED

```
✅ L3 통과 — 모든 reviewer APPROVE

@qa-verifier: APPROVE (plan ↔ 결과 정합)
@plan-reviewer: APPROVE (회귀 0, scope 일치)

다음 단계: /task-end (단계 7 — 작업 리포트 + archive)
```

### Decision.BLOCKED

```
❌ L3 BLOCK — 회귀 개선 필요

@plan-reviewer:
  - BLOCK: scope: PR 이 plan 의 scope_paths 외 파일 포함
    src/critter_gym/render/viewer.py (plan 에 명시 X)

@qa-verifier:
  - BLOCK: freshness: G1 후 추가된 acceptance 발견
    qa-checklist 에 'action space 차원 변경' 신규 (rules/80 위반)

다른 reviewer: APPROVE
→ scope 재확인 또는 새 task slug 생성
```

### Decision.SUGGEST_CUTOFF

```
⚠️ L3 SUGGEST — 보완 권장 (사용자 컷오프 가능)

@plan-reviewer:
  - SUGGEST: docstring: step() 반환값 설명 보강 권장 (critter_env.py:42)

[1] 보완 후 재리뷰
[2] 컷오프 (현재 결과로 task-end)
```

### Decision.NO_PROGRESS_ESCALATE

```
🚨 NO-PROGRESS — 동일 BLOCK 2회

이전 round 와 동일한 reviewer 가 동일한 BLOCK 반환.
사용자 직접 개입 권장.
```

---

## Selective Re-evaluation (재진입 시)

L3 재진입 (회귀 개선 후) 시:
- BLOCK reviewer 만 재호출
- 변경 파일 (`git diff HEAD~1`) 이 다른 vertical 영향 시 그쪽도 재호출
- 무영향 reviewer 의 verdict 는 cache 사용

```python
def re_review(plan, prev_verdicts, new_diff):
    targets = [v.agent for v in prev_verdicts if v.kind == "BLOCK"]
    for path in new_diff.changed_files:
        for agent in route_for_path(path):
            if agent not in targets:
                targets.append(agent)
    return spawn_parallel(targets) + cached(prev_verdicts, exclude=targets)
```

---

## iteration log

`.claude/.session-log/task-review-{plan-slug}-iterations.json`:

```json
[
  {
    "round": 1,
    "verdicts": [
      {"agent": "@qa-verifier", "kind": "APPROVE"},
      {"agent": "@plan-reviewer", "kind": "BLOCK", "axis": "scope", "message": "..."}
    ],
    "decision": "BLOCKED",
    "ts": "..."
  },
  {
    "round": 2,
    "verdicts": [{"agent": "@plan-reviewer", "kind": "APPROVE"}],  // selective
    "decision": "APPROVED",
    "ts": "..."
  }
]
```

---

## 비용 통제 (cross-vertical-scenarios.md)

| 항목 | 추정 |
|---|---|
| 기본 작업 | qa-verifier + plan-reviewer = 2 agent × ~3.5k = ~7k |
| vertical reviewer 추가 시 | agent 1개당 ~3.5k 가산 |
| Selective re-eval | 첫 round 의 1/N |
| Haiku 격리 (qa-verifier) | 모델 비용 ~75% 절감 vs 모두 Sonnet |

---

## L3 qa-verifier 호출 패턴 (MALFORMED 방지)

⚠ 본 섹션 원칙 (qa-verifier 채널 강화):
- `@qa-verifier` 의 `tools: [Read]` 강제 (Bash/Grep/Glob 제거)
- `_lib/qa_verifier_prompt.py` helper 표준화
- `aggregate-verdicts.py` 3-tier fallback 으로 강건성 확보

### 표준 호출 (helper 사용 — 권장)

```bash
# 메인이 명령 사전 실행
test_results=$(python3 .claude/hooks/_lib/test_*.py 2>&1 | tail -5)
elapsed=$(echo '...' | python3 .claude/hooks/X.py 2>&1 | grep ms)

# helper 로 prompt 빌드
prompt=$(python3 .claude/skills/_lib/qa_verifier_prompt.py \
  --purpose L3 \
  --plan docs/_active/<slug>/plan.md \
  --inline "{\"test_results\": \"$test_results\", \"elapsed\": \"$elapsed\"}" \
  --axes "acceptance 정합" --axes "회귀" --axes "성능")

Agent(@qa-verifier, "$prompt")
```

helper 가 4 강제 요소 자동 포함. agent 의 `tools: [Read]` 가 Bash 호출 차단.

### 사례

`harness-self-verification` task (2026-04-27) L3 단계에서 `@qa-verifier` 가 **MALFORMED × 2 회 연속** 발생. 분석:

| 호출 | 결과 | tool_uses | duration | 원인 |
|---|---|---|---|---|
| L1 round 1 (단순 plan 텍스트 검증) | BLOCK 정상 | 4 | 20s | OK |
| L1 round 2 (단순 plan 텍스트 검증) | APPROVE 정상 | 2 | 16s | OK |
| **L3 round 1** (명령 실행 + 결과 파싱 + verdict) | **MALFORMED** | 7 | 12s | turn 한도 도달 전 verdict 미작성 |
| **L3 round 2** (동일 prompt 자동 재호출) | **MALFORMED** | 11 | 16s | maxTurns 5 hit |

**근본 원인**: qa-verifier 는 Haiku + maxTurns 5 짧은 검증 전용. prompt 가 *bash 명령 실행 + 결과 파싱 + verdict 작성* 동시 요구 → turn 1-2 가 명령 실행에 소비, turn 3-5 가 결과 파싱·thinking 에 소비 → verdict 작성 시점에 maxTurns 도달.

### 원칙

> **qa-verifier 는 *텍스트 판정만* 수행. 명령 실행은 메인이 사전 수행 + 결과를 prompt 에 inline 으로 제공.**

`task-evaluate` SKILL.md 의 `qa-verifier 호출 시 prompt 단순화 원칙` (검증 축 ≤ 3, 한 줄 명확 통과 조건) 의 **확장 — 명령 실행 위임** 추가.

### Bad 예 (MALFORMED 위험)

```
Agent(@qa-verifier, """
3축 검증:
1. acceptance 정합 — plan.md 의 [...] 검증
2. 회귀 — `python3 .claude/hooks/_lib/test.py` 실행 후 OK 확인
3. 성능 — `echo {...} | python3 .claude/hooks/X.py` 실행 후 elapsed 추출
""")
```

→ qa-verifier 가 Bash tool 호출 → Read tool 호출 → thinking → maxTurns hit → verdict 못 냄.

### Good 예 (명령 결과 inline)

```python
# 메인이 사전 실행
test_a = bash("python3 .claude/hooks/_lib/test.py 2>&1 | tail -3")
elapsed = bash("echo '...' | python3 .claude/hooks/X.py 2>&1 | grep ms")

Agent(@qa-verifier, f"""
⚠️ 본 호출은 단순 텍스트 판정 — 명령 실행 없음.

3축 검증 (모두 결과 inline):
1. acceptance 정합 — plan.md 의 [...] vs 구현 비교 (텍스트 판정)
2. 회귀 — test 결과:
   ```
   {test_a}
   ```
   → OK 인지 판정
3. 성능 — elapsed: '{elapsed}' → < 100ms 인지 판정

verdict 형식 강제 (자유 본문 금지):
- 마지막 줄 반드시: APPROVE / SUGGEST: ... / BLOCK: ...
""")
```

→ qa-verifier 는 turn 1 에 prompt 읽기 + turn 2 에 verdict 작성 완료. tool 호출 없음.

### 적용 범위

본 패턴은 **L3 (`task-review`) 와 L1 (`task-evaluate`) 모두 적용**. L1 의 plan 텍스트 검증은 보통 명령 실행 안 시키므로 자연 준수되나, L3 처럼 unit test / hook elapsed 등 검증 시점이 늦은 단계에서 메인이 사전 실행 의무 있음.

---

## 다이어그램 매핑

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의:
- **L3 코드 리뷰 loop** (≥2 reviewer 병렬 합의)
- **단계 7 → 8** (G2 통과 → L3 → task-end)

task-evaluate (L1) 와 **대칭 구조** — 같은 route-evaluators + aggregate-verdicts 재사용.
