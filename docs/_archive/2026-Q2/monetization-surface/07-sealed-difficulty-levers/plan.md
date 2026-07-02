---
slug: sealed-difficulty-levers
initiative: monetization-surface
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/eval_harness.py
  - src/critter_gym/eval_package.py
  - src/critter_gym/env_tier.py
  - tests/test_eval_harness.py
  - tests/test_eval_package.py
  - tests/test_env_tier.py
  - docs/reference/env-tiers.md
  - docs/reference/sealed-eval-packaging.md
  - docs/reference/tier-eval-bundle.md
extracted_to: []
supersedes: []
mode: standard
task_type: general
---

# 정직성 갭 수리 — sealed eval 이 난이도 레버(patch_radius/num_gyms)를 담게 (monetization-surface #7)

> 작성일: 2026-07-01 | 상태: 계획 | 추진 EC: **M5-EC1/EC2 정직성 경화** (우리가 남긴 follow-up)

## 목표

#5(env_tier) 리뷰에서 우리가 **직접 문서화한 정직성 부채**를 갚는다: `SealedEvalSet` 이
`patch_radius`/`num_gyms` 를 받지 못해 `env_tier.build_sealed` 가 이 둘을 **드롭**하고, 그래서
이 레버를 튜닝한 티어의 sealed 변형이 full 티어 env 보다 덜 어려울 수 있다(현재 `sealed_config`
docstring·`env-tiers.md`·`tier-eval-bundle.md` 가 이 한계를 명시). 이 task 는 `SealedEvalSet` 이
두 레버를 담게 하여 **sealed 를 티어에 충실하게** 만들고, **커밋먼트에 묶어** rug-pull 방어까지
확장한다.

**정직한 현황(코드로 확인, 반드시 plan 에 명시)**: 내장 `hard` 티어의 값은 `patch_radius=2`,
`num_gyms=3` 으로 **CritterEnv/SealedEvalSet 기본값과 동일**하다. `SealedEvalSet.env_factory` 가
두 knob 을 안 넘겨도 CritterEnv 가 같은 기본값을 쓰므로 — **내장 hard 의 sealed 는 이미 충실**하다
(드롭이 무해). 갭이 실제로 무는 것은 이 레버를 **비-기본값으로 튜닝한 custom 티어**뿐이다. 따라서
이 task 의 가치는 (a) custom 티어의 난이도 레버를 sealed 가 충실히 반영, (b) 두 레버를 커밋먼트에
바인딩(swap 방어), (c) 문서의 "sealed 가 덜 어려울 수 있음" 경고를 **제거/축소**(더 이상 참이 아님).
과대표현 없이 정확히 이 범위만 주장한다.

## 선행 조건

- `src/critter_gym/eval_harness.py` — `SealedEvalSet.__init__`/`env_factory`(현재 patch_radius/
  num_gyms 미전달), `_eval_seeds`/`_offset`(seed 유도 — 이 변경과 독립).
- `src/critter_gym/eval_package.py` — `seed_commitment` material(현재 두 레버 미포함).
- `src/critter_gym/env_tier.py` — `_SEALED_KNOBS`/`_SEALED_DROPPED`/`sealed_config`/`build_sealed`.
- **하위호환 필수**: 신규 param 기본값 = 현재 CritterEnv 기본값(patch_radius=2, num_gyms=3) →
  기존 호출·scoring **byte-identical**. 커밋먼트 값은 material 확장으로 바뀌나 golden 하드코딩
  없음(확인) → 결정론/불일치 테스트 무영향.
