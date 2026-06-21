---
name: task-evaluate
description: |
  계획서를 ≥2 agent 병렬 호출로 평가하고 verdict 를 종합한다 (L1).
  /task-start 직후 자동 호출 또는 사용자 명시 호출.
  paths 라우팅으로 plan 의 영향 vertical 만 자동 선택, 무관계 agent 호출 회피.
argument-hint: "[plan-path] (optional, 기본=docs/_active/**/plan.md 최신)"
allowed-tools: Bash, Read, Glob, Grep, Agent
domain: lifecycle
---

# Task Evaluate (L1 — 📋 계획 평가, Loop 1: Plan Evaluation 진입점)

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의 **L1 계획 정련** 진입점. plan.md 를 분석해 영향 받는 vertical 의 agent 들을 **paths 라우팅** 으로 자동 선택하고 **단일 메시지 병렬** 호출, **verdict aggregator** 로 종합.

---

## 입력

```
/task-evaluate                                              # 최신 plan 자동 탐지
/task-evaluate docs/_active/<slug>/plan.md     # 명시 경로
```

---

## Reviewer prompt — helper 강제 (rules/80 §G, harness-prompt-cache-optimization)

reviewer (plan-reviewer) 호출 prompt 는
`_lib/reviewer_prompt.py` 의 `build_reviewer_prompt` 함수 사용 의무.

```python
# CLI
python3 .claude/skills/_lib/reviewer_prompt.py \
  --agent plan-reviewer --purpose L1 \
  --variable '{"plan": "...", "context": "..."}' \
  --axes "scope" --axes "검증 방법" --axes "리스크"
```

**fixed prefix + variable 분리** — 매 호출 동일한 fixed prefix (가이드/원칙/형식 제약)
가 Anthropic prompt cache hit 대상 (1024+ token 임계 충족). 호출당 ~30% 절감 추정.

**금지** (anti-pattern):
- ❌ 자유 prompt 직접 작성 — fixed prefix 매번 미세 다름 → cache miss
- ❌ 가이드/원칙을 매 호출 prompt 에 inline 으로 작성 — helper 의 fixed prefix 활용

qa-verifier 는 별도 helper (`_lib/qa_verifier_prompt.py`) 사용 — 기존 정책 유지.

## Mode 분기 (rules/80 §F mode tiering)

plan frontmatter `mode:` 값에 따라 절차 분기. `route-evaluators.py` 가 자동 처리:

| Mode | reviewers | 비고 |
|---|---|---|
| 🟢 quick-fix | `[@qa-verifier]` (single) | rules/80 §A.2 예외. ≥2 reviewer 강제 우회. plan-reviewer skip. |
| 🟡 standard | `[@plan-reviewer, @qa-verifier]` (현재 default) | 현재 정책 그대로 |
| 🔴 heavy | standard + paths routing 의무 (매칭 vertical auditor 가 존재하면 추가) | route-evaluators.py 가 strict 매칭 |

mode 부재 = standard default (backward compat).

## 동작 (4 step)

### Step 1: plan.md 식별

- 인자 있으면 그 경로
- 없으면 `find docs/ -name "*-plan.md" -newer ... | sort | tail -1` 로 최신 plan 추정
- plan 의 frontmatter 에서 `domains:`, `scope_paths:`, `acceptance:`, **`mode:`** 추출

### Step 2: paths 라우팅 알고리즘

`scripts/route-evaluators.py` 호출:

```python
def route_evaluators(plan):
    agents = ["@plan-reviewer", "@qa-verifier"]   # lifecycle 무조건 2개

    declared = plan.frontmatter.get("domains", [])
    scope_paths = plan.frontmatter.get("scope_paths", [])

    # 명시 도메인 → vertical auditor (해당 agent 가 실재할 때만 추가)
    for d in declared:
        agent = f"@{d.split('.')[0]}-auditor"     # 예: @rl-env-auditor (존재 시)
        if agent_exists(agent) and agent not in agents:
            agents.append(agent)

    # paths 매칭 보완 (rules paths 와 매칭)
    for path in scope_paths:
        for rule in load_rules():
            if path_match(rule.frontmatter.paths, path):
                agent = f"@{rule.frontmatter.domain}-auditor"
                if agent_exists(agent) and agent not in agents:
                    agents.append(agent)

    return dedupe(agents)
```

**의도**:
- 기본 작업 → lifecycle 2 agent (plan-reviewer + qa-verifier)
- vertical auditor agent 가 추가로 존재하면 매칭 시에만 합류
- 무관계 vertical 의 agent 는 **호출 안 함** (lazy invocation, 토큰 절감)

> 현재 이 프로젝트에 존재하는 evaluator agent 는 `@plan-reviewer` + `@qa-verifier` 둘뿐이다. vertical auditor 가 신설되면 위 라우팅이 자동으로 포함한다.

### Step 3: 병렬 스폰 (단일 메시지)

