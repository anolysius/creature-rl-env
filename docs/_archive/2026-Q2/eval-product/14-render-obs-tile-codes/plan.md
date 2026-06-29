---
slug: render-obs-tile-codes
initiative: eval-product
status: active
started: 2026-06-29
acceptance_freeze: true
mode: standard
domains: [agents, rl-env]
scope_paths:
  - src/critter_gym/llm_eval.py
  - tests/test_llm_eval.py
extracted_to: []
supersedes: []
---

# render_obs 타일-코드 버그 수정 — LLM이 보던 뒤섞인 지도 바로잡기 (LLM floor root-cause 후보)

> 작성일: 2026-06-29 | 상태: 계획

## 목표

`render_obs`(LLM이 소비하는 텍스트 맵)의 글리프/살라언스 코드가 env가 실제 emit하는
`local_patch` 코드와 **어긋나** 있어, LLM이 체계적으로 뒤섞인 지도를 본다. 이를 바로잡는다.

**확정된 불일치 (런타임 검증 완료):**
- env (`critter_env.py:53`): `_PATCH_EMPTY, _PATCH_CREATURE, _PATCH_GYM = 0, 1, 2`,
  `local_patch = Box(0, 2)`.
- `render_obs` (`llm_eval.py:50`): `_TILE_GLYPHS = {0:".", 1:"#", 2:"C", 3:"G"}` + 살라언스가
  gym=code 3, creature=code 2 를 가정.
- 결과: env **생물(1) → "#"벽**, env **체육관(2) → "C"생물**, **"G"는 절대 안 뜸**(env가 3을 안 냄).

**왜 중대한가:** scripted oracle/type_blind는 raw obs를 읽어 정상(체육관 클리어)인데, **LLM만**
`render_obs` 텍스트를 소비해 체육관을 생물로/생물을 벽으로 본다 → LLM이 체육관을 못 찾고 Catch
루프. 이는 task #6·#7이 묘사한 증상과 정확히 일치하며, **LLM 측정 floor의 root-cause 후보**다.

**왜 안 잡혔나:** `test_llm_eval.py`의 합성 obs(`_make_obs`)가 env 실제 코드가 아니라 render_obs의
*틀린 가정*(gym=3, creature=2)을 그대로 써서 테스트가 통과 — env 출력과 대조한 적 없는 사각지대.

**전진하는 마일스톤**: M3 benchmark-reliability — LLM eval의 신뢰성(렌더러가 env를 정직 반영).

## 선행 조건

- 영향: `render_obs`를 쓰는 건 LLM 에이전트 경로뿐. scripted arm은 raw obs → `score_agent` 수치
  **byte-identical**(렌더러 미사용).
- env·obs 스키마·전투 무변경. 본 task는 렌더러↔env 코드 정합만 고친다.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/llm_eval.py` | `_TILE_GLYPHS`·범례·살라언스 코드(gym 3→2, creature 2→1)를 env 코드에 맞춤 | medium |
| `tests/test_llm_eval.py` | (1) 버그를 인코딩한 기존 합성 테스트의 코드 수정 (2) **실 env obs 대조 회귀 테스트 신규** | low |

### 영향 범위

- `render_obs`는 텍스트만 생성 → `score_agent`/scripted 수치 불변.
- 기존 테스트 중 wrong-code를 쓰던 것(`test_render_gym_salience_and_on_gym_flag`=patch 3,
  `test_render_creature_salience`=patch 2)은 수정 후 깨지므로 올바른 코드로 갱신.

## Step별 계획

1. **실 env 회귀 테스트 (Red)**: 합성이 아닌 **실제 `CritterEnv` obs**로, env가 emit하는 코드를
   `render_obs` 글리프/살라언스와 대조하는 테스트. 핵심: env의 `_PATCH_CREATURE`/`_PATCH_GYM`
   상수를 import해 render_obs가 그 코드를 각각 "C"/"G"로 렌더하고, 살라언스(visible/on-tile)도
   그 코드로 발화함을 단언. (현재는 실패해야 함.)
2. **수정 (Green)**: `_TILE_GLYPHS = {0:".", 1:"C", 2:"G"}`, 범례에서 "#=wall" 제거, 살라언스
   `_nearest_in_view(patch, 2)`=gym·`_nearest_in_view(patch, 1)`=creature, `center==2`=on-gym·
   `center==1`=on-creature. 가능하면 env 상수를 import해 **드리프트 재발 방지**(SSOT).
3. **기존 테스트 갱신**: wrong-code 합성 테스트를 올바른 env 코드로 수정.
4. **무회귀 확인**: scripted `score_agent` 수치 byte-identical(렌더러 미사용) 확인.

## 산출/후속 (deliverables)

- **커밋 단위**: 작은 정합 수정이라 단일 원자 커밋(Red 테스트 + Green 수정 + 기존 테스트 갱신 함께).
- **재측정 follow-up 진입조건**: 본 fix가 **merge된 뒤**, 별도 후속으로 `--battle-memory`(또는
  무상태) demonstrator probe를 재실행해 floor가 풀리는지 정직 기록. 본 task의 acceptance 아님
  (정합 수정까지만) — 재측정은 사람/비용 게이트.

## 검증 방법

- `python -m pytest tests/test_llm_eval.py -q` (신규 회귀 + 갱신 통과).
- 전체 스위트 그린(회귀 0), `mypy src` / `ruff check .` clean.
- 실 env sanity: 체육관/생물이 시야에 있는 obs를 render → "G"/"C"가 올바른 위치에 뜸.

## 리스크

| 리스크 | 완화 |
|---|---|
| 살라언스/center 분기 코드 누락 수정 | grep로 모든 `== 2`/`== 3`/`patch, 2`/`patch, 3` 점검 + 실 env 테스트가 잡음 |
| 수정 후에도 floor 유지 가능 | 결과 reframe 금지 — 고친 뒤 재측정해야 floor 풀림 확정. 본 task는 *정합 수정*까지; 재측정은 후속 |
| env 상수 import 결합 | private(`_PATCH_*`) import가 꺼림칙하면 llm_eval에 매칭 상수 정의 + 실 env 대조 테스트로 SSOT 강제 |

## Acceptance Criteria (G1 통과 시 freeze)

- [ ] AC1: 회귀 테스트가 env의 `_PATCH_CREATURE`/`_PATCH_GYM` **상수를 import**해 `render_obs`의
      글리프/살라언스가 그 코드와 일치함을 단언 — SSOT 대조로 드리프트 재발을 *테스트가* 차단
      (구현자 재량 아님). 실제 `CritterEnv` obs도 함께 렌더해 "G"/"C"가 맞게 뜸을 단언(수정 전 실패).
- [ ] AC2: `_TILE_GLYPHS`·범례·살라언스 코드(gym/creature)·center 분기가 env 코드에 맞게 수정됨.
- [ ] AC3: 버그를 인코딩했던 기존 합성 테스트가 올바른 env 코드로 갱신됨.
- [ ] AC4: scripted `score_agent` 수치 byte-identical(렌더러 미사용 — 무회귀).
- [ ] AC5: 전체 스위트 그린(회귀 0) + `mypy src` / `ruff check .` clean.
- [ ] AC6: 정직 경계 — 본 task는 렌더러↔env *정합 수정*이며, "floor가 풀린다"는 재측정으로
      확인할 후속 가설임을 plan/report에 명시(결과 reframe 금지).
