# QA Checklist — metrics-viz (G1 freeze) · M3-EC3

> G1 통과 시 freeze (2026-06-22). task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (4종 차트): `viz.py` = `plot_baseline_spread`/`plot_generalization_gap`/`plot_seed_distributions`/`plot_learning_curve`(+`save_all`), 각 `Figure` 반환
- [x] AC2 (numpy-only 격리): viz top-level matplotlib 미import(지연); 측정 모듈(generalization/scoreboard/leaderboard) matplotlib/viz 미import — import 순수성
- [x] AC3 (데이터 헬퍼 numpy-only): `spread_data`/`gap_data`/`seed_distribution_data`/`LearningCurve` core 테스트; 시드분포=held-out `EvalResult.returns`
- [x] AC4 (headless): plot 함수 `Agg` 백엔드
- [x] AC5 (`[viz]` smoke): `importorskip("matplotlib")` 가 Figure 내용(axes/artist 수) + PNG 비어있지 않음 검증(core skip); `matplotlib` `[viz]` extra 추가
- [x] AC6 (단일 평가 통합): `Leaderboard.from_score_table` 무회귀; `benchmark --plot DIR` 1회 ScoreTable 로 리더보드+4차트(시드분포), graceful; ruff
- [x] AC7 (학습곡선 실제 데이터원): `train_ppo.py` 가 `LearningCurve` 누적 + `[viz]` 시 저장(합성 아닌 실제), 개명 키 기반
- [x] AC8 (툴체인+무회귀): `mypy src`∧`ruff check .`∧`pytest -q`∧`python -m build` 통과; 기존 92 tests 회귀 0
