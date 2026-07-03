---
slug: community-llm-entry
initiative: eval-product
status: completed
ended: 2026-07-03
extracted_to:
  - docs/how-to/submit-your-model.md
  - docs/how-to/submit-your-model.ko.md
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# community-llm-entry — 결과 보고서

## 요약

| 항목 | 값 |
|---|---|
| 테스트 | 690 → **695** (+5, 회귀 0); ruff clean; mypy 신규 0 |
| 채점 SSOT | `community.score_submission_on_season` — `--demo` 와 LLM 엔트리가 **단일 루프** 공유 (0.75 재현 테스트로 고정), 월드별 `reset()` 격리 |
| 산출 보장 | `community.build_submission` — `validate_submission` 자체검증 (out-of-schema 산출 불가) |
| CLI | `community_submit.py --llm` (provider claude-cli/anthropic, memory 3종, quota 경고, 기존 `--demo`/`--validate` 동작 불변) |
| LLM 실호출 | **0** (fake complete end-to-end + `--help` 테스트) — 실측·제출 커밋 = 사용자 승인 게이트 |
| L1 / L3 | plan-reviewer MALFORMED 1회→재호출 SUGGEST 2건(영향도 표·검증 커맨드) 반영, qa APPROVE / **2/2 APPROVE** |

## 계획 대비 실적

- ✅ AC1 채점 SSOT — 공유 함수 + reset 격리 (0.75 재현·reset 카운트 테스트)
- ✅ AC2 fake end-to-end `validate_submission()==[]`
- ✅ AC3 무회귀 — 695 green, `--validate` 기존 예시 VALID 재확인
- ✅ AC4 quota 게이트 — 예상 호출수 경고 + "제출 커밋=사람 결정" (출력·docstring·how-to 3중)
- ✅ AC5 how-to en/ko LLM 엔트리 소절

## 다음 단계 (사람 게이트)

실측 실행 승인 + 월드 수 결정 시:
```bash
python scripts/community_submit.py --llm --provider claude-cli --battle-memory \
  --submitter <name> --model-name "claude-fable-5 (claude-cli)" --n-worlds <4|8>
```
(4월드 ≈ 최대 800호출/~1.5h, 8월드 ≈ 최대 1600호출/~3h). 산출 JSON 을
`community/submissions/` 에 커밋하는 것(=보드 등재)이 최종 사람 결정.
