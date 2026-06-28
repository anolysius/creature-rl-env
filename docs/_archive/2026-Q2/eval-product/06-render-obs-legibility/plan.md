---
slug: render-obs-legibility
initiative: eval-product
status: active
started: 2026-06-27
acceptance_freeze: true
domains: [agents]
task_type: env
mode: standard
scope_paths:
  - src/critter_gym/llm_eval.py
  - tests/test_llm_eval.py
extracted_to: []
supersedes: []
---

# render_obs 가독성 수정 — LLM이 과제를 오해하지 않게

> 작성일: 2026-06-27 | 상태: 계획 | 이니셔티브: eval-product (M5)

## 목표

stateful-llm-agent(#5) 실측 probe가 무상태·stateful 모두 **0% of oracle**로 floor했고, 1 에피소드
transcript 진단(seed 1506920)으로 원인이 **`render_obs`의 오도**임을 확정했다 — 난이도도 파싱 버그도 아님:

1. **0-마스킹 오도 (핵심)**: env(`critter_env.py:354`)는 `player_hp/type/level`을 **전투 중에만** 채우고
   오버월드에선 0으로 마스킹한다(그 필드는 *전투 중인* 활성 생물만 묘사). 그런데 `render_obs:77`는 이를
   그대로 `"Your creature: hp 0, type 0, level 0"`로 찍는다. → LLM이 step 1에서 **"나는 생물이 없다"**고
   오판(실제로는 `reset()`이 `starter_party()`로 파티를 줌). 과제를 처음부터 잘못 이해.
2. **gym/creature 살라언스 부재**: transcript에서 LLM이 **체육관(G) 타일을 생물(C)로 착각**하고 "생물
   잡으러 간다"며 진입 → 보스전 패배 루프. 5×5 view에 glyph는 있으나 "여기/근처에 G가 있고 진입 시
   보스전"이라는 명시가 없다.
3. **목표 미설명**: `DEFAULT_SYSTEM`이 "스타터 파티를 갖고 시작한다 / G 타일에 올라 보스를 이겨라 /
   C 타일에서 Catch로 야생 생물을 잡는다"를 말하지 않는다.

본 task는 **`render_obs` + `DEFAULT_SYSTEM`을 obs만으로 진실되게** 고쳐 LLM이 과제를 오해하지 않게 한다.

**M5-EC1 기여**: agentic-LLM 측정이 공정하려면 obs가 과제를 *정직하고 읽기 쉽게* 전달해야 한다. 본
수정 전의 0%는 측정 도구의 결함이지 능력 신호가 아니므로, 이 수정이 "기억 줬을 때 N% of oracle"을
의미 있게 만드는 선행 조건이다.

## 선행 조건

- #5 stateful-llm-agent done(main 머지). `StatefulLLMAgent`/`LLMAgent`/`score_agent` 존재.
- 474 tests green, 1.0.0rc1, main HEAD `4bd101a`.
- **진단 근거**: transcript(scratchpad/diag_out.txt) — seed 1506920, 40스텝, gym0/caught0, 20스텝
  탐색 후 gym을 creature로 착각해 W/E 루프. obs 첫 줄이 "hp 0, type 0, level 0".

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/llm_eval.py` | `render_obs`: 오버월드에서 오도하는 "Your creature: hp 0…" 제거 → 정확한 표현(전투 중에만 스탯 표시 명시) + 시야 내 G/C 살라언스 한 줄 + "현재 타일이 gym" 플래그. `DEFAULT_SYSTEM`: 스타터 파티·목표·catch 흐름 1~2문장 추가 | 중 — LLM이 읽는 텍스트 변경(의도) |
| `tests/test_llm_eval.py` | 오버월드 obs에 "hp 0" 오도 문구 부재 + 전투 중엔 스탯 표시 + G/C 살라언스 + 결정론 유지 테스트 | 저 |

### 영향 범위 (import 그래프)

- `render_obs`는 `LLMAgent`/`StatefulLLMAgent.act`가 프롬프트 빌드에 사용 + `scripts/llm_eval_demo.py`가
  출력. **scripted agent(oracle/type_blind/random)는 render_obs를 쓰지 않음** → `score_agent`의 수치·무회귀
  무관(렌더는 LLM 텍스트일 뿐). 즉 채점 numerics 무영향.
- 기존 render 테스트 2개(`test_render_obs_is_deterministic`, `test_render_obs_includes_core_fields`)는
  출력 변경에 맞게 갱신 가능(byte-identical 보장 대상 아님 — render는 *개선 대상*).

## Step별 계획

1. **`render_obs` 오버월드 분기** — `in_battle` 분기: 전투 중이면 현재처럼 player/enemy 스탯 표시(정확);
   오버월드면 "Your creature: hp 0…" 줄을 **제거**하고 대신 "(creature stats show during battle)" 같은
   정확한 안내 + 보유 사실 오해 방지. obs엔 파티 크기 필드가 없으므로 **거짓 수치 날조 금지** — "N마리
   보유" 같은 단언 대신 "you have a starter party; its stats appear in battle"로 진실 한도 내 표현.
2. **G/C 살라언스** — `local_patch`를 스캔해 G(=3)/C(=2)가 보이면 "A gym (G) is visible nearby" /
   "A wild creature (C) is visible nearby"를 추가하고, **중앙 타일이 G면** "You are on a gym — moving
   here starts a boss battle"를 명시(중앙=patch_radius,patch_radius). 결정론 유지.
3. **`DEFAULT_SYSTEM`** — "스타터 파티 보유 / 목표=G 타일 보스 격파 / C 타일에서 Catch로 야생 포획 /
   숨은 타입표는 전투로 추론" 1~2문장 추가(간결·결정론).
4. **테스트** — (a) 오버월드 render에 "hp 0" 오도 문구 부재 + 파티 관련 정확 문구 존재, (b) 전투 obs엔
   player/enemy 스탯 그대로, (c) patch에 G/C 있을 때 살라언스 문구, (d) 중앙 G일 때 gym 플래그,
   (e) 결정론(같은 obs→같은 문자열) 유지, (f) 기존 코어 필드(position/battle/gym/action 범례) 유지.
5. **무회귀 확인** — 전체 pytest(474 기준) green, scripted `score_agent` 수치 불변(렌더 무관 입증).

## 검증 방법

- `mypy src` · `ruff check .` · `pytest`(.venv) green · `python -m build` clean.
- scripted `score_agent`(oracle/random) 수치 **불변**(렌더는 LLM 텍스트일 뿐, 채점 경로 무관) — 테스트로 고정.
- **선택적 재측정(사용자 로컬)**: 본 수정 후 `--stateful` probe 재실행 → 0% floor가 풀리는지 확인. 단
  결과 숫자는 본 task acceptance 아님(메커니즘/가독성만 게이트) — 나오면 그대로 기록, reframe 금지.

## 리스크

- **거짓 정보 날조 금지**: obs에 파티 크기 필드가 없으므로 "N마리 보유" 같은 수치 단언 금지 — 진실
  한도("스타터 파티 보유, 스탯은 전투 중 표시")만. obs가 실제로 주는 정보를 넘어서는 진술은 또 다른 오도.
- **과대 금지**: 본 수정이 점수를 올린다고 단정 금지 — 호라이즌/전투 난이도가 남아 여전히 floor일 수
  있음. 본 task는 *오도 제거*이지 점수 보장 아님(report에 명시).
- **render 테스트 갱신**: 출력 변경으로 기존 2 테스트 수정 필요 — scripted 채점 무회귀와 구분(렌더≠채점).

## Acceptance Criteria (G1 통과 시 freeze)

*사전약정 — 결과(probe 점수)가 아니라 렌더의 정직성/가독성 메커니즘으로만 판정.*

- [ ] AC1: 오버월드 obs render에 오도하는 "Your creature: hp 0, type 0, level 0" 문구가 **없고**, 스타터
  파티 보유가 오해되지 않는 정확한 표현이 있다(거짓 수치 날조 없이).
- [ ] AC2: 전투 중 obs render는 player/enemy 스탯을 (현재처럼) 정확히 표시한다.
- [ ] AC3: 시야(local_patch)에 gym(G)/creature(C)가 있으면 살라언스 문구가 나오고, 중앙 타일이 gym이면
  "여기 진입=보스전" 플래그가 나온다 — 테스트로 증명.
- [ ] AC4: `render_obs`는 결정론(같은 obs→같은 문자열)을 유지하고 코어 필드(position·battle·gyms·action
  범례)를 계속 포함한다.
- [ ] AC5: `DEFAULT_SYSTEM`이 스타터 파티 보유·목표(G 보스 격파)·catch 흐름을 설명한다.
- [ ] AC6: 무회귀 — scripted `score_agent`(oracle/random) 수치 불변, 전체 pytest green, mypy·ruff·build clean.
  정직 경계(렌더 수정≠점수 보장, probe=사용자 로컬) docstring/report 명시.
