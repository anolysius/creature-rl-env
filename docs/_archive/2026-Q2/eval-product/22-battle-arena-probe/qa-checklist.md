# QA Checklist — battle-arena-probe (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-7)

- [ ] AC1 — arena 메커니즘: reset 즉시 전투, K회 연속 전투 후 종료(승패 무관 진행), 전투당 힐/commit-window 기존 gym 규칙 동일, 같은 seed → 같은 trace.
- [ ] AC2 — 기존 경로 무회귀: additive(기존 CritterEnv/eval 무수정), 기존 전체 테스트 회귀 0, `llm_eval_run.py` 는 `--arena` 미지정 시 기존과 동일 동작.
- [ ] AC3 — band 변별 sanity: arena 4-arm SE-rate band 에서 oracle > type_blind, oracle 승수 > 0 (winnable) — held-out seed 테스트.
- [ ] AC4 — telemetry 재사용: SE-rate=`_super_effective_move`, 정규화=`se_inference_score`, 다중-run 판정=`classify_inference` — 새 임계 0.
- [ ] AC5 — 프로브 스크립트 + 정직 라벨: `battle_arena_probe.py` 가 arena vs 오버월드 band 출력 + scripted-only·LLM-실측-승인-필요·헤드라인-금지 라벨.
- [ ] AC6 — LLM wiring 실행-없이 검증: `--arena` 를 fake complete 로 단위 검증, 실제 LLM 호출 0 (사용자 승인 게이트 명시).
- [ ] AC7 — 문서: `docs/reference/battle-arena.md` — 필수 4섹션(모드 계약 / 측정 프레임 / scripted band 실측 표 / 경계), reference 규격 선례 준수.

## Default DoD

- [ ] 전체 테스트 green, 회귀 0. `mypy src` 신규 오류 0 · `ruff check .` clean. L3 APPROVED(≥2). CHANGELOG append.
