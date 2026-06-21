# Cross-Vertical Scenarios + 토큰 절감 전략

> 작성일: 2026-04-25 | 버전: v1
> 목적: E2E 다중 vertical 작업 시 하네스 동작 walkthrough + 토큰 비용 통제 전략
> 관련: [process-diagram.md](./process-diagram.md), [layer-architecture.md](./layer-architecture.md), [master-plan.md §Phase 4](./master-plan.md)

---

## 시나리오: "절차생성 맵에 새 wrapper + 렌더 오버레이 추가"

환경 로직 · 렌더 · 벡터화 성능이 모두 얽힌 E2E 작업. 4 vertical 동시 활성화: 🔵 lifecycle · 🟢 rl-env · 🟡 render · 🟣 perf.

### 요구사항

- **env**: 새 observation wrapper (`FrameStack` 변형) 추가, space 일관성 유지
- **로직**: (A) 시드 전파 → (B) step 5-tuple 보존 → (C) 벡터화 경로 유지 3단계
- **render**: 디버그 오버레이 신규 (결정적 `rgb_array`)

### 영향 경로

```
crittergym/wrappers/**                     ← 🟢🟣
crittergym/envs/procgen/**                 ← 🟢
crittergym/render/**                       ← 🟡
crittergym/tests/contract/**               ← 🟢
benchmarks/**                              ← 🟣
```

---

## Step-by-step 동작

### 1️⃣ `/task-start "framestack wrapper + 디버그 오버레이 추가"`

```yaml
# plan.md 자동 분류
---
domains: [rl-env, render, perf]
scope_paths:
  - crittergym/wrappers/**
  - crittergym/render/**
  - benchmarks/**
acceptance:
  # G1 통과 시 qa-checklist 자동 합산
---
```

### 2️⃣ `/task-evaluate` — L1 평가 (병렬 스폰)

`task-evaluate` 가 `domains:` + `scope_paths:` 분석 → 매칭 agent **단일 메시지 병렬** 스폰.
기본 동봉은 `@plan-reviewer` + `@qa-verifier`. 도메인 auditor 는 vertical 에 추가됐을 때만 함께 스폰:

```
[병렬 호출 — 1 message]
├─ @plan-reviewer       (🔵 lifecycle, Sonnet) — 기본 동봉
├─ @qa-verifier         (🔵 lifecycle, Haiku)  — 기본 동봉
├─ @rl-env-auditor      (🟢 paths 매칭)        — if added
├─ @perf-auditor        (🟣 paths 매칭)        — if added
└─ @render-auditor      (🟡 paths 매칭)        — if added
```

**Verdict 예시** (도메인 auditor 가 모두 추가됐다고 가정):

| Agent | Verdict | 이유 |
|---|---|---|
| plan-reviewer | APPROVE | 범위·리스크 OK |
| qa-verifier | APPROVE | plan↔acceptance 정합 |
| rl-env-auditor | SUGGEST | "wrapper 의 observation_space 재정의 명시" |
| perf-auditor | **BLOCK** | "프레임 스택이 per-step Python 루프 — 벡터화 불가 패턴" |
| render-auditor | APPROVE | rgb_array 결정성 영향 없음 |

→ Aggregator: 1+ BLOCK → 전체 BLOCK → 사용자 plan 보완 → L1 재진입 → 모두 APPROVE → **G1 통과**

### 3️⃣ G1 통과 — qa-checklist 자동 생성

```yaml
acceptance:
  lifecycle:        # 🔵 horizontal
    - type_check, lint, unit_tests, contract pass
    - 재현성 회귀 0
  rl-env:           # 🟢
    - wrapper 가 reset/step 계약 보존 ((obs,info) / 5-tuple)
    - observation_space.contains(obs) 통과
    - 시드 전파 (self.np_random)
  perf:             # 🟣
    - 프레임 스택 벡터화 경로 (per-step Python 루프 금지, L1 보완)
    - steps-per-second 회귀 < 5%
  render:           # 🟡
    - 디버그 오버레이 rgb_array 결정적 (시드 고정 시 동일 프레임)
    - 프레임 dtype/shape 계약 준수
```

### 4️⃣ `/task-loop` — L2 TDD micro/macro

매 코드 편집 시 hook 들이 **paths 자동 매칭** 으로 발화 (deterministic, **LLM 미호출**):

