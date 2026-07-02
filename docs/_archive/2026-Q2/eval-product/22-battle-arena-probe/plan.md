---
slug: battle-arena-probe
initiative: eval-product
status: active
started: 2026-07-02
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/envs/arena_env.py
  - src/critter_gym/envs/__init__.py
  - src/critter_gym/arena.py
  - scripts/battle_arena_probe.py
  - scripts/llm_eval_run.py
  - tests/test_arena_env.py
  - docs/reference/battle-arena.md
extracted_to: []
supersedes: []
---

# battle-arena-probe — LLM engagement confound 분리 (전투-전용 프로브 모드)

> 작성일: 2026-07-02 | 상태: 계획 | 마일스톤: **M3-EC4** (논문 §5 한계 — LLM SE-rate
> 바닥의 원인 미분리: "추론 불가" vs "전투 지속 실패")

## 목표

LLM probe 의 SE-rate(≈14%, chart-blind floor 근처)가 (a) **추론을 못 해서**인지
(b) **오버월드 탐색/생존에 막혀 전투 경험을 못 쌓아서**인지 현 측정으로는 분리 불가.

**battle-arena 프로브 모드**: 오버월드를 생략하고 리셋 즉시 전투에 투입, 전투가 끝나면
곧바로 다음 전투 — K회 연속. 탐색·생존 confound 를 **구조적으로 제거**해 순수 전투
추론(SE-rate)을 측정할 수 있는 진단 도구를 만든다.

- **범위 = 하네스 + scripted arm 검증 (자율·무료)**. LLM 실측은 CLI 구독 quota →
  **사용자 승인 대기** (이 task 에 미포함, 러너 wiring 까지만).
- 기존 측정 파이프라인 재사용: `_super_effective_move` telemetry,
  `se_inference_score` 정규화, `classify_inference` 사전약정 분류기 — **새 임계 발명 0**.

## 선행 조건 (이미 충족)

- scripted 4-arm(`learnability.reference_arm`)은 in_battle obs 에서 순수 전투 정책 —
  arena 에서 그대로 동작 (오버월드 분기는 arena 에서 도달 불가).
- `eval_harness._super_effective_move` 는 `env._mode == "battle"` + `env._battle` 만
  요구 — CritterEnv 서브클래스에서 그대로 유효.
