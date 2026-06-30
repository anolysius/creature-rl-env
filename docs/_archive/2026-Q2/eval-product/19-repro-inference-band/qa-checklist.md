# QA Checklist — repro-inference-band (G1 freeze)

## Acceptance Criteria

- [ ] **AC1 [hard]** `reproduce_results.inference_band(quick)` 가 demonstrator config 의 `InferenceBaseline` 결정론 반환, SE-rate 단조(oracle≥infer≥type_blind≥probe), quick 이 full 보다 작은 n_worlds. 신규 테스트.
- [ ] **AC2 [tooling]** `reproduce_results.py` main() 이 "(3) eval-product inference band" 섹션 출력(4-arm SE-rate). 헤더 (1)(2)(3) 반영. 기존 (1)(2) 무변경(회귀 0).
- [ ] **AC3 [honesty]** 출력에 "scripted band=무료·결정론·재현 가능 / LLM 실측(§5 SE 50%)=유료·평가자 로컬·본 repro 미포함" 명시.
- [ ] **AC4 [regression]** 전체 pytest 회귀 0(523 유지 + 신규). mypy/ruff clean. 기존 throughput/headroom 무변경.

## Default pass-criteria

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5).
- [ ] L3 (task-review) APPROVED (task-end 선결).
