# QA Checklist — battle-system (G1 freeze 대상) · M1-EC1

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (타입표): `TypeChart.effectiveness` ≥3 타입 rock-paper-scissors 2.0/0.5/1.0, 결정론, 다중타입 곱연산
- [x] AC2 (creature 모델): `Creature`/`Move` types·stats·moves + take_damage/heal(클램프)/is_fainted
- [x] AC3 (데미지): 결정론 floor(power·atk/def·type_eff) 최소1, 타입우위 증가, known-value, 랜덤 없음
- [x] AC4 (턴 순서): 두 MOVE 는 speed 높은 쪽 먼저, 타이 결정론
- [x] AC5 (스위치+아이템): Switch 교체; UseItem 힐+소비(둘 다 턴 소모); 아이템 enum/dict 추상화, 단일 POTION
- [x] AC6 (종료): 전멸 시 terminated + info[winner] 정확; 기절 시 강제 스위치/없으면 패배
- [x] AC7 (scripted 상대): scripted_opponent 합법·타입인지; scripted vs scripted max_turns 내 결정론 종료
- [x] AC8 (결정론): 동일 초기 state + 동일 행동 시퀀스 → 동일 결과(숨은 랜덤 0)
- [x] AC9 (툴체인 green): ruff ∧ mypy src ∧ pytest ∧ build
