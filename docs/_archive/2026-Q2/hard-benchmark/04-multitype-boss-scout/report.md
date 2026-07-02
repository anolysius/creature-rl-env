---
slug: multitype-boss-scout
initiative: hard-benchmark
status: completed
ended: 2026-07-01
extracted_to:
  - docs/reference/multitype-boss.md
changelog_entry: docs/CHANGELOG.md
---

# 다중-타입 보스 — env 변경 + JAX parity + scout — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 추진 | hard-benchmark "더 깊은 절대 난이도"(#3 후속), de-risked 슬라이스 |
| 수정/신규 | 6 코어 수정(region/party/critter_env/learnability/jax_env/jax_train) + 3 신규(테스트 2, scout 1) + evergreen 1 |
| 테스트 | 592 → **614** (+22, 회귀 0) |
| parity | numpy↔jax_env **0 mismatch** (14 케이스: random+gym-clearing+held-out) |
| lint/type | ruff All checks passed · mypy Success |
| L3 리뷰 | **2/2 APPROVE** (plan-reviewer + qa-verifier) |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 결과 | 근거 |
|---|---|---|
| AC1 numpy 다중타입 opt-in | ✅ | `generate_region(boss_secondary=True)` primary≠secondary(결정론, coords 뒤 draw→off byte-identical), `Region.boss_secondary_types`. obs `enemy_type`=primary(shape 불변). effectiveness 곱(battle 재사용). |
| AC2 oracle 다중타입 | ✅ | `_boss_types`가 보스 전체 타입 읽어 `_favorable_type_vs`(multi_effectiveness); infer/probe는 primary 유지(hidden 격리). single 회귀 없음. |
| AC3 jax_env + parity 0 | ✅ | `gym_type2`(sentinel -1) + `_boss_def_eff`(곱), player→boss 2지점만; boss→player·obs primary 불변. parity 0(test_jax_multitype_boss_parity 14). |
| AC4 회귀 0 + 하위호환 | ✅ | 614 passed(592 전부 유지, off byte-identical), ruff/mypy clean. jax_battle.py/full 불변(범위 밖). |
| AC5 scout | ✅ | `multitype_boss_scout.py --quick`: parity 0 + recurrent PPO 학습 + 단일/다중 oracle-frac 수치+Δ + 1-seed raw·multi-seed=후속·proxy·CPU 라벨. |
| AC6 테스트+CHANGELOG+시드 | ✅ | 신규 테스트 22개 AC1-3 커버. CHANGELOG 1줄(본 task-end). 후속 시드(아래) report 명시. |

## 실측 (scout --quick, 1 seed — SIGNAL)

| config | oracle(winnable) | recurrent PPO | of oracle |
|---|---|---|---|
| single-type | 5.00 ✓ | 1.38 | 28% |
| multi-type | 3.62 ✓ | 0.88 | 24% |

- **정직한 발견**: 숨은 두 번째 타입이 **oracle 천장도 5.00→3.62로 낮춤**(곱 effectiveness가 super-effective 이점을 줄임; 여전히 winnable). 학습 agent oracle-frac 28%→24%, Δ≈+3.4pp. 둘 다 "더 깊은 난이도"와 일관.
- **강한 정직 경계**: **1-seed raw 신호, robust 임계 없음**. "더 어렵다" 입증엔 multi-seed(≥3)+사전약정 측정 필요(후속). PPO(非SOTA)·CPU·grid16 단일·oracle=proxy.

## 변경 파일 상세

**수정(코어)**: `region.py`(Region 필드+opt-in draw), `party.py`(gym_boss secondary), `envs/critter_env.py`(_gym_secondary+param, obs primary), `learnability.py`(oracle 전체타입, infer/probe primary), `jax_env.py`(gym_type2+_boss_def_eff 곱, 2지점), `jax_train.py`(multitype_hard_env_spec).
**신규**: `tests/test_multitype_boss.py`(8), `tests/test_jax_multitype_boss_parity.py`(14, parity 0), `scripts/multitype_boss_scout.py`.
**흡수(evergreen)**: `docs/reference/multitype-boss.md`.

## 발견된 이슈 (심각도)

- **[insight] oracle 천장 하락** — 다중타입에서 oracle도 덜 깬다(5.00→3.62). 이건 절대 난이도 상승의 정직한 지표이자, "학습 agent만 어려워진 게 아니라 최적 전략 자체가 더 어렵다"는 신호. 후속 측정에서 정량화.
- **[프로세스]** plan-reviewer가 L1·L3 첫 호출에서 빈 출력(stall) → verdict-first 재호출로 정상 verdict(seeded proposal `plan-reviewer-verdict-first`가 근본 대응, 별도 PR).

## 타입 체크 / 빌드 결과

- `.venv/bin/python -m pytest` → 614 passed, 1 warning(기존 gymnasium, 무관).
- `ruff check` → All checks passed. `mypy`(6 코어) → Success.
- `scripts/multitype_boss_scout.py --quick` → 정상, parity 0.

## 후속 task 시드

- **`multitype-boss-headroom`** — 다중-seed(≥3), 사전약정(`classify_headroom` frac 고정) 헤드룸 측정: 숨은 두 번째 타입이 강한 메모리 agent(recurrent PPO)의 oracle headroom 을 **robust 하게** 올리는가. 본 scout 가 학습·parity·winnable·1-seed Δ 를 확인해 전제를 검증함.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 무엇 |
|---|---|
| `docs/reference/multitype-boss.md` | opt-in API·hidden secondary·JAX 곱 eff·scout 발견·후속 — 살아있는 참조. |
