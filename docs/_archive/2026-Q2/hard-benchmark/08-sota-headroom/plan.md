---
slug: sota-headroom
initiative: hard-benchmark
status: active
started: 2026-07-08
acceptance_freeze: true
mode: standard
task_type: general
domains: [rl-env]
scope_paths:
  - src/critter_gym/headroom.py
  - scripts/sota_headroom.py
  - tests/test_sota_headroom.py
extracted_to: []
supersedes: []
---

# SOTA-headroom 재측정 — material하게 더 강한 memory agent에도 hard한가

> 작성일: 2026-07-08 | 상태: 계획 | 이니셔티브: hard-benchmark (M3 신뢰성 자산)

## 목표

**hard-benchmark의 핵심 미해결 질문을 정면으로 다룬다.** #3 (memory-headroom)은 `hard_env_spec`
(grid16·5×5 view·5 gym·420 step)에서 recurrent PPO(GRU **h128**)가 oracle의 **43%**에 그쳐
"(a) hard-and-learnable ROBUST"로 판정했다. 그러나 #3 report가 스스로 못박은 경계:

> *"현 '강한 agent' = recurrent PPO는 **baseline**(SOTA 아님). 더 크거나 나은 algo는 headroom을
>   닫을 수도 있다 — SOTA-class 대비 = OPEN."*

게다가 #3의 recurrent net은 **의도적으로 좁았다**(h128 < feedforward h256, 이득=capacity 아닌
memory 격리 목적). 그래서 "43% headroom"이 진짜 절대 난이도인지, 아니면 **agent를 덜 키워서**인지
구분되지 않았다. 본 task는 그 confound를 친다: 같은 config에서 recurrent PPO를 **capacity+budget으로
material하게 키워**(더 넓은 GRU + 더 큰 budget) 재측정한다.

사전약정 질문 (데이터 전 freeze):
- **더 강한 recurrent PPO가 headroom을 닫는가?** best-scaled config에 #3와 **동일한**
  `classify_headroom(frac=0.75, k=1.0)` 적용:
  - **(a) headroom-ROBUST** (opt-bound mean+std ≤ 0.75·oracle) → 더 강한 baseline에도 hard
    = #3 결론 *강화* (단 여전히 SOTA 아님).
  - **(b) headroom-CLOSES** (pess-bound mean−std ≥ 0.75·oracle) → #3의 43%는 *부분적으로
    capacity 약점*이었다 → **#3 헤드라인 reframe, 사람 정지**.
  - **(c) EXCEEDS oracle** → scripted oracle이 이 config의 유효 ceiling 아님.
  - **(!) VACUOUS** (best-scaled ≤ tiny) → 더 큰 config가 안 이김 → verdict 보류.
  - inconclusive → seed/budget 확충.

**정직 프레이밍(북극성 5)**: CPU·few-run·ONE config. "더 강한 agent"는 여전히 **recurrent PPO의
scaled 변형**(더 큰 arch class·GPU-scale compute·SOTA algo 아님). robust가 나와도 "SOTA에도 hard
입증"이 **아니라** "material하게 더 강한 baseline에도 headroom 유지 → hard 주장 *강화*(SOTA는 여전히
OPEN)". oracle = scripted ceiling proxy. 헤드라인 금지. **best-config 선택·sweep grid·runs escalation
규칙을 데이터 전 freeze**(p-hacking 방지 — 여러 config 중 유리한 것 사후 선택 금지).

