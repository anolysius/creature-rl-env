---
slug: super-effective-economy
initiative: hard-benchmark
status: active
started: 2026-07-08
acceptance_freeze: true
mode: standard
task_type: env
domains: [rl-env]
scope_paths:
  - src/critter_gym/battle.py
  - src/critter_gym/jax_env.py
  - src/critter_gym/envs/critter_env.py
  - scripts/super_effective_scout.py
  - tests/test_super_effective_economy.py
  - tests/test_jax_super_effective_parity.py
extracted_to: []
supersedes: []
---

# Super-effective-only 배틀경제 knob + 변별밴드 scout

> 작성일: 2026-07-08 | 상태: 계획 | 이니셔티브: hard-benchmark (M3 신뢰성 자산)

## 목표

**직전 scout(06-strict-battle)가 남긴 후속을 직접 실행한다.** `strict_battle_scout.py`의 마지막
NOTE가 명시: *"strict zeroes only RESISTED (< NEUTRAL) hits… if the attrition probe shows ~+0.00, the
attrition confound PERSISTS via neutral grinding… A stronger variant (e.g. **only-super-effective
damage**…) is a separate design decision, not this scout's call."*

strict_battle은 **저항타(eff < NEUTRAL)**만 0으로 만들었다. 하지만 **중립타(eff == NEUTRAL) grinding**
+ 파티 순환 + 재진입 힐로 attrition confound(§5-(i))가 안 닫혔다(scout=falsify). 본 task는 한 단계 더:
opt-in **`super_effective_only`** knob — **super-effective(eff > NEUTRAL) 타만 데미지, 중립·저항은 0**.
"올바른 타입 선택"이 이김의 *유일한* 경로가 되는 경제.

두 개의 사전약정 측정 질문:
- **Q1 (변별 밴드 widening)**: SE-only가 scripted arm의 변별 밴드(oracle − type_blind gym-clear
  spread)를 strict/default보다 **넓히는가**?
- **Q2 (fairness / winnability)**: SE-only에서 oracle이 여전히 **winnable**(≥ 절반 gym clear)한가?
  중립타까지 0이면 oracle 파티가 어떤 boss에 super-effective 수단이 없을 때 그 gym이 구조적으로
  unwinnable이 될 수 있다 — 이게 깨지면 SE-only는 "공정한 레버"가 아니라 "그냥 너무 가혹".

**정직 프레이밍(북극성 5)**: scripted arm only, ONE 결정론 seed set, no learned/LLM agent, no robust
threshold — 방향 SIGNAL이지 measurement 아님. attrition probe가 안 닫히거나 oracle이 unwinnable이면
그대로 falsify 보고. 헤드라인 금지.

**이 task가 advance하는 EC**: hard-benchmark 이니셔티브의 절대난이도 레버 탐색 — "강한 agent에도 hard"의
*spec 레버* 후보 확장(strict_battle 계열). 판매 티어 난이도 레버 후보(`boss_pool_size`와 병렬).

## 선행 조건

