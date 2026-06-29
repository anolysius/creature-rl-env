---
slug: inference-telemetry
initiative: eval-product
status: completed
ended: 2026-06-29
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md  # task table #13
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# 직접 추론 메트릭 (super-effective 무브 사용률) — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 498 → **502** (+4, 회귀 0), 2 skip |
| mypy / ruff / build | clean(31) / clean / clean |
| **메트릭 변별** | **oracle SE-rate 61% vs type_blind 7%** (read-only) |
| 무회귀 | scripted byte-identical (default oracle 1.125/1.0), score_agent 무변경 |
| L1 / L3 | 2/2 APPROVE / 2/2 APPROVE |
| 변경 | eval_harness.py · llm_eval_run.py · test_eval_harness.py |

## 평이한 한 문단 요약 (수식 없이)

기존 "체육관 클리어" 점수는 **버티기만 하면 약한 공격을 반복해 이길 수 있어서**(소모전) "규칙을 추론했나"를
깨끗이 못 쟀습니다. 그래서 *이기든 지든 상관없이* "전투에서 숨은 상성표를 알아내 **효과적인 기술을 골라
쓰는 비율**"을 직접 재는 지표를 추가했습니다. env는 한 글자도 안 바꾸고 **읽기만** 했습니다. 검증 결과:
규칙을 아는 전문가는 61%, 규칙을 모르는 baseline은 7% — 추론 행위 자체를 깔끔히 가립니다.

## 계획 대비 실적

| AC | 결과 | 근거 |
|---|---|---|
| AC1 telemetry 함수 + 가드 | ✅ `_super_effective_move`(action 0-3·eff>1.0) + `score_inference_telemetry`(0-move→0.0) |
| AC2 env read-only / score_agent 불변 | ✅ `test_telemetry_is_read_only_score_agent_unchanged` + scripted 1.125/1.0 |
| AC3 oracle 높음·random∈[0,1]·결정론 | ✅ oracle 61% ≥ type_blind 7%, unit-interval, a==b |
| AC4 러너 --telemetry / 미지정 불변 | ✅ 플래그 추가, 조건부 출력 |
| AC5 무회귀 + 정직 경계 | ✅ 498→502, mypy/ruff/build clean, "exploit≠추론 증명·read-only" 명시 |

## 변경 파일 상세

- **`src/critter_gym/eval_harness.py`**: `InferenceTelemetry(super_effective_rate, n_battle_moves)` +
  `_super_effective_move(env, action)`(read-only: battle ∧ action 0-3 → chosen move의 `chart.multi_effectiveness > 1.0`)
  + `score_inference_telemetry(submission, sealed)`(seeds 루프, reset 훅, action 4/5 제외, 0-move 가드).
  `Side` import 추가. `score_agent`/`_play_once` 무변경.
- **`scripts/llm_eval_run.py`**: `--telemetry` — submission + oracle/type_blind 앵커의 SE-rate 출력.
- **`tests/test_eval_harness.py`**: +4 (oracle>blind, unit-interval+결정론, 0-move 가드, read-only 불변).

## 왜 이 메트릭 (attrition confound 우회)

probe로 확인: 전투 `damage=max(1,...)` → 살면 중립 무브 attrition으로 승 → gym-clear 기반 inference_score는
"추론 필수+학습 가능" sweet spot이 노브로 안 잡힘(전투 모델 변경=벤치마크 정의 변경=사람 게이트). 사용자 결정에
따라 **자율안전 대안**: env 무변경, SE-rate로 *추론 exploit*을 승리와 분리해 직접 측정. oracle 61% / blind 7%로
변별 입증.

## 정직 경계 (계승)

- SE-rate는 *exploit 빈도*이지 "추론했다"의 완전 증명 아님 — oracle/blind 앵커 대비로 읽기. 단일 config·proxy.
- env **read-only** (변경 0 → parity·baseline·obs/reward 불변). 점수 보장 아님.
- 실측 LLM SE-rate는 후속 probe(acceptance 아님).

## 흡수처 매핑

- `extracted_to`: INITIATIVE.md task table. InferenceTelemetry 정의 SSOT는 docstring(코드).

## 타입 체크 / 빌드 결과

mypy clean(31) · ruff clean · build → `critter_gym-1.0.0rc1` · pytest 502 passed / 2 skipped.
