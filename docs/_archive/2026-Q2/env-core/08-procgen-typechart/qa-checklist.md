# QA Checklist — procgen-typechart (G1 freeze) · M2-EC2

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (TypeChart 데이터주도+무회귀): TypeChart()=FIXED_CHART(FIRE>GRASS>WATER); effectiveness/multi_effectiveness 유지; 비교 가능
- [x] AC2 (생성기 내부정합+결정론): generate_typechart(seed,vary) antisymmetric(A super B⟹B not-very A), self=neutral, 모순0, 동일시드 동일차트
- [x] AC3 (시드별 변주): 다른 시드 다른 차트(전부동일 아님); 표본 ≥1 시드가 FIXED_CHART 와 다름(vacuous 방지)
- [x] AC4 (obs 미노출): obs 효과관계 미노출(타입 id만); obs 키 불변(infer-the-meta)
- [x] AC5 (env 통합+scripted 수정): vary 에서 Battle∧scripted_opponent 가 그 시드 차트 사용; FIXED 와 다른 시드로 데미지 차이 단언; fixed=FIXED_CHART
- [x] AC6 (region 차트+train/test): Region(vary) chart 보관; train 차트 vs held-out 차트 다름(누수0)
- [x] AC7 (결정론+M1 보존): 동일 시드+행동 동일 trajectory(procgen); vary=False=M1(64 green); check_env(fixed+procgen)
- [x] AC8 (툴체인): ruff∧mypy src∧pytest∧build; 기존 64 회귀 0; check_env
