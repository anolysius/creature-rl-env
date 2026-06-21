# How-to — Verdict-Equivalence 게이지 운영

> reviewer 프롬프트 최적화(W1 prefix 슬림화 / W2 캐시 복구 / W3 라우팅 정밀화)가
> **품질을 떨어뜨리지 않았음을 증명**하는 회귀 게이지. 프롬프트를 바꾸기 *전에* 반드시 통과시킨다.

## 언제 돌리는가

reviewer/qa-verifier 프롬프트 helper (`_lib/reviewer_prompt.py`, `_lib/qa_verifier_prompt.py`) 또는
`SHARED_GUIDELINES` fixed prefix 를 변경하는 **모든 task** 는 적용 전 본 게이지를 통과해야 한다.
매 커밋 강제가 아니라 **프롬프트 변경 제안 시 on-demand** (LLM 스폰 비용 때문).

## 구성 (3분리)

```
[1] 결정론 코어  _lib/verdict_equivalence.py   (Python, 단위테스트 가능)
[2] agent 스폰   operator (또는 thin workflow)  ← LLM, 본 게이지에서 사람/오케스트레이터가 수행
[3] 코어 ingest  verdict_equivalence.py report  → 동등성/recall 리포트 + PASS/FAIL
```

Python 은 LLM 을 직접 호출 못 하므로 [2] 만 operator 몫. 나머지는 결정론.

## 3-step 절차

### Step 1 — 프롬프트 생성 (결정론)

corpus 의 각 item × variant(control/candidate) 프롬프트를 코어가 생성:

```bash
cd .claude/skills/_lib
python3 verdict_equivalence.py build-prompts \
  --corpus verdict_corpus/corpus.json --item <item-id> --variant control
python3 verdict_equivalence.py build-prompts \
  --corpus verdict_corpus/corpus.json --item <item-id> --variant candidate
```

- **control** = 현재 프롬프트 (helper 원본).
- **candidate** = 변경 프롬프트. 후속 W1/W2/W3 task 가 `build_prompts(..., variant_overrides=...)` 로 변형 주입.
- 본 게이지 도입 task(`harness-verdict-equivalence`)는 게이지만 — control==candidate (스모크 검증용).

### Step 2 — agent 스폰 (operator, LLM)

각 (item × variant) 를 **K=3회** 스폰(비결정성 대응). reviewer 종류는 corpus item 의 `reviewer` 필드:
- `plan-reviewer` → Agent tool plan-reviewer subagent
- `qa-verifier` → Agent tool qa-verifier (Read-only, inline 자족 프롬프트)

각 스폰의 **raw verdict 텍스트**를 결과 jsonl 한 줄로 적재:

```jsonl
{"item_id":"ki_nondeterministic_reset","variant":"control","run_index":0,"verdict_text":"...","known_issue":true,"expected_min_decision":"BLOCK"}
{"item_id":"ki_nondeterministic_reset","variant":"candidate","run_index":0,"verdict_text":"...","known_issue":true,"expected_min_decision":"BLOCK"}
...
```

> ⚠️ `verdict_text` 는 ingest 단계에서 decision 라벨로 환원되고 **리포트엔 라벨만 남는다** (raw 본문 비커밋).

### Step 3 — ingest + 리포트 (결정론)

```bash
python3 verdict_equivalence.py report \
  --results <results.jsonl> --corpus verdict_corpus/corpus.json
```

- `decision_match` (per item): candidate 가 control 대비 **악화되지 않음** (severity 다수결 비교).
  control 이 BLOCK/SUGGEST 한 item 을 candidate 가 APPROVE 로 떨구면 불일치.
- `known_issue_recall` (per variant): 골든 위반 item 을 `expected_min_decision` 이상으로 잡은 run 비율.
- exit code: PASS=0 / FAIL=1.

## 게이트 해석

PASS 조건 (전부 충족):

| 지표 | 기준 |
|---|---|
| `decision_match_rate_overall` | ≥ `t_match_overall` (default 0.9) |
| `decision_match_rate_known_issue` | = `t_match_known_issue` (default 1.0) — known-issue 가 있을 때 |
| `known_issue_recall(candidate)` | ≥ `known_issue_recall(control)` — 둘 다 측정됐을 때 |

임계값은 `corpus.json` 의 `thresholds` 로 override.

## W1/W2/W3 적용 절차 (게이지 통과 의무)

프롬프트 최적화 task 의 흐름:

1. candidate 변형을 `build_prompts(item, "candidate", variant_overrides=...)` 로 정의.
2. corpus 전체를 control/candidate × K=3 스폰 (Step 2).
3. `report` 실행 (Step 3).
4. **PASS 면에만 프롬프트 변경 적용.** FAIL 이면 변형 폐기 또는 재설계.
5. 적용 후 `collect-token-usage.py` 로 절감 실측 → report.md 에 동등성 PASS + 절감 둘 다 기록.

| 작업 | 게이지 의무 |
|---|---|
| **W1** prefix 슬림화 | ✅ 통과 후 적용 |
| **W2** 캐시 복구 (fixed prefix 안정화) | ✅ 통과 후 적용 |
| **W3** 라우팅 정밀화 | ✅ reviewer 선택이 verdict 에 영향 → 통과 후 적용 |

## 코퍼스 확장

`verdict_corpus/corpus.json` 의 `items` 에 추가:
- archive 대표 task → `{id, reviewer, source: "<plan 경로>", expected_min_decision}` (decision 다양성)
- known-issue 골든 → `{id, reviewer, known_issue: true, source_inline: "<위반 plan>", expected_min_decision}` (recall 기준점)

known-issue 골든은 **control 이 반드시 잡아야 하는** 고의 위반. RL 환경 도메인 예시:
- **nondeterministic reset** — `reset(seed=...)` 가 동일 seed 에 다른 초기 상태를 내는 plan (재현성 파괴)
- **observation-space dtype 변경** — 기존 checkpoint 와 호환 안 되는 obs space dtype/shape 변경
- **non-SMART acceptance** — 측정 불가능한 acceptance criteria (scope-creep / acceptance-누락 포함)

## 관련

- 코어: [`.claude/skills/_lib/verdict_equivalence.py`](../../../.claude/skills/_lib/verdict_equivalence.py)
- 단위테스트: `python3 -m unittest .claude/skills/_lib/test_verdict_equivalence.py`
- 재사용 helper: `reviewer_prompt.py` / `qa_verifier_prompt.py` / `aggregate-verdicts.py` (수정 0)
  - ⚠️ `aggregate-verdicts.py` 는 verdict 파싱(`run_decision`) 시점에 lazy-load 된다. **full repo 체크아웃 전제** — partial checkout(파서 파일 부재) 시 `report`/`ingest` 단계에서 `ImportError`. import 자체는 실패하지 않음(지연 로딩).
- 토큰 실측: [`.claude/skills/task-end/scripts/collect-token-usage.py`](../../../.claude/skills/task-end/scripts/collect-token-usage.py)
