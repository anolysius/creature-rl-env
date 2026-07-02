# QA Checklist — custom-env-api (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-9)

- [ ] AC1 — `src/critter_gym/env_tier.py` 신규: `TierSpec`(+`to_json`/`from_json`), `validate_tier_spec`, `register_tier`/`tier_names`/`get_tier`, `make_tier_env`/`tier_env_factory`, `sealed_config`/`build_sealed`. stdlib-only, 신규 의존성 0, eval_package 미import.
- [ ] AC2 — curated 프리셋 `standard`+`hard` 내장 등록, 둘 다 검증 가드 통과.
- [ ] AC3 — 검증 가드: 비정상·unwinnable knob 을 `validate_tier_spec`가 `ValueError` 거부. `make_tier_env`/`register_tier`가 항상 가드 재적용(우회 없음).
- [ ] AC4 — 결정론·구별: 같은 seed reset 결정론 동일; `hard`≠`standard` knob; overrides 반영 + 잘못된 override 거부.
- [ ] AC5 — 정직 메타: `hard` `difficulty_note`가 실측(feedforward PPO ~11–16% of oracle, oracle winnable) + "SOTA/recurrent open" 명시(문자열 검증).
- [ ] AC6 — sealed tie-in: `build_sealed`가 지원 서브셋만 전달(일치), `sealed_config`가 `num_gyms`/`patch_radius` 드롭(docstring+테스트 규정, 정직 명시). descriptor round-trip.
- [ ] AC7 — `tests/test_env_tier.py` 신규: AC1-6 커버, 전체 스위트 회귀 0 (baseline 539).
- [ ] AC8 — `scripts/list_env_tiers.py`: 목록·난이도 메타·커스텀(통과+거부)·정직-scope 캡션 무오류.
- [ ] AC9 — 정직성: 난이도 실측 한정 + open 명시(코드·데모). CHANGELOG 1줄 entry.

## Default DoD

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] `ruff check` / `mypy src/critter_gym/env_tier.py` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
