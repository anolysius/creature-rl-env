---
slug: agentic-battle-memory
initiative: eval-product
status: active
started: 2026-06-29
acceptance_freeze: true
mode: standard
domains: [agents, rl-env]
scope_paths:
  - src/critter_gym/llm_eval.py
  - tests/test_llm_eval.py
  - scripts/llm_eval_run.py
extracted_to: []
supersedes: []
---

# 전투-결과를 기억하는 agentic 메모리 — 얇은 어댑터 confound 제거 + 공정 재측정 토대

> 작성일: 2026-06-29 | 상태: 계획

## 목표

봉인 eval에서 측정된 **chart-blind floor (inference_score 0.00)** 가 "프런티어 LLM이 숨은 차트를
추론 못 한다"는 *능력 verdict* 인지, 아니면 **어댑터가 추론 신호를 버려서** 생긴 *측정 아티팩트* 인지를
가르기 위해, LLM 에이전트의 메모리를 "두껍게" 만든다.

구체 confound (코드로 확인):
- `StatefulLLMAgent`는 `_history`에 `(_obs_summary, action)`만 누적하고,
  `_obs_summary`(`llm_eval.py:233-240`)는 **위치 + gyms** 만 담는다 — 전투에서 어떤 무브가
  적 hp를 얼마나 깎았는지(=효과성 신호)를 **구조적으로 버린다**.
