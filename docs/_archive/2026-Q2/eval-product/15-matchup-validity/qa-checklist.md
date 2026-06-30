# QA Checklist — matchup-validity (G1 freeze)

> G1 통과 시점에 freeze. task-end 에서 1:1 대조.

## Acceptance Criteria

- [x] **AC1 [hard, deterministic]** vary=True, num_types∈{3,4,6}, ≥40 seed(train+heldout)에서 생성된 모든 region 의 모든 placed boss 타입에 대해 `any(chart.effectiveness(s, boss) > NEUTRAL for s in _STARTER_TYPES) == True` (SE counter 존재 보장). ✅ `test_every_placed_boss_has_super_effective_party_type` (80 seed × 3 num_types) PASS.
- [x] **AC2 [quantitative]** ✅ 비붕괴: `test_oracle_se_rate_does_not_collapse_with_world_count` — oracle SE-rate **1.000 at every n∈{1,2,3,4,6,8}** (pre-fix 0.055/0.227/0.115). 변별: `test_oracle_discriminates_from_chart_blind_at_eval_scale` — band **+0.93 (n=8) / +0.97 (n=16)** ≥ 0.3. **정직 보정**: band 는 집계 속성(type_blind 고정 챔피언)이라 n=1/3 소표본에선 우연히 동률 → band 는 현실 규모(n=8,16)에서, 비붕괴 floor 는 모든 n 에서 검증. floor 0.5 측정 후 유지(p-hacking 아님 — floor 약화 0).
- [x] **AC3 [regression]** ✅ fixed mode(vary=False) byte-identical(필터는 `if vary:` 밖). 전체 pytest **517 passed**(514+3 신규), 2 skipped, 회귀 0. mypy 31 files clean / ruff clean / build OK.
- [x] **AC4 [honesty]** ✅ report 에 경계 명시 예정(task-end). 전투 economy 재설계는 사람 게이트.

## Default pass-criteria (lifecycle minimum floor)

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5, 모든 mode 강제). — task-end.
- [ ] L3 (task-review) APPROVED (task-end 선결). — 다음 단계.
