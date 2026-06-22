---
slug: procgen-typechart
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
milestone: M2
exit_criteria: [M2-EC2]
---

# Report — procgen-typechart (시드별 내부정합 타입표) · M2-EC2 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약
**moat 의 핵심 novelty.** 시드마다 다른, 내부적으로 정합한 타입 상성표를 생성하고 **obs 에 노출하지 않아**
에이전트가 고정표를 외울 수 없고 **경험에서 메타를 추론(infer-the-meta)** 해야 한다. 이제 held-out 시드는
새 맵(EC1) + **새 타입표**(EC2)를 함께 생성한다. Acceptance 8/8, **71 tests green**, check_env(fixed+procgen).

## 산출물
| 파일 | 변경 | 내용 |
|---|---|---|
| `src/critter_gym/types.py` | 갱신 | `TypeChart` frozen dataclass(beats frozenset, 비교가능) + `FIXED_CHART` + `generate_typechart(seed,vary)` |
| `src/critter_gym/region.py` | 갱신 | `Region.chart` 필드; `generate_region` 이 시드로 차트 생성 |
| `src/critter_gym/envs/critter_env.py` | 갱신 | `_region_chart` 보관; Battle ∧ scripted_opponent 에 전달(scripted 차트 누락 버그 수정) |
| `tests/test_types.py`·`test_region.py`·`test_gym_battle.py` | 갱신 | 데이터주도·생성기 정합·변주·obs 미노출·env 통합·region 차트 (7 신규) |

## Acceptance 결과 (G1 freeze ↔ 실측, 1:1)
- ✅ AC1 TypeChart 데이터주도 + 무회귀 — `TypeChart()`=FIXED_CHART, effectiveness/multi 유지, 비교 가능
- ✅ AC2 생성기 내부정합 + 결정론 — 30 시드 antisymmetric/self-neutral, 동일 시드 동일 차트
- ✅ AC3 시드별 변주 — 40 시드 >1 차트, ≥1 시드가 FIXED 와 다름(vacuous 방지)
- ✅ AC4 obs 미노출 — vary obs 키 == fixed obs 키; chart/effectiveness 필드 없음(infer-the-meta)
- ✅ AC5 env 통합 + scripted 수정 — vary env(seed0)=generate_typechart(0); seed0 차트가 FIRE-vs-GRASS flip → seed0_dmg < fixed_dmg; fixed=FIXED_CHART
- ✅ AC6 region 차트 + train/test — Region(vary) chart 결정론 보관; train·held-out 각각 >1 차트
- ✅ AC7 결정론 + M1 보존 — procgen 결정론 green; vary=False=M1(64 green); check_env(fixed+procgen)
- ✅ AC8 툴체인 — ruff∧mypy(10)∧pytest(71)∧build∧check_env; 기존 64 회귀 0

## 설계 메모 (후속 인계)
- **데이터주도 TypeChart**: `beats: frozenset[(attacker,defender)]` (super 관계). `effectiveness` = (a,b)∈beats→super / (b,a)∈beats→not-very / else neutral. `TypeChart()` 기본=FIXED(M1 무회귀).
- **생성기**: 각 타입쌍을 `default_rng(seed)` 동전던지기로 방향 결정 → antisymmetric·모순0 구성. K=3 → 8 차트.
- **infer-the-meta**: 차트는 obs 에 *절대* 안 들어감 — 타입 id 만. 에이전트는 배틀 데미지로 메타 추론.
- **scripted 버그 수정**: 기존 `_step_battle` 가 `scripted_opponent` 에 차트 미전달 → 항상 FIXED 사용. 이제 `self._region_chart` 전달(Battle 과 동일 차트 — 공정·결정론). fixed 모드 동작 불변.
- **K=3 제한(L3 관찰)**: 8 차트뿐이라 in-distribution 열거 가능 — 메타 *깊이* 는 K 확장(후속)에서. 본 task=메커니즘 + 비-degenerate 검증.

## L3 리뷰
- @plan-reviewer (Opus): APPROVE — 5축 전부 통과. scripted 버그 수정 정확·fixed 무회귀 입증; AC5 strict 데미지 부등식이 vacuous-pass 방지. K=3 제한은 의도된 후속.
- @qa-verifier: APPROVE — AC 8/8 정합, 회귀 0, moat 불변식(차트 미노출·내부정합·train/test 분리) 성립.

## 마일스톤 M2 진행
- [x] M2-EC1 시드→절차 region + train/test (`procgen-region`)
- [x] **M2-EC2 절차 타입표 (infer-the-meta)** ← 본 task
- [x] M2-EC3 train/test 누수 0; held-out 시드가 **새 맵 + 새 타입표** 생성 (EC1+EC2 로 충족)
- [ ] M2-EC4 PPO **train-vs-test 갭** 측정·리포트 — `generalization-harness`

## 후속
- 다음 권장: `generalization-harness`(M2-EC4 — PPO 를 train/test 시드로 돌려 일반화 갭 측정; 손으로 본 데모를 정식 결과로). 이게 **킬러 데모의 직접 토대**이자 M2 완성.
- (후속 깊이) 타입 수 K 확장 + procgen creature 타입 → 메타 추론 난이도 ↑.
