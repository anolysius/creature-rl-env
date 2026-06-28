---
slug: inference-score-metric
initiative: eval-product
status: active
started: 2026-06-28
acceptance_freeze: true
domains: [agents]
task_type: env
mode: standard
scope_paths:
  - src/critter_gym/eval_harness.py
  - scripts/llm_eval_run.py
  - tests/test_eval_harness.py
extracted_to: []
supersedes: []
---

# inference score — 고객용 moat 지표 (오염 불가 봉인 eval의 in-context 추론 정량화)

> 작성일: 2026-06-28 | 상태: 계획 | 이니셔티브: eval-product (M5)

## 목표

고객(프런티어 랩/RL 연구자)에게 파는 희소재 = **"외울 수도 오염될 수도 없는, 숨은 규칙을 in-context로
추론해야만 풀리는 eval"**. 이를 *정량 지표*로 만든다:

> **inference score = (submission − type_blind) / (oracle − type_blind)**, [0,1] 클램프.
> `0` = 규칙 모르는 baseline(type_blind) 수준 / `1` = 규칙 아는 expert(oracle) 수준.

probe 진단으로 확정한 사실(scout, 무료 scripted): 적절한 난이도 밴드에서 **oracle 100% vs type_blind
50%** — 이 gap이 "숨은 타입표 추론" 능력의 측정 축. type_blind는 표를 모르고 치므로 floor, oracle은
표를 알아 ceiling. 그 사이 어디에 LLM이 떨어지는지가 **게이밍·암기 불가능한 능력 신호**.

또한 현 `SealedEvalSet`은 grid_size·boss 수치를 노출 안 해(grid10·boss120/12/12 고정) LLM이 *항법*에서
막히거나 전투가 2턴이라 *학습 불가*였다. **config 노브**를 열어 navigable + inference-gated + 학습 여유
있는 demonstrator config(예: grid5·num_types3·boss140/6/18)를 봉인 set으로 타깃 가능하게 한다.

**M5-EC1 직접 기여**: "비공개 held-out eval"의 *가치 명제*(un-gameable 능력 측정)를 고객이 보는 한 숫자로.

## 선행 조건

- #5~#7 done(main `295f624`). `SealedEvalSet`/`Scorecard`/`score_agent`/`LLMAgent`/`StatefulLLMAgent`,
  `scripts/llm_eval_run.py`(oracle·type_blind·LLM 3-arm 출력) 존재. 484 tests green.
