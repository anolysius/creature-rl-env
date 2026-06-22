---
slug: generalization-harness
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
milestone: M2
exit_criteria: M2-EC4
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/generalization.py
  - tests/test_generalization.py
  - scripts/train_ppo.py
extracted_to: []
supersedes: []
---

# generalization-harness (M2-EC4)

> 작성일: 2026-06-21 | 상태: 계획

## 목표

**PPO 를 train 시드로 학습 → train(held-in) + test(held-out) 양쪽에서 평가 → train-vs-test
일반화 갭을 측정·리포트** 한다 (Procgen 관례). 이것이 M2 의 마지막 미충족 EC(M2-EC4)이며,
M3 리더보드(M3-EC1) + 킬러 데모(M3-EC6 "unseen 시드에서도 보스 격파")의 토대다.

핵심 = **정책-비의존(policy-agnostic) numpy-only 측정 하네스**. PPO 는 그 하네스의 한 소비자일
뿐이며 `[rl]` extra(torch/sb3) 뒤에 격리한다. 하네스 자체(롤아웃·평균·갭·리포트)는 core 의존성
(numpy)만으로 동작·테스트되어 CI 에서 항상 검증된다.

## 선행 조건

- ✅ M2-EC1 `procgen-region` — `train_seeds(n, start=0)` / `heldout_seeds(n)` / `is_held_out(seed)`,
  `TEST_SEED_OFFSET=1_000_000` (`src/critter_gym/region.py`).
- ✅ M2-EC2/EC3 `procgen-typechart` — `vary=True` 시 시드별 새 맵 **+ 새 타입표**(infer-the-meta),
  누수 0. 등록된 env id `CritterGym-procgen-v0` (`registration.py`, `kwargs={"vary": True}`).
