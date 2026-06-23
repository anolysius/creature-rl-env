---
slug: learnability-measurement
initiative: env-core
status: active
started: 2026-06-22
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/envs/critter_env.py
  - src/critter_gym/registration.py
  - src/critter_gym/learnability.py
  - scripts/learnability.py
  - tests/test_champion_action.py
  - tests/test_learnability.py
extracted_to: []
supersedes: []
---

# learnability-measurement — 학습 정책이 추론을 *학습*하는가 (정직한 측정)

> 작성일: 2026-06-22 | 상태: 계획
> 전진 EC: **M3 신뢰성** + **M3-EC4 writeup 토대**. `reasoning-load-bearing`(archive 16)의 정직한 follow-up.
> 선행 의존: `CritterGym-commit-v0` (PR #20, 이 브랜치가 stack). DESIGN §3.1.1 follow-up #1·#2.

## 목표

`reasoning-load-bearing`은 *task 구조*가 추론을 강제함을 **scripted-arm**으로 증명했다(infer 0.84 > probe 0.47).
열린 질문: **학습 정책(PPO)이 commit-v0에서 실제로 추론을 *학습*해 infer-arm 수준 일반화에 접근하는가?**
이 task는 (1) 학습 정책이 추론을 *표현*할 수 있게 하는 **챔피언-선택 액션 UX**(전제)와 (2) 학습 정책을
reference arm(oracle/infer/type_blind/probe)과 대조하는 **학습 측정 하네스**를 만들고, (3) 결과를 **정직히
보고**한다(결과-불문).

**⚠ 정직성 설계(typechart-depth/§4 교훈 적용)**: acceptance를 "PPO가 probe를 이긴다" 같은 *성능 결과*로
freeze하지 **않는다**(학습은 stochastic·미수렴 가능 — freeze 불가 주장). acceptance = **하네스·액션 UX가
동작 + 측정이 산출·정직 보고**. PPO가 infer에 도달하면 (A)의 learnability 완성; 도달 못 해도 "구조는 추론을
허용하나 X budget의 PPO는 아직 학습 못 함 → Y 필요"라는 *그 자체로 정직한 결과*. 헤드라인보다 정직성.

## 선행 조건

- ✅ `CritterGym-commit-v0`(commit_mode + super_mult3 + boss140/18) — reasoning-load-bearing(PR #20). 이 브랜치 stack.
- ✅ `scripts/train_ppo.py`(PPO + gap), `generalization.measure_generalization`(정책-비의존), reference arm 로직
  (`tests/test_reasoning_gate.py`의 4-arm). 재사용/추출.
- ⚠ **현 commit 모드 한계**: env에서 챔피언=active_a(크리처 0) 고정 — 학습 정책이 infer를 *표현 불가*. Step 1이 해소.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `critter_env.py` | commit 모드 **챔피언-선택 액션 UX** — 보스전 turn-0 commit window(action 4=챔피언 cycle, 첫 move가 commit-lock). enemy_type 관측 기반 선택. | **높음** | critical. obs/action shape 불변, M1·기존 commit 무회귀 |
| `registration.py` | (필요시) commit-v0 가 챔피언-액션 모드 반영 | 낮 | |
| `learnability.py` (신규) | reference arm(oracle/infer/type_blind/probe) + 학습 정책을 commit-v0에서 공통 측정하는 **numpy-only** API. 4-arm 로직을 test에서 product 모듈로 승격(AC3 "product API" 정합) | 중 | `[rl]` 무의존 — 학습 정책은 주입식 PolicyFn |
| `scripts/learnability.py` (신규) | `[rl]`: PPO를 commit-v0 held-in 학습 → held-in/out gap + reference arm 대조 리포트 | 중 | train_ppo.py 패턴 재사용. CI 비검증(무거운 학습) |
| `tests/test_champion_action.py` (신규) | 챔피언-액션 UX 결정론 단위 — cycle/commit-lock/enemy_type 관측/M1·기존 commit 무회귀 | **높음** | |
| `tests/test_learnability.py` (신규) | learnability.py reference arm 재현(scripted infer>probe 유지) + 측정 API 계약. 학습 정책은 stub/scripted로 계약 검증(무거운 PPO는 importorskip smoke) | 중 | numpy-only 계약 |

### 영향 범위 (import 그래프)

`critter_env.py`(챔피언 액션) ← `learnability.py`(측정) ← `scripts/learnability.py`(`[rl]` 소비자). 챔피언-액션은
commit 모드에서만 활성(기본 off·비-commit 무변) → M1·procgen-v0·기존 commit-v0 scripted gate 무회귀.
`learnability.py`는 `generalization.measure_generalization` 재사용(정책-비의존).

## Step별 계획 (TDD)

1. **Step 1 — 챔피언-선택 액션 UX (Red→Green)**: commit 모드 보스전에 turn-0 commit window. action 4=챔피언
   cycle(첫 move 전), 첫 move=commit-lock(이후 switch no-op 유지). enemy_type 관측. 결정론 단위 테스트.
   M1·비-commit·기존 commit gate 무회귀. **check_env(commit-v0) 통과.**
2. **Step 2 — learnability 측정 API (Red→Green)**: `learnability.py` — reference arm 4종 + 임의 PolicyFn을
   commit-v0 held-in/out에서 측정(`measure_generalization` 재사용). 4-arm scripted 재현(infer>probe 유지).
3. **Step 3 — 학습 스크립트 + 측정 산출 (Red→Green)**: `scripts/learnability.py`(`[rl]`) — PPO를 commit-v0
   held-in 학습 → 학습 정책 gap + reference arm 대조 리포트. importorskip smoke(CI) + 실제 학습은 수동.
4. **Step 4 — 측정 실행 + 정직 보고**: 실제 PPO 학습 1회 실행 → 결과(학습 정책이 infer/probe 대비 어디)
   를 report에 **정직히** 기록. DESIGN §3.1.1 follow-up #1 상태 갱신(달성/미달성 불문 정직).

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build` (canonical clean, numpy-only core).
- 챔피언-액션: 결정론 단위(cycle/lock/관측) + `check_env`(commit-v0) + M1·procgen·기존 commit gate 무회귀.
- learnability API: reference arm scripted 재현(`infer − probe ≥ 0.1` 유지, commit-v0 액션 경유로도).
- `scripts/learnability.py`: importorskip smoke(sb3 미설치 graceful). 실제 학습 결과는 report에 수치 기록.

## 리스크

- **R1 (높음·정직성)**: PPO가 infer에 미도달 가능. → **acceptance를 성능으로 freeze 안 함**(위 정직성 설계).
  미달도 정직한 결과로 보고. typechart-depth 교훈 적용.
- **R2 (높음)**: 챔피언-액션이 obs/action 계약·M1·기존 commit-v0 gate를 깸. → commit 모드 한정 + shape 불변 +
  무회귀 가드 + check_env.
- **R3 (중)**: 학습 budget/시간 과다(killer-demo 100k 선례). → smoke는 작은 step, 실제 측정은 수동 1회, 결과 수치만 report.
- **R4 (중)**: turn-0 commit window가 probing 재도입(cycle로 정보 누출?). → cycle은 enemy_type 외 정보 안 줌
  (데미지 미발생), 첫 move 후 lock — scripted gate로 infer>probe 유지 확인.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: commit 모드 **챔피언-선택 액션 UX** — 보스전 turn-0 commit window(action 4 cycle, 첫 move commit-lock),
  enemy_type 관측 가능. 결정론 단위 테스트. **M1·비-commit·기존 commit-v0 scripted gate 무회귀** + `check_env`.
- **AC2**: `learnability.py`(numpy-only) — reference arm(oracle/infer/type_blind/probe) + 임의 PolicyFn을 commit-v0
  held-in/out에서 측정하는 API. scripted reference가 `infer − probe ≥ 0.1` 재현(액션 UX 경유 포함).
- **AC3**: `scripts/learnability.py`(`[rl]`) — PPO를 commit-v0 held-in 학습 → 학습 정책 gap + reference arm 대조
  리포트 출력. importorskip smoke가 CI 통과(sb3 미설치 graceful). **(성능 결과는 acceptance 아님 — R1.)**
- **AC4**: **측정 1회 실행 + 정직 보고** — 학습 정책이 reference arm(infer/probe/blind) 대비 어디인지 report에
  수치로 기록. 결과 불문(도달=완성/미달=정직한 한계+next). DESIGN §3.1.1 follow-up 상태 갱신.
  - **정량 컷오프**(L1 plan-reviewer soft 흡수, 재현성): PPO ~100k timesteps(killer-demo 선례), eval held-in
    N=20 / held-out N=20 고정 시드. report에 `{oracle, infer, type_blind, probe, learned}` × {held-in, held-out}
    평균 표 + gap. 더 긴 학습은 후속 — 1회 측정의 budget을 고정해 결과를 재현가능하게.
- **AC5**: M1·procgen·기존 commit-v0 완전 무회귀 + honesty 가드 무회귀(learnability 과대표현 차단 유지).
- **AC6**: 툴체인 canonical clean (`mypy src`·`ruff`·`pytest -q`·`build`). 신규 core 모듈 numpy-only.
