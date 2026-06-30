# 레퍼런스: observation & action space (한국어)

> 영어(SSOT): [observation-action-space.md](observation-action-space.md) · `src/critter_gym/envs/critter_env.py` 기준 검증.

action space는 **`Discrete(6)`**이며 모드(오버월드 vs 전투)에 따라 재해석됩니다. observation은
`Dict` space로, 모든 env family에서 동일한 13개 키가 존재합니다(조화된 계약) — 그래서 단일 정책
네트워크가 family들을 가로질러 학습할 수 있습니다.

## Action space — `Discrete(6)`

| 액션 | 오버월드 | 전투 |
|---|---|---|
| `0` | 북쪽 이동 | 공격 무브 0 사용 |
| `1` | 남쪽 이동 | 공격 무브 1 사용 |
| `2` | 동쪽 이동 | 공격 무브 2 사용 |
| `3` | 서쪽 이동 | 공격 무브 3 사용 |
| `4` | 내 타일의 생물 Catch | 다음 파티원으로 Switch |
| `5` | Wait (무동작) | Pass / 아이템 |

전투에서 무브 `0–3`은 각각 **다른 숨은 타입**을 가지며, 어느 것이 super-effective인지는
**입힌 데미지로 추론**해야 합니다(observation에 절대 노출되지 않음). `in_battle` 플래그가 어느
해석이 활성인지 알려줍니다.

## Observation space — `Dict`

| 키 | Space | 의미 |
|---|---|---|
| `agent_pos` | `Box(0, grid_size-1, (2,), int64)` | 에이전트 행, 열 |
| `local_patch` | `Box(0, 2, (5,5), int8)` | 자기중심 시야; 타일 코드 `0`=빈칸 `1`=생물 `2`=체육관 |
| `caught` | `Box(0, num_creatures, (1,), int64)` | 지금까지 잡은 생물 수 |
| `gyms_defeated` | `Box(0, num_gyms, (1,), int64)` | 지금까지 격파한 체육관 수 |
| `evolved` | `Box(0, max_party, (1,), int64)` | 진화한 파티원 수 |
| `in_battle` | `Box(0, 1, (1,), int8)` | 체육관 보스전 중 `1` |
| `player_hp` | `Box(0, hp_max, (1,), int64)` | 활성 생물 hp (전투 중만; 오버월드선 `0`-마스킹) |
| `player_type` | `Box(0, num_types-1, (1,), int64)` | 활성 생물 타입 (전투 중만) |
| `player_level` | `Box(0, level_max, (1,), int64)` | 활성 생물 레벨 (전투 중만) |
| `enemy_hp` | `Box(0, hp_max, (1,), int64)` | 적 hp (전투 중만) |
| `enemy_type` | `Box(0, num_types-1, (1,), int64)` | 적 타입 (전투 중만) |
| `player_charge` | `Box(0, max_charge, (1,), int64)` | 듀얼 charge (family C; 그 외 `0`) |
| `enemy_charge` | `Box(0, max_charge, (1,), int64)` | 듀얼 charge (family C; 그 외 `0`) |

**오버월드 마스킹:** `player_*` / `enemy_*` 전투 필드는 전투 밖에서 `0`-마스킹됩니다(`0`은 "전투
아님"을 뜻하지 *"생물 없음"이 아님* — 스타터 파티는 항상 존재). 텍스트 렌더러
(`critter_gym.llm_eval.render_obs`)가 이를 정직하게 반영합니다.

## 보상 — RLVR (검증 가능 boolean 서브골)

dense shaping 없음. 검증 가능한 서브골 완료마다 `+1.0`:
- 생물 catch (생물 타일에 서서 액션 `4`),
- 체육관 보스 격파.

모든 체육관 격파 시 에피소드 **종료(terminate)**; 스텝 예산(`max_steps`)에서 **잘림(truncate)**.
이동·대기·빈/체육관 타일 catch는 `0.0`.

## 등록된 환경

`from critter_gym.registration import register_envs; register_envs()` 후 `gym.make(<id>)`.

| id | kwargs (기본 대비) | 설명 |
|---|---|---|
| `CritterGym-v0` | — | 고정 M1 월드 (family A 기준) |
| `CritterGym-procgen-v0` | `vary=True, num_types=12, num_gyms=8, max_steps=400` | 절차 region + 시드별 숨은 타입표; **train/test 시드 분리** |
| `CritterGym-commit-v0` | procgen + `super_mult=3.0, boss_hp=140, boss_atk=18, commit_battles=True` | 팀-커밋 보스 경제 (타입표 추론 load-bearing) |
| `CritterGym-forage-v0` | family B, procgen kwargs | contact-collect 수집 메커닉 (장르 일반화) |
| `CritterGym-duel-v0` | family C, procgen kwargs | 타입 무관 스태미나/커밋 듀얼 전투 |
| `CritterGym-muster-v0` | family D, `num_creatures=12, boss_hp=300, boss_def=24, max_steps=600` | 수집-게이트 파워 (이기려면 먼저 파티를 모아야 함) |

## Train / test 시드 분리 (해자 속성)

`reset(seed)`는 region을 **정확히** 재현합니다. 시드는 `region.TEST_SEED_OFFSET`(= 1,000,000)로
분리: train 시드 `< offset`, held-out(test) 시드 `>= offset`. held-out 시드는 **새 맵 *과* 새 숨은
타입표**를 생성하므로 정책이 외울 수 없습니다. held-out 시드는
`critter_gym.generalization.heldout_seeds(n)`로, 봉인·오염가드 eval은 `critter_gym.eval_harness`로.
