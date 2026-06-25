# QA Checklist — jax-family-integration (G1 freeze)

> Frozen: 2026-06-25. Mode: standard.

## Acceptance (frozen → 결과)

- [x] AC1 ✅: `make_jax_env(family=forage)`+`(family=muster)` env step + jit(`test_jit_and_vmap_families`).
- [x] AC2 (비협상) ✅: numpy `ForageEnv`/`MusterEnv` 대비 **parity 0 mismatch** — 24 passed(fixed+vary, random+gym-clearing+catch-then-gym).
- [x] AC3 (muster 상호작용) ✅: 부스트→enemy_hp parity 검증 + `party_atk_boost` 누적기로 evolve 리셋 미러. descope 미발동.
- [x] AC4 (무회귀) ✅: 396 passed(372+24). family A byte-identical(party_atk_boost critter 미관여).
- [x] AC5 ✅: vmap forage·muster 배치(`test_jit_and_vmap_families`).
- [x] AC6 (정직) ✅: family A/B/D·non-commit·CPU·vmap-only·duel(C) 별도 후속 라벨(docs).
- [x] AC7 (사전약정 pilot) ✅: parity 0 + muster 상호작용(catch+evolve 가드) 입증, falsify 0. descope 미발동.
- [x] AC8 ✅: mypy(28)/ruff/pytest(396)/build clean + 문서(jax-throughput.md·DESIGN §4·INITIATIVE) + CHANGELOG.

## Default pass-criteria
- [ ] 신규 코드 테스트 동반. L3 APPROVED. feature→PR.
