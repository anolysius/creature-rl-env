# QA Checklist — se-rate-rigor (G1 freeze)

## Acceptance Criteria

- [x] **AC1 [hard]** ✅ `se_inference_score`: `test_se_inference_score_anchors`(oracle→1.0·blind→0.0·mid→(0,1)·span≤0→0.0·clamp) + `_on_band`(infer proxy∈(0,1)·결정론) PASS.
- [x] **AC2 [tooling]** ✅ 러너 `--telemetry`: agent telemetry 를 `n_runs=max(1,runs)`회 실행 → SE 정규화 → runs>1 `classify_inference` robust SE verdict(mean±std + verdict) / runs=1 단일 se_inference_score. runs=1 telemetry 1회=무회귀.
- [x] **AC3 [rigor]** ✅ `se_inference_score` 는 Scorecard.inference_score span 공식 mirror(같은 [0,1] frame) → `classify_inference` frozen 임계 그대로 재사용, 새 임계 0. `test_classify_reuse_on_normalized_se_scores`(oracle→infers·type_blind→at-floor) PASS.
- [x] **AC4 [regression]** ✅ pytest **523 passed**(520+3), 2 skipped, 회귀 0. score_agent 본문 무변경=byte-identical. mypy 31 clean / ruff clean / build OK.
- [x] **AC5 [honesty]** ✅ `se_inference_score` docstring + 러너 출력에 "scripted-proxy band·유료 N-run=평가자 로컬·신호이지 verdict 아님·max_steps 동일 운용점" 명시.

## Default pass-criteria

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5).
- [ ] L3 (task-review) APPROVED (task-end 선결).
