---
slug: battle-legibility
initiative: eval-product
status: active
started: 2026-06-28
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

# 전투 obs 가독성 — LLM이 "숨은 타입표 추론" 루프에 진입하게

> 작성일: 2026-06-28 | 상태: 계획 | 이니셔티브: eval-product (M5)

## 목표

#6(render 수정) 후에도 stateful probe가 0% floor. 진단 probe(5×5 grid·체육관 1개·num_types 3·150스텝)에서
**탐색 벽은 사라졌고**(battle-entries 19) 진짜 벽이 **전투**임을 확정했다. 같은 config에 scripted 대조:

| 정책 | 결과 | 의미 |
|---|---|---|
| oracle (타입표 앎) | **gym 1 클리어, 3턴** | 매치업은 winnable |
| type_blind (타입표 모름, 그냥 공격) | 59턴 다 패배, 0 gym | 타입표 없이는 못 이김 |
| claude-opus-4-8 (우리 LLM) | 19전투 다 패배, 0 gym | **type_blind처럼 행동** |

transcript: LLM이 (a) move 0만 반복(다른 무브 0~3 = 다른 타입 미탐색), (b) 파티 교체(action 4)·커밋
윈도우로 챔피언 선택 안 함, (c) 2턴 만에 사망, (d) 체육관을 생물로 착각해 "Catch"로 턴 낭비. 즉 LLM이
**"무브를 바꿔 보며 super-effective를 추론한다"는 게임의 핵심 루프에 진입조차 못 함** — 전투 obs/시스템
프롬프트가 그 메커닉(무브가 여러 타입·교체·커밋·재시도)을 안 알려주기 때문.

본 task는 **전투 가독성**을 올린다(렌더 + 시스템 프롬프트). **벤치마크 정직성**: 무브 타입을 직접 떠먹이지
않는다(그러면 추론 측정이 무의미) — "다른 무브를 시도→적 hp 변화 관찰→기억"으로 *추론하게* 만드는 것까지.
이게 env가 측정하려는 in-context hidden-rule 추론이다.

**M5-EC1 기여**: agentic-LLM이 우리 환경의 핵심 능력(숨은 규칙 추론)을 *시도라도* 할 수 있게 obs가
메커닉을 정직하게 전달해야 공정한 측정. 0% floor가 "추론 실패"인지 "메커닉 무지"인지 분리.

## 선행 조건

- #6 render-obs-legibility done(main `06a9bc5`). `render_obs` in_battle 분기 존재, `DEFAULT_SYSTEM`,
  `_ACTION_LEGEND_BATTLE` 존재. 480 tests green.
