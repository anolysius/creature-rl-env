# How-to: 토큰 usage 실측 (transcript JSONL 집계)

> 출처 task: `rules80-token-savings-actuals` (2026-06-11). 별도 텔레메트리 인프라 없이
> Claude Code 세션 transcript 만으로 rules/80 §F/§G 류 비용 가설을 실측한다.

## 데이터 원천 (로컬 전용 — 커밋 금지)

```
~/.claude/projects/<project-slug>/
├── <session-id>.jsonl                  # 메인 세션 (project-slug = repo 절대경로의 / → -)
└── <session-id>/subagents/
    ├── agent-*.jsonl                   # 서브에이전트 호출 (동일 스키마)
    └── agent-*.meta.json               # {agentType, description, toolUseId}
```

`type: "assistant"` 레코드의 `message.usage` 에 `input_tokens` /
`cache_creation_input_tokens` / `cache_read_input_tokens` / `output_tokens` 기록.

## 실행

```bash
python3 .claude/skills/task-end/scripts/collect-token-usage.py \
  --since 2026-06-01 [--until YYYY-MM-DD] [--output PATH]
# 단위테스트
cd .claude/skills/task-end/scripts && python3 -m unittest test_collect_token_usage
```

stdout 에 agentType 별 hit rate 표, `--output` (default: 측정 task 의 `_artifacts/`) 에 집계 JSON.

## 반드시 알아야 할 함정 3가지

1. **message.id 중복** — 동일 assistant 메시지가 스트리밍 누적으로 ~3중 기록됨.
   전역 dedup (마지막 레코드 승) 없이는 ~3배 과대집계. 파서가 처리하나, 직접 grep 으로
   재집계할 때 주의.
2. **hit rate ≠ helper 효과** — 높은 weighted hit rate 의 주성분은 **대화-내(turn 2+)
   캐시 재사용**이다. cross-call fixed prefix 효과는 `first_call_cache_hit` 지표로 봐야 한다
   (2026-06 실측: qa-verifier 0/39 — 서브에이전트 system prompt 앞부분의 세션별 가변
   컨텍스트 때문에 cache key 불일치).
3. **토큰 수 ≠ 비용** — cache_read 는 0.1x, cache_creation 은 1.25x(5m ephemeral) 가격.
   비용 비교는 JSON 의 `est_input_cost_savings_vs_nocache` 사용.

## 산출물 취급

- 집계 JSON 은 숫자만 포함 (raw 텍스트/프롬프트 없음) → 커밋 안전. transcript 원본은 절대 커밋 금지.
- mode(quick-fix/standard/heavy) 분포는 best-effort (transcript 내 plan.md 경로 최빈값 매핑) —
  세션 ≠ task 임을 report 에 명시할 것.

## 실측 사례

- 첫 실측 report (archive 의 `rules80-token-savings-actuals` task)
  — §G cross-call cache 기각 + §F 표본 부족 판정
