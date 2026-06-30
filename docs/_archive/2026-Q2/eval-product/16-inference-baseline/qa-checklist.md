# QA Checklist — inference-baseline (G1 freeze)

## Acceptance Criteria

- [x] **AC1 [hard]** ✅ `inference_baseline(sealed)` 4-arm 결정론 반환. 3 신규 테스트 PASS: `test_inference_baseline_band_is_monotone`(SE 단조 [100,90,7,0]·oracle SE==1.0·infer>type_blind), `_is_deterministic`, `_inference_score_anchors`(oracle iscore==1.0·type_blind==0.0). **정직 보정(Green 측정)**: per-world 격리가 올바른 의미론(learnability 일치) → infer SE=90%(persist의 39%는 stale 메모리 아티팩트). gym-clears는 infer=oracle로 saturate(#12 attrition) → SE-rate가 변별자(앵커 테스트가 이를 박제).
- [x] **AC2 [tooling]** ✅ 러너 `--telemetry` 가 `inference_baseline`로 full 4-arm band(oracle/infer/type_blind/probe + submission) 출력. score_agent/score_inference_telemetry 본문 무변경(추가 함수·display-only) → 채점 경로 byte-identical.
- [x] **AC3 [regression]** ✅ pytest **520 passed**(517+3), 2 skipped, 회귀 0. mypy 31 clean / ruff clean / build OK.
- [x] **AC4 [doc/honesty]** ✅ `docs/reference/inference-baseline.md`: 보정 band 수치(2 config×2 n) + 고정 재측정 명령 + "이전 수치 비교 불가·실측 사용자 로컬·infer=proxy(LLM 아님)·attrition 사람 게이트" 명시.

## Default pass-criteria

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5). — task-end.
- [ ] L3 (task-review) APPROVED (task-end 선결). — 다음 단계.
