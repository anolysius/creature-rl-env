---
slug: jax-duel-integration
initiative: jax-throughput
status: active
started: 2026-06-25
mode: standard
task_type: general
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/jax_env.py
  - tests/test_jax_duel_parity.py
extracted_to: []
supersedes: []
---

# duel(C) JAX 통합 — KR2 마무리 (4/4 family 벡터화)

> 작성일: 2026-06-25 | 상태: 계획 | milestone: **M4-EC1/EC2** (family breadth)

## 목표

마지막 남은 family **duel (C)** 를 `jax_env` 에 `family=duel` 로 통합해, numpy
`DuelEnv(commit_battles=False)` 대비 **parity 0 mismatch** 를 달성한다. 이로써 4/4 family
(critter A / forage B / muster D / duel C) 가 전부 JAX 벡터화 = "환경 폭(breadth)" 주장 완성.

duel 은 type-matchup 배틀 family(A/B/D)와 **구조적으로 다른 배틀 시스템**이다:
- **type chart 없음** — 데미지가 stat 기반(`floor(attack × (1+charge))`), 상성 추론 무용.
- **RPS/stamina 듀얼** — ATTACK(공격)/CHARGE(충전)/GUARD(방어)의 가위바위보식 자원 게임.
  ATTACK>CHARGE, GUARD>ATTACK, CHARGE>GUARD.
- **단일 active(party[0]) 1v1** — 스위칭/파티와이프 없음. 보스는 결정론(`echarge≥1`이면 ATTACK 아니면 CHARGE).
- **overworld 는 family A(CATCH-collect) 재사용** — `DuelEnv` 는 `_step_overworld` 미override.

## 선행 조건

- main HEAD `d925263`, 396 tests green (2 skip). numpy `DuelEnv` = SSOT (`src/critter_gym/envs/duel_env.py`).
- `jax_env.py` 는 이미 family A/B/D + commit/non-commit 배틀 통합 완료. `JaxEnvState` 는 `reset()`
  에서만 생성(다른 곳에서 위치-기반 생성 없음 — 필드 추가 안전).