```
[Edit crittergym/wrappers/framestack.py]
  PostToolUse 발화:
    ✅ env-contract-check    (🟢 wrappers/** 매칭)
    ✅ determinism-guard     (시드 경로 검사)
    ✅ perf-loop-check       (🟣 hot path 루프 감지)
    ❌ render-determinism-guard (render/** 미매칭, 패스)

[Edit crittergym/render/overlay.py]
  PostToolUse 발화:
    ✅ render-determinism-guard (🟡 render/** 매칭)
    ❌ perf-loop-check (hot path 아님, 패스)

[Edit crittergym/tests/contract/baseline_trajectory.npz]
  PreToolUse:
    ❌ protected-paths guard 차단! "재현성 baseline 보호 경로"
  → 사용자 안내: "baseline 재생성은 별도 승인 절차 경유"
```

**TDD 사이클** (도메인별 test 동시):
- Red: wrapper space test + 벡터화 벤치 회귀 test + render 재현성 test
- Green: 구현 (위 hook 들이 매 편집 감시)
- Refactor: 정리 (hook 재발화)

→ 모든 도메인 hook warning 0 + acceptance pass → **G2 통과**

### 5️⃣ `/task-review` — L3 multi-reviewer (병렬 스폰)

PR diff 의 영향 경로로 reviewer 라우팅. 기본 동봉은 `@qa-verifier`, 도메인 reviewer 는 추가됐을 때만:

```
[병렬 호출]
├─ @qa-verifier        (🔵 plan ↔ 결과 정합성) — 기본 동봉
├─ @rl-env-auditor     (🟢 env/wrapper PR)     — if added
├─ @perf-auditor       (🟣 벤치 회귀)          — if added
└─ @render-auditor     (🟡 렌더 결정성)        — if added
```

모두 APPROVE → L3 종료. 1+ BLOCK → 회귀 개선.

### 6️⃣ `/task-end` + 커밋

도메인별 변경 자동 분류:
- 🟢 rl-env: wrapper 추가, space 재정의, 시드 전파
- 🟣 perf: 벡터화 프레임 스택, 벤치 회귀 확인
- 🟡 render: 디버그 오버레이 1개 신규
- 🔵 lifecycle: type-check / lint / contract / 재현성 결과

---

## 핵심 메커니즘

| 메커니즘 | 동작 | 비용 영향 |
|---|---|---|
| **paths 자동 라우팅** | rule/hook 의 `paths:` frontmatter 매칭 시만 활성 | 무관계 hook 미발화 → 절감 |
| **multi-agent 병렬** | `task-evaluate`/`task-review` 가 영향 경로 분석 → 매칭 agent 만 호출 | 4 vertical 도 paths 안 맞으면 호출 안 함 |
| **verdict aggregator** | N agent verdict 합산. 1+ BLOCK → 전체 BLOCK | 추가 호출 없음 (집계만) |
| **acceptance 자동 합산** | G1 통과 시 도메인별 acceptance 자동 그룹핑 | 사용자 수작업 제거 |
| **horizontal layer 재사용** | task-* skill 은 1번 작성, 모든 vertical 동일 사용 | 중복 코드 제거 |

---

## 실패 시나리오 처리

| 상황 | 처리 |
|---|---|
| L1 1+ BLOCK | plan 보완 → L1 재진입. **selective re-evaluation** (보완 부분만 재평가, 전체 재실행 X) |
| L2 hook block (protected-paths 등) | 즉시 차단 + 어느 hook·왜·우회방법 안내 |
| L2 acceptance 1개 fail | task-loop 재시도. max 5 도달 → 사용자 |
| L3 1+ BLOCK | 회귀 개선 → L3 재진입. 어느 reviewer 가 BLOCK 했는지 명시 |
| Cross-vertical 정책 충돌 | rules `priority:` 낮은 쪽 우선. 충돌 시 task-evaluate 가 사용자에게 먼저 알림 |
| no-progress (동일 fail 2회) | 즉시 사용자 에스컬레이션 (rules/80 강제) |

---

## 토큰 비용 모델

### 단계별 호출 수

(아래 수치는 도메인 auditor 3개가 모두 추가된 worst-case 기준. 기본 동봉 2 agent 만이면 L1/L3 호출 수가 비례 감소.)

| 단계 | Agent 호출 | Hook 발화 | 사용자 응답 | LLM 토큰 |
|---|---|---|---|---|
| 1 task-start | 0 | 0 | plan 작성 | ~500 in / ~2k out |
| 2 task-evaluate (L1) | **5** (병렬) | 0 | aggregator | ~3k in × 5 / ~500 out × 5 |
| 3 G1 + qa-checklist | 0 (template) | 0 | 자동 생성 | ~200 in / ~1k out |
| 4 task-loop (L2) | 1/iter (qa-verifier) | 다수 (deterministic) | TDD 작성 | ~2k in × N / ~3k out × N |
| 5 task-verify (G2) | 1 (qa-verifier) | 다수 | — | ~3k in / ~500 out |
| 6 task-review (L3) | **4** (병렬) | 0 | review verdict | ~5k in × 4 / ~1k out × 4 |
| 7 task-end | 0 | 0 | report | ~1k in / ~3k out |