- stdlib만. 신규 의존성 0.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 종류 | 영향도 | 변경 요지 |
|---|---|---|---|
| `src/critter_gym/eval_harness.py` | 수정 | 중(핵심 moat, 하위호환 주의) | `SealedEvalSet` 에 patch_radius/num_gyms param + env_factory 전달 |
| `src/critter_gym/eval_package.py` | 수정 | 중 | `seed_commitment` material 에 두 레버 추가(바인딩) |
| `src/critter_gym/env_tier.py` | 수정 | 낮음 | `_SEALED_KNOBS` 에 두 레버 추가, `_SEALED_DROPPED`→(num_creatures,), docstring |
| `tests/test_eval_harness.py` | 수정 | 낮음 | sealed env 가 patch_radius/num_gyms 반영 + 기본값 하위호환 |
| `tests/test_eval_package.py` | 수정 | 낮음 | 두 레버 다르면 커밋먼트 다름(바인딩) |
| `tests/test_env_tier.py` | 수정 | 낮음 | drop 테스트 갱신(포함으로), custom 티어 레버가 sealed 도달 |
| `docs/reference/env-tiers.md` | 수정 | 낮음 | sealed 드롭 규칙 → num_creatures 만; "덜 어려움" 경고 축소 |
| `docs/reference/sealed-eval-packaging.md` | 수정 | 낮음 | 커밋먼트 material 목록 갱신 |
| `docs/reference/tier-eval-bundle.md` | 수정 | 낮음 | 바인딩 계약 note(레버 포함) 갱신 |

### 영향 범위

- `SealedEvalSet` 소비처: `eval_package`(build_manifest/issue_certificate), `env_tier.build_sealed`,
  `eval_marketplace`(간접), `inference_baseline`/reproduce_results, 다수 테스트. 기본값 보존으로
  회귀 0 목표(byte-identical). 커밋먼트 값 변화는 golden 부재로 무영향.

## Step별 계획

**Step 1 (Red→Green): SealedEvalSet 이 두 레버를 담는다**
- `SealedEvalSet.__init__` 에 `patch_radius: int = 2`, `num_gyms: int = 3` 추가(+양수/음이 아님
  검증은 CritterEnv 에 위임하거나 최소 sanity). `env_factory` 가 CritterEnv 에 두 값 전달.
- 테스트(test_eval_harness): 기본값 SealedEvalSet 의 env 가 patch_radius=2/num_gyms=3(하위호환) /
  비-기본 patch_radius/num_gyms 지정 시 env 가 그 값 사용(반영 확인).

**Step 2 (Red→Green): 커밋먼트 바인딩 + 매니페스트 공개 노출**
- `eval_package.seed_commitment` material 에 `patch_radius`, `num_gyms` 추가.
- **L1 SUGGEST 반영 — 구매자-대면 노출**: `EvalManifest` 공개 config 필드(grid_size/boss_*/
  num_types/max_steps/commit_battles) 옆에 `patch_radius`, `num_gyms` 추가 + `build_manifest`
  payload 에 포함. 이유: 커밋먼트로 swap 은 막아도 매니페스트에 두 레버가 없으면 구매자가 "무엇으로
  평가받는지" 모름 → 정직성 목표와 부분 상충. 매니페스트가 난이도 레버를 **투명하게 노출**해야 함.
- 테스트(test_eval_package): 두 레버만 다른 두 SealedEvalSet → 커밋먼트 다름(swap 검출) /
  매니페스트 JSON 에 patch_radius/num_gyms 존재(구매자 가시성) / 매니페스트에 여전히 비밀 seed 부재 /
  기존 결정론/불일치/no-leak/round-trip 테스트 무영향 확인.

**Step 3 (Red→Green): env_tier 가 레버를 드롭하지 않는다**
- `_SEALED_KNOBS` 에 `patch_radius`, `num_gyms` 추가. `_SEALED_DROPPED` → `("num_creatures",)`.
  `sealed_config`/`build_sealed` docstring 을 "이제 patch_radius/num_gyms 반영; num_creatures 만
  드롭(SealedEvalSet arg 아님)"으로 갱신.