- 그런데 `DEFAULT_SYSTEM`(task #7)은 LLM에게 "무브를 써보고 적 hp 감소를 *관찰·기억*해
  super-effective 무브를 찾으라"고 지시한다. **지시는 있는데 메모리가 그 신호를 못 받친다** —
  이 지시↔메커니즘 불일치가 "얇은 claude-cli 어댑터" confound의 정체다.

이 task는 전투 무브의 **관찰 가능한 결과(데미지·적 hp 변화)** 를 적 타입별로 누적해 프롬프트에
surface 하는 메모리를 추가한다. 그래야 이후 측정이 "LLM의 추론 능력"을 *공정하게* 재는 시험이 되지,
"추론 신호를 버린 메모리"의 아티팩트가 되지 않는다.

**전진하는 마일스톤**: M3 benchmark-reliability — EC4(arXiv writeup)가 보고할 headline 추론 측정의
confound를 제거(floor가 어댑터 탓이 아님을 입증하는 토대). eval-product 이니셔티브의
"적정 호라이즌 공정 재측정" 후속 라인(INITIATIVE.md "이후").

## 선행 조건

- 완료된 토대: #5 `StatefulLLMAgent` / #6 `render-obs-legibility` / #7 `battle-legibility` /
  #8 `inference-score-metric` / #10 `inference-score-rigor`(`classify_inference`) /
  #11 첫 robust 측정(0.00 floor) / #12 `inference-telemetry`(SE-move rate). 모두 archive.
- env·전투 모델·obs 스키마는 **무변경** (전투 `damage=max(1)` 재설계는 별도 사람 게이트 — 본 task 범위 밖).
- 채점(`score_agent`)·scripted arm 수치는 byte-identical 유지(어댑터만 변경).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/llm_eval.py` | 전투-결과 인지 메모리 추가 (신규 클래스 또는 `StatefulLLMAgent` 확장) | medium | env import 없음 (obs만 소비) |
| `tests/test_llm_eval.py` | 신규 메모리 동작·측정-무결성·무회귀 테스트 | low | unittest |
| `scripts/llm_eval_run.py` | 신규 에이전트를 러너 플래그로 노출 (`--battle-memory` 등) | critical(scripts/**) | stub 무회귀 |

### 영향 범위 (import 그래프)

- `llm_eval.py`는 `eval_harness.Agent` Protocol(`act(obs)->int` + 선택적 `reset()`)만 만족하면 됨 —
  `score_agent`는 duck-typing으로 호출하므로 채점부 변경 0.
- 러너는 `LLMAgent`/`StatefulLLMAgent`를 생성하는 분기만 가짐 → 신규 에이전트 분기 1개 추가.
- env·battle·spaces 무변경 → JAX 패리티 테스트 영향 0.

## Step별 계획

1. **관찰 결과 추출 (read-only)**: obs에서 전투 상태(`in_battle`, `enemy_hp`, `enemy_type`,
   `player_hp`)를 읽는 헬퍼. env 무변경 — obs에 이미 있는 필드만 소비(#12 telemetry와 동일 규율).
2. **전투-결과 메모리**: 직전 obs를 보관 → 직전 행동이 전투 공격무브(0-3)였고 현재도 같은 전투면
   `enemy_hp_delta = prev_enemy_hp - cur_enemy_hp`를 직전 무브에 귀속. 적 타입별
   `{enemy_type: {move: 최신 관찰 데미지}}` — **(타입, 무브)당 단일값 덮어쓰기**(리스트 누적 X).
   상한 = num_types × 4무브로 **결정론적 bounded**(토큰 폭증 불가).
3. **프롬프트 surface (측정-무결성 핵심)**: 누적표를 *원시 관찰* 로만 렌더 —
   "vs enemy type 3: move1→40dmg, move0→8dmg" 식. **"best move=1" 같은 추천/정답은 절대 넣지 않는다**
   (추천을 넣으면 추론을 어댑터가 대신 = 측정 무효화). 어떤 무브가 정답인지 LLM이 스스로 고르게 둔다.
4. **격리**: `reset()`이 전투 메모리를 clear(월드 간 누수 0). window/예산 경계도 bound.
5. **러너 노출**: `--battle-memory` 플래그로 신규 에이전트 선택. stub 경로 무회귀.
6. **무결성 가드 테스트**: surface 텍스트에 hidden type 이름/차트/정답-무브 라벨이 **없음** 을
   단언하는 테스트(벤치마크 정직성 회귀 방지).

## 검증 방법

- `python3 -m unittest discover -s tests -p 'test_llm_eval.py'` (신규 + 기존 무회귀).
- 전체 스위트 그린 유지(502 → +N, 회귀 0): `python3 -m unittest discover -s tests`.
- `mypy src` / `ruff check .` clean.
- stub-LLM end-to-end: 신규 에이전트가 봉인 set에서 `score_agent`로 채점되고, 채점 수치는
  메모리 종류와 무관(어댑터↔채점 분리) — `score_agent` 출력 byte-identical 확인.
- **측정 무결성 단언**: 관찰표 surface 문자열이 적 타입별 *관찰 데미지* 만 담고, 정답 무브/차트
  미노출(테스트로 강제).

## 리스크

| 리스크 | 완화 |
|---|---|
| surface가 추론을 대신해 측정 무효화 | Step3 규율 + Step6 가드 테스트로 "추천/정답 금지, 원시 관찰만" 강제 |
| 토큰 폭증(누적표 무한 성장) | 적 타입별 무브별 최신 관찰만 유지(bounded) |
| 실측 LLM run은 비용·rate-limit·로컬 | 본 task는 *메커니즘 + 무회귀*까지만 자율. 실제 프런티어 재측정 run은 사용자 로컬(키/구독) — INITIATIVE 정직 경계 계승 |
| floor가 메모리 개선 후에도 유지될 가능성 | 결과는 reframe 없이 기록 — 개선 후에도 floor면 "어댑터 아닌 능력 신호"로 한 발 더, 그래도 전투-attrition·표본 confound 잔존 명시 |

## Acceptance Criteria (G1 통과 시 freeze)

- [ ] AC1: 전투-결과 인지 메모리가 `eval_harness.Agent` Protocol(`act`+`reset`)을 만족하고
      봉인 set에서 `score_agent`로 채점된다(stub end-to-end 테스트 그린).
- [ ] AC2: 메모리가 적 타입별 무브 *관찰 데미지* 를 (타입,무브)당 **최신 단일값으로 덮어쓰며**
      누적·프롬프트에 surface 한다. 표 크기 상한 = num_types×4(bounded — 테스트로 단언).
- [ ] AC3: **측정 무결성** — surface 문자열에 hidden type 이름·차트·정답-무브 추천이 **없다**
      (가드 테스트로 강제). 추론은 LLM 몫. 同 가드 테스트가 신규 클래스 docstring에
      **정직 경계 문구(메커니즘이지 측정 결과 아님)** 존재도 단언(AC8 실행가능화).
- [ ] AC4: `reset()`이 전투 메모리를 clear → 월드 간 누수 0(테스트).
- [ ] AC5: `score_agent` 채점 수치가 어댑터 변경과 무관하게 byte-identical(채점↔어댑터 분리 회귀 0).
- [ ] AC6: 전체 unittest 스위트 그린(회귀 0), `mypy src` / `ruff check .` clean.
- [ ] AC7: 러너에 신규 에이전트 플래그 노출, stub 경로 무회귀.
- [ ] AC8: 정직 경계 — 신규 클래스 docstring에 "메커니즘이지 측정 결과 아님 / 실측은 사용자 로컬 /
      결과 reframe 금지" 명시. **AC3 가드 테스트가 docstring 존재를 실행 단언**(문서-only 아님).