**총 평균** (이 시나리오, worst-case auditor 풀세트):
- L1: 5 × 3.5k = ~17.5k tokens
- L2: 5 iterations × ~5k = ~25k tokens
- L3: 4 × 6k = ~24k tokens
- 보조: ~10k tokens
- **합계: ~75k tokens / E2E 작업 1건**

### 모델 분배 정책

| Agent | 모델 | 이유 |
|---|---|---|
| `plan-reviewer` | **Sonnet** | 추론 깊이 (계획 평가는 메타 사고) |
| `qa-verifier` | **Haiku** | 정합성 비교 (deterministic, Haiku 충분) |
| `rl-env-auditor` (if added) | Haiku | rule-based 계약 검사, Haiku 충분 |
| `perf-auditor` (if added) | **Sonnet** (복잡 벡터화 추론) / Haiku (단순 루프 감지) | 도메인 복잡도에 따라 |
| `render-auditor` (if added) | Haiku | 결정성 패턴 매칭, deterministic |

→ Sonnet:Haiku ≈ 1:4 비율. **Haiku 80% 활용으로 비용 ~75% 절감** vs 모두 Sonnet.

---

## 토큰 절감 전략 (12 항목)

### 🥇 1. Hook 우선, Agent 차선

| 검증 종류 | 도구 | LLM 호출 | 비용 |
|---|---|---|---|
| Deterministic (regex, AST) | **Hook (Python)** | ❌ | $0 |
| 의미 판단·추론 | Agent (LLM) | ✅ | $$$ |

원칙: **deterministic 검증은 무조건 hook**. agent 는 추론이 필요한 곳에만.

예시:
- `np.random.randint(` 전역 RNG 사용 감지 → hook (regex)
- "이 wrapper 가 observation_space 계약을 의미상 위반하는가?" → agent (의미 판단)

### 🥇 2. Paths 기반 라우팅 (최대 절감)

`task-evaluate`/`task-review` 가 plan 의 `scope_paths` 분석 → **매칭되는 agent 만 호출**.

```
env 만 변경 작업 → @rl-env-auditor 1명만 호출 (4명 병렬 X)
render + env → 2명만 호출
4 vertical 모두 → 4명 병렬
```

**Lazy invocation** — 무관계 vertical 의 agent 는 아예 호출하지 않음.

### 🥈 3. Verdict-only 응답 강제

agent 가 분석 결과를 **장문 설명 X, verdict 만**:

```
APPROVE
SUGGEST: <축>: <한줄>
BLOCK: <축>: <한줄>
```

→ 평균 output 200 tokens (vs 자유 형식 1000+)

### 🥈 4. Skill 우선 (Bash + Python deterministic)

```
/check-contract crittergym/wrappers/framestack.py
  → python3 .claude/hooks/env_contract_check.py
  → output: "OK: reset 2-tuple, step 5-tuple, space contains"
  → LLM 호출: 0
```

vs agent:
```
@rl-env-auditor "이 wrapper 가 step 계약을 지키는가?"
  → LLM 호출: ~3k tokens
```

→ **slash command 가 가능하면 무조건 skill**.

### 🥉 5. 격리 컨텍스트 (메인 보호)

agent 호출 시 **격리 컨텍스트** — 메인 세션 토큰 미증가:

```
@rl-env-auditor (격리)
  └─ context: env 계약 rules + scope_paths 만 (~3k)
  └─ 메인 세션에는 verdict 만 반환 (~200)

vs 메인 세션에서 직접 처리:
  └─ 메인 컨텍스트에 계약 rules 추가 → ~3k 영구 증가
```

→ **격리 = 메인 컨텍스트 1회성 사용 + 다음 작업에 영향 X**

### 🥉 6. Selective Re-evaluation

L1 재진입 시 **변경된 부분만 재평가**:

```
1차: 5 agent → BLOCK 1건 (perf-auditor)
2차 (재평가): perf-auditor 만 재호출 (4 agent skip)
```

→ 재평가 비용 1/5

### 7. Frontmatter-driven On-demand 로드

context 파일을 매번 전체 주입 X. context-router 훅이 **사용자 프롬프트 키워드 매칭** 시만 주입:

```
"계약 확인해줘" 입력 시 context/contracts/gym-api.md 로드 (~2k)
"wrapper 만들어줘" 입력 시 wrapper 모듈 노트 로드
다른 경우: context 미로드
```

### 8. PreCompact 핵심만 보존

Compact 시 전체 보존 X. **계약 SSOT + 결정성 상태 + 작업 컨텍스트** 만:

```
Compact 직전:
  └─ compact-preserve hook 발화
  └─ 보존: 계약 명세, determinism-whitelist, 현재 plan 만
  └─ 폐기: 일반 대화 history
```

