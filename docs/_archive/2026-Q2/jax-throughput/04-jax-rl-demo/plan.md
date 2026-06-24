---
slug: jax-rl-demo
initiative: jax-throughput
status: active
started: 2026-06-24
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
scope_paths:
  - src/critter_gym/jax_train.py
  - scripts/jax_rl_demo.py
  - tests/test_jax_train.py
  - pyproject.toml
  - docs/explanation/jax-throughput.md
  - docs/explanation/competitive-analysis.md
  - DESIGN.md
  - docs/CHANGELOG.md
  - docs/_active/jax-throughput/INITIATIVE.md
extracted_to: []
supersedes: []
---

# RL 학습 데모 — JAX 벡터화 env로 실제 PPO 학습 1회 ("속도 실재" 가시화, M4 마감)

> 작성일: 2026-06-24 | 상태: 계획 | 마일스톤: **M4** (jax-throughput INITIATIVE override, functional-readiness-first)

## 한 문단 요약 (수식 없이)

지난 세션에 우리는 게임 엔진을 JAX로 다시 짜서 "수천 개를 한꺼번에 돌리면 34~1000배 빠르고 결과는 원본과 안 틀린다"는 **벤치마크 숫자**를 만들었습니다. 그런데 숫자만으로는 "그래서 실제로 빨리 배우긴 하느냐"가 안 보입니다. 이번 작업은 그 빠른 엔진 위에서 **AI를 실제로 한 번 학습시켜**, ① 점수가 올라가는 곡선과 ② 같은 학습을 옛날 느린 방식으로 했을 때보다 얼마나 빠른지를 **정직하게** 보여줍니다. 즉 "빠르다(숫자)"를 "**실제로 빠르게 배운다(데모)**"로 마감합니다. 작고 싸지만, 제품으로서의 가치를 눈에 보이게 만드는 작업입니다.

## 목표

