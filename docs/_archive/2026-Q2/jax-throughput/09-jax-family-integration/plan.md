---
slug: jax-family-integration
initiative: jax-throughput
status: active
started: 2026-06-25
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env, perf]
scope_paths:
  - src/critter_gym/jax_env.py
  - tests/test_jax_family_parity.py
extracted_to: []
supersedes: []
---

# forage + muster family를 jax_env에 통합 (M4 폭 / KR2)

> 작성일: 2026-06-25 | 상태: 계획 | Initiative: jax-throughput (task 9) | 자율 런 KR2

## 목표

현재 family A(critter)만 JAX화된 `jax_env`를 **family B(forage) + family D(muster)** 까지 확장한다.
`make_jax_env(JaxEnvConfig(family=...))`가 numpy `ForageEnv`/`MusterEnv`(둘 다 non-commit 기본 배틀)와
**full parity 0 mismatch**가 되도록. duel(family C)은 완전히 다른 RPS 배틀 엔진이라 **별도 후속 task**.

**왜 (KR2·moat)**: "generalizes within the genre" 주장의 토대 — 4 family가 *standalone numpy*뿐 아니라
*벡터화 JAX*로도 돌면 (B) 장르 전이 실험을 10–100× 싸게 robust화. M4 폭.

**Acceptance 성격**: *측정+정직 보고*. parity 0 비협상. muster 부스트×evolve 상호작용을 freeze 전
pilot이 엄격 검증 — 미러 불가하면 **forage-only로 정직 descope**.

## 선행 조건

- `jax_env.py` (commit + non-commit, parity 0) — 확장.
- `jax_overworld.py`는 이미 `contact=True`(forage) 로직 보유(참고 — jax_env overworld_branch는 별도
  구현이라 contact 로직을 jax_env에 추가).
