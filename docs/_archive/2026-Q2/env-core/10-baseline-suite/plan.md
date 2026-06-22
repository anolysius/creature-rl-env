---
slug: baseline-suite
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
milestone: M3
exit_criteria: M3-EC1
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/scoreboard.py
  - tests/test_scoreboard.py
  - scripts/benchmark.py
  - pyproject.toml
extracted_to: []
supersedes: []
---

# baseline-suite (M3-EC1)

> 작성일: 2026-06-21 | 상태: 계획

## 목표

**베이스라인 4종(random / scripted / PPO / recurrent)의 train+test 분리 점수표**를 재현 가능하게
생성한다 (M3-EC1). 이 점수표가 리더보드(M3-EC2)·측정 viz(M3-EC3)·킬러 데모(M3-EC6)의 **데이터
토대**다. M2 에서 만든 `critter_gym.generalization` 갭 하네스를 베이스라인 N개로 확장하는 얇은
오케스트레이션 레이어 `critter_gym.scoreboard` 를 신설한다.

generalization-harness 의 패턴을 그대로 계승: **점수표 빌더는 numpy-only**(core CI 가 random+scripted
2종으로 상시 검증), 무거운 학습 베이스라인(PPO·recurrent)은 `[rl]` extra 뒤 `scripts/benchmark.py`
한 소비자로 격리.

## 선행 조건

- ✅ M2-EC4 `generalization-harness` — `measure_generalization`/`GapReport`/`split_train_pool`
  (`src/critter_gym/generalization.py`). 점수표는 베이스라인마다 이걸 1회씩 호출.
- ✅ `baselines.py` — `random_policy`(floor), `greedy_policy`(scripted). PPO 소비자 패턴은
  `scripts/train_ppo.py` 에 이미 존재(재사용).
- recurrent 베이스라인 = `sb3_contrib.RecurrentPPO`(`MultiInputLstmPolicy`) — `sb3-contrib` 의존
  추가 필요(현재 `[rl]` extra 에 없음).

## 기존 `benchmark.py` 의 결함 (이번에 정정)

train_ppo.py 와 동일 부류 (generalization-harness 에서 train_ppo 만 고쳤고 benchmark 는 미정정):
1. `CritterEnv().target_catches` — env 에 `target_catches` **속성이 없음** → 실행 시 AttributeError
   (CLI 가 CI 비포함이라 미검출).
2. `range(50_000, …)` 를 "held-out" 이라 호칭 — `TEST_SEED_OFFSET=1_000_000` 기준 사실 **train 영역**.
3. `CritterEnv()` (`vary=False`) — procgen 변형 미사용, train/test 의미가 없음.
4. random/greedy **2종만**, train/test 분리 없음 — M3-EC1 의 4종 train+test 표가 아님.

