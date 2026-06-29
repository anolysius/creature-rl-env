# QA Checklist — inference-telemetry (G1 freeze 대상)

> 생성: 2026-06-29 (L1 2/2 APPROVE) | freeze 확정 (사용자 "직접 추론 메트릭" 선택 = GO)

- [x] AC1: InferenceTelemetry(super_effective_rate, n_battle_moves) + score_inference_telemetry가 battle move-결정마다 eff>1.0 read-only 집계, action 4/5 제외, 0-move 시 0.0 가드.
- [x] AC2: env read-only — score_agent/scripted 수치 byte-identical(테스트 고정).
- [x] AC3: oracle SE-rate ≥0.5 + random∈[0,1] + 같은 submission+seed 결정론.
- [x] AC4: llm_eval_run.py --telemetry가 SE-rate(submission+oracle/random 앵커) 출력, 미지정 시 기존 경로 불변.
- [x] AC5: 무회귀 + mypy·ruff·build clean + 정직 경계(exploit≠추론 증명·점수 보장 아님·read-only) 명시.

## 표준 DoD
- [x] mypy · ruff · pytest(.venv) · build clean
- [x] CHANGELOG 1 entry (standard)
- [ ] 단일 커밋
