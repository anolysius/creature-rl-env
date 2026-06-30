---
slug: matchup-validity
initiative: eval-product
status: active
started: 2026-06-30
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
scope_paths:
  - src/critter_gym/region.py
  - tests/test_region.py
extracted_to: []
supersedes: []
---

# eval-config matchup validity — 모든 procgen 세계가 "추론으로 exploit 가능한 super-effective 무브"를 보장

> 작성일: 2026-06-30 | 상태: 계획 | 마일스톤: eval 측정 validity (oracle = robust 변별자)

## 목표

`generate_region(vary=True)` 가 **배치하는 모든 gym boss 에 대해, 플레이어 party 가 strictly
super-effective(effectiveness > NEUTRAL) 한 무브 타입을 최소 하나 보유**하도록 보장한다.
즉 매 held-out 세계가 *추론으로 exploit 가능한 결정적 한 수*를 항상 갖게 해 oracle 이 robust 한
변별자가 되도록 한다 (현재는 유리한 일부 world 에서만 그러함).

이는 **procgen 생성 correctness 수정**이다(render_obs 타일-코드 버그 #14 와 동성격) — 전투 모델
재설계(=벤치마크 정의 변경=사람 게이트)가 아니다. 데미지 공식·obs/action 스키마·전투 economy
는 손대지 않는다. 오직 *어떤 boss 타입을 세계에 배치할지* 의 생성 필터만 좁힌다.

## 선행 조건 (재현된 증거)

`region.generate_region` (line 109–115) 의 `winnable` 필터:
```python
winnable = [t for t in active_types
            if any(chart.effectiveness(s, t) >= NEUTRAL for s in _STARTER_TYPES)]
```
- `_STARTER_TYPES = (FIRE, WATER, GRASS)` = party 의 무브 타입과 일치(각 starter 가 자기 타입 무브 1개).
- 버그: boss 타입 `t` 자신이 `_STARTER_TYPES` 에 포함 → `effectiveness(t, t) = NEUTRAL ≥ NEUTRAL`
  이 **항상 참** → num_types=3 에서 필터가 **사실상 no-op**(아무 타입도 배제 못 함).
- 결과: per-seed chart 가 transitive(a>b>c, a>c)일 때 최상위 타입 `a` 는 어떤 타입에도 안 짐 →
  party 에 `a` 를 super-effect 하는 무브 부재 → 그래도 boss 로 배치됨.
- oracle(`learnability._Arm`)은 `_favorable_type` 가 `None`(SE 타입 없음)이면 현재 생물로 그냥
  공격(neutral attrition) → super-effective 무브를 못 씀.

**재현 (확정)** — `SealedEvalSet(master_seed=20260627, n_worlds=N, num_types=3, grid_size=5,
boss_hp=140, boss_atk=6, boss_def=18)` 에 `score_inference_telemetry(reference_arm("oracle"))`:

| n_worlds | oracle SE-rate | n_moves |
|---|---|---|
| 1 | 1.000 | 4 |
| 2 | 1.000 | 18 |
| 3 | 1.000 | 12 |
| 4 | **0.055** | 274 |
| 6 | **0.227** | 172 |
| 8 | **0.115** | 391 |

→ "oracle 100%" 는 유리한 1–3 world 아티팩트. world 가 늘면 SE-무브 부재 world 가 섞여 SE-rate
붕괴 + n_moves 폭증(attrition grind). 이러면 추론 잘하는 LLM 과 못하는 LLM 이 변별 불가.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/region.py` | `winnable` 필터를 `>= NEUTRAL` → `> NEUTRAL` 로 좁히고 변수명/주석 갱신(`exploitable`), 빈-집합 가드 | **중** | vary=True 세계의 boss 타입 분포 변경. fixed(vary=False) 분기 무영향(M1 byte-identical). |
| `tests/test_region.py` | 생성 불변식 테스트 신규(모든 placed boss 에 SE 타입 존재) + 회귀 가드 | 중 | property-style, 다수 seed. |

### 영향 범위 (import 그래프)

- `region.generate_region(vary=True)` 출력 → `CritterEnv`(env reset) → `eval_harness`(SealedEvalSet,
  score_agent, score_inference_telemetry), `learnability`(reference arms), `llm_eval` 채점.
- **분포 변경의 의미**: held-out 세계 분포가 "SE-exploitable boss 만 배치"로 좁아짐. 이는 의도된
  validity 수정(render fix 와 동성격). 누수/결정론/seed-split 불변식은 보존(필터만 좁힘, seed→chart
  매핑·rng 소비 순서 영향 → §리스크 참조).
- fixed mode(vary=False, M1)는 `if vary:` 블록 밖 → **byte-identical 보존**.

## Step별 계획 (TDD: Red → Green → Refactor)

1. **Red** — `tests/test_region.py` 에 생성 불변식 테스트 추가(현재 실패):
   - `test_every_placed_boss_has_super_effective_party_type`: vary=True, num_types∈{3,4,6}, 다수 seed
     (train + heldout)에서 각 region 의 모든 `gyms` boss_type 에 대해
     `any(chart.effectiveness(s, boss) > NEUTRAL for s in _STARTER_TYPES)` 가 참.
   - `test_no_world_is_se_barren` (telemetry 수준): demonstrator config 로 oracle SE-rate 가
     n_worlds∈{1,2,3,4,6,8} 전부에서 붕괴하지 않음(floor 임계 — Green 후 실측해 정직 보정).
2. **Green** — `region.py` 필터를 `> NEUTRAL` 로 좁힘:
   - `winnable` → `exploitable` 로 명명, 주석을 "winnable" → "inference-exploitable(SE 보장)"로 정정.
   - 빈-집합 가드: `exploitable` 가 비면(이론상 num_types≥3 에서 도달 불가 — 증명은 주석) 명시
     `ValueError`(또는 안전 fallback) — silent 분포 왜곡 금지.
   - `_STARTER_TYPES` ↔ party 무브 타입 일치 불변식을 주석으로 박제(latent coupling 경고).
3. **Refactor** — 주석/docstring 의 "every gym is winnable" 서술을 "every gym is
   inference-exploitable(SE counter 보장)"로 정합. 중복 제거.

## 검증 방법

- `tests/test_region.py` 신규 불변식 테스트 통과.
- 재현 스크립트 재실행: oracle SE-rate 가 n_worlds∈{1,2,3,4,6,8} 에서 robust(붕괴 없음) +
  type_blind 대비 변별 band 유지(oracle − type_blind ≥ 마진).
- fixed mode 회귀: `generate_region(s, vary=False)` 출력 기존 테스트 byte-identical.
- 전체 스위트: `.venv/bin/python -m pytest -q` (baseline **514 passed, 2 skipped**) → 회귀 0 +
  신규 통과.
- `mypy src` · `ruff check .` clean.

## 리스크

| 리스크 | 완화 |
|---|---|
| 필터를 좁히면 vary 세계의 rng 소비/boss 분포가 바뀌어 *기존* region 스냅샷 테스트가 깨질 수 있음 | 기존 test_region 은 결정론·disjoint·chart-differ 만 검사(정확값 스냅샷 아님) → 통과 예상. 깨지면 의도된 분포 변경으로 테스트 기대 갱신(스냅샷 아닌 불변식 유지). |
| 빈 `exploitable` 집합 → `rng.choice(0)` 크래시 | num_types≥3 에서 토너먼트 in-degree 합 = C(n,2) ≥ n → 최소 1 타입은 누군가에게 짐 → exploitable 비공집합(증명 주석). 그래도 명시 가드 추가. |
| oracle SE-rate 가 100% 가 아닐 수 있음(commit-economy 로 cross-gym 챔피언 lock) | **정직 경계**: 본 task 의 hard 보장은 *generation 불변식*(SE 무브 존재)뿐. oracle 이 매번 SE 를 쓰는지는 전투 economy 속성(사람 게이트 영역). AC 는 "존재 보장 100% + SE-rate 붕괴 정지"로 정직 설정, "SE-rate=100%" 로 과대 설정 금지. |
| 분포 변경 = 벤치마크 정의 변경 아닌가? | 아니다 — boss *타입 배치 필터* correctness 수정(render fix 동성격). 데미지 공식·스키마·economy 불변. INITIATIVE 정직성 문화 준수. |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[hard, deterministic]** vary=True, num_types∈{3,4,6}, ≥40 seed(train+heldout)에서 생성된
   모든 region 의 모든 placed boss 타입에 대해 `any(chart.effectiveness(s, boss) > NEUTRAL for s in
   _STARTER_TYPES)` == True (SE counter 존재 보장). 신규 테스트로 검증.
2. **[quantitative]** demonstrator config(master_seed=20260627, grid5, types3, boss140/6/18)에서
   oracle SE-rate 가 n_worlds∈{1,2,3,4,6,8} **전부에서 붕괴하지 않음**(모두 ≥ Green 후 실측해 freeze
   할 floor, 단 ≥0.5 목표) **그리고** type_blind 대비 변별 band(oracle − type_blind) ≥ 0.3 유지.
   (정확 floor 는 Green 직후 실측 보정 — p-hacking 방지 위해 측정 전 "붕괴 정지 + band≥0.3" 골격 freeze.)
3. **[regression]** fixed mode(vary=False) byte-identical(M1 보존). 전체 pytest 회귀 0
   (514 passed 유지 + 신규 통과). mypy/ruff clean.
4. **[honesty]** report 에 "SE 무브 *존재* 보장이지 oracle 이 매번 SE 를 쓴다는 보장 아님"
   경계 명시. 전투 economy 재설계는 사람 게이트로 남김.
