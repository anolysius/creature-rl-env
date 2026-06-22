---
slug: creature-evolution
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
milestone: M1
exit_criteria: [M1-EC2]
---

# Report — creature-evolution (진화 = long-horizon 투자) · M1-EC2 ✅ → **M1 완성**

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약
진화 메커니즘을 구현해 **M1 의 마지막 EC 를 닫았다**. 배틀 승리 시 active creature 가 레벨업하고, 임계
(evolve_level=2)에서 자동 진화해 강해진다 — 진화는 boolean-verifiable subgoal 리워드(+1). Acceptance 9/9,
**54 tests green**, check_env 통과. **이로써 마일스톤 M1(고정월드 full subgoal chain) 완성.**

## 산출물
| 파일 | 변경 | 내용 |
|---|---|---|
| `src/critter_gym/creatures.py` | 갱신 | `level`, `EvolvedForm`, `gain_level`/`can_evolve`/`evolve()`(stats↑·hp 비례·재진화 불가) |
| `src/critter_gym/party.py` | 갱신 | 스타터 3종 evolved form + 보스 타입 `[GRASS,GRASS,WATER]`(FIRE가 2 gym 커버) |
| `src/critter_gym/envs/critter_env.py` | 갱신 | num_gyms 기본 3, 승리→레벨업→자동진화·리워드, obs `evolved`/`player_level`, info |
| `tests/test_creatures.py` | 갱신 | 진화 메커니즘 단위 (레벨/임계/stats/hp 스케일/no-form) |
| `tests/test_gym_battle.py` | 갱신 | 승리 레벨업·진화 리워드·obs·비-vestigial payoff·결정론 |

## Acceptance 결과 (G1 freeze ↔ 실측, 1:1)
- ✅ AC1 진화 데이터 모델 — gain_level/can_evolve/evolve() 결정론, stats↑·이름변경·재진화불가
- ✅ AC2 배틀 승리 레벨업 — 승리 시 active creature level+1
- ✅ AC3 임계 게이트 진화 — level≥evolve_level 자동 진화, 미만 no-op
- ✅ AC4 RLVR 진화 subgoal — 진화 step reward=2.0(gym +1, evolve +1); 레벨업·부분진행 0
- ✅ AC5 evolved 더 강함 — max_hp·attack > base
- ✅ AC6 obs 노출 + 준수 — evolved(+배틀 player_level), check_env 통과, obs∈space 양 모드
- ✅ AC7 결정론 — 동일 시드+행동 → 동일 trajectory(레벨·진화 포함)
- ✅ AC8 통합/비-vestigial payoff — scripted 집중 → 진화 gym0 후 발생(첫 진화 gyms_defeated<num_gyms), 이후 gym 에서 evolved 사용
- ✅ AC9 툴체인 — ruff∧mypy∧pytest(54)∧build; 기존 45 회귀 0

## 설계 메모 (후속 인계)
- **레벨/진화**: 배틀 승리 시 그 시점 active creature `gain_level()`; `level≥evolve_level`(2) ∧ evolved form 존재 시 자동 `evolve()`. action_space 불변(Discrete(6)) — EVOLVE 명시 액션은 후속.
- **payoff non-vestigial**: num_gyms 기본 3 + 보스 `[GRASS,GRASS,WATER]` → FIRE가 gym0 승리로 진화 후 evolved 로 gym1 처리. 깊은 "집중 vs 스위칭" trade-off 는 M2 escalating gym 에서 심화.
- **진화 영속**: `_party` 에서 진화 상태가 에피소드 내 지속(투자 payoff), `reset` 시 starter_party 로 초기화.
- **known design (L3 @plan-reviewer 관찰, 비차단)**: `_maybe_enter_battle` 가 gym 진입마다 party full-heal →
  gym 간 HP 자원관리 horizon 이 얕음. M1 스코프 정합; 자원관리 깊이는 후속(아이템/회복 비용) 고려.

## L3 리뷰
- @plan-reviewer (Opus 우회): APPROVE — 5축 전부 통과, 비차단 design 관찰 1건(위 known design).
- @qa-verifier: APPROVE — AC 9/9 정합, 회귀 0.

## 마일스톤 M1 — **완성** ✅
- [x] M1-EC1 턴제 배틀 (`battle-system`)
- [x] M1-EC2 진화 (`creature-evolution`) ← 본 task
- [x] M1-EC3 배틀=gated checkpoint + env 통합 (`gym-boss-progression`)
- [x] M1-EC4 subgoal boolean 리워드 (catch/gym/evolve)
- [~] M1-EC5 ≥1 boss 격파 (scripted 충족; PPO/풀 베이스라인은 M3 `baseline-suite`)

## 후속 — M2 (moat)
- M1 완성 → 다음은 **M2 procgen + train/test seed split** (우리 moat, 킬러 데모 토대):
  `procgen-region`, `procgen-typechart`, `generalization-harness`.
- (소규모) typechart-fixed: 타입 수 확장 / 밸런싱. 자원관리 깊이(HP 영속·회복 비용).
