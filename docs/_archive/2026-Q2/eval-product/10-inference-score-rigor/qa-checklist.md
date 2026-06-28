# QA Checklist — inference-score-rigor (G1 freeze 대상)

> 생성: 2026-06-28 (L1 2/2 APPROVE) | freeze 확정 ("권장 진행" 위임 = G1 GO)
> **사전약정 결정규칙 (데이터 보기 전 고정)**: `infer_thresh=0.50`, `floor_eps=0.10`, `k=1.0`.

- [x] AC1: classify_inference + InferenceVerdict 3-branch(m−k·s≥infer_thresh→infers / m+k·s≤floor_eps→at-chart-blind-floor / else inconclusive), 빈 run ValueError, mean/std/n_runs 정확.
- [x] AC2: 임계(0.5/0.1/1.0) 데이터 전 고정 — 코드 기본값 + 본 체크리스트 기록.
- [x] AC3: llm_eval_run.py --runs N 집계 + verdict 출력, N=1 기존 경로 불변.
- [x] AC4: classify_inference property 테스트(LLM 없이) 통과.
- [x] AC5: 무회귀 + mypy·ruff·build clean + 정직 경계 명시.

## 표준 DoD
- [x] mypy · ruff · pytest(.venv) · build clean
- [x] CHANGELOG 1 entry (standard)
- [ ] 단일 커밋
