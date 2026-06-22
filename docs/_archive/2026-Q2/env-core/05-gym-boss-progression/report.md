---
slug: gym-boss-progression
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
milestone: M1
exit_criteria: [M1-EC3, M1-EC4, M1-EC5]
---

# Report — gym-boss-progression (배틀을 월드에 연결) · M1-EC3 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약
배틀 엔진(M1-EC1)을 `CritterEnv.step` 에 연결. **처음으로 "탐험 → gym 진입 → 턴제 배틀 → 보스 격파"가
한 에피소드에서 돈다.** 보스 격파 = boolean subgoal 리워드(RLVR). Acceptance 9/9, **45 tests green**,
check_env 통과. M1-EC3 충족 + EC4(subgoal 리워드)·EC5(scripted ≥1 boss 격파) 부분 충족.

## 산출물
| 파일 | 변경 | 내용 |
|---|---|---|
| `src/critter_gym/envs/critter_env.py` | 갱신 | OVERWORLD/BATTLE 모드 머신, obs 확장, step 분기, 리워드, 종료 진화 |
| `src/critter_gym/party.py` | 신규 | 고정 스타터 party(3타입) + gym 보스 factory(타입별 격파 가능) |
| `tests/test_gym_battle.py` | 신규 | AC1–AC8 (11 케이스) |
| `tests/test_env.py` | 갱신 | 종료 의미 진화(catch 비종료) 반영 |
| `tests/test_baselines.py` | 갱신 | num_gyms=0 으로 catch 베이스라인 격리 |

## Acceptance 결과 (G1 freeze ↔ 실측, 1:1)
- ✅ AC1 gym 배치 — 시드 결정론, creature 비겹침, gyms_defeated 노출
- ✅ AC2 모드 전환 — gym 진입 in_battle=1 + 양측 active obs; obs∈space
- ✅ AC3 에이전트 배틀 — 0-3 무브/4 스위치, 상대 scripted, 매 step=1턴, battle.py 해소
- ✅ AC4 RLVR 리워드 — 격파 +1 ∧ gyms_defeated++; 이동·턴·패배 0 (total==gyms+catches)
- ✅ AC5 종료 — 전 gym 격파→terminated, budget→truncated, catch 비종료(scaffolding 테스트 갱신)
- ✅ AC6 결정론 — 동일 시드+행동 → 동일 trajectory(배틀 포함)
- ✅ AC7 Gymnasium 준수 — 확장 obs `check_env` 통과; obs∈space 양 모드
- ✅ AC8 ≥1 boss 격파 — scripted(내비+배틀)가 seed3에서 2 gym 모두 격파(14스텝)
- ✅ AC9 툴체인 — ruff∧mypy(9 files)∧pytest(45)∧build; env-validation·scaffolding 회귀 0

## 설계 메모 (후속 인계)
- **모드 머신**: action_space는 Discrete(6) 불변; `obs["in_battle"]` 로 에이전트가 0-3 의미(이동 vs 무브)를 구분.
- **리워드 RLVR**: catch +1, gym 격파 +1. 그 외 0. `info["subgoals"]={caught, gyms_defeated}`.
- **종료 진화**: caught≥C → 전 gym 격파로. `num_gyms>0` 가드로 num_gyms=0(순수 catch) 설정 보호.
- **배틀 진입 시 gym 인덱스 저장**(`_battle_gym_idx`) — L3 SUGGEST 반영, "배틀 중 위치 불변" 불변식 명시화.
- **obs 확장**: in_battle, player/enemy hp·type, gyms_defeated. local_patch 에 gym=2 추가(perceivable).
- **경계(의도적 후속)**: party 빌딩(catch→팀), 아이템 env 노출, 다중-보스 party, 최종보스.

## L3 리뷰 반영
- @plan-reviewer SUGGEST(mode-machine): 승리 시 gym 인덱스를 `_agent_pos` 재유도 대신 배틀 진입 시 저장 →
  `_battle_gym_idx` 도입, `_current_gym_index` 제거.
- @qa-verifier: APPROVE (AC 9/9 정합).
- 운영 메모: plan-reviewer 초기 호출 3회가 API 529(서버 과부하)로 실패 → Opus 모델 우회로 완료.

## 마일스톤 진행 (M1)
- [x] M1-EC1 턴제 배틀 sub-MDP (`battle-system`)
- [x] **M1-EC3 배틀=gated checkpoint + env 통합** ← 본 task
- [x] **M1-EC4 subgoal boolean 리워드** (gym 격파 +1) ← 본 task
- [~] M1-EC5 ≥1 boss 격파 (scripted 충족; PPO/풀 베이스라인은 후속)
- [ ] M1-EC2 진화 (`creature-evolution`) — M1 남은 EC

## 후속
- 다음 권장: `creature-evolution`(M1-EC2, M1 마지막 미충족 EC) 또는 M1-EC5 풀 충족(`baseline-suite`: 배틀 인지 베이스라인 + PPO).
- gym 밸런싱/난이도 곡선, 에이전트가 gym 위치를 더 잘 인지하도록 obs 강화는 후속 고려.
