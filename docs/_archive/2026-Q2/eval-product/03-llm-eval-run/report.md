---
slug: llm-eval-run
initiative: eval-product
status: completed
ended: 2026-06-27
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md   # eval-product #3 행
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# Real-LLM sealed-eval 러너 (비용-제한) — 결과 보고서 (eval-product #3)

## 요약

"우리 시뮬이 프런티어 LLM 기준 몇 % of oracle?"를 실측하기 위한 **비용-제한 러너**. #2 `LLMAgent` +
`anthropic_complete`로 실제 모델(`claude-opus-4-8` 기본)을 #1 봉인 set서 `score_agent` 채점.
- `SealedEvalSet`에 **`max_steps` 노브 추가**(기본 200=byte-identical; 작은 값으로 per-step LLM 호출 비용
  상한) — env_factory가 CritterEnv에 전달.
- 신규 **`scripts/llm_eval_run.py`**: argparse(model/worlds/max-steps/num-types/master-seed) + 시작 시 예상
  콜 수 + ⚠️ 비용 경고 + frac_of_oracle/oracle/blind/cleared/caught 출력. 기본 3월드×40스텝≈120콜(작은 첫 probe).

**실행은 사용자 로컬**(키=사용자·채팅/커밋 금지·SDK env서 읽음). 러너는 stub 없이도 키/SDK 부재 시 명확
ImportError. CI는 max_steps 캡 테스트(무-API).

## 계획 대비 실적

| AC | 상태 | 결과 |
|---|---|---|
| AC1 step 상한 | ✅ | SealedEvalSet(max_steps)→env 캡, max_steps=8 ≤8스텝 / 기본 200 무변경, 2 테스트 |
| AC2 러너 | ✅ | argparse+비용 경고+score_agent→frac_of_oracle 출력, ruff clean, 키 없을 때 명확 에러 |
| AC3 회귀0/보안/정직 | ✅ | 기본 byte-identical, 461→463(+2), mypy30/ruff/build clean, 키 비노출+정직 경계 |
| AC4 task-end 산출 | ✅ | INITIATIVE #3 + CHANGELOG |

## 변경 파일 상세

**수정**:
- `src/critter_gym/eval_harness.py` — `SealedEvalSet.__init__(max_steps=200)` + `env_factory`가 CritterEnv
  `max_steps=` 전달. 기본 200 = byte-identical(기존 동작 무변경).
- `tests/test_eval_harness.py` — max_steps 캡 + 기본 무변경 2 테스트.

**신규**:
- `scripts/llm_eval_run.py` — 실제 LLM 비용-제한 러너(사용자 로컬 실행).

## 발견된 이슈

- **(보안)** 러너는 API 키를 인자로 받지 않음 — SDK가 env(`ANTHROPIC_API_KEY`)서 읽음. docstring에 "키
  채팅/커밋 금지" 명시. 실행은 사용자 로컬(이 환경엔 SDK·키 없음 → 여기서 측정 불가, 의도된 게이트).
- **(비용)** per-step LLM 호출이라 worlds×max_steps로 콜 수 폭증 → 기본 작게(120콜) + 시작 시 경고.

## 흡수처 매핑

- `docs/_active/eval-product/INITIATIVE.md` #3 행 — 실제 LLM 측정 러너(난이도 실측 도구).
- ADR 가치 없음(#1/#2 위 비용-제한 러너 + max_steps 노브).

## 타입 체크 / 빌드 결과

- `mypy src`: 30 files clean. `ruff check .`: passed. `build`: 1.0.0rc1 OK. `pytest`: 463 passed, 2 skipped.

## 후속 (사용자 실행 — 게이트)

사용자가 로컬에서 `ANTHROPIC_API_KEY` set + `pip install anthropic` 후
`python scripts/llm_eval_run.py --model claude-opus-4-8 --worlds 3 --max-steps 40` 실행 → 출력 회수 →
"프런티어 LLM이 우리 봉인 환경서 N% of oracle" *실측 숫자* 기록. (작은 probe부터, 만족 시 worlds/max-steps↑.)
