# QA Checklist — battle-legibility (G1 freeze 대상)

> 생성: 2026-06-28 (L1 2/2 APPROVE 후) | freeze: 확정 (사용자 "#7 진행해줘" = G1 GO)

## Acceptance Criteria (plan §AC, 사전약정)

- [x] AC1: DEFAULT_SYSTEM 전투 전략 설명(무브 0~3=다른 숨은 타입·시도+기억·action4 교체·패배 후 재시도); super-effective 정답은 미노출(추론은 LLM).
- [x] AC2: render_obs 전투 분기 전술 힌트(다른 무브·적 hp 관찰·교체) + 전투 중 player/enemy 스탯 유지.
- [x] AC3: 오버월드 Catch가 C 타일서만 동작함 명확 안내(gym/creature 혼동 차단).
- [x] AC4: render_obs 결정론 + 양 분기 코어필드 유지.
- [x] AC5: 무회귀 — scripted 수치 불변, pytest green, mypy·ruff·build clean, obs 스키마 무변경 + 정직 경계 명시.

## 표준 DoD
- [x] mypy · ruff · pytest(.venv) · build clean
- [x] CHANGELOG 1 entry (standard)
- [ ] 단일 커밋