라우팅된 N agent 를 **단일 메시지에 multiple Agent tool** 로 호출.

```
[1 message — 병렬]
- Agent(@plan-reviewer "{plan-path}")
- Agent(@qa-verifier "{plan-path}")
# (vertical auditor 가 존재하고 라우팅에 매칭되면 같은 메시지에 추가)
```

**중요** (rules/80 강제, Phase 4d):
- 순차 호출 BLOCK
- 단일 메시지 multiple Agent tool 만 허용

### Step 4: Verdict Aggregator

`scripts/aggregate-verdicts.py` 호출:

```python
def aggregate(verdicts: list[Verdict]) -> Decision:
    # 1) 모두 APPROVE → 통과
    if all(v.kind == "APPROVE" for v in verdicts):
        return Decision.APPROVED        # → G1 진입 권유

    # 2) BLOCK 1+ 있으면
    blocks = [v for v in verdicts if v.kind == "BLOCK"]
    if blocks:
        # 동일 BLOCK 2회 연속 → no-progress
        if is_repeat_block(blocks, prev_round_log):
            return Decision.NO_PROGRESS_ESCALATE
        return Decision.BLOCKED(blocks) # plan 보완 → L1 재진입

    # 3) SUGGEST 만 → 사용자 컷오프 가능
    suggests = [v for v in verdicts if v.kind == "SUGGEST"]
    return Decision.SUGGEST_CUTOFF(suggests)
```

**verdict 파싱**:
- 각 줄: `<KIND>: <축>: <한줄>` 또는 단독 `APPROVE`
- KIND ∈ `{APPROVE, SUGGEST, BLOCK}`
- 형식 위반 시 → `MALFORMED_VERDICT` 로그, 해당 verdict skip

---

## Selective Re-evaluation (재진입 시)

L1 재진입 (plan 보완 후) 시 **변경된 부분만 재평가** — cross-vertical-scenarios.md 토큰 절감 #6.

```python
def re_evaluate(plan, prev_verdicts):
    # 이전에 BLOCK 한 agent 만 재호출
    targets = [v.agent for v in prev_verdicts if v.kind == "BLOCK"]

    # plan 변경 라인이 다른 vertical 영향 있으면 그쪽도 재호출
    diff_paths = git_diff_paths(plan)
    for path in diff_paths:
        for agent in route_for_path(path):
            if agent not in targets:
                targets.append(agent)

    # 무영향 agent 의 verdict 는 cache 사용
    return spawn_parallel(targets) + cached(prev_verdicts, exclude=targets)
```

---

## iteration log

매 round 의 verdict 를 저장 → no-progress 감지에 사용.

```
.claude/.session-log/task-evaluate-{plan-slug}-iterations.json
[
  {"round": 1, "verdicts": [...], "decision": "BLOCKED", "ts": "..."},
  {"round": 2, "verdicts": [...], "decision": "BLOCKED", "ts": "..."},  # 동일 BLOCK → no-progress
]
```

---

## 사용자 응답 형식

aggregator 결과를 사용자에게 사람-읽는 형식으로:

### Decision.APPROVED → G1 Gate Summary Card 제시 (rules/80 §H)

L1 통과 시 G1 confirm 을 **Gate Summary Card** 로 제시한다. 자유 텍스트 "G1 통과 권유" 금지 — 긴 컨텍스트에서 무엇을 승인하는지 상실 방지 (rules/80 §H).

1. qa-checklist.md 가 없으면 먼저 생성 (G1 freeze 대상 acceptance).
2. helper 로 G1 카드 조립 — 소분류(`--row`)는 plan 의 변경 단위에서 메인이 한 줄씩 보강:
   ```bash
   python3 .claude/skills/_lib/gate_summary_card.py g1 \
     --plan docs/_active/<slug>/plan.md \
     --qa   docs/_active/<slug>/qa-checklist.md \
     --yes  "acceptance freeze + 구현 시작" \
     --row '{"domain":"<도메인>","sub":"<소분류 한 줄>","impact":"<N file>"}'
   ```
3. stdout 의 카드(5블록: 헤더 앵커 / 승인 대상 1줄 / 대분류→소분류 표 / 🔒 freeze 될 acceptance / 명시 옵션)를 그대로 사용자에게 출력.
4. 사용자 `[1] GO` → acceptance freeze (`acceptance_freeze: true`) + 첫 Step 구현 시작. `[2]` → 보완 후 재평가. `[3]` → 취소.

> L1 평가 결과(evaluator verdict 표)는 카드 **위에** 간단히 덧붙인다 (2/2 APPROVE 등). 카드 자체는 G1 의사결정 surface 로 자기완결.

### Decision.BLOCKED
```
❌ L1 BLOCK — plan 보완 필요

@plan-reviewer:
  - BLOCK: scope: scope_paths 에 tests/test_env.py 누락
  - BLOCK: risk: observation space 변경 시 기존 체크포인트 호환성 명시 X

다른 evaluator 는 통과/유보:
@qa-verifier: APPROVE
```