→ post-compact 토큰 절약

### 9. Cache-friendly Prompts

agent system prompt 일관 유지 → **Anthropic prompt cache 활용**:

```
@rl-env-auditor system prompt: 동일 (캐시 히트)
@rl-env-auditor user query: 매번 다름 (캐시 미스)
```

→ system prompt 부분 90% 캐시 (cost ~10% with cache, vs 100% no cache)

### 10. Batch Parallel Tool Calls

병렬 호출 시 **단일 메시지에 multiple Agent tool**:

```yaml
# 좋음 (1 message, parallel)
- Agent(@plan-reviewer)
- Agent(@qa-verifier)
- Agent(@perf-auditor)

# 나쁨 (3 messages, sequential)
msg1: Agent(@plan-reviewer) → 결과 받기
msg2: Agent(@qa-verifier) → 결과 받기
msg3: Agent(@perf-auditor) → 결과 받기
```

→ 병렬은 wall-clock + 토큰 절약 (메인 세션 turn 수 감소)

### 11. Iteration Cap (rules/80 강제)

```yaml
L1: 사용자 컷오프 (소프트)
L2-outer: max 5 (하드)
L3: 사용자 컷오프 (소프트)
no-progress: 동일 fail 2회 시 즉시 사용자
```

→ **무한 루프 방지** = 비용 폭탄 방지

### 12. Rule Path Narrowing

rules 의 `paths:` 를 좁게 → 무관계 파일에 hook 발화 X:

```yaml
# 나쁨
paths: ["**/*.py"]  # tests, scripts 까지 매칭 가능

# 좋음
paths:
  - "crittergym/envs/**/*.py"
  - "crittergym/wrappers/**/*.py"
```

→ false positive 감소 + hook 발화 횟수 감소

---

## 비용 한계선 가이드

### 작업 규모별 토큰 예산

| 작업 규모 | 예산 (tokens) | 추천 전략 |
|---|---|---|
| 🟢 Small (1 vertical, 1-3 파일) | ≤ 30k | hook + skill 만, agent 최소 |
| 🟡 Medium (1-2 vertical, 5-10 파일) | 30-80k | L1 평가 1-2 agent |
| 🟠 Large (3+ vertical, 10+ 파일) | 80-200k | full L1·L3 multi-agent |
| 🔴 Massive (E2E feature) | 200k+ | **분할 권고** — 작은 작업으로 쪼개기 |

### 메트릭 모니터링 (Phase 5 운용 시)

session-report (Stop hook) 가 매 세션 종료 시 기록:

```yaml
session_metrics:
  total_tokens: 78k
  agent_calls: 9
  hook_fires: 47
  iterations:
    L1: 2
    L2: 4
    L3: 1
  flagged:
    - "L1 2회 — perf 벡터화 plan 보완 필요"
```

→ Phase 5 튜닝 자료. false positive 빈번 vertical 의 hook matcher 좁히기.

### 비용 폭주 신호

다음 패턴은 **즉시 사용자 알림** (rules/80):

| 신호 | 임계값 | 조치 |
|---|---|---|
| 단일 작업 토큰 | 200k 초과 | 작업 분할 권고 |
| L2-outer iteration | 5회 도달 | 자동 사용자 에스컬레이션 |
| no-progress | 2회 연속 동일 fail | 즉시 사용자 |
| agent 호출 수 | 단일 단계 10+ | 라우팅 검토 (paths 매칭 과잉) |

---

## 정리

### 메커니즘 (cross-vertical 동작)

E2E 다중 vertical 작업도 **process layer (horizontal) 가 변하지 않음**:
- 사용자: `/task-start → /task-evaluate → /task-loop → /task-verify → /task-review → /task-end` (동일 슬롯)
- 변하는 건 **자동으로 호출되는 agent/hook 의 수** (paths 라우팅이 결정)

이게 단일 하네스 + horizontal/vertical layer 의 핵심 가치: **vertical 추가가 process layer 를 건드리지 않음**.

### 토큰 통제 (3 핵심)

1. **Hook 우선**: deterministic 검증은 LLM 미호출 (비용 $0)
2. **Paths 라우팅**: 무관계 agent 미호출 (lazy invocation)
3. **Haiku 격리 + Sonnet 한정**: 모델 비용 ~75% 절감

이 3개만 지켜도 평균 작업당 토큰 비용 **베이스라인의 25-30%** 수준 유지 가능.

---

## 변경 이력

| 일자 | 버전 | 변경 |
|---|---|---|
| 2026-04-25 | v1 | 초안. cross-vertical walkthrough + 토큰 절감 12 전략 + 비용 한계선 가이드 |
