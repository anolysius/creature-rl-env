# QA Checklist — env-validation (G1 freeze 대상)

> G1 통과 시 freeze. task-verify(G2)·task-end 가 이 목록과 1:1 대조.

## Acceptance Criteria
- [x] AC1 (Gymnasium 준수): `check_env(CritterEnv(), skip_render_check=True)` 예외 없이 통과
- [x] AC2 (베이스라인 존재): `random_policy`·`greedy_policy` import 가능, 임의 obs 에 유효 행동(0–5) 반환
- [x] AC3 (spread 가드): held-out 시드에서 mean(greedy)>mean(random) ∧ mean(random)>0 ∧ mean(greedy)≤target_catches
- [x] AC4 (일반화/결정론): 동일 시드+정책→전체 trajectory 동일; 다른 시드→다른 초기 obs; benchmark.py 재현
- [x] AC5 (throughput): random ≥20k step 측정, `rate >= 5000` steps/s/core 단언; 실수치 report 기록
- [x] AC6 (PPO 데모): `train_ppo.py`([rl] extra) `trained_mean >= random_mean + 0.5` 단언; 수치+곡선 report 캡처; core 에 torch/sb3 불포함
- [x] AC7 (툴체인 green): torch 없이 ruff ∧ mypy src ∧ pytest -q ∧ python -m build 통과