- 진단 근거: scratchpad probe_existence(seed 1.5M, grid5·types3) + oracle/type_blind 대조.
- **obs 한계**: 현 obs는 commit_window 상태·개별 무브 타입·파티 구성을 노출 안 함(env 변경=범위 밖).
  따라서 본 task는 **obs가 주는 정보 한도**(player/enemy type·hp) + 시스템 프롬프트 가이드로만 가독성 향상.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/llm_eval.py` | `DEFAULT_SYSTEM`에 전투 전략 가이드(무브 0~3=다른 숨은 타입·시도+기억·action4 교체·커밋 윈도우·패배 후 재시도) 추가. `render_obs` 전투 분기에 전술 힌트(다른 무브 시도·적 hp 변화로 효과 가늠·교체) 추가. 오버월드 catch 명확화(C 타일에서만) | 중 — LLM 텍스트(의도) |
| `tests/test_llm_eval.py` | 전투 render 힌트·DEFAULT_SYSTEM 전투 가이드·결정론·무회귀 테스트 | 저 |

### 영향 범위

- `render_obs`/`DEFAULT_SYSTEM`은 LLMAgent/StatefulLLMAgent.act + demo만 사용. scripted 채점 무관(무회귀).
- env·obs 스키마 **무변경**(commit_window/move-type 노출은 별도 env task로 분리).

## Step별 계획

1. **DEFAULT_SYSTEM 전투 가이드** — 추가 문장: "전투에서 무브 0~3은 서로 다른 *숨은 타입*이다 — 같은
   적에 여러 무브를 시도하고 적 HP가 가장 많이 떨어지는(super-effective) 무브를 기억하라. 효과 없으면
   action 4로 다른 파티원으로 교체. 전투 시작 시 action 4로 보낼 창을 고를 수 있다(다른 행동 시 확정).
   지면 파티가 회복되니 같은 체육관을 재진입해 배운 걸로 다시 시도하라."
2. **render_obs 전투 힌트** — 전투 분기에 한 줄: "Tip: try different attack moves (0-3) — each is a
   different hidden type; watch the enemy hp drop to find the super-effective one, or Switch (4)."
   (적 hp는 이미 표시 → 턴 간 변화로 데미지 가늠 가능.)
3. **오버월드 catch 명확화** — DEFAULT_SYSTEM/overworld 힌트에 "Catch(4)는 wild creature(C) 타일에
   *정확히 서 있을 때만* 동작 — 체육관(G)에선 Catch 불가"를 명시(진단의 catch-루프 낭비 차단).
4. **테스트** — (a) 전투 render에 무브-다양성/교체 힌트 존재, (b) DEFAULT_SYSTEM에 무브-타입·교체·재시도
   가이드 존재, (c) 결정론 유지, (d) 오버월드/전투 분기 모두 코어필드 유지, (e) 무회귀(scripted 수치 불변).
5. **선택적 재측정(사용자/자율)** — 수정 후 existence probe(grid5·types3) 재실행 → 체육관 클리어 여부
   확인. **결과 숫자는 acceptance 아님**(가독성 메커니즘만 게이트); 나오면 그대로 기록, reframe 금지.

## 검증 방법

- mypy·ruff·pytest(.venv)·build clean. scripted `score_agent` 수치 불변(렌더↔채점 분리) 테스트.
- 재측정은 신호이지 acceptance 아님(과대 금지).

## 리스크

- **벤치마크 정직성 훼손 금지(핵심)**: 무브 타입/super-effective 표를 직접 알려주면 추론 측정이 무의미.
  "시도→관찰→기억하라"는 *전략 안내*까지만, 정답(어떤 무브가 효과적)은 LLM이 추론. AC에 명시.
- **점수 보장 아님**: 가이드를 줘도 num_types·2턴 사망 등으로 여전히 floor일 수 있음(report 명시).
- **obs 한계 정직**: commit_window/move-type 미노출은 env 변경이라 범위 밖 — 시스템 프롬프트가 메커닉을
  *설명*하되 obs에 없는 실시간 상태를 날조하지 않음.

## Acceptance Criteria (G1 통과 시 freeze)

*사전약정 — 가독성/정직성 메커니즘으로만 판정, 점수 결과 아님.*

- [ ] AC1: `DEFAULT_SYSTEM`이 전투 전략을 설명한다 — 무브 0~3이 다른 숨은 타입임 / 무브를 시도하고
  효과를 기억하라 / action 4로 파티 교체 / 패배 후 재시도. **단 어떤 무브가 super-effective인지는 알려주지
  않는다**(추론은 LLM 몫).
- [ ] AC2: `render_obs` 전투 분기에 전술 힌트(다른 무브 시도·적 hp 변화 관찰·교체)가 있고, 전투 중
  player/enemy 스탯 표시는 유지된다.
- [ ] AC3: 오버월드에서 Catch가 C 타일에서만 동작함이 명확히 안내된다(체육관/생물 혼동 차단).
- [ ] AC4: `render_obs` 결정론 유지 + 오버월드/전투 양 분기 코어필드(position·battle·gyms·action 범례) 유지.
- [ ] AC5: 무회귀 — scripted `score_agent` 수치 불변, 전체 pytest green, mypy·ruff·build clean. obs 스키마
  무변경. 정직 경계(추론은 LLM 몫·점수 보장 아님·obs 한도) docstring/report 명시.
