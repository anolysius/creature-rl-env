---
slug: super-effective-economy
initiative: hard-benchmark
status: completed
ended: 2026-07-08
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# Super-effective-only 배틀경제 knob + 변별밴드 scout — 결과 보고서

## 요약 (수치 표)

직전 06-strict-battle scout가 NOTE로 지목한 후속을 실행: opt-in `super_effective_only` knob
(strict의 **strict superset** — 중립 eff==NEUTRAL 타까지 0, super-effective만 데미지)을 엔진
3-지점에 배선하고, 3경제(default/strict/SE-only) scripted 변별밴드를 측정.

| 항목 | 결과 |
|---|---|
| 테스트 | **718 → 746** (+28 신규, 회귀 0) |
| lint/type | ruff clean, mypy 수정 3파일 clean (render.py:82는 baseline pre-existing) |
| **Q1 변별밴드 widening** (16 seed) | grid16 spread **2.56 → 2.81 (+0.25)**, grid10 **1.62 → 1.69 (+0.06)** — SE-only가 strict/default보다 완만히 넓힘 (positive SIGNAL) |
| **Q2 oracle winnability** | **winnable=True 전 config** (grid16 5.00/5, grid10 3.00/3) — 공정 레버 생존 |
| attrition probe (confound) | strict **불변**(5→5, 3→3) vs SE-only **부분 축소**(5→3.75, 3→2.31) — **~0 미달, 완전 폐쇄 아님** |

**정직 결론 (SIGNAL, not measurement)**: SE-only는 (a) 변별밴드를 *완만히* 넓히고, (b) oracle
winnability를 지키며(공정 레버), (c) strict가 **전혀 못 건든** 중립-grinding attrition을 **부분**
축소한다 — 그러나 **~0까지 닫지는 못한다**. non-commit party-cycling이 운으로 super-effective
멤버를 만나기 때문. 완전 폐쇄는 commit-mode(순환 제거, 별개 축)가 필요. scripted·1-seed·no-robust
-threshold — 헤드라인 금지. 학습/LLM arm의 진짜 난이도는 money-gated 후속.

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 knob semantics | ✅ | `test_se_only_{neutral,resisted,super,is_strict_superset,multitype_neutral,symmetric,mutual_zero}` + default byte-identical(회귀 0) |
| AC2 numpy↔jax parity | ✅ | `test_jax_super_effective_parity.py` 16 케이스(commit×secondary×seed) green |
| AC3 default 무회귀 | ✅ | 718→746(+28만), `test_jax_hard_config_parity` 포함 green, ruff/mypy(수정파일) clean |
| AC4 scout 3경제 출력 | ✅ | `scripts/super_effective_scout.py --quick`가 spread+attrition+winnability 출력 |
| AC5 정직 프레이밍 | ✅ | scout docstring·print에 scripted·1-seed·SIGNAL·falsify·헤드라인 금지 + Q2 falsify + secondary-unwinnable caveat 은폐 없이 |

## 변경 파일 상세

**수정 (엔진 3-지점 — strict_battle 선례 대칭)**
- `src/critter_gym/battle.py` (+12): `Battle.__init__` `super_effective_only` param + `damage()`에
  `if self.super_effective_only and eff <= NEUTRAL: return 0` (strict 클램프보다 위 = dominance).
- `src/critter_gym/envs/critter_env.py` (+6): param + `self.` 저장 + Battle 생성 passthrough.
- `src/critter_gym/jax_env.py` (+15/-3): `JaxEnvConfig.super_effective_only` + `_gym_damage`
  compile-time const 분기(`eff <= 1.0`). False = byte-identical jaxpr.

**신규**
- `scripts/super_effective_scout.py` (+137): 3경제 대조 scout(2 config × 3 arm × 3 economy) +
  attrition probe + winnability 플래그 + honest NOTE.
- `tests/test_super_effective_economy.py` (+205): knob 계약 12 케이스 + winnability sweep +
  secondary-unwinnable caveat 존재 증명.
- `tests/test_jax_super_effective_parity.py` (+120): numpy↔jax parity 16 케이스.

## 발견된 이슈 (심각도)

- **[낮음/설계경계] SE-only + boss_secondary → 구조적 unwinnable 가능**: 숨겨진 secondary가
  super×resisted=NEUTRAL 천장을 만들면 SE-only가 모든 party move를 0으로 → 그 gym unwinnable.
  단일타입 월드는 guarantee #15로 winnable 보장(eff==super_mult>NEUTRAL). **버그 아님** — Q2의
  정직한 falsifiable 경계. `test_se_only_secondary_can_be_unwinnable_is_a_measured_finding`이
  구체 seed로 증명. knob은 opt-in default-off라 무해.
- **[낮음/baseline] mypy render.py:82**: imageio overload 에러, ed4a054에 이미 존재(본 변경 무관).

## 흡수처 매핑 (extracted_to)

**흡수 없음(빈 배열)** — 살아있는 evergreen 결정 4-질문 검토 결과:
1. 새 설계 narrative? **No** — SE-only는 기존 strict_battle 경제 레버의 파생, 새 아키텍처 아님.
2. 새 절차/runbook? **No** — scout 실행법은 docstring에 self-contained.
3. 새 명세/표? **No** — 결과는 SIGNAL(1-seed), reference로 굳힐 단계 아님(money-gated 재측정 선행).
4. 새 ADR? **No** — opt-in default-off knob, 아키텍처 결정 변경 없음(strict_battle ADR 패턴 계승).

INITIATIVE.md(hard-benchmark) Task 목록에 1행만 추가. 판매 티어 난이도 레버 후보로
`boss_pool_size`·`strict_battle`과 병렬 기록.

## 타입 체크 / 빌드 결과

- `pytest`: 746 passed, 0 regression.
- `ruff check .`: All checks passed.
- `mypy src`: 수정 3파일 clean; render.py:82 1건은 pre-existing baseline(무관).
