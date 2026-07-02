# QA Checklist — multitype-boss-scout (G1 freeze, heavy)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-6)

- [ ] AC1 — numpy 다중타입 보스 opt-in: `generate_region(boss_secondary=True)`가 gym마다 primary≠secondary 2타입 배치(결정론), `Region.boss_secondary_types` 병렬 필드. off면 byte-identical. effectiveness 두 타입 곱(battle 재사용). obs `enemy_type`=primary only(secondary 숨김, shape 불변).
- [ ] AC2 — oracle 다중타입: oracle arm이 enemy 전체 타입으로 `multi_effectiveness` 유리무브 선택(chart-knowing expert); single-type 회귀 없음.
- [ ] AC3 — jax_env 다중타입 + parity 0: jax_env 곱 effectiveness, obs primary only. numpy↔jax_env parity **0 mismatch**(obs+reward+term+trunc; random+gym-clearing; train·held-out seed).
- [ ] AC4 — 회귀 0 + 하위호환: 전체 스위트 592 → all pass(opt-in off byte-identical), ruff/mypy clean. 독립 포트 jax_battle.py/jax_battle_full.py 불변(범위 밖).
- [ ] AC5 — scout: `multitype_boss_scout.py`(+`multitype_hard_env_spec`) `--quick` 무오류 — parity 0 + recurrent PPO 학습(유한 곡선) + 단일/다중 oracle-frac 둘 다 수치+격차 Δ(%p) + "1-seed raw·robust 임계 없음·multi-seed(≥3) 측정=후속" 라벨 + proxy·CPU 라벨.
- [ ] AC6 — 신규 테스트(test_multitype_boss/test_jax_multitype_boss_parity)가 AC1-3 커버. CHANGELOG 1줄. 후속 task 시드(다중-seed 사전약정 헤드룸 측정) report 명시.

## Default DoD (heavy)

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] 신규 parity 테스트 0 mismatch.
- [ ] `ruff check` / `mypy`(수정 src) 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
