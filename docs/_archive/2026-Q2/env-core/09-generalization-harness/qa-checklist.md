# QA Checklist — generalization-harness (G1 freeze) · M2-EC4

> G1 통과 시 freeze (2026-06-21). task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (정책-비의존 하네스): `generalization.py` 가 `evaluate`/`measure_generalization`/`GapReport.to_dict`/`format_report`/`split_train_pool` 제공
- [x] AC2 (numpy-only): 모듈이 `torch`/`stable_baselines3` 미import — import 순수성 테스트 강제
- [x] AC3 (split API + 누수0 호출부): `train_seeds()`/`heldout_seeds()` 기반; train 인자 held-out 혼입 → ValueError; 하드코딩 50_000 제거
- [x] AC4 (결정론): 고정 seed → 고정 return; `rollout` 재현성 테스트 통과
- [x] AC5 (procgen 변형 위 측정): `vary=True`(test=새 맵+새 타입표) env_factory 로 갭 측정 동작
- [x] AC6 (held-in ∩ 학습 = ∅): `split_train_pool` 두 출력 disjoint + 합집합=입력 numpy-only boolean 테스트 (낙관편향 방지 핵심)
- [x] AC7 (리포트 계약): `to_dict()` 키 `{train_mean,test_mean,gap,n_train,n_test}` + `format_report` 수치 포함 (numpy-only CI 강제)
- [x] AC8 (train_ppo.py 소비자+정정): 하네스 사용 학습→held-in+held-out→gap 리포트; `target_catches` dead-kwarg 정정+`vary=True`; `[rl]` 격리, core/CI 무영향
- [x] AC9 (툴체인+무회귀): `mypy src`∧`ruff check .`∧`pytest -q`∧`python -m build` 통과; 기존 71 tests 회귀 0
