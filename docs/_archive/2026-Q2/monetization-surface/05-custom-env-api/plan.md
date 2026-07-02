---
slug: custom-env-api
initiative: monetization-surface
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/env_tier.py
  - tests/test_env_tier.py
  - scripts/list_env_tiers.py
extracted_to: []
supersedes: []
mode: standard
task_type: general
---

# 커스텀/고난도 env 티어 API (monetization-surface #5)

> 작성일: 2026-07-01 | 상태: 계획 | 추진 EC: **M5-EC2** (커스텀/고난도 env API)

## 목표

difficulty-scaling·hard-benchmark 이니셔티브가 *실증한* 난이도 레버(grid 크기·호라이즌·boss·타입 수)를
**이름붙은, 검증된, 재현 가능한 env 티어 API**로 패키징한다 — 구매자가 `standard`/`hard` 같은 curated
난이도 등급을 한 줄로 인스턴스화하거나, 자기만의 커스텀 티어를 정의(검증 가드 통과 시)할 수 있는
판매 표면(M5-EC2). #4(판매 패키징)와 대칭 — #4 가 "eval 을 팔 수 있게" 했다면 #5 는 "더 어려운/맞춤
env 를 팔 수 있게" 한다.

현재 빈틈(코드로 확인): 난이도 knobs 는 `CritterEnv.__init__`(grid_size, num_gyms, max_steps,
patch_radius, num_types, boss_hp/atk/def, …)에 흩어져 있고, 어떤 조합이 "실제로 더 어렵지만 여전히
풀 수 있는지"의 지식은 이니셔티브 문서·아카이브에만 있다. 구매자가 재현 가능하게 고를 수 있는
**curated tier 레지스트리 + 난이도 메타데이터 + 검증 가드**가 없다.

**정직성 게이트(이니셔티브 불변식 계승)**: 이 task 는 *기술 artifact*만 만든다(빌드+로컬 검증 자율).
실판매·가격·hosting=사람. 특히 **난이도 주장의 정직성**이 핵심 — `hard` 티어의 난이도 수치는
difficulty-scaling/hard-benchmark 에서 **실측된 것**(feedforward PPO 가 grid16 에서 oracle 의
~11–16%, oracle 은 여전히 winnable)만 기술하고, "SOTA/recurrent 에도 hard"는 **미해결(open)** 임을
descriptor·docstring 에 명시한다. 측정 안 한 것을 hard 라 팔지 않는다. (정직성 > 헤드라인.)

## 선행 조건

- `src/critter_gym/envs/critter_env.py` — `CritterEnv.__init__` knobs (재사용 대상).
- `src/critter_gym/env_family.py` — `register_family`/`make_family`/`family_names` 레지스트리 패턴
  (동일 idempotent-register 관례를 티어에 맞춤).