- main = ed4a054 (PR #116 머지), 718 tests green, working tree clean. ✅
- `strict_battle` 3-지점 배선 선례 존재: `battle.py:130`(damage), `jax_env.py:234`(_gym_damage
  compile-time const), `critter_env.py:270`(passthrough). SE-only는 **동일 패턴**을 따른다.
- `strict_battle_scout.py`(archive 06) = 구조 템플릿(arms·attrition probe·winnability·honest NOTE).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/battle.py` | `Battle.__init__`에 `super_effective_only: bool = False` + `damage()` 클램프 1줄 | **중** | 기본 False → 기존 경제 byte-identical |
| `src/critter_gym/envs/critter_env.py` | `__init__` param + `self.` 저장 + Battle 생성 passthrough | **중** | strict_battle 3-지점과 대칭 |
| `src/critter_gym/jax_env.py` | `JaxEnvConfig`에 필드 + `_gym_damage` compile-time const 분기 | **중** | False → byte-identical jaxpr(기존 parity 유지) |
| `scripts/super_effective_scout.py` (신규) | strict scout 구조 재사용, default/strict/SE-only 3-모드 대조 + attrition probe + winnability | 낮음 | numpy only, 무료 |
| `tests/test_super_effective_economy.py` (신규) | knob 계약 + default 무회귀 + numpy↔jax parity(SE-only on/off) | 낮음 | |

### 영향 범위 (import 그래프)

- `battle.py.damage()` 호출처: `Battle.step`(자기 자신), `scripted_opponent`(별도 legacy formula 사용 —
  변경 없음, docstring 이미 명시), `critter_env`의 gym-battle 해석. SE-only=False면 전부 무변경.
- `jax_env._gym_damage` compile-time const → False면 jaxpr byte-identical → **기존
  `test_jax_hard_config_parity` 무회귀**(핵심 리스크 지점).

## Step별 계획

1. **battle.py 엔진 knob** — `super_effective_only` 필드 + `damage()`에
   `if self.super_effective_only and eff <= NEUTRAL: return 0` (strict 클램프보다 위, 더 강함).
   docstring에 "SE-only는 strict의 strict superset — 중립까지 0" 명시.
2. **critter_env.py passthrough** — `__init__` param + `self.super_effective_only` + Battle 생성 인자.
3. **jax_env.py mirror** — `JaxEnvConfig.super_effective_only` + `_gym_damage`에
   `if super_effective_only: return jnp.where(eff <= 1.0, 0.0, _damage(...))` 분기.
4. **tests** — (a) default off → 기존 damage byte-identical, (b) SE-only on → 중립·저항 0·SE만 통과,
   (c) numpy `Battle.damage` ↔ jax `_gym_damage` parity(on/off 양쪽), (d) 기존 hard-config parity 무회귀.
5. **scout script** — hard-commit grid16 + base grid10에서 arms(oracle/infer/type_blind) ×
   3경제(default/strict/SE-only). spread(oracle−blind) 표 + DELTA + attrition probe(→0 여부) +
   **winnable 플래그 강조**. honest NOTE(scripted·1-seed·SIGNAL·falsify 환영).

## 검증 방법

- `.venv/bin/python -m pytest -q` → 718 + 신규 무회귀(기존 parity 포함 green).
- `.venv/bin/python -m mypy src` + `.venv/bin/python -m ruff check .` → 수정 3파일
  (battle/critter_env/jax_env, 전부 `disallow_untyped_defs=true`·ruff 대상) clean.
- `.venv/bin/python scripts/super_effective_scout.py --quick` → 3경제 표 + winnability 출력.
- 신규 knob=False 경로가 기존 테스트를 하나도 안 깨뜨림(byte-identical 확인).

## 리스크

- **R1 (jax parity 회귀)**: SE-only 필드 추가가 default jaxpr을 바꾸면 기존 parity 테스트 깨짐 →
  compile-time const `if` 분기로 False=기존 표현식 보장(strict_battle 선례 동일). **완화: 필수 테스트.**
- **R2 (oracle unwinnable = falsify)**: SE-only에서 oracle이 winnable 밑돌면 "공정 레버 아님". 이건
  *버그가 아니라 측정 결과* — 그대로 Q2 falsify로 보고, knob은 opt-in default-off로 남긴다(무해).
- **R3 (scripted proxy 한계)**: 변별 밴드가 넓어져도 그건 scripted 간 spread일 뿐 — 학습/LLM arm의
  진짜 난이도는 별개(money-gated 후속). 헤드라인 금지 규율로 완화.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `Battle(super_effective_only=True).damage()`가 super-effective(eff>NEUTRAL) 타만 >0,
  중립·저항 타는 정확히 0을 반환. default(False)는 기존 `max(1, …)` 공식과 byte-identical.
- **AC2**: numpy `Battle.damage` ↔ jax `_gym_damage`가 SE-only on/off 양쪽에서 parity(신규 테스트).
- **AC3**: `super_effective_only=False`(default)에서 전체 기존 테스트 스위트 무회귀(718 green,
  특히 `test_jax_hard_config_parity` 포함).
- **AC4**: `scripts/super_effective_scout.py --quick`가 default/strict/SE-only 3경제의 arm spread +
  attrition probe + **oracle winnability 플래그**를 출력(사전약정 Q1·Q2 판정 재료).
- **AC5**: scout 출력·docstring에 정직 프레이밍(scripted·1-seed·SIGNAL·falsify·헤드라인 금지) 명시,
  Q2(winnability) 결과를 falsify 가능 결론으로 정직 서술.