- 테스트(test_env_tier): 기존 `test_sealed_config_drops_unsupported_knobs` 를 **포함 검증으로 갱신**
  (patch_radius/num_gyms 가 이제 cfg 에 존재) / `test_sealed_config_drops_num_creatures` 유지 /
  patch_radius/num_gyms 를 튜닝한 custom 티어의 `build_sealed` 가 그 값을 sealed 에 전달.

**Step 4 (문서): 정직성 note 갱신**
- `env-tiers.md`: "Sealed-eval tie-in — dropped knobs" 를 num_creatures 만 드롭으로, "덜 어려울 수
  있음" 경고를 **제거**(더 이상 참 아님) 하고 "patch_radius/num_gyms 이제 sealed 에 반영+커밋먼트
  바인딩"으로 대체.
- `sealed-eval-packaging.md`: 커밋먼트가 묶는 config 목록에 두 레버 추가.
- `tier-eval-bundle.md`: 바인딩 계약의 resolved-knob 목록에 두 레버 반영.

## 검증 방법

- `.venv/bin/python -m pytest -q` 전체 green, 회귀 0(baseline 592). 특히 기존 sealed/eval/env_tier/
  marketplace 테스트가 기본값 보존으로 통과.
- `ruff check` / `mypy src/critter_gym/eval_harness.py src/critter_gym/eval_package.py
  src/critter_gym/env_tier.py` 통과.
- 데모 `scripts/list_env_tiers.py`·`package_sealed_eval.py`·`tier_eval_bundle_demo.py` 무오류
  (기본값 보존 확인).

## 리스크

| 리스크 | 완화 |
|---|---|
| **하위호환 깨짐** — SealedEvalSet 소비처 회귀 | 신규 param 기본값=현 기본값 → byte-identical. 전체 스위트로 회귀 0 확인. |
| 커밋먼트 값 변화로 외부 기대 깨짐 | golden 하드코딩 없음(확인). 커밋먼트는 매번 재계산 — 결정론/바인딩 유지. prototype 범위. |
| 과대표현 — "이제 hard 가 더 어렵다" 오주장 | plan·문서에 "내장 hard 는 이미 충실(값=기본); 이 task 는 custom 티어 충실성+레버 바인딩" 정확히 한정. |
| 다파일 수정 회귀 표면 | 3 코어 모듈 수정이나 additive-값-보존 성격. 각 Step Red→Green + 전체 스위트. |

## Acceptance Criteria (G1 통과 시 freeze)

1. `SealedEvalSet` 이 `patch_radius`/`num_gyms` param 을 받고 `env_factory` 가 CritterEnv 에
   전달. 기본값(2, 3)에서 기존 동작 **byte-identical**(하위호환).
2. `seed_commitment` 이 patch_radius/num_gyms 를 material 에 포함 → 두 레버만 다른 sealed 는
   커밋먼트가 달라짐(swap/ rug-pull 방어 확장). **그리고** `EvalManifest`/`build_manifest` 가 두
   레버를 공개 필드로 노출(구매자가 난이도 레버를 투명하게 확인; 비밀 seed 는 여전히 미노출).
3. `env_tier` 의 `_SEALED_KNOBS` 가 patch_radius/num_gyms 포함, `_SEALED_DROPPED` = num_creatures
   만. `build_sealed` 가 튜닝된 두 레버를 sealed 에 전달; docstring 갱신.
4. **회귀 0**: 전체 스위트 592 → 592+/− 조정분 all pass(기본값 보존). ruff/mypy clean. 3 데모 무오류.
5. **정직성 문서 갱신**: env-tiers.md/sealed-eval-packaging.md/tier-eval-bundle.md 가 "이제 두 레버
   반영+바인딩; num_creatures 만 드롭"으로 갱신, "sealed 가 덜 어려울 수 있음" 경고 제거. 내장 hard
   는 이미 충실했음을 과대표현 없이 반영.
6. 관련 테스트(eval_harness/eval_package/env_tier) 가 AC1–3 을 커버. CHANGELOG 1줄 entry.