### Decision.SUGGEST_CUTOFF
```
⚠️ L1 SUGGEST — 보완 권장 (사용자 컷오프 가능)

@plan-reviewer:
  - SUGGEST: verification: 검증 방법에 build 추가 권장

[1] 보완 후 재평가 (/task-evaluate 재호출)
[2] 컷오프 (현재 plan 으로 G1 진입)
```

### Decision.NO_PROGRESS_ESCALATE
```
🚨 NO-PROGRESS — 동일 BLOCK 2회 연속

이전과 동일한 보완 사항이 반복되고 있습니다:
- @plan-reviewer BLOCK: risk: 체크포인트 호환성 미명시 (round 1, 2 동일)

사용자 직접 개입 권장 — agent verdict 가 plan 의 의도와 어긋날 가능성.
```

---

## 호출 비용 (cross-vertical-scenarios.md 토큰 모델)

- 기본 작업: plan-reviewer + qa-verifier = 2 agent × 평균 3.5k tokens = ~7k
- vertical auditor 추가 시: agent 1개당 ~3.5k 가산
- Selective re-evaluation: 첫 round 비용의 1/N (BLOCK agent 만)

---

## Agent 별 prompt 가이드 (MALFORMED 방지)

Agent 별로 검증 capacity 가 다름. prompt 작성 시 다음 가이드 준수:

| Agent | 모델 | maxTurns | 권장 검증 축 | 복잡 검증 처리 |
|---|---|---|---|---|
| `@qa-verifier` | Haiku | 5 | **≤ 3** | acceptance 정합 / iteration cap / cost 통제 만. cross-task linkage 같은 복잡 검증은 plan-reviewer 위임 |
| `@plan-reviewer` | Sonnet | (default) | 5 | 5축 표준 (목표·범위·step·검증·리스크). cross-task linkage 같은 복잡 검증 추가 가능 |

**qa-verifier 호출 시 prompt 단순화 원칙**:
- 검증 축 ≤ 3
- 각 축은 한 줄 명확한 통과 조건 (모호 X)
- cross-vertical 또는 다른 task 의 산출물 비교 같은 복잡 작업은 plan-reviewer 로 이관
- **명령 실행은 메인이 사전 수행, qa-verifier 는 텍스트 판정만** — `tools: [Read]` 로 강제 (Bash/Grep/Glob 제거, qa-verifier-channel-strengthen 2026-04-27)

**Helper 사용 (필수)**:
```bash
# 메인이 사전 실행 후 inline 으로 prompt 빌드
prompt=$(python3 .claude/skills/_lib/qa_verifier_prompt.py \
  --purpose L1 \
  --plan docs/_active/<slug>/plan.md \
  --inline "{\"context\": \"...\"}" \
  --axes "acceptance 정합" --axes "회귀")
Agent(@qa-verifier, "$prompt")
```

helper 가 4 강제 요소 자동 포함 (EXTERNAL READ FORBIDDEN 명시 + INLINE 마커 + axes ≤ 3 + verdict 형식).

**위반 시**: qa-verifier 가 verdict 미생성 (MALFORMED). 강건성:
1. aggregator 의 3-tier fallback (Tier 3 휴리스틱) 으로 본문에서 verdict 추출
2. Tier 3 도 0건이면 자동 재호출 (1회)
3. 그래도 fail 시 사용자 알림

---

## MALFORMED_VERDICT 자동 재호출 절차

agent verdict 가 형식 위반 (`APPROVE` / `SUGGEST: ...` / `BLOCK: ...` 형식 없이 빈 본문 또는 자유 문장) 시 aggregator 가 감지:

```python
# aggregate-verdicts.py 의 parse_verdicts() 가 매칭 0건이면 MALFORMED 표시
malformed_agents = [agent for agent in spawned if verdicts_per_agent[agent] == 0]
```

**처리**:
1. **1회 자동 재호출** — 동일 prompt + 강조 prefix: *"[CRITICAL] 이전 호출에서 verdict 미생성. 출력의 마지막 라인은 반드시 APPROVE / SUGGEST: / BLOCK: 형식 강제. 검증 thinking 길어져도 verdict 우선 출력."*
2. **재호출 후에도 MALFORMED** → 사용자 알림: *"⚠️ {agent} MALFORMED 2회 연속 — agent 정의 또는 prompt 결함 의심. 메타 fix 후 재시도 권장."*
3. 재호출 비용은 round 당 1회로 제한 (no-progress 와 별개 카운트)

---

## 다이어그램 매핑

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의 **L1 계획 정련 loop** 진입점.
- 통과 시 → **G1 DoR** 게이트
- 재진입 시 → 사용자 plan 보완 → 재호출
- no-progress → 사용자 에스컬레이션