→ scoreboard 빌더 + split API + `vary=True` 로 정정하며 4종 train+test 표로 격상.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/scoreboard.py` | **신규** | 높음 (신규 공개 API) | numpy-only N-베이스라인 점수표 빌더 |
| `tests/test_scoreboard.py` | **신규** | 중 | random+scripted 로 빌더 검증 (torch 불요) |
| `scripts/benchmark.py` | 리팩터 | 중 | 4종 train+test 표 소비자; dead-bug 정정 |
| `pyproject.toml` | 수정 | 낮음 | `[rl]` extra 에 `sb3-contrib` 추가 (RecurrentPPO) |

### 영향 범위 (import 그래프)

- `scoreboard.py` → import `generalization.{measure_generalization, GapReport, EnvFactory, PolicyFn}`.
  **torch/sb3 import 금지** (import 순수성 테스트로 가드).
- `test_scoreboard.py` → import `scoreboard`, `baselines`, `region`. numpy-only.
- `benchmark.py` → import `scoreboard`(빌더), `baselines`(random/scripted); sb3/sb3-contrib 는
  함수 내부 지연 import (없으면 안내 후 부분 표 또는 exit). 기존 throughput 측정은 유지.
- 기존 `src/**`(generalization·env·region) **무수정** — 순수 추가 + 스크립트·pyproject.

## Step별 계획

### Step 1 — 점수표 빌더 (`scoreboard.py`, numpy-only) [RED→GREEN]

```python
@dataclass(frozen=True)
class BaselineRow:
    name: str
    report: GapReport          # train(held-in)/test(held-out)/gap

@dataclass(frozen=True)
class ScoreTable:
    rows: tuple[BaselineRow, ...]
    def to_markdown(self) -> str: ...           # | baseline | train | test | gap |
    def to_dict(self) -> dict[str, dict]: ...    # {name: GapReport.to_dict()} — M3-EC2 forward-hook

def score_baselines(
    env_factory: EnvFactory,
    policies: dict[str, PolicyFn],      # name -> policy
    train_seeds, test_seeds,
) -> ScoreTable:
    """각 베이스라인을 measure_generalization 으로 평가해 한 표로 모음.
    split 누수 가드는 measure_generalization 에서 상속(재검증 불필요)."""
```

- 정책-비의존: random/scripted 는 물론 PPO·recurrent(호출부에서 obs→action 람다로 래핑)도 동일 경로.
- 결정론: 결정론 정책이면 동일 seeds → 동일 표. `to_dict` 키는 M3-EC2 리더보드 forward-hook.

### Step 2 — 빌더 테스트 (`test_scoreboard.py`, numpy-only) [RED→GREEN]

torch 없이 (CI 항상):
- `score_baselines({random, scripted}, …)` 가 2행 표 생성; 각 행 train/test/gap 일관.
- **벤치마크 유효성 가드**: scripted(greedy) test_mean > random test_mean (spread 보존 — 표 형태로).
- `to_markdown` 에 베이스라인명 + 세 수치(train/test/gap) 포함; `to_dict` 키 = 베이스라인명, 값 키 =
  `{train_mean,test_mean,gap,n_train,n_test}`.
- 결정론: 같은 입력 → 같은 `to_dict`.
- import 순수성: `scoreboard` 가 torch/sb3 미import (소스 정적 검사).
- split 누수 가드 상속 확인: train 인자에 held-out 혼입 → ValueError (measure_generalization 경유).
- **`[rl]` smoke (heavy 경로 검증)**: `pytest.importorskip("stable_baselines3"/"sb3_contrib")` 로
  가드한 테스트 — PPO(`MultiInputPolicy`) + RecurrentPPO(`MultiInputLstmPolicy`) 를 Dict-obs env 에
  구성하고 1-step predict 를 정책으로 래핑해 `score_baselines` 가 4행 표를 오류 없이 생성하는지 확인.
  sb3 미설치 core CI 에선 **skip**(numpy-only 순수성 무손상), `[rl]` 설치 시 lazy-import 분기 검증
  → "4종 표" 주장의 비-CI 부분을 boolean 화 + dead-bug 재발 방지.

### Step 3 — `benchmark.py` 4종 표 소비자로 리팩터 [GREEN]

- `vary=True` env factory + `split_train_pool(train_seeds(N), n_eval)` (held-in) + `heldout_seeds(N)`.
- core 베이스라인(random/scripted)은 항상; PPO/recurrent 는 sb3/sb3-contrib **지연 import** 후
  짧게 학습(train_ppo 패턴 재사용, `_SeededReset` 로 learn 풀 한정)해 표에 추가. 미설치 시 안내 +
  core 2행만 출력(비차단).
- `score_baselines(...).to_markdown()` 출력 + 기존 throughput(steps/s) 라인 유지.
- dead-bug 정정: `target_catches` 속성참조 제거(에피소드 최대점수는 표에 불필요 — 베이스라인 spread 가
  유효성 신호), `range(50_000)` → split API, `vary=False` → `vary=True`.

### Step 4 — `pyproject.toml` [GREEN]

- `[rl]` extra 에 `sb3-contrib>=2.0` 추가 (RecurrentPPO). core/dev 의존 무변(numpy-only 유지).

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build`.
- `python scripts/benchmark.py`(+`[rl]`) 는 수동 — 4종 train+test 표 + throughput 육안 확인(데모,
  acceptance 아님). core 베이스라인만으로도 2행 표가 떠야 함(sb3 미설치 graceful).
- 기존 81 tests 무회귀 + 신규 test_scoreboard.py green.

## 리스크

| 리스크 | 완화 |
|---|---|
| scoreboard 에 torch 의존 누수로 core CI 오염 | import 순수성 테스트로 가드 |
| benchmark.py 가 CI 에서 무겁게 실행 | scripts/ 비-testpaths + sb3 지연 import (기존 정책) |
| RecurrentPPO API/Dict obs 비호환 | `MultiInputLstmPolicy` 사용; CI 비포함이라 게이트 비차단 (수동 데모) |
| 짧은 학습으로 PPO/recurrent 표가 빈약 | 데모용 — spread/표 형태가 산출물, 학습 품질은 acceptance 아님 |
| pyproject 의존 추가가 core 설치 무겁게 | `sb3-contrib` 는 `[rl]` extra 한정 — core/CI 무영향 (build 로 검증) |
| `to_dict` 키 `train_mean`/`test_mean` 가 미결 명명 (generalization.py docstring·milestones M3-EC2 가 "리더보드 freeze 전 heldin/heldout 재명명 고려"로 표시) 인데 scoreboard 가 그대로 forward-hook 고정 | 본 task 는 같은 키 계승(무회귀)만; **개명 결정은 M3-EC2(리더보드 포맷)에서** — scoreboard 는 GapReport.to_dict 위임이라 단일 지점 개명으로 전파됨(추가 부채 없음) |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/scoreboard.py` 가 **정책-비의존** N-베이스라인 점수표 빌더 제공
   (`score_baselines` → `ScoreTable` with `to_markdown`/`to_dict`, train/test 분리 + gap).
2. 빌더는 **numpy-only** — `torch`/`stable_baselines3`/`sb3_contrib` 미import (import 순수성 테스트).
3. 점수표는 split API(`train_seeds`/`heldout_seeds`) 기반이며, split 누수 가드를
   `measure_generalization` 에서 상속(train 인자 held-out 혼입 → ValueError).
4. **결정론** — 결정론 정책 + 고정 seeds → 동일 `to_dict`/표.
5. **벤치마크 유효성** — CI 가 random+scripted 2종으로 표를 생성하고 scripted test_mean > random
   test_mean(spread) 을 boolean 검증.
6. **리포트 계약** — `to_markdown()` 에 베이스라인명 + train/test/gap 수치 포함; `to_dict()` =
   `{베이스라인명: {train_mean,test_mean,gap,n_train,n_test}}` (M3-EC2 forward-hook, numpy-only CI 강제).
7. **(CI-검증 가능)** `scripts/benchmark.py` 가 scoreboard 빌더를 사용하도록 리팩터되고, 기존
   dead-bug(`target_catches` AttributeError, `range(50_000)` train-영역 오칭, `vary=False`)이 정정됨;
   sb3 미설치 환경에서 **graceful**(core 2행 random/scripted 표 + throughput 출력, 비차단). ruff 통과.
8. **(`[rl]` smoke 로 검증)** PPO(`MultiInputPolicy`)+recurrent(`sb3_contrib.RecurrentPPO`,
   `MultiInputLstmPolicy`) lazy-import 분기가 구성 오류 없이 동작 — `importorskip` 가드 smoke 가
   4종 표 생성을 확인(core CI 에선 skip). `sb3-contrib` 가 `[rl]` extra 에 추가됨.
9. `mypy src` · `ruff check .` · `pytest -q` · `python -m build` 통과 + 기존 81 tests 무회귀.
