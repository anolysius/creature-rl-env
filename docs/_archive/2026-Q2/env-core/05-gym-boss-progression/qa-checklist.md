# QA Checklist — gym-boss-progression (G1 freeze) · M1-EC3/EC4/EC5(부분)

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (gym 배치): reset(seed) N≥1 gym 타일 시드 결정론(creature 비겹침), gyms_defeated 노출, 동일시드 동일배치
- [x] AC2 (모드 전환): 미격파 gym 진입 in_battle=1 + obs 양측 active(hp·type); 종료 시 in_battle=0
- [x] AC3 (에이전트 배틀): BATTLE 0-3=무브,4=스위치; 상대 scripted; 매 step=1턴; battle.py 해소
- [x] AC4 (RLVR 리워드): gym 격파 reward+1 + info[subgoals][gyms_defeated]++; 이동·턴·패배=0(dense shaping 없음)
- [x] AC5 (종료): 전 gym 격파 terminated; budget truncated; catch 비종료 subgoal(scaffolding 테스트 갱신)
- [x] AC6 (결정론): 동일 시드+행동 시퀀스 → 동일 trajectory(배틀 포함)
- [x] AC7 (Gymnasium 준수): 확장 obs check_env 통과; obs∈space 양 모드
- [x] AC8 (≥1 boss 격파, EC5 부분): test-local scripted(내비+배틀) 한 에피소드 ≥1 gym 격파
- [x] AC9 (툴체인 green): ruff∧mypy src∧pytest∧build; env-validation·scaffolding 회귀 0
