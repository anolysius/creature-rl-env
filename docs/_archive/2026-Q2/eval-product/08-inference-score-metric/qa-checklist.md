# QA Checklist — inference-score-metric (G1 freeze 대상)

> 생성: 2026-06-28 (L1: plan-reviewer APPROVE + qa-verifier SUGGEST 반영) | freeze 확정

- [x] AC1: SealedEvalSet grid_size·boss_hp·boss_atk·boss_def 노브 → env_factory 반영, 기본값 byte-identical.
- [x] AC2: Scorecard.inference_score + score_agent (mean−tb)/(oracle−tb), [0,1] 클램프, 분모≤0→0.0.
- [x] AC3: inference_score 경계 테스트(tb→0, oracle→1, 중간→사이, 분모 가드).
- [x] AC4: llm_eval_run.py 노브 CLI + 3-arm + inference_score 고객용 출력.
- [x] AC5: 무회귀(기본 byte-identical) + pytest green + mypy·ruff·build clean + 정직 경계 명시.

## 표준 DoD
- [x] mypy · ruff · pytest(.venv) · build clean
- [x] CHANGELOG 1 entry (standard)
- [ ] 단일 커밋