- numpy SSOT (read-only): `ForageEnv`(contact-collect overworld), `MusterEnv`(CATCH+`c.attack+=12`,
  evolve가 `attack=form.attack`로 부스트 리셋 — creatures.py:97), `registration` family config.

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/jax_env.py` | `JaxEnvConfig.family`(0 critter/1 forage/2 muster) + `JaxEnvState.party_atk_boost`(muster) + overworld_branch forage 변형(contact-collect, CATCH inert) + muster catch 부스트 누적/evolve 리셋 + battle 공격에 부스트 반영 | **높음** | family A(critter) byte-identical 보존(default family=critter) |
| `tests/test_jax_family_parity.py` | 신규 — numpy `ForageEnv`/`MusterEnv` 대비 parity + muster catch×evolve 상호작용 probe | 신규 | 비협상 게이트 |

## Step별 계획

**Step 1 (Red)**: `tests/test_jax_family_parity.py` — forage·muster 각각 numpy 대비 full-episode parity
(13 obs+reward+term+trunc, fixed+vary, random+gym-clearing) + muster catch→evolve→catch 시퀀스 probe
(부스트 리셋 검증). FAIL.

**Step 2 (Green)**:
1. `JaxEnvConfig.family`(int 상수 _FAM_CRITTER=0/_FAM_FORAGE=1/_FAM_MUSTER=2) + `JaxEnvState.party_atk_boost`
   ((P,) float32, reset에서 0).
2. overworld_branch family 분기(python static):
   - forage: 이동 landed 타일 creature면 contact-collect(reward 1, creature 제거, 그 step gym-enter
     없음), CATCH inert; gym-enter는 collect 안 한 move만.
   - critter/muster: 기존 CATCH-collect. muster는 catch시 `party_atk_boost += MUSTER_ATK`(전 멤버).
3. battle 공격: muster면 `_stat(s,act,1) + party_atk_boost[act]`(commit fight + noncommit 양쪽). 승리
   evolve시 해당 멤버 `party_atk_boost[act]=0`(numpy `attack=form.attack` 미러).
4. `family`는 compile-time 상수 → 정적 분기(default critter byte-identical).

**Step 3 (검증/벤치)**: jit+vmap smoke. (벤치 행은 선택.)

**Step 4 (문서)**: jax-throughput.md(family 통합 Update) + INITIATIVE task 9 + DESIGN §4.

## 검증 방법

- **freeze 전 pilot (게이트)**: forage·muster parity 배터리(fixed+vary, random+gym-clearing, ≥12 seed)
  0 mismatch + **muster catch×evolve 상호작용**(catch→evolve→catch가 numpy와 일치) 입증. muster 미러
  불가하면 **forage-only descope**(정직 reframe·정지 보고).
- TDD: `pytest tests/test_jax_family_parity.py`.
- 무회귀: 372 green + 신규. family A(critter) commit/non-commit parity 무회귀(byte-identical).
- canonical.

## 리스크

| 리스크 | 완화 |
|---|---|
| muster 부스트×evolve 상호작용 미러 실패 | `party_atk_boost` 누적기(catch +12 / evolve 리셋)로 정확 미러. pilot이 catch→evolve→catch probe로 검증. 실패시 forage-only descope. |
| forage contact-collect/gym-enter 상호배제 오류 | creature·gym 타일은 procgen상 distinct. collect시 gym-enter skip 명시 미러. parity가 가드. |
| family 필드 추가가 critter parity 깸 | family=critter default + party_atk_boost는 critter 미관여. byte-identical 무회귀 테스트. |
| muster 강보스(hp300/def24)·고 max_steps 발산 | config-driven(boss/max_steps cfg). parity가 가드. |

## Acceptance Criteria (G1 freeze)

- **AC1**: `make_jax_env(JaxEnvConfig(family=forage))` + `(family=muster)`가 full-episode env step 생성.
  jit 컴파일.
- **AC2 (비협상 게이트)**: numpy `ForageEnv`/`MusterEnv`(non-commit) 대비 **parity 0 mismatch** — 13 obs+
  reward+term+trunc, full 에피소드, fixed+vary, random+gym-clearing(≥12 seed). **freeze 전 pilot 입증**.
- **AC3 (muster 상호작용)**: catch→evolve→catch 시퀀스서 부스트 리셋이 numpy와 일치(probe 테스트).
- **AC4 (무회귀)**: 372 tests green + 신규. family A(critter) commit/non-commit parity byte-identical.
- **AC5**: vmap이 forage·muster 에피소드 배치 처리(jit/vmap smoke).
- **AC6 (정직 범위)**: family B/D 통합·non-commit·CPU·vmap-only·duel(C)은 별도 후속(RPS 엔진) 명시.
  muster descope 가능성 정직.
- **AC7 (사전약정 pilot)**: pilot이 parity 0 + muster 상호작용 입증. muster 미러 불가하면 forage-only
  정직 descope·정지 보고.
- **AC8**: `mypy src`·`ruff`·`pytest`·`build` clean. 문서(jax-throughput.md + INITIATIVE + DESIGN §4) +
  CHANGELOG 1줄.

## Pilot 결과 (freeze 전 parity 게이트)

**parity 0 mismatch (비협상)**: 신규 `test_jax_family_parity.py` **24 passed** — numpy `ForageEnv`/
`MusterEnv`(non-commit) 대비 13 obs+reward+term+trunc, full 에피소드, fixed+vary, random+gym-clearing/
catch-then-gym 정책, seed 배터리. forage(contact-collect/CATCH inert/gym-enter 상호배제) + muster
(catch 부스트 + battle damage 반영 + evolve 리셋) 모두 0 mismatch.

**muster 상호작용 입증 (핵심)**: muster 부스트는 attack→battle damage→enemy_hp obs로 흐르므로,
`test_muster_parity_catch_then_gym`의 enemy_hp/player_hp parity가 **부스트의 정확성 검증 그 자체**.
`evolve()`가 `attack=form.attack`로 부스트를 리셋하는 상호작용(creatures.py:97)을 `party_atk_boost`
누적기(catch +12 전멤버 / evolve시 해당 멤버 0)로 정확 미러 — **descope 불필요**. **non-vacuity 가드**
(`test_muster_buff_actually_exercised`)가 배터리가 catch(부스트 적용) **및** evolve(부스트 리셋) 양
경로를 실제 자극함을 증명.

**무회귀**: 372→396(+24), family A(critter) commit/non-commit parity byte-identical(party_atk_boost는
critter 미관여). mypy(28)/ruff/build clean.