- 매치업 보장(#15): vary 모드 보스는 파티가 strictly super-effective 무브를 가진
  타입만 draw — arena 의 보스 시퀀스도 region gyms 에서 오므로 동일 보장.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향 |
|---|---|---|
| `src/critter_gym/envs/arena_env.py` (신규) | `ArenaEnv(CritterEnv)` — reset 즉시 전투, 종료 시 다음 전투 체인, K회 후 terminate | additive (기존 무수정) |
| `src/critter_gym/envs/__init__.py` | `ArenaEnv` export 1줄 | 미미 |
| `src/critter_gym/arena.py` (신규) | scripted 4-arm arena band(`arena_band`) + submission telemetry(`score_arena_telemetry`) | additive |
| `scripts/battle_arena_probe.py` (신규) | scripted 검증 프로브: 4-arm SE-rate band + 정직 라벨 | 도구 |
| `scripts/llm_eval_run.py` | `--arena` 플래그: LLM 을 arena 에 투입하는 wiring (실행=사용자 승인 후) | 기존 경로 무변경 |
| `tests/test_arena_env.py` (신규) | arena 메커니즘 + band sanity + 결정론 | +테스트 |
| `docs/reference/battle-arena.md` (신규) | evergreen (모드 계약·측정 프레임·경계) | 문서 |

### ArenaEnv 설계 (mirror-first)

- `ArenaEnv(k_battles=10, **CritterEnv kwargs)` — region 은 기존 procgen 그대로
  (chart·gym 보스 타입·seed split 전부 유지). 보스 시퀀스 = region gyms 순환
  (`i % n_gyms`, 타입 RECUR → cross-battle 추론 여지 유지).
- reset: `CritterEnv.reset` 후 즉시 1번째 전투 진입 (기존 `_maybe_enter_battle` 의
  힐·commit-window 규칙 재사용). 전투 종료(승/패/truncation) 시 즉시 다음 전투 진입,
  `k_battles` 소진 시 terminate. `max_steps` truncation 은 그대로.
- 전투 내부 로직은 **오버라이드 없이 부모 `_step_battle` 그대로** — 전투 경제
  byte-identical (arena 는 전투를 바꾸지 않고 전투 *사이*만 바꾼다).
- obs 계약 유지: `in_battle=1`, `gyms_defeated`=누적 승수 (obs space 상한만
  `k_battles` 로 재선언). 레벨/진화는 에피소드 내 지속 (기존과 동일).
- 보상 RLVR 유지: 승리 +1, 진화 +1.
- JAX 포트 **범위밖** — arena 는 LLM/scripted 진단 도구이지 훈련 경로가 아님
  (llm_eval numpy-only 선례).

## Step별 계획

1. **Red**: `tests/test_arena_env.py` — (a) reset 즉시 in_battle=1, (b) K회 전투 후
   terminate (승패 무관), (c) 전투당 파티 힐 + 보스 시퀀스 region gyms 순환,
   (d) 같은 seed → 같은 trace (결정론), (e) `gyms_defeated` obs = 누적 승수·상한 K,
   (f) commit/non-commit 양쪽 동작, (g) 4-arm band sanity: arena 에서
   oracle se_rate > type_blind se_rate (band 가 변별함), oracle 승수 > 0.
2. **Green(env)**: `arena_env.py` + export.
3. **Green(band)**: `arena.py` — `arena_band(seeds, **knobs)` (4-arm SE-rate/승수,
   `_super_effective_move` 재사용) + `score_arena_telemetry(submission, seeds, **knobs)`.
4. **프로브 스크립트**: `battle_arena_probe.py` — scripted 4-arm arena band 실측 출력
   (오버월드 band 와 나란히 비교), HONEST 라벨(scripted-only·1 seed set·
   LLM 실측=승인 필요·헤드라인 금지).
5. **LLM wiring**: `llm_eval_run.py --arena` — arena 에 LLM 투입 + arena band 대조
   출력 (기존 경로 byte-identical; fake `complete` 로 단위 검증).
6. **문서**: `docs/reference/battle-arena.md` + CHANGELOG (task-end).

커밋 단위: 단일 커밋 (additive 프로브 모드 원자 변경 — 브랜치 = 단독 PR).

## 검증 방법

- `.venv/bin/python -m pytest -q` — 전체 (baseline 677 + 신규, 회귀 0)
- `mypy src` (신규 오류 0) · `ruff check .`
- `battle_arena_probe.py` 실행 출력을 report.md 에 기록 (수치는 결과보고, AC 아님)

## 리스크

| 리스크 | 대응 |
|---|---|
| scripted arm 이 arena 에서 의도밖 동작 (오버월드 분기 의존) | `_Arm.__call__` 은 in_battle 이면 순수 전투 분기 — (g) band sanity 테스트로 실검증 |
| 부모 `step()` 의 `_gym_defeated` 전승 종료 로직과 충돌 | ArenaEnv 가 `step()` 종료 판정을 오버라이드 (K 소진 기준); 전투 로직 자체는 부모 그대로 |
| `gyms_defeated` obs 상한 초과 (K > num_gyms) | observation_space 를 K 상한으로 재선언 + 테스트 |
| LLM 프롬프트(render_obs)가 arena 특수 상황을 오도 | arena 는 obs 계약을 바꾸지 않음(in_battle 분기 그대로); 러너에 arena 설명 1줄만 추가 |
| scope creep (LLM 실측까지 하고 싶어짐) | 실측=quota=사용자 승인 게이트 — 이 task 는 wiring 까지, report 에 명시 |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (arena 메커니즘)**: reset 즉시 전투, K회 연속 전투 후 종료(승패 무관 진행),
  전투당 힐/commit-window 는 기존 gym 규칙과 동일, 같은 seed → 같은 trace — 테스트.
- **AC2 (기존 경로 무회귀)**: 기존 CritterEnv/eval 경로 무수정(additive) —
  전체 기존 테스트(677) 회귀 0. `llm_eval_run.py` 는 `--arena` 미지정 시 기존과
  동일 동작.
- **AC3 (band 변별 sanity)**: arena 4-arm SE-rate band 에서 oracle > type_blind
  (band 가 추론을 변별), oracle 승수 > 0 (winnable) — held-out seed 테스트.
- **AC4 (telemetry 재사용)**: arena SE-rate 는 `_super_effective_move` 로 계측,
  정규화는 `se_inference_score`, 다중-run 판정은 `classify_inference` — 새 임계 0.
- **AC5 (프로브 스크립트 + 정직 라벨)**: `battle_arena_probe.py` 가 arena vs
  오버월드 band 를 출력하고 scripted-only·LLM-실측-승인-필요·헤드라인-금지 라벨 포함.
- **AC6 (LLM wiring, 실행 없이 검증)**: `--arena` 가 fake complete 로 단위 검증됨 —
  실제 LLM 호출은 이 task 에서 실행하지 않음 (사용자 승인 게이트 명시).
- **AC7 (문서)**: `docs/reference/battle-arena.md` evergreen 1장 — 필수 4섹션:
  (1) 모드 계약 (ArenaEnv 시그니처·K 체인 규칙·obs/보상 계약·부모 전투 로직 무수정),
  (2) 측정 프레임 (SE-rate telemetry·se_inference_score 정규화·classify_inference
  재사용 — 새 임계 0), (3) scripted band 실측 표 (probe 스크립트 출력), (4) 경계
  (scripted-only·LLM 실측=사용자 승인 게이트·JAX 범위밖·진단 도구≠리더보드).
  `multitype-boss.md`/`strict-battle.md` 와 같은 reference 규격.
