---
slug: community-llm-entry
initiative: eval-product
status: active
started: 2026-07-03
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/community.py
  - scripts/community_submit.py
  - tests/test_community.py
  - docs/how-to/submit-your-model.md
  - docs/how-to/submit-your-model.ko.md
extracted_to: []
supersedes: []
---

# community-llm-entry — LLM 커뮤니티 리더보드 엔트리 wiring

> 작성일: 2026-07-03 | 상태: 계획 | 마일스톤: M5-EC3 (공개 리더보드 운영 — 첫 LLM 엔트리 경로)

## 목표

커뮤니티 리더보드(#10)에는 검증기(`--validate`)와 scripted 예시(`--demo`)만 있다.
**실제 LLM 을 시즌 공개 스펙으로 채점해 schema-valid 제출 JSON 을 뽑는 경로**를 만든다
(첫 후보: Claude Fable 5 via claude-cli). **wiring 구축·fake 검증 = 이 task (자율·무료)** /
**실제 quota 측정 + 제출 파일 커밋 = 후속 (사용자 승인)**.

설계 원칙: 시즌 스펙·지표·스키마는 기존 SSOT 그대로 (`BenchmarkSpec` env, 지표=순수 mean
gym-clears on `season_seeds`, `validate_submission` 통과 강제) — **아레나 수치와 무관한
정규 경로** (battle-arena.md 의 "arena ≠ leaderboard" 라벨 준수).

## 작업 범위

| 파일 | 변경 |
|---|---|
| `src/critter_gym/community.py` | additive 2함수: `score_submission_on_season(agent, *, season, n_worlds)` (`.act(obs)`/callable(obs) + 월드별 `reset()` 훅 — 지표·env 는 `--demo` 와 동일 루프) + `build_submission(...)` (schema-valid dict 조립, `validate_submission` 자체검증) |
| `scripts/community_submit.py` | `--llm` 모드 (provider claude-cli/anthropic, `--battle-memory/--stateful/--window`, `--season/--n-worlds/--submitter/--model-name/--date/--out`) — 얇은 CLI, `--demo`/`--validate` byte-identical. quota 경고 출력(예상 호출수) |
| `tests/test_community.py` | fake complete 로 end-to-end: fake LLM agent 채점→`build_submission`→`validate_submission()==[]`; `--demo` 무회귀; 월드간 reset 격리 |
| `docs/how-to/submit-your-model.md` (+`.ko.md`) | "LLM 엔트리 실행법" 소절 (quota 경고·self-reported 라벨 포함) |

### 영향도

| 대상 | 등급 | 근거 |
|---|---|---|
| `community.py` 신규 2함수 | 낮음 | additive — 기존 소비처(`--validate` CI 게이트·`load_submissions`·site 빌드) 무변경 |
| `community_submit.py` `--llm` 분기 | 낮음 | 기존 `--demo`/`--validate` 경로는 공유-함수 승격 외 로직 동일 (기존 테스트가 게이트) |
| how-to en/ko | 낮음 | 문서 소절 추가 |

검증 커맨드: `.venv/bin/python -m pytest -q` (전체) + `mypy src` + `ruff check .`.

## Step별 계획

1. **Red**: test_community.py 에 LLM-entry 테스트 (fake complete, 실호출 0).
2. **Green**: community.py 2함수 + community_submit.py `--llm`.
3. **문서**: how-to en/ko 소절 + CHANGELOG (task-end).

커밋 단위: 단일 커밋 (단독 PR).

## 리스크

| 리스크 | 대응 |
|---|---|
| `--demo`/`--validate` 회귀 | 기존 경로 코드 무변경 (스크립트는 분기 추가만) + 기존 테스트 |
| LLM 월드간 기억 누수로 점수 왜곡 | 월드마다 `reset()` 훅 호출 (sealed 채점과 동일 규율) — 테스트로 고정 |
| 지표 불일치 (community=gym-clears vs eval_harness=return) | `--demo` 의 채점 루프를 공유 함수로 승격해 재사용 — 두 경로 분기 없음 |
| date 필드 비결정론 | `--date` 인자 (기본=오늘) — 제출물은 사용자 artifact, 결정론 요구 없음; `--demo` 는 기존 그대로 |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (채점 SSOT)**: LLM 채점이 `--demo` 와 동일한 env(`BenchmarkSpec.env_factory`)·
  seeds(`season_seeds`)·지표(순수 mean gym-clears) 를 **공유 함수로** 사용 — 별도 채점
  루프 금지. 월드마다 agent `reset()` 훅 (기억 격리).
- **AC2 (schema-valid 산출)**: fake LLM agent 로 end-to-end 실행 시 산출 JSON 이
  `validate_submission()==[]` (self_reported:true 강제·spec verbatim·score 범위 포함) —
  실제 LLM 호출 0 인 테스트.
- **AC3 (무회귀)**: `--demo`/`--validate` 경로 byte-identical (기존 코드 무변경, 기존
  테스트 통과), 전체 스위트 회귀 0 (baseline 690).
- **AC4 (quota 게이트 명시)**: `--llm` 실행 시 예상 LLM 호출수 경고 출력; 실제 측정·제출
  파일 커밋은 이 task 범위밖 (사용자 승인) — help/docstring/how-to 에 명시.
- **AC5 (문서)**: how-to en/ko 에 LLM 엔트리 소절 (명령·비용·self-reported 라벨).