- scout 근거(무료 scripted, 6 held-out seeds): boss(140/6/18)·grid5·types3 → oracle 1.00 / type_blind
  0.50 / 생존 ~5턴. 원본 boss(120/12/12)도 oracle 1.00 / type_blind 0.50이나 2턴(학습 빠듯).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/eval_harness.py` | `SealedEvalSet`에 `grid_size`·`boss_hp`·`boss_atk`·`boss_def` 노브(기본=현 CritterEnv 기본값 → byte-identical) + env_factory 전달. `Scorecard`에 `inference_score: float` 필드 + `score_agent`가 계산(oracle≤type_blind면 0). | 중 — core, 단 기본값 무회귀 |
| `scripts/llm_eval_run.py` | `--grid-size`·`--boss-hp/atk/def` CLI + **고객용 출력**(oracle/type_blind/LLM 3-arm + inference_score headline + demonstrator preset 문서) | 저 |
| `tests/test_eval_harness.py` | inference_score 계산(경계: 0·1·중간·oracle≤tb→0) + SealedEvalSet 노브 전달 + 기본값 무회귀 | 저 |

### 영향 범위

- `Scorecard`는 NamedTuple → 필드 *추가*. 기존 필드 순서 보존하고 **끝에 추가**(기존 positional 사용처 점검;
  현재 모두 keyword 생성이면 안전). 기존 호출부/테스트 무회귀 확인.
- `SealedEvalSet` 신규 노브 기본값 = CritterEnv 기본(grid10·boss120/12/12) → 기존 봉인 set byte-identical.

## Step별 계획

1. **SealedEvalSet 노브** — `__init__`에 `grid_size=10, boss_hp=120, boss_atk=12, boss_def=12`(전부 키워드,
   기본=CritterEnv 기본). `env_factory`가 CritterEnv에 전달. 양수/유효성 검증.
2. **Scorecard.inference_score** — NamedTuple 끝에 `inference_score: float` 추가. `score_agent`에서
   `(mean_gyms − type_blind_gyms) / (oracle_gyms − type_blind_gyms)` 계산, 분모≤0이면 0.0, [0,1] 클램프.
   기존 `frac_of_oracle` 등 유지.
3. **러너 고객 출력** — `llm_eval_run.py`에 노브 CLI + 출력에 "Inference score: X.XX (0=no-knowledge
   baseline, 1=expert) — un-gameable in-context inference on a sealed never-seen world" headline +
   demonstrator preset(grid5·types3·boss140/6/18) docstring 안내.
4. **테스트** — inference_score: mean=tb→0, mean=oracle→1, 중간→0.5 근처, oracle≤tb→0(분모 가드);
   SealedEvalSet grid_size/boss 노브가 env_factory 산물에 반영; 기본값 시 기존 수치 byte-identical.
5. **선택 재측정(probe)** — demonstrator config에서 oracle/type_blind/LLM 3-arm → 첫 inference_score
   실측. 결과 숫자는 acceptance 아님(지표 *메커니즘*만 게이트); 나오면 그대로 기록, reframe 금지.

### 구현 세부 (L1 qa-verifier SUGGEST 반영)

- **AC1 env_factory 바인딩**: `SealedEvalSet.env_factory()`의 lambda가 `CritterEnv(commit_battles=…,
  vary=True, num_types=…, max_steps=…, grid_size=self.grid_size, boss_hp=self.boss_hp,
  boss_atk=self.boss_atk, boss_def=self.boss_def)`로 전달. CritterEnv가 이미 받는 동명 파라미터에 1:1 매핑.
- **AC4 CLI**: `llm_eval_run.py` argparse에 `--grid-size`(int, 기본 10)·`--boss-hp`(기본 120)·
  `--boss-atk`(기본 12)·`--boss-def`(기본 12) 추가, `SealedEvalSet(...)`에 전달. 출력은 기존 3-arm 표에
  한 줄 추가: `Inference score: {card.inference_score:.2f}  (0 = no-knowledge baseline / 1 = expert)` +
  한 줄 설명(un-gameable in-context inference on a sealed never-seen world). demonstrator preset은 docstring에
  `--grid-size 5 --num-types 3 --boss-hp 140 --boss-atk 6 --boss-def 18` 예시로 안내(플래그 조합, 코드 분기 없음).

## 검증 방법

- mypy·ruff·pytest(.venv)·build clean. 기본 SealedEvalSet `score_agent` 수치 byte-identical(기존 테스트 green).
- inference_score 경계 property 테스트.

## 리스크

- **NamedTuple 필드 추가 호환**: positional 사용처가 있으면 깨질 수 있음 — 끝에 추가 + 사용처 점검으로 차단.
- **지표 과대 해석 금지**: inference_score는 *특정 config*에서의 신호이지 절대 능력치 아님 — config(난이도
  밴드·oracle proxy·단일 seed-set) 동반 보고. type_blind를 floor로 쓰는 정당성(규칙 모름)도 명시.
- **점수 보장 아님**: 지표는 도구 — LLM이 높게 나온다고 보장 안 함(낮으면 낮은 대로 정직 기록).
- **demonstrator config는 데모**: 봉인/오염가드 메커니즘은 그대로지만 grid5·1gym은 *시연용*이지 제품
  난이도 표준 아님(별도 사람/전략 게이트) — 명시.

## Acceptance Criteria (G1 통과 시 freeze)

- [ ] AC1: `SealedEvalSet`이 `grid_size`·`boss_hp`·`boss_atk`·`boss_def` 노브를 받아 `env_factory`가 반영하고,
  기본값(grid10·boss120/12/12)은 기존과 **byte-identical**(기존 score_agent 수치 불변).
- [ ] AC2: `Scorecard`에 `inference_score` 필드가 있고 `score_agent`가 `(mean−type_blind)/(oracle−type_blind)`로
  계산하며 [0,1] 클램프, 분모≤0(oracle≤type_blind)이면 0.0.
- [ ] AC3: inference_score 경계가 테스트로 고정 — submission=type_blind→0, =oracle→1, 중간→사이값, 분모 가드.
- [ ] AC4: `llm_eval_run.py`가 노브 CLI + oracle/type_blind/LLM 3-arm + inference_score를 고객용으로 출력.
- [ ] AC5: 무회귀 — 기본 SealedEvalSet 수치 byte-identical, 전체 pytest green, mypy·ruff·build clean.
  정직 경계(지표=특정 config 신호·점수 보장 아님·demonstrator=시연용) docstring/report 명시.
