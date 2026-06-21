# QA Checklist — scaffolding (G1 freeze 대상)

> G1 통과 시 freeze. task-verify(G2)·task-end 가 이 목록과 1:1 대조.

## Acceptance Criteria
- [x] AC1 (설치): `pip install -e ".[dev]"` 가 깨끗한 venv 에서 성공
- [x] AC2 (등록): `gymnasium.make("CritterGym-v0")` 가 에러 없이 env 인스턴스 생성
- [x] AC3 (Gymnasium API): `reset(seed)`→`(obs,info)`, `step`→5-튜플, obs ∈ observation_space
- [x] AC4 (결정론): 동일 seed reset 2회 → 초기 obs 정확히 동일 (numpy array_equal)
- [x] AC5 (RLVR catch 리워드): 창조물 칸 CATCH → reward=+1 ∧ info.subgoals.caught 증가; 빈 칸 CATCH reward=0; dense shaping 없음
- [x] AC6 (종료 subgoal): caught≥C → terminated=True; step budget 초과 → truncated=True
- [x] AC7 (툴체인 green): `ruff check .` ∧ `mypy src` ∧ `pytest -q` ∧ `python -m build` 모두 통과
- [x] AC8 (커플링 확정): HARNESS-PORT-MANIFEST §(c) #1·#2·#3·#4 정합을 report.md 에 확인 기록
