# QA Checklist — render-obs-legibility (G1 freeze 대상)

> 생성: 2026-06-27 (L1 APPROVED 후) | freeze: pending → G1 통과 시 확정

## Acceptance Criteria (plan §AC, 사전약정)

- [x] AC1: 오버월드 render에 오도 "Your creature: hp 0, type 0, level 0" 부재 + 스타터 파티 오해 없는 정확 표현(거짓 수치 날조 없이).
- [x] AC2: 전투 중 render는 player/enemy 스탯 정확 표시(현행 유지).
- [x] AC3: 시야에 G/C 있으면 살라언스 문구 + 중앙 타일 gym이면 "진입=보스전" 플래그, 테스트 증명.
- [x] AC4: render_obs 결정론 유지 + 코어필드(position·battle·gyms·action 범례) 계속 포함.
- [x] AC5: DEFAULT_SYSTEM이 스타터 파티·목표(G 보스 격파)·catch 흐름 설명.
- [x] AC6: 무회귀 — scripted score_agent 수치 불변, 전체 pytest green, mypy·ruff·build clean + 정직 경계 명시.

## 표준 DoD

- [x] mypy src clean
- [x] ruff check . clean
- [x] pytest green 480/2skip (회귀 0; .venv)
- [x] python -m build clean
- [x] CHANGELOG 1 entry (standard)
- [ ] 단일 커밋
