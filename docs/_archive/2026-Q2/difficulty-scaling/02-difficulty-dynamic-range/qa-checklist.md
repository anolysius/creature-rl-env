# QA Checklist — difficulty-dynamic-range (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 1:1 대조.

## Acceptance Criteria

- [ ] **AC1** — `region.py` `generate_region(..., min_gyms=None)`: vary 시 gym 수 floor/exact 제어. 기본 None=`_MIN_GYMS`(무변경). 재출현 pool 로직 보존.
- [ ] **AC2** — `critter_env.py` `min_gyms: int|None = None` opt-in config → generate_region 전달. 기본 None=무회귀. obs 형태 불변.
- [ ] **AC3** — `difficulty_generalization.py`에 고-gym config + 변별 분해능 측정(gym ∈ {3,5,8}서 oracle−type_blind 절대 spread, `measure_learnability` 재사용) + 사전약정 규칙 함수 + gap(multi-run + `classify_gap`).
- [ ] **AC4** — 측정+정직 보고(성능 freeze 아님). 헤드라인이 사전약정 규칙(분해능↑ 달성/미달 + winnability + gap verdict)과 일치 + caveat 라벨. "PPO 못 푸는 hard-benchmark는 범위 밖" 명시.
- [ ] **AC5** — `tests/test_difficulty_dynamic_range.py`(numpy-only): region min_gyms(정확/범위/기본 무변경) / 변별 property(고-gym 절대 spread > 저-gym, 고정 seed) / winnability(고-gym oracle 대부분 클리어) / backward-compat(기본 동일 trajectory).
- [ ] **AC6** — core CI numpy-only 불변: 287 tests 무회귀(기본 None opt-in), PPO `[rl]` importorskip. canonical clean(mypy·ruff·pytest·build).
- [ ] **AC7** — freeze 전 pilot로 R1(분해능)·R2(winnability)·R3(재출현) 측정 → 사전약정 규칙 분기 확정. falsify 시 정직 reframe. pilot 결과·규칙·확정 분기 report 박제.
- [ ] **AC8** — 문서: DESIGN §3.1.1(pilot 발견 + 동적 범위 결과 + 범위 밖 명시) + competitive-analysis + CHANGELOG + INITIATIVE. JAX 재포트 후속(R5) 명시. broken-link 0.

## 사전약정 결정규칙 (freeze — 데이터 보기 전 고정)

- **분해능↑ 달성**: scripted, 고-gym config(num_gyms=8, min=8)서 **oracle − type_blind 절대 gym-clear spread ≥ 2.0**(현 baseline ~1.0의 ≥2배) **AND** gym ∈ {3,5,8}서 spread **단조 증가**. 둘 다 = 달성. 미충족 = 정직 reframe.
- **winnability 유지**: 고-gym서 oracle gym-clear / num_gyms ≥ 0.70.
- **gap**: 기존 `classify_gap`(floor=0.3·k=1.0), std-across-runs. 어느 결과든 정직 보고.
- **무회귀**: min_gyms=None일 때 동일 seed → 동일 region(byte-identical).
- **범위 밖(정직)**: "PPO가 oracle에 못 닿는 hard-benchmark"는 본 task 아님 — 분해능 한 레버.