**이 task가 advance하는 EC**: hard-benchmark 절대 난이도 — "강한 agent에도 hard"의 capacity confound
차단(#3 경계 상환). competitive-analysis "Difficulty(absolute)" 정밀화.

## 선행 조건

- main = 0119178 (#7 머지), 746 tests green, clean. ✅
- 학습 하네스: `jax_train.train_recurrent_ppo`(GRU, width=`PPOConfig.hidden`),
  `evaluate_gym_clears_recurrent`, `hard_env_spec`, `learning_verdict`. width는 config.hidden으로
  **자유 조절(엔진 변경 불요)**. GRU는 단층만(더 깊은 arch=별개 heavy task, 본 task 밖).
- 판정: `headroom.classify_headroom(frac=0.75,k=1.0)` — #3와 동일 (pre-registered SSOT).
- 템플릿: `ppo_baseline.py:124-179` `_run_strength_compare` — capacity×budget sweep + best-non-tiny
  선택 + non-vacuity guard + classify_headroom. 이걸 **recurrent PPO 버전으로** 재사용.
- #3 스크립트 `hard_benchmark_memory.py` — config 상수·oracle 계산·eval 야드스틱 mirror.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/headroom.py` | 신규 순수 함수 `classify_scaled_headroom` (sweep 결과 dict + oracle + tiny_label → best-non-tiny 선택 + verdict/non_vacuous/exceeds) | **중** | additive·numpy-only·기존 `classify_headroom` 무변경 → **CI에서 jax 없이 판정규칙 단위테스트 가능** |
| `scripts/sota_headroom.py` (신규) | hard_env_spec에서 recurrent PPO capacity+budget sweep → 헬퍼로 분류·출력 | 낮음 | `[jax]`+`[rl]` 필요, CPU |
| `tests/test_sota_headroom.py` (신규) | `classify_scaled_headroom` 5-branch 단위테스트(robust/closes/exceeds/vacuous/inconclusive + 경계·입력검증) | 낮음 | numpy-only, CI |

### 영향 범위 (import 그래프)

- `classify_scaled_headroom`는 `classify_headroom`을 내부 재사용(중복 규칙 0). headroom.py는 CI(numpy)
  경로 — jax 미의존 유지(신규 함수도 numpy-only). 기존 headroom import처(ppo_baseline·hard_benchmark_
  memory·multitype_boss_headroom) 무영향(순수 추가).
- 학습 코드(jax_train) **무변경** — width는 기존 config.hidden 레버로만 조절.

## Step별 계획

1. **headroom.py 순수 헬퍼** — `classify_scaled_headroom(sweep: dict[str, Sequence[float]], oracle,
   *, tiny_label, frac=0.75, k=1.0) -> ScaledHeadroomVerdict`. 로직: tiny 제외 best-mean config 선택
   → `classify_headroom(best_runs, oracle, frac, k)` → non_vacuous(best_mean > tiny_mean)·exceeds
   (best_mean > oracle) 플래그. 반환 NamedTuple(직렬화·결정론). 빈 sweep·non-positive oracle raise.
2. **tests** — 5-branch(robust/closes/exceeds/vacuous/inconclusive) + tiny 제외 선택 + 경계·입력검증.
   `ppo_baseline`의 branch 라벨과 정합.
3. **scout script** — `hard_benchmark_memory.py` config/oracle mirror. recurrent PPO를 사전약정 sweep
   grid로 학습·held-out eval → `classify_scaled_headroom` → 5-branch 출력. sweep 전체·oracle·winnable·
   #3 baseline(h128) 대비 출력. honest NOTE. `--quick`(smoke)·`--runs N`.
4. **본측정** — full budget로 완주, 사전약정 branch 그대로 보고(reframe 포함).

## 사전약정 (G1 freeze — 데이터 무관 불변)

- **sweep grid**(freeze): tiny=`GRU h128`(=#3 published) / wide=`h256` / wider=`h384`(또는 h256+
  long budget). budget: base_iters=300(=#3 full), long_iters=600(scaled config에 부여).
- **best 선택 규칙**(freeze): tiny 제외 config 중 **held-out mean 최대**를 "strong baseline"으로.
  (최고성능 = 정직한 "가장 강한 scaled". 최심/최장 아님 — over-budget underfit 회피.)
- **판정**(freeze): `classify_headroom(frac=0.75, k=1.0)` on best-scaled runs. non-vacuity(best>tiny)
  미충족 시 verdict 보류. exceeds(best>oracle) 시 (c).
- **runs**(freeze): 기본 3(mean±std), opt-bound가 0.75·oracle의 ±0.3 gym 이내 **borderline** 시 5로
  확충(#3 3→5 seed 규율 계승). **임계·frac·k는 확충해도 불변.**

## 검증 방법

- `.venv/bin/python -m pytest -q` → 746 + 신규(헬퍼 단위테스트) 무회귀 green.
- `.venv/bin/python -m mypy src` + `ruff check .` → headroom.py(신규 함수) clean.
- `.venv/bin/python scripts/sota_headroom.py --quick` → smoke(작은 budget) 무오류: sweep 출력·
  oracle winnable·branch 판정. **본측정은 full budget 별도 실행**(CPU, background 가능).

## 리스크

- **R1 (CPU 비용)**: recurrent PPO는 hidden replay가 width² — h384/600iter × 3 config × 3 run은
  CPU에서 무거움(30–60분+). **완화**: `--quick` smoke로 파이프라인 검증 후 full은 background 실행.
  sweep 3 config·runs 3 고정, borderline만 5.
- **R2 (best-config 사후선택 = p-hacking)**: 여러 config 중 유리한 것 고르면 편향. **완화**: 선택
  규칙(held-out mean 최대)·grid·runs escalation을 **데이터 전 freeze**, sweep 전체 출력(비단조성 가시화).
- **R3 (여전히 SOTA 아님 = 과대해석)**: robust여도 "SOTA에도 hard 입증" 금지 — "scaled baseline에도
  headroom 유지 → 강화, SOTA는 OPEN"으로만. **완화**: honest NOTE + report 경계 명시.
- **R4 (VACUOUS)**: scaled config가 tiny를 못 이기면(학습 실패) robust verdict 무의미. **완화**:
  non-vacuity guard가 verdict 보류 → 정직 보고(학습 튜닝 후속).

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `headroom.classify_scaled_headroom` 신규(순수·numpy·결정론) — best-non-tiny 선택 +
  `classify_headroom` 위임 + non_vacuous/exceeds 플래그. 기존 `classify_headroom` 무변경.
- **AC2**: 단위테스트가 5-branch(robust/closes/exceeds/vacuous/inconclusive) + tiny-제외 선택 +
  경계(빈 sweep·non-positive oracle raise)를 커버.
- **AC3**: 전체 기존 스위트 무회귀(746 green), ruff/mypy clean.
- **AC4**: `scripts/sota_headroom.py --quick`가 무오류로 recurrent PPO sweep·oracle winnable·
  #3 h128 대비·사전약정 branch 판정을 출력(pipeline 검증). script가 판정 전 사전약정 규칙 출력.
- **AC5**: 본측정(full budget, ≥3 run) 완주 — 사전약정 branch를 **그대로** 보고(reframe/robust/
   vacuous 무관). 정직 라벨(CPU·runs·non-SOTA·oracle proxy·scaled-not-arch·frozen) 명시.