- ✅ `baselines.py` — `random_policy(obs, rng)`, `greedy_policy(obs, grid_size)` (테스트용 정책).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/generalization.py` | **신규** | 높음 (신규 공개 API) | numpy-only 측정 하네스 |
| `tests/test_generalization.py` | **신규** | 중 | 하네스를 baseline 정책으로 검증 (torch 불요) |
| `scripts/train_ppo.py` | 리팩터 | 중 | 하네스 소비자로 재작성; 시드 split 버그 수정 |

### 영향 범위 (import 그래프)

- `generalization.py` → import `envs.critter_env.CritterEnv`, `region.{train_seeds,heldout_seeds}`.
  **torch/sb3 import 금지** (core 순수성 — `tests/test_generalization.py` 가 import 가드로 검증).
- `test_generalization.py` → import `generalization`, `baselines`, `region`. numpy-only.
- `train_ppo.py` → import `generalization`(하네스), `baselines`(random 기준선); sb3 는 함수 내부
  지연 import (없으면 exit 2, 기존 패턴 유지).
- 기존 `src/**`(env·battle·region·typechart) **무수정** — 순수 추가 + 스크립트 1개 리팩터.

## 기존 train_ppo.py 의 결함 (이번에 정정)

1. `HELDOUT = range(50_000, 50_120)` 하드코딩 → `TEST_SEED_OFFSET=1_000_000` 이므로 50_000 은
   **사실 train 영역**(held-out 아님). split API 를 우회한 채 "held-out" 이라 호칭 → 누수성 오해.
2. `CritterEnv(**CFG)` 를 `vary=False` 로 호출 → 타입표 변형(infer-the-meta) 미적용. train/test 가
   시드 분리만 되고 "새 타입표" moat 을 실측하지 않음.
3. train 시드 풀이 불명확(DummyVecEnv 가 무시드 reset) → "train 점수" 정의가 없어 **갭 측정 불가**.

→ 새 하네스는 `train_seeds()`/`heldout_seeds()` + `vary=True` 로 셋을 모두 해소한다.

## Step별 계획

### Step 1 — 측정 하네스 (`generalization.py`, numpy-only) [RED→GREEN]

공개 API (정책-비의존):

```python
PolicyFn = Callable[[Obs], int]          # obs -> action
EnvFactory = Callable[[], CritterEnv]     # 동일 config 의 새 env 생성

def rollout(env_factory, policy, seed) -> float:
    """단일 에피소드를 고정 seed 로 실행, 총 보상 반환 (결정론)."""

@dataclass(frozen=True)
class EvalResult:
    seeds: tuple[int, ...]; returns: tuple[float, ...]
    mean: float; std: float; n: int

def evaluate(env_factory, policy, seeds) -> EvalResult: ...

@dataclass(frozen=True)
class GapReport:
    train: EvalResult; test: EvalResult
    gap: float          # train.mean - test.mean (Procgen 관례: 양수 = 과적합)
    def to_dict(self) -> dict: ...        # 리더보드/JSON 행

def measure_generalization(env_factory, policy, train_seeds, test_seeds) -> GapReport: ...
def format_report(report: GapReport) -> str:   # 사람용 markdown 표

def split_train_pool(seeds, n_eval) -> tuple[tuple[int,...], tuple[int,...]]:
    """train 풀(연속 range)을 학습용 ∥ held-in 평가용 으로 **disjoint** 분할.
    (앞 = 학습, 뒤 n_eval = held-in eval). 둘 다 < OFFSET, 교집합 ∅ 보장."""
```

- `train_seeds`(held-in eval 시드) 는 split 의 train 영역(< OFFSET), `test_seeds` 는 held-out
  (≥ OFFSET) 에서 와야 함. 하네스가 `is_held_out` 로 **인자 정합성 검증**(train 인자에 held-out
  시드 섞이면 ValueError) → M2-EC3 누수 0 을 호출부에서도 강제.
- **held-in eval ∩ 학습 시드 = ∅** 는 `split_train_pool` 이 구조적으로 보장 — 갭 낙관편향
  방지의 load-bearing 불변식. region.py 가 split helper 를 안 줘서 하네스가 책임진다.
- `to_dict()` 키는 안정 계약: `{"train_mean","test_mean","gap","n_train","n_test"}` (M3 리더보드
  행 forward-hook). `format_report` 는 이 키들을 사람용 markdown 표로 렌더.

### Step 2 — 하네스 테스트 (`test_generalization.py`, baseline 정책) [RED→GREEN]

torch 없이 검증 (CI 항상 실행):
- `rollout` 결정론: 같은 seed → 같은 보상 (2회 호출 동일).
- `evaluate` 산술: `n == len(seeds)`, `mean == np.mean(returns)`.
- `measure_generalization`: `gap == train.mean - test.mean`; `vary=True` env_factory 로 동작.
- 정합성 가드: train 인자에 `heldout_seeds()` 시드 → ValueError.
- **disjointness**: `split_train_pool(train_seeds(N), n_eval)` 의 두 출력이 교집합 ∅ +
  합집합 = 입력 (boolean 테스트 — 갭 낙관편향 핵심 불변식).
- **리포트 계약**: `to_dict()` 가 `{train_mean,test_mean,gap,n_train,n_test}` 키를 모두 가짐;
  `format_report()` 출력 문자열에 세 수치(train/test/gap)가 포함 (numpy-only boolean 검증).
- **import 순수성**: `generalization` 모듈이 `torch`/`stable_baselines3` 를 import 하지 않음
  (`sys.modules` 검사 또는 소스 정적 검사).

### Step 3 — `train_ppo.py` 를 하네스 소비자로 리팩터 [GREEN]

- **CFG 시그니처 정정**: 기존 `CFG` 는 `CritterEnv` 에 없는 `target_catches=3` kwarg 를 가져 실행 시
  TypeError (dead bug — `[rl]` 미설치라 CI 미검출). 실제 시그니처
  `(grid_size, num_creatures, num_gyms, max_steps, patch_radius, vary)` 로 재구성 —
  `target_catches` 제거, 필요시 `num_gyms` 명시. `vary=True` 추가.
- `vary=True` 의 동일 config env factory.
- train/eval 시드 분할: `learn, heldin = split_train_pool(train_seeds(N_TRAIN), n_eval=N_EVAL)`.
  학습은 `learn` 풀에서(에피소드별 시드 순환 — DummyVecEnv reset 시 풀에서 시드 주입),
  held-in eval = `heldin`(학습과 disjoint), held-out eval = `heldout_seeds(N_TEST)`.
- 학습 종료 후 `measure_generalization(...)` → `format_report()` 출력 (train mean / test mean / gap).
- 통과 기준 유지·명확화: held-out mean ≥ random held-out mean + MARGIN (학습이 실제로 됐는지);
  갭은 리포트로 출력(임의 임계값으로 FAIL 시키지 않음 — 과적합은 측정 대상이지 실패 조건 아님).
- sb3 미설치 시 exit 2 (기존 패턴). `[rl]` extra 외 core/CI 무영향.

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build` (run-tdd.py COMMANDS).
- `python scripts/train_ppo.py --timesteps 40000` 는 `[rl]` extra 설치 시 수동 실행(CI 비포함) —
  갭 리포트가 train/test mean + gap 을 출력하는지 육안 확인 (plan acceptance 아님, 데모 확인용).
- 기존 71 tests 무회귀 + 신규 test_generalization.py green.

## 리스크

| 리스크 | 완화 |
|---|---|
| 하네스에 torch 의존이 새어들어 core CI 오염 | import 순수성 테스트(Step 2)로 가드 |
| train_ppo.py 가 CI 에서 실행돼 무거워짐 | scripts/ 비-testpaths + sb3 지연 import, 기존 정책 유지 |
| held-in eval 시드가 학습 시드와 겹쳐 "갭"이 낙관 편향 | `split_train_pool` 이 학습∥held-in 을 구조적 disjoint 분할 + boolean 테스트(AC#6) 강제 |
| 짧은 학습으로 PPO 가 random 도 못 이김(데모 flaky) | 쉬운 config 유지(기존 CFG 계열) + MARGIN 보수적; CI 비포함이라 게이트 비차단 |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/generalization.py` 가 **정책-비의존** train-vs-test 갭 측정 하네스를 제공
   (`evaluate` / `measure_generalization` / `GapReport.to_dict` / `format_report`).
2. 하네스는 **numpy-only** — `torch`/`stable_baselines3` 미import (import 순수성 테스트로 강제).
3. split 은 `train_seeds()`/`heldout_seeds()` 기반이며, train 인자에 held-out 시드 혼입 시 거부
   (M2-EC3 누수 0 호출부 강제). 하드코딩 50_000 류 제거.
4. 측정은 **결정론**(고정 seed → 고정 return) — `rollout` 재현성 테스트 통과.
5. 갭 측정은 **procgen 변형**(`vary=True`, test 시드 = 새 맵 + 새 타입표) 위에서 동작.
6. **held-in eval ∩ 학습 시드 = ∅** — `split_train_pool` 의 두 출력이 disjoint + 합집합=입력임을
   numpy-only 테스트가 boolean 검증 (갭 낙관편향 방지의 load-bearing 불변식).
7. **리포트 계약** — `GapReport.to_dict()` 가 `{train_mean,test_mean,gap,n_train,n_test}` 키를
   모두 제공하고 `format_report()` 출력에 세 수치가 포함됨을 numpy-only 테스트로 검증
   (M3 리더보드 행 forward-hook; `[rl]` 없이 CI 강제).
8. `scripts/train_ppo.py` 가 하네스를 사용해 `learn` 풀 학습 → held-in + held-out 평가 → gap
   리포트 출력. 기존 `target_catches` dead-kwarg 정정(유효 시그니처) + `vary=True`.
   `[rl]` extra 뒤 격리, core/CI 무영향.
9. `mypy src` · `ruff check .` · `pytest -q` · `python -m build` 전부 통과 + 기존 71 tests 무회귀.