- charge obs 키는 이미 harmonized: base `CritterEnv._obs` 가 `player_charge`/`enemy_charge`=0 노출,
  `DuelEnv._obs` 가 실값 채움. JAX `encode_obs` 는 현재 두 키 모두 0 → duel 만 실값으로 채우면 됨.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/jax_env.py` | `_FAM_DUEL=3` enum + `JaxEnvState`에 `player_charge`/`enemy_charge` 필드 + duel battle branch + overworld duel 분기(=critter collect) + 진입시 charge 리셋 + `encode_obs` family-aware charge + step dispatch | 중 | family A/B/D byte-identical 유지(추가 필드는 비-duel 0, 추가 분기는 compile-time `family` 상수로 무회귀) |
| `tests/test_jax_duel_parity.py` (신규) | numpy `DuelEnv(commit_battles=False)` vs JAX duel parity 배터리 + non-vacuity 가드 + jit/vmap smoke | 중 | `importorskip("jax")`, CI numpy-only |

### 영향 범위 (import 그래프)

- `jax_env.py` 는 `jax_train`, `scripts/bench_throughput.py`, parity 테스트들이 import. **module-level
  default-config 인스턴스(`jax_env_step`/`encode_obs`/`jax_reset`)는 무변경**(family A commit) — 기존
  import·parity·bench byte-identical. duel 은 `make_jax_env(JaxEnvConfig(family=_FAM_DUEL, commit=False))`
  로만 접근.
- `JaxEnvState` 에 필드 2개 추가 → `reset()` 에서 채움. 다른 생성처 없음(검증됨). pytree(NamedTuple)
  자동 flatten → vmap/jit 무영향.

## Step별 계획

1. **(pre-freeze pilot)** scratchpad 에 jax_env.py 복제 + duel 로직 추가한 프로토타입으로 numpy `DuelEnv`
   대비 parity 배터리(RPS 해소·charge 누적·교착 cap·동시 데미지·승리 evolve) 0 mismatch 검증. **falsify
   시 정직 reframe** 후에야 freeze.
2. `JaxEnvState` 에 `player_charge`/`enemy_charge` (`()` int32) 추가, `reset()` 에서 0 초기화.
3. `_FAM_DUEL=3` enum 추가. `overworld_branch` 의 collect 분기에서 duel 을 critter 경로(explicit CATCH)로
   취급(현 `else` 가 이미 critter — duel 자동 포함). 진입시 `player_charge`/`enemy_charge` 0 리셋(on_gym gated).
4. `duel_battle_branch(s, action)` 신규: `p_act = action≤2 ? action : GUARD`, `e_act = echarge≥1 ? ATTACK : CHARGE`.
   `p_dmg = floor(attack×(1+pcharge))` if ATTACK else 0 (보스 GUARD 안 함); `e_dmg = floor(boss_atk×(1+echarge))`
   if e ATTACK & p≠GUARD else 0. charge 갱신(ATTACK→0, CHARGE→min(MAX,+1), GUARD→unchanged). **동시 데미지**
   (`max(0,·)` 양쪽). `battle_turn`(진입시 0 리셋됨)을 duel turn 카운터로 재사용, cap `_DUEL_TURN_CAP=40`.
   done/win/level/evolve/reward 경제는 기존 `fight` 분기와 동일(active=0).
5. `step()` dispatch: `family==_FAM_DUEL` → `duel_battle_branch`, elif commit → `battle_branch`, else
   `noncommit_battle_branch` (compile-time 분기).
6. `encode_obs`: family-aware — duel 은 `player_charge`/`enemy_charge` 상태 필드에서 채움(in_battle 무관하게
   numpy 미러: numpy 는 항상 현재값 노출, overworld·battle 종료 후엔 0), 비-duel 은 0(byte-identical).
7. `tests/test_jax_duel_parity.py`: random + gym-clearing(=ATTACK 위주) + charge-exploit + stalemate 정책으로
   full-episode parity(13 obs+reward+term+trunc), fixed+vary 차트, + non-vacuity 가드(ATTACK/CHARGE/GUARD·
   교착cap·evolve 실자극 증명) + jit/vmap smoke.

## Pilot 결과 박제 (2026-06-25, freeze 전)

scratchpad 프로토타입(`jax_env_proto.py` + duel branch) vs numpy `DuelEnv(commit_battles=False)`:
- **19,200 compared steps** (fixed+vary × 12 seed × {random, gym-seeking, charge-exploit, stalemate})
  → **0 mismatch** (13 obs + reward + term + trunc).
- **always-attack(gym-seeking)는 0승** — 보스(hp120/atk12)가 탱키해 charge-0 공격만으론 못 이김(보스가
  out-trade). → 승리엔 **RPS 최적 플레이 필요**(보스 결정론 악용). **scripted optimal**(보스 charge턴엔
  ATTACK, 보스 attack턴엔 GUARD = `enemy_charge≥1`이면 GUARD 아니면 ATTACK)으로 1,245 steps
  → **0 mismatch + win 60회 + evolve 24회**. ⇒ 승리·evolve 경제 경로까지 정확 미러.
- **falsify 없음** → 본 plan 그대로 freeze. non-vacuity 가드는 `duel_optimal` 정책으로 win+evolve 자극.

## 검증 방법

- `python3 -m pytest tests/test_jax_duel_parity.py -q` (신규) — 0 mismatch.
- 기존 parity 전부 무회귀: `test_jax_{parity,battle_parity,env_parity,difficulty_parity,battle_full_parity,
  noncommit_env_parity,family_parity}.py` + `test_jax_ppo.py` + numpy-only CI 셋.
- G2: `mypy src` · `ruff check .` · `pytest -q` · `python -m build`.

## 리스크

- **동시 데미지 미러 오류**: duel 은 속도순 없이 양쪽 데미지가 매 턴 동시 적용(보스 기절시켜도 보스 반격이
  player 에 적중). type-matchup 의 speed-order 와 다름 → pilot 이 동시-기절(both faint=loss) 케이스 자극.
- **charge obs noise**: charge 키는 비-duel 0(masked) → encode_obs family-aware 안 하면 byte-identical
  깨짐. duel 만 실값. → pilot 이 overworld(charge=0)·battle(charge>0)·battle 종료 후(0 리셋) 전부 비교.
- **`battle_turn` 재사용**: duel turn cap(40)≠`battle_max_turns`(200). duel-family config 에선 noncommit
  branch 미호출이라 battle_turn 은 duel 전용 → 안전. pilot 이 교착 40턴 cap(=loss) 확인.
- **damage 공식 혼동**: duel 은 `_damage`(min1 clamp·defense·eff) **미사용**, raw `floor(atk×(1+charge))`.
  → 별도 산식, 코드 주석 명시.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1** `make_jax_env(JaxEnvConfig(family=_FAM_DUEL, commit=False))` 가 numpy `DuelEnv(commit_battles=False)`
  대비 **parity 0 mismatch**: 13 obs 키(charge 2키 포함) + reward + terminated + truncated, full 에피소드,
  fixed + vary(per-seed) 차트, ≥4 정책(random / gym-clearing / charge-exploit / stalemate).
- **AC2** non-vacuity 가드: 테스트 배터리가 실제로 ATTACK·CHARGE·GUARD 세 액션, 교착 turn-cap(loss),
  그리고 evolve(win) 경로를 모두 자극함을 별도 테스트로 증명.
- **AC3** family A/B/D 무회귀: 기존 parity 테스트 전부 green, default-config module-level API byte-identical.
- **AC4** jit + vmap smoke: duel env 가 jit 컴파일 + 배치 vmap 동작(obs shape 검증).
- **AC5** G2 통과: mypy(0 err) · ruff(clean) · pytest(전체 green, 회귀 0) · build(clean).
- **AC6** 정직 보고: family A/B/D/**C** 4/4 벡터화 달성을 jax-throughput.md(duel Update)+DESIGN §4 에 기록하되
  CPU·vmap-only·GPU 미측정 등 한계 명시. **속도 수치는 측정하면 보고, 측정 안 하면 주장 안 함**(parity 가 본 task 핵심).
