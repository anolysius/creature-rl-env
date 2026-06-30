# QA Checklist — agentic-battle-memory (G1 frozen 2026-06-29)

Frozen acceptance (G1). 1:1 대조는 task-end 종료 카드에서.

- [x] **AC1** 전투-결과 인지 메모리가 `eval_harness.Agent` Protocol(`act(obs)->int` + `reset()`)을
      만족하고 봉인 set에서 `score_agent`로 채점된다 (stub end-to-end 테스트 그린).
- [x] **AC2** 적 타입별 무브 관찰 데미지를 (타입,무브)당 **최신 단일값 덮어쓰기**로 누적·프롬프트에
      surface. 표 크기 상한 = num_types×4 (bounded — 테스트로 단언).
- [x] **AC3** 측정 무결성: surface 문자열에 hidden type 이름·차트·정답-무브 추천 **없음**(가드 테스트).
      同 테스트가 신규 클래스 docstring의 정직-경계 문구 존재도 단언.
- [x] **AC4** `reset()`이 전투 메모리 clear → 월드 간 누수 0 (테스트).
- [x] **AC5** `score_agent` 채점 수치가 어댑터 변경과 무관 byte-identical (채점↔어댑터 분리).
- [x] **AC6** 전체 unittest 스위트 그린(회귀 0) + `mypy src` / `ruff check .` clean.
- [x] **AC7** 러너에 신규 에이전트 플래그 노출, stub 경로 무회귀.
- [x] **AC8** 신규 클래스 docstring에 정직 경계(메커니즘이지 측정 결과 아님 / 실측은 사용자 로컬 /
      결과 reframe 금지) 명시 — AC3 가드 테스트가 실행 단언.

## Default DoD (pass-criteria)
- [x] 회귀 0 (기존 502 테스트 그린 유지)
- [x] mypy/ruff clean, build 가능
- [x] CHANGELOG 1줄 entry (standard narrative)
- [x] L3 리뷰 APPROVED (plan-reviewer + qa-verifier 2/2, SUGGEST 5건 전부 반영)
