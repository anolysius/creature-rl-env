# QA Checklist — creature-evolution (G1 freeze) · M1-EC2

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (진화 데이터 모델): Creature level + evolved-form 스펙; gain_level/can_evolve/evolve() 결정론; evolve() stats↑+이름변경+재진화불가
- [x] AC2 (배틀 승리 레벨업): 승리 시 그 시점 active creature level+1
- [x] AC3 (임계 게이트 진화): level≥evolve_level 자동 진화(강화 stats); 미만 진화 안 함
- [x] AC4 (RLVR 진화 subgoal): 진화 시 reward+1 + info[subgoals][evolved]++; 레벨업·부분진행=0
- [x] AC5 (evolved 더 강함): evolved form 이 base 대비 더 큰 stats(max_hp·attack) — 상대 단언
- [x] AC6 (obs 노출+준수): obs evolved(+배틀 player_level); check_env 통과; obs∈space 양 모드
- [x] AC7 (결정론): 동일 시드+행동 → 동일 trajectory(레벨·진화 포함)
- [x] AC8 (통합/비-vestigial payoff): scripted 집중 투입 → 진화(evolved≥1) ∧ 진화 creature 가 이후 배틀에 사용; gym/catch subgoal 정상 (num_gyms=3)
- [x] AC9 (툴체인 green): ruff∧mypy src∧pytest∧build; 기존 45 회귀 0
