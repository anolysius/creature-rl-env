# QA Checklist — sealed-difficulty-levers (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-6)

- [ ] AC1 — `SealedEvalSet`이 `patch_radius`/`num_gyms` param을 받고 `env_factory`가 CritterEnv에 전달. 기본값(2,3)에서 기존 동작 byte-identical(하위호환).
- [ ] AC2 — `seed_commitment`이 patch_radius/num_gyms를 material에 포함(swap 방어); **그리고** `EvalManifest`/`build_manifest`가 두 레버를 공개 필드로 노출(구매자 가시성, 비밀 seed 미노출 유지).
- [ ] AC3 — `env_tier`의 `_SEALED_KNOBS`가 두 레버 포함, `_SEALED_DROPPED`=num_creatures만. `build_sealed`가 튜닝된 레버를 sealed에 전달; docstring 갱신.
- [ ] AC4 — 회귀 0: 전체 스위트 592 → all pass(기본값 보존), ruff/mypy clean, 3 데모(list_env_tiers·package_sealed_eval·tier_eval_bundle_demo) 무오류.
- [ ] AC5 — 정직성 문서 갱신: env-tiers.md/sealed-eval-packaging.md/tier-eval-bundle.md가 "이제 두 레버 반영+바인딩+매니페스트 노출; num_creatures만 드롭", "sealed가 덜 어려울 수 있음" 경고 제거. 내장 hard는 이미 충실했음을 과대표현 없이.
- [ ] AC6 — eval_harness/eval_package/env_tier 테스트가 AC1-3 커버. CHANGELOG 1줄 entry.

## Default DoD

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] `ruff check` / `mypy` (3 코어 모듈) 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