`jax_env`(#42, family A commit-mode 벡터화 full-episode env) 위에서 **JAX-native(vmap+jit, on-device) 학습 루프**를 1회 돌려 M4를 *데모*로 마감한다. 산출물 = (a) 학습 곡선(에피소드 리턴이 학습과 함께 상승) + (b) 학습 rollout throughput을 numpy/sb3 경로와 **정직 비교**. 벤치 숫자를 "실제로 빠르게 학습되는 환경"으로 전환.

**왜 JAX-native 루프인가 (설계 핵심)**: sb3 PPO로 `jax_env`를 감싸면 step마다 host↔device 경계를 넘나들고 sb3가 병목이 되어 **vmap 속도가 사라진다** → "속도 실재"를 못 보여줌. 진짜 데모는 정책·rollout·업데이트가 전부 device 위 lock-step으로 도는 최소 PPO/A2C(PureJaxRL식)다. 이것이 #42 벡터화 surface를 RL 루프가 *실소비*하는 모습.

**왜 지금 / 순서 근거**: (1) env 메커닉 무변경 → **spec-stability 게이트 충돌 없음**(난이도 재설계와 달리 JAX 재포트 유발 안 함). (2) 방금 만든 #42 surface를 즉시 제품 가치로 마감. (3) RL-on-JAX-env 통합 하네스를 만들어 두면 후속 변별-난이도 재설계의 **재사용 enabler**가 되고, 재설계 전에 현 env가 실제 RL 루프에서 멀쩡한지 싸게 검증. (4) throughput은 측정값이 deterministic → 정직 보고 쉬움((B)의 noisy-RL 함정 적음).

## 선행 조건

- `[jax]` extra 설치된 .venv (현 CPU jax 0.4.30). PPO 학습용 NN/optimizer는 **새 무거운 dep 없이 손수 구현 우선**(아래 리스크 R3).
- `jax_env.jax_env_step` / `jax_reset` / `encode_obs` (parity 0 mismatch 입증 완료) — 본 task는 그 위에 *학습 루프만* 얹는다. **env 코어·jax_env 무변경**(변경 시 parity 재검증 필요 = scope 밖).
- seed split 헬퍼: `generalization.split_train_pool`, `region.heldout_seeds` (재사용, train↔held-out disjoint 유지).
- **branch first** (rules/85): G1 통과 후 `feature/jax-rl-demo` 에서 작업 → PR → main. main 직접 금지.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/jax_train.py` | **신규** | 중 | JAX-native 최소 학습 루프(obs flatten + tiny MLP + 손수 Adam + region-bank auto-reset + lax.scan rollout + jit update). `import jax` 모듈(코어 numpy-only 보존, `__init__` 미import). |
| `scripts/jax_rl_demo.py` | **신규** | 저 | 데모 실행: 학습 곡선 + throughput 비교 + 정직 framing 출력. `[jax]`(+필요시 numpy/sb3 비교행). |
| `tests/test_jax_train.py` | **신규** | 저 | `importorskip("jax")` smoke — 몇 iter 실행/params 갱신(변화)/리턴 finite/obs-flatten 결정론·차원. **학습 품질은 CI 비검증**(머신 의존). |
| `pyproject.toml` | 조건부 | 저 | pilot이 손수 optimizer로 학습 불충분 판정 시에만 `optax` 를 `[jax]` extra에 추가(문서화). 기본은 무변경. |
| `docs/explanation/jax-throughput.md` | 갱신 | 저 | §4/§5 에 RL-demo 결과(학습 곡선 + train-throughput) narrative 추가. |
| `DESIGN.md` | 갱신 | 저 | §4 M4 progress 1줄(데모 마감). |
| `docs/CHANGELOG.md` · `INITIATIVE.md` | append | 저 | task-end. |

### 영향 범위 (import 그래프)

`jax_train.py` → imports `jax`, `jax_env`(step/reset/encode_obs), `region.generate_region`. **역방향 의존 0** (코어·envs·다른 jax 모듈이 jax_train을 import 안 함). `critter_gym/__init__.py` 는 jax_train 미import → core CI numpy-only 불변. 기존 281+2=283 tests 무회귀(신규는 importorskip 격리).

## Step별 계획

> **G1 freeze 전 PILOT 필수** (아래 "리스크/Pilot" + AC7). pilot 결과가 헤드라인 분기((a)/(b)/(c))를 결정한 뒤 freeze.

1. **obs flatten + tiny policy** — `encode_obs` dict(13키) → 결정론적 float 벡터(jittable). 작은 MLP(policy logits over 6 actions + value), params=pytree. 손수 init.
2. **region bank auto-reset** — train seeds로 N개 region을 numpy procgen(reset은 numpy, 1회/episode) → batched state bank. 에피소드 term/trunc 시 bank에서 인덱스 재선택으로 reset(jittable). seed split 유지(train bank vs held-out eval).
3. **rollout + update** — `lax.scan`으로 T-step rollout(vmap B envs) + advantage/return 계산 + PPO/A2C-lite loss + 손수 Adam 1 step, 전체 `jit`. (R3: optax 없이 시도, 부족하면 optax 추가.)
4. **데모 스크립트** — 학습 루프 K iter 실행, iter별 mean episode return 누적(학습 곡선) + 학습 rollout env-steps/s 측정 + numpy/sb3 동예산 wall-clock 비교 + 정직 framing 출력. (선택) 끝에 held-out seed eval 1패스(일반화 story 연결, 헤드라인 아님).
5. **테스트 + 문서** — smoke 테스트(importorskip) + jax-throughput.md/DESIGN/CHANGELOG 갱신.

## 검증 방법

- **CI(numpy-only)**: 신규 import 0 회귀 → 기존 283 tests green 유지. `test_jax_train.py` 는 importorskip(미설치 skip).
- **로컬 [jax]**: smoke 테스트 통과(몇 iter 실행/params 변화/리턴 finite/flatten 결정론·차원). 데모 스크립트 실행 → 학습 곡선 + throughput 표 산출(background run, 완료 시 자동 재호출).
- **canonical**: `mypy src`(현 25) · `ruff check .` · `pytest -q` · `python -m build` clean.
- **정직 보고 검증**: 헤드라인이 pilot 분기와 일치(과대 금지) — throughput=vmap 한정·single run·CPU·학습=신호 라벨.

## 리스크 / Pilot (freeze 전 검증 — §4 교훈·정직성 규율)

| # | 리스크 | Pilot 검증 | 분기 |
|---|---|---|---|
| R1 | **싸게 학습이 안 보일 수 있음** — jax_env는 기본 config(10×10·max_steps 200·boss 120, super_mult 증폭 없음)로 하드코딩. 리워드(catch/gym/evolve)가 random 탐색서 sparse하면 곡선이 평평. | 최소 루프로 cheap budget(예: B=512×T·수십 iter) 돌려 **mean return 상승 여부** 확인. | (a) 명확 상승 → 헤드라인 "학습+빠름" / (b) 평평·noisy → 헤드라인 = **train-rollout throughput**(vmap vs numpy), 학습 곡선은 *정직 partial/signal* 보고. **둘 다 유효 M4 데모**(속도 실재). |
| R2 | **region-bank auto-reset이 jit/vmap 아래서 실패**(numpy procgen을 scan 내부 호출 불가). | bank 인덱스 재선택 방식이 jit 통과하는지. | (c) 실패 시 **fixed-horizon(truncate-only, mid-rollout reset 없음)** 에피소드로 데모 후퇴(문서화). |
| R3 | **손수 optimizer로 학습 부족**. | 손수 Adam로 R1 곡선 나오는지. | 부족 시 `optax` 를 `[jax]` extra 에 추가(정직 문서화) — dep 추가는 최소화 원칙이나 학습 품질 우선. |
| R4 | **throughput 비교가 안 빠를 수 있음**(학습 루프 오버헤드가 vmap 이득 상쇄). | vmap'd 학습 rollout env-steps/s vs numpy sb3 동예산. | 거의 robust(벤치서 이미 vmap 34~73× full-env). 안 빠르면 정직 보고(원인 분석). |

**Pilot 산출 = AC7 분기 확정** → 그 분기로 acceptance freeze.

### 사전약정 결정규칙 (데이터 보기 전 고정 — 사후편향 차단)

pilot 측정값을 보기 *전에* 아래 규칙을 고정한다. pilot 숫자가 규칙을 만족하는지로 헤드라인 분기를 *기계적으로* 결정 — 결과를 보고 헤드라인을 고르지 않는다(p-hacking 차단). 이 규칙들은 **성능 임계가 아니라 "어느 정직 서사를 쓸지"의 분기 규칙**이다(§4 교훈: 성능이 아니라 측정+정직보고로 freeze).

- **R1 학습 가시성 → (a) vs (b)**: 학습 곡선을 앞 윈도우(초기 20% iter)와 뒤 윈도우(마지막 20% iter)의 mean episode return으로 요약. **(a) "학습+빠름" iff `mean_late − mean_early ≥ std_late`** (상승폭이 후기 변동성을 명확히 초과 = 노이즈 아닌 상승). 그 외 = **(b)**: 헤드라인은 train-rollout throughput, 학습 곡선은 *partial/signal*로 정직 보고. (단일 run이므로 std는 환경-배치 간 episode-return std 사용 — 측정 가능한 노이즈 척도.)
- **R2 auto-reset → (c) 후퇴 여부**: region-bank 인덱스 재선택 reset이 `jax.jit` 아래서 **tracer/concretization 에러 없이 통과하면 region-bank**, 에러 발생 시 **(c) fixed-horizon(truncate-only)**으로 후퇴(문서화). (이진 판정 — 에러 유무.)
- **R4 speed → 헤드라인 정직성**: **"빠르다" 주장은 측정된 부등식으로만** — vmap'd 학습-rollout env-steps/s `>` numpy sb3 collection env-steps/s(동일 환경 수·동일 머신). 부등식이 성립하면 배율(×)을 vmap·CPU·single-run 라벨과 함께 보고, 성립 안 하면 "안 빨랐음"을 원인과 함께 정직 보고(헤드라인 철회). 절대 배율 숫자에 사전 임계 없음(측정값 그대로 보고).

**정직성 사전약정** (헤드라인 과대 차단, freeze 시 박제):
- "fast" = **wall-clock로 동일 env-steps 수집/학습**, JAX-vmap vs numpy — 이득은 vmap 한정(bench framing 일관), single machine·CPU·single run = *direction*.
- 학습 = **신호**(reward 상승 신호), tuned SOTA 숫자 아님. N·budget·단일run caveat 명시.
- env·jax_env 무변경 → parity 보존(재검증 불요). config 하드코딩 한계(grid/boss/super_mult 고정) 명시.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1** — `src/critter_gym/jax_train.py` 신규: JAX-native 최소 학습 루프(obs flatten + tiny MLP policy/value + optimizer + region-bank/fixed-horizon auto-reset + lax.scan rollout + jit update). `import jax` 모듈, 코어 numpy-only 보존(`__init__` 미import).
- **AC2** — `scripts/jax_rl_demo.py` 신규: 학습 1회 실행 → **학습 곡선**(iter별 mean episode return) + **학습 rollout throughput**(env-steps/s) + numpy/sb3 동예산 wall-clock **정직 비교** + framing 출력. seed split 유지(train bank vs held-out).
- **AC3** — **측정 산출 + 정직 보고**(성능 freeze 아님, §4 교훈). *검증 가능 형태*: 보고된 헤드라인이 위 **사전약정 결정규칙**이 산출한 분기와 일치((a)/(b)/(c)) — 결과를 보고 고른 헤드라인이면 위반. 모든 수치는 caveat 라벨 동반(throughput=vmap·CPU·single-run / 학습=신호). "빠르다"는 R4 부등식 성립 시에만 주장. *성능 임계가 아니라 분기-일치 + 라벨 동반으로 검증*.
- **AC4** — core CI numpy-only 불변 (*구조적·자동 검증*): (i) `python3 -c "import critter_gym"` 후 `sys.modules`에 `jax` 부재(=`__init__` 미import) — 또는 `grep`로 `__init__.py`에 jax_train import 0 확인; (ii) jax 미설치 환경 가정 하 `pytest -q` = 기존 283 tests green(신규 jax 테스트는 importorskip로 skip). AC6의 toolchain 통과와 별개의 *격리 구조* 검증.
- **AC5** — `tests/test_jax_train.py`(`importorskip("jax")`) smoke: 몇 iter 실행 / params 갱신(학습 전후 pytree 값 변화) / 리턴 finite / obs-flatten 결정론(동일 state→동일 벡터)+차원(고정 D) 검증. **학습 품질(곡선 상승)은 CI 비주장**(머신 의존 → 데모 스크립트 몫).
- **AC6** — canonical clean (*toolchain 0-exit*): `mypy src`(현 25, jax_train 포함; jax.* 는 mypy override로 ignore_missing_imports) · `ruff check .`(product code) · `pytest -q` · `python -m build`. (AC4=격리 *구조*, AC6=도구 *통과* — 중첩 아님.)
- **AC7** — **freeze 전 pilot**으로 R1·R2·R4 측정 → **사전약정 결정규칙**(위)이 헤드라인 분기를 기계적으로 확정. pilot이 (a)를 falsify(`mean_late−mean_early < std_late`)하면 (b)/(c)로 정직 reframe. pilot 결과·적용 규칙·확정 분기를 report에 박제.
- **AC8** — 문서: jax-throughput.md(§4/§5 데모 결과) + DESIGN §4(1줄) + competitive-analysis "competitively fast" 행(데모로 보강) + CHANGELOG + INITIATIVE 갱신. broken-link 0.

## 커밋 단위 / 마일스톤

- **커밋 단위**(feature/jax-rl-demo): ① jax_train.py + smoke 테스트(AC1·AC5) → ② 데모 스크립트(AC2) → ③ pilot 후 결과 측정 + 문서(AC3·AC8). pilot은 freeze 전이라 별도 커밋 없음(plan/report에 기록).
- **M4 마감 의미**: 본 task로 M4(JAX throughput)는 *family A 핵심 데모까지 마감*. 남는 M4-EC3(GPU 벤치)·jax-battle-full·다른 family는 환경/우선순위 게이트(후속). **M5(genre generalization) 진입 조건**은 별개 사람 게이트 — 본 task는 M4 마감이지 M5 착수 아님.
