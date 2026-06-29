---
slug: inference-telemetry
initiative: eval-product
status: active
started: 2026-06-29
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

# 직접 추론 메트릭 — super-effective 무브 사용률 (attrition confound 우회)

> 작성일: 2026-06-29 | 상태: 계획 | 이니셔티브: eval-product (M5)

## 목표

probe 여정으로 확인: 현 전투는 `damage=max(1,...)`라 **살아남으면 중립 무브 attrition으로 이김** →
gym-clear 기반 inference_score는 "추론 필수 + 학습 가능" sweet spot이 노브로 안 잡힘(전투 *모델* 변경은
벤치마크 정의 변경=사람 게이트). **대안(자율안전)**: env를 안 바꾸고, **전투에서 agent가 숨은 타입표를
추론해 super-effective 무브를 찾아 쓰는가**를 *직접* 측정한다 — 이기든 지든, attrition과 무관하게 *추론
행위 자체*를 잼.

> **메트릭**: `super_effective_rate` = (agent의 battle move-결정 중 super-effective[eff>1.0]인 비율).
> oracle(타입표 앎)≈높음 / random≈우연 수준 / chart-blind LLM이 그 사이 어디 → "추론해 exploit하는 정도".
> **read-only**: env._battle 상태 + chart를 *읽기만* 함(env 무변경 → parity·baseline·obs·reward 불변).

**M5-EC1 기여**: 승리(attrition 오염)와 분리된, *추론 그 자체*의 verifiable 신호 — 고객용 KPI를 보강.

## 선행 조건

- #5~#11 done(main `4c6edc3`). `score_agent`/`SealedEvalSet`/`Agent`/`reference_arm` 존재. 498 tests green.
- battle API(확인): `env._battle.state.active(Side.A).moves[i].type`, `active(Side.B).types`,
  `env._battle.chart.multi_effectiveness(move_type, defender_types)`; action 0–3 → move `min(action, len(moves)-1)`.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/eval_harness.py` | `InferenceTelemetry(NamedTuple)`(super_effective_rate, n_battle_moves) + `score_inference_telemetry(submission, sealed)` — 에피소드 돌며 battle move-결정마다 chosen move의 eff>1.0 여부 read-only 집계. `score_agent`/`_play_once` 무변경(별도 함수) | 중 — 신규 read-only 경로 |
| `scripts/llm_eval_run.py` | `--telemetry` 플래그 — LLM + oracle/random 앵커의 super_effective_rate 출력(추론 직접 신호) | 저 |
| `tests/test_eval_harness.py` | telemetry: oracle 높음·random∈[0,1]·결정론·n_moves>0·0-battle 가드 | 저 |

### 영향 범위

- env 무변경(읽기만) → JAX parity·기존 baseline·obs/reward 전부 불변. `score_agent` 경로 byte-identical.
- 신규 함수만 추가 — 기존 호출부 무영향.

## Step별 계획

1. **telemetry 함수** — `play`-스타일 루프(기존 `_play_once` 미러, 단 reset 훅도 호출): 각 스텝에서 env가
   battle이고 action∈{0..3}이면, `env._battle`의 active A moves·active B types·chart로 `eff>1.0` 판정,
   (se_hits, n_moves) 누적. action 4(switch/commit-cycle)·5(pass)는 move 아님 → 제외. 에피소드/seed 합산
   → `super_effective_rate = se_hits / max(1, n_moves)`.
2. **러너 `--telemetry`** — 미지정 시 기존 출력 불변. 지정 시 submission + `reference_arm("oracle")`·random
   anchor의 SE-rate 출력 + "추론 직접 신호(승리와 분리)" 설명.
3. **테스트** — oracle SE-rate 높음(≥0.5; 타입표 exploit) / random∈[0,1] / 같은 submission+seed 결정론 /
   battle 발생 시 n_battle_moves>0 / 전투 0회 agent(항상 Wait)는 rate 0.0(div 가드).
4. **무회귀** — 전체 pytest green, `score_agent` 수치 불변, mypy·ruff·build clean.

## 검증 방법

- mypy·ruff·pytest(.venv)·build clean. oracle/random anchor로 SE-rate 의미 검증(LLM 불요).
- **실측(probe)는 후속** — `--telemetry`로 LLM SE-rate 측정은 별도. 결과 숫자는 acceptance 아님(메트릭 메커니즘만 게이트).

## 리스크

- **메트릭 해석 한계**: SE-rate는 *exploit 빈도*이지 "추론했다"의 완전 증명 아님(우연 SE 가능) — oracle/random
  앵커 대비로 읽고, 단일 config·proxy 경계 동반. report 명시.
- **read-only 규율**: env 내부(`_battle`)를 *읽기만* — 절대 변경 금지(변경 시 parity 깨짐). 테스트로 score_agent 불변 고정.
- **과대 금지**: 높은 SE-rate라도 "푼다"로 reframe 금지 — exploit 신호일 뿐. 점수 보장 아님.

## Acceptance Criteria (G1 통과 시 freeze)

- [ ] AC1: `InferenceTelemetry`(super_effective_rate, n_battle_moves) + `score_inference_telemetry(submission, sealed)`가
  battle move-결정마다 chosen move의 eff>1.0을 read-only 집계해 SE-rate를 반환(action 4/5 제외, 0-move 시 0.0 가드).
- [ ] AC2: env 무변경(read-only) — `score_agent`/scripted 수치 **byte-identical**(테스트로 고정).
- [ ] AC3: oracle SE-rate가 높고(타입표 exploit, ≥0.5) random은 [0,1]이며, 같은 submission+seed에 결정론.
- [ ] AC4: `llm_eval_run.py --telemetry`가 SE-rate(submission + oracle/random 앵커)를 출력, 미지정 시 기존 경로 불변.
- [ ] AC5: 무회귀 — 전체 pytest green, mypy·ruff·build clean. 정직 경계(exploit 신호≠추론 증명·점수 보장 아님·read-only) 명시.