- `src/critter_gym/eval_harness.py` — `SealedEvalSet`(main 존재). 티어가 sealed-eval config 를
  산출할 수 있게 tie-in(단 **import eval_package 금지** — #4 는 별도 미머지 브랜치, cross-branch 의존 회피).
- 참조 패턴: `scripts/package_sealed_eval.py`/`build_site.py` — 순수 함수 + `main()` + stdlib.
- 실측 난이도 출처: hard-benchmark INITIATIVE(grid16 feedforward PPO ~11–16% of oracle; oracle winnable),
  difficulty-scaling(변별 분해능·headroom robustness). stdlib만. 신규 의존성 0.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 종류 | 영향도 | 변경 요지 |
|---|---|---|---|
| `src/critter_gym/env_tier.py` | 신규 | 낮음(신규, 기존 import만) | TierSpec + curated 프리셋 + 레지스트리 + 검증 가드 + 팩토리 + descriptor |
| `tests/test_env_tier.py` | 신규 | 낮음 | 프리셋 결정론·검증 가드·커스텀 등록·descriptor round-trip·sealed tie-in·정직 메타 |
| `scripts/list_env_tiers.py` | 신규 | 낮음(데모) | 티어 목록·난이도 메타 출력 + 커스텀 등록 데모 + 정직-scope 캡션 |

기존 파일 **수정 없음** — 순수 추가(additive). `critter_env`/`eval_harness` 공개 API만 소비.

### 영향 범위 (import 그래프)

- `env_tier.py` → `critter_gym.envs.critter_env`(CritterEnv), `critter_gym.eval_harness`(SealedEvalSet,
  tie-in) 만. 역방향 의존 없음. eval_package **미import**.
- `test_env_tier.py` → `env_tier` + `critter_env`/`eval_harness`.
- `list_env_tiers.py` → `env_tier` (순수 stdlib).
- 기존 테스트/스크립트 회귀 표면 없음(additive-only).

## Step별 계획

**Step 1 (Red→Green): TierSpec + 검증 가드**
- `TierSpec`(직렬화 가능 dataclass/NamedTuple): `name`, knob dict(grid_size/num_gyms/max_steps/
  patch_radius/num_types/boss_hp/boss_atk/boss_def/commit_battles), `harder_knobs`(난이도를 올리는
  knob 목록), `difficulty_note`(실측/미측 정직 문자열). `validate_tier_spec(spec)` — 정상 범위
  가드(양수 grid/boss, patch_radius≥0, num_types≥2 등) + **winnability 정합**(boss_def 가 공격을
  전부 무력화하지 않음 등 명백-불가 조합 거부). 실패 시 `ValueError`(명확 메시지).
- 테스트: 유효 spec 통과 / 음수·비정상 knob 거부 / 명백-불가 조합 거부 / 메시지 명확.

**Step 2 (Red→Green): curated 프리셋 레지스트리**
- 내장 티어 2종 등록: `standard`(CritterEnv 기본치 = 무료 baseline 난이도), `hard`(실측 hard
  config: grid16 + 작은 고정 시야 + 긴 호라이즌; boss 는 winnable 유지). `register_tier(name, spec)`
  (idempotent, env_family 관례), `tier_names()`, `get_tier(name)`.
- 테스트: `tier_names()` 에 standard/hard 존재 / 프리셋이 검증 가드 통과 / 재등록 idempotent /
  다른 spec 재등록 거부 / 미지 티어 KeyError.

**Step 3 (Red→Green): env 팩토리 + 결정론**
- `make_tier_env(name, *, seed=None, **overrides) -> CritterEnv` — 티어 knob 으로 CritterEnv 생성,
  overrides 병합(검증 재적용). `tier_env_factory(name)` — thunk 반환(SealedEvalSet.env_factory 관례).
- 테스트: standard/hard 팩토리가 CritterEnv 생성 / 같은 seed reset 결정론 동일 / hard 가 standard 와
  실제 다른 knob(grid 등) / overrides 반영 + 잘못된 override 는 가드에 걸림.

**Step 4 (Red→Green): descriptor + sealed tie-in + 정직 메타**
- `TierSpec.to_json()`/`from_json()` round-trip. `sealed_config(name) -> dict` — 티어 knob 중
  **`SealedEvalSet.__init__` 이 실제 받는 서브셋만** 전달(`num_types`/`commit_battles`/`max_steps`/
  `grid_size`/`boss_hp`/`boss_atk`/`boss_def`). `build_sealed(name, master_seed, **overrides) ->
  SealedEvalSet` (eval_harness 만 사용).
- **L1 SUGGEST 반영 — knob 서브셋 명시**: `SealedEvalSet` 은 `num_gyms`/`patch_radius` 를 받지
  않는다(생성자 확인). `sealed_config` 는 이 둘을 **의도적으로 드롭**하고 그 사실을 docstring 에
  규정 + 테스트로 고정한다. **정직성 함의**: `patch_radius`/`num_gyms` 는 난이도 레버이므로,
  `hard` 티어의 sealed 변형은 full tier env 보다 **덜 어려울 수 있다** — `sealed_config`/
  `build_sealed` docstring 과 데모가 "sealed 변형은 SealedEvalSet 지원 knob 만 반영; 드롭된
  난이도 레버(patch_radius/num_gyms)는 sealed 에 미반영"을 명시(측정 없는 난이도 주장 방지).
- 테스트: descriptor round-trip / `difficulty_note` 가 실측 근거를 담고 "SOTA/recurrent open" 명시
  (문자열 포함 assert) / `build_sealed` 가 hard 티어의 지원 knob(grid_size/boss_* 등)을 sealed 로
  전달(일치) / **`sealed_config` 결과에 `num_gyms`/`patch_radius` 키가 없음**(드롭 규칙 고정) /
  드롭 사실이 docstring/note 에 문자열로 존재.

**Step 5 (데모): `scripts/list_env_tiers.py`**
- 내장 티어 목록 + 각 티어의 난이도 메타(harder_knobs, difficulty_note) 출력 → 커스텀 티어 등록
  데모(검증 통과 1건 + 거부 1건) → hard 티어로 env 1스텝 smoke + `build_sealed` 로 sealed config
  출력. **정직-scope 캡션**(실측 난이도 vs open 항목) 명시. build_site 규율(순수 + main() + stdout).

## 검증 방법

- `.venv/bin/python -m pytest tests/test_env_tier.py -q` 전부 green.
- 전체 스위트 회귀 0 (현재 baseline 확인 후 +신규). report 에 숫자 기록.
- `.venv/bin/python scripts/list_env_tiers.py` 무오류 실행 + 정상/거부 케이스 + 정직-scope 캡션.
- `ruff check` / `mypy src/critter_gym/env_tier.py` 통과.

## 리스크

| 리스크 | 완화 |
|---|---|
| **난이도 과대표현** — `hard`를 "SOTA 에도 hard"로 오인 판매 | `difficulty_note`·docstring·데모에 "실측=feedforward PPO ~11–16% of oracle(grid16); SOTA/recurrent=open" 3중 명시. 측정치만 주장. |
| winnability 미보장 — hard 가 oracle 도 못 푸는 unfair 난이도 | 검증 가드가 명백-불가 조합 거부 + hard 프리셋은 실측상 oracle winnable(2.81) 유지. (단 가드는 정적 sanity — 완전 winnability 증명 아님을 note 에 명시.) |
| cross-branch 의존 (#4 eval_package) | eval_package **미import**. eval_harness(main) 의 SealedEvalSet 만 tie-in. |
| **sealed 변형 난이도 손실** — SealedEvalSet 이 patch_radius/num_gyms 미지원(생성자 확인) → hard sealed 가 full tier 보다 덜 어려울 수 있음 | `sealed_config` 가 지원 서브셋만 전달·드롭 knob 을 docstring/note/데모에 명시. 측정 없는 난이도 주장 금지(정직). SealedEvalSet 확장은 후속 task(스코프 밖). |
| 커스텀 티어 검증 우회 | `make_tier_env`/`register_tier` 가 항상 `validate_tier_spec` 재적용. 테스트가 우회 부재 확인. |
| stacked-PR 함정(#94 미머지) | 본 브랜치는 main 기준(#94 무관). 단독 PR. |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/env_tier.py` 신규 — `TierSpec`(+`to_json`/`from_json`), `validate_tier_spec`,
   `register_tier`/`tier_names`/`get_tier`, `make_tier_env`/`tier_env_factory`, `sealed_config`/
   `build_sealed` 공개 API. stdlib-only, 신규 의존성 0, eval_package 미import.
2. **curated 프리셋**: `standard`(기본치) + `hard`(실측 hard config) 내장 등록, 둘 다 검증 가드 통과.
3. **검증 가드**: 비정상 knob(음수·비상식) 및 명백-불가(unwinnable) 조합을 `validate_tier_spec`가
   `ValueError`로 거부. `make_tier_env`/`register_tier`가 항상 가드 재적용(우회 없음).
4. **결정론·구별**: 같은 seed 로 tier env reset 결정론 동일; `hard`가 `standard`와 실제 다른 knob;
   overrides 반영 + 잘못된 override 거부.
5. **정직 메타**: `hard`의 `difficulty_note`가 실측 근거(feedforward PPO ~11–16% of oracle, oracle
   winnable)를 담고 "SOTA/recurrent 난이도=open(미측정)"을 명시(테스트가 문자열 포함 검증).
6. **sealed tie-in**: `build_sealed(name, master_seed)`가 티어 knob 중 `SealedEvalSet` 지원
   서브셋(grid_size/num_types/max_steps/boss_*/commit_battles)만 전달(일치)하고, `sealed_config`가
   `num_gyms`/`patch_radius`를 **드롭**함을 docstring·테스트로 규정. 드롭된 난이도 레버가 sealed 에
   미반영됨을 정직 명시. descriptor `to_json/from_json` round-trip.
7. `tests/test_env_tier.py` 신규 — AC1–6 커버, 전체 스위트 회귀 0.
8. `scripts/list_env_tiers.py` — 티어 목록·난이도 메타·커스텀 등록(통과+거부)·정직-scope 캡션 무오류.
9. **정직성**: 난이도 주장이 실측 한정 + open 항목 명시(코드·데모). CHANGELOG 1줄 entry.
