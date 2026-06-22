# QA Checklist — baseline-suite (G1 freeze) · M3-EC1

> G1 통과 시 freeze (2026-06-21). task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (정책-비의존 빌더): `scoreboard.py` 가 `score_baselines`→`ScoreTable`(`to_markdown`/`to_dict`, train/test 분리+gap) 제공
- [x] AC2 (numpy-only): 모듈이 `torch`/`stable_baselines3`/`sb3_contrib` 미import — import 순수성 테스트
- [x] AC3 (split 누수 가드 상속): split API 기반 + train 인자 held-out 혼입 → ValueError (measure_generalization 경유)
- [x] AC4 (결정론): 결정론 정책+고정 seeds → 동일 `to_dict`/표
- [x] AC5 (벤치마크 유효성): CI 가 random+scripted 표 생성 + scripted test_mean > random test_mean (spread) boolean 검증
- [x] AC6 (리포트 계약): `to_markdown` 에 베이스라인명+train/test/gap 수치; `to_dict`={이름:{train_mean,test_mean,gap,n_train,n_test}} (numpy-only CI)
- [x] AC7 (benchmark.py CI-검증): scoreboard 리팩터 + dead-bug 3종 정정(`target_catches`/`range(50_000)`/`vary=False`) + sb3 미설치 graceful 2행, ruff 통과
- [x] AC8 (`[rl]` smoke): PPO(`MultiInputPolicy`)+RecurrentPPO(`MultiInputLstmPolicy`) lazy-import 분기 4종 표 생성 확인(importorskip, core CI skip) + `sb3-contrib` 추가
- [x] AC9 (툴체인+무회귀): `mypy src`∧`ruff check .`∧`pytest -q`∧`python -m build` 통과; 기존 81 tests 회귀 0
