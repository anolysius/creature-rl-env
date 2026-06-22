# QA Checklist — procgen-region (G1 freeze) · M2-EC1

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (생성기 결정론): generate_region(seed) 동일시드 동일 Region(creatures·gyms·start); 위치 grid내+disjoint
- [x] AC2 (시드별 변주): vary=True 다른 시드 다른 region(개수·gym타입·위치 중 변주, 표본 비교)
- [x] AC3 (env 위임+무회귀+종료): reset→generate_region; vary=False 기존 동작 보존(54 green); vary=True 항상 gym≥1 → 종료 계약 유효
- [x] AC4 (train/test split+가드): train_seeds/test_seeds disjoint, region 누수0; train_seeds(start+n>TEST_SEED_OFFSET)→ValueError; 규약 문서화
- [x] AC5 (procgen 등록): make("CritterGym-procgen-v0") vary=True; check_env 통과; obs∈space train ∧ held-out 표본 모두(경계=max)
- [x] AC6 (결정론 보존): 동일 시드+행동 → 동일 trajectory (fixed·procgen 양 모드)
- [x] AC7 (M1 동작 보존): procgen region 에서 배틀·gym격파·진화 동작(scripted procgen 시드 ≥1 gym 격파)
- [x] AC8 (툴체인 green): ruff∧mypy src∧pytest∧build; 기존 54 회귀 0; check_env 통과
