---
slug: env-validation
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/baselines.py
  - src/critter_gym/__init__.py
  - tests/**
  - scripts/**
  - pyproject.toml
extracted_to: []
supersedes: []
---

# env-validation — 벤치마크 성립성 검증 레이어

> 작성일: 2026-06-21 | 상태: 계획

## 목표
스캐폴딩(`01-scaffolding`)이 *코드가 도는가*를 증명했다면, 본 task 는 *이게 RL **벤치마크**로 성립하는가*를
**재현 가능하게** 박는다. 손으로 한 번 보여준 검증(check_env / random·PPO spread / held-out 일반화 /
steps/s)을 **테스트·베이스라인·스크립트**로 고정해 env 를 키울 때마다 도는 회귀 가드로 만든다.

성립 3조건 (DESIGN §5):
1. **Gymnasium 준수** — 표준 `check_env` 통과 (생태계 상호운용 전제).
2. **베이스라인 spread** — random < scripted (자명하지도, 불가능하지도 않음). DESIGN §5 baselines.
3. **일반화 측정** — train/test 시드 분리 점수 (Procgen 관례, 우리 moat).
4. **throughput** — steps/s 측정 (DESIGN §4 채택 게이트, 회귀 가드).

## 선행 조건
- `01-scaffolding` 머지 완료 (main). `CritterEnv` + `gymnasium.make("CritterGym-v0")` 존재.
- 무거운 학습 deps(torch/sb3)는 **core 의존성에 넣지 않는다** — optional extra `[rl]` 로 분리.
  기본 test суite·CI 는 numpy 만으로 돈다.
- 제품 코드 변경은 `feature/*` 브랜치 (G1 후).

## 작업 범위
### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | criticality | 비고 |
|---|---|---|---|
| `src/critter_gym/baselines.py` | 신규 | critical | `random_policy`, `greedy_policy` (numpy only, 패키지 동봉 — DESIGN §5) |
| `src/critter_gym/__init__.py` | 갱신 | critical | baselines export |
| `tests/test_compliance.py` | 신규 | low | `gymnasium.utils.env_checker.check_env` 통과 |
| `tests/test_baselines.py` | 신규 | low | spread 가드 (greedy>random>0) + 정책별 유효 행동 |
| `tests/test_determinism.py` | 신규 | low | 동일 시드 → 전체 trajectory 동일; 다른 시드 → 다름 |
| `tests/test_throughput.py` | 신규 | low | steps/s 측정 + 보수적 floor 회귀 가드 |
| `scripts/benchmark.py` | 신규 | critical | CLI — held-out 시드 random/greedy 평균 + steps/s 리포트 |
| `scripts/train_ppo.py` | 신규 | critical | **optional** PPO 데모 (`[rl]` extra). test suite 제외 (무거움) |
| `pyproject.toml` | 갱신 | critical | optional-deps `[rl]` (stable-baselines3) 추가 |

### 영향 범위 (import 그래프)
- `baselines.py` → `numpy` + `critter_gym.envs.critter_env` 의 액션 상수만. 신규, 기존 영향 없음.
- core deps 불변 (gymnasium, numpy). `[rl]` 은 opt-in — 기본 사용자·CI 영향 0.
- `scripts/**` 는 패키지 import 외 부수효과 없음 (실행형).

## Step별 계획
1. **베이스라인** — `baselines.py`:
   - `random_policy(obs, rng) -> int`: 균등 랜덤 행동.
   - `greedy_policy(obs) -> int`: `local_patch` 에 창조물 보이면 가장 가까운 쪽으로 이동, 내 칸이면 CATCH;
     안 보이면 결정론적 탐험(스텝 카운트 기반 sweep). 부분관찰에서 동작.
   - 둘 다 순수 함수 (numpy), 학습 deps 무관.
2. **compliance** — `test_compliance.py`: `check_env(CritterEnv(), skip_render_check=True)` 무에러.
3. **spread 가드** — `test_baselines.py`: 고정 held-out 시드 집합(예: 50000~50099)에서
   `mean(greedy) > mean(random)` ∧ `mean(random) > 0` ∧ `mean(greedy) ≤ target_catches`.
4. **determinism** — `test_determinism.py`: 동일 시드 + 동일 정책 → step별 (obs,reward) 시퀀스 완전 동일;
   다른 시드 → 초기 obs 다름.
5. **throughput** — `test_throughput.py`: random 정책으로 N(예: 20k) 스텝 측정, steps/s 계산,
   보수적 floor(예: ≥5k/s — 파국적 회귀만 잡음) 통과. 실제 수치는 report 에 기록(50k 목표 대비).
6. **CLI 리포트** — `scripts/benchmark.py`: `--seeds`/`--episodes` 인자로 random·greedy 평균 + steps/s 출력.
   `scripts/train_ppo.py`: `[rl]` extra 설치 시 PPO 학습 곡선(held-out) 출력 — 본 세션 데모의 재현.
7. **green** — ruff/mypy/pytest/build (core, torch 없이) 통과.

## 검증 방법
- `pytest -q` — compliance/spread/determinism/throughput 4 suite (numpy only, 빠름).
- `python scripts/benchmark.py` — 사람이 읽는 리포트 (수치는 report.md 에 캡처).
- PPO 곡선은 `[rl]` extra 옵트인 — CI 비포함, report 에 관측치 기록.

## 리스크
- **greedy 탐험 설계**: 부분관찰에서 탐험이 부실하면 spread 가 작아 가드가 약함. → sweep 탐험으로
  random 대비 유의미 우위 확보. 그래도 약하면 patch_radius·creature 밀도 조정은 *테스트 픽스처* 한정
  (env 기본값 불변 — scope creep 방지).
- **throughput floor 의 환경 의존성**: CI 머신 편차 → 보수적 floor(5k)로 false-fail 회피, 실수치는 기록.
- **PPO 비결정성**: 데모 스크립트라 seed 고정하되 테스트 단언 안 함(무거움+머신편차). 회귀 가드는
  scripted spread 가 담당.
- **check_env 경고**: gymnasium 버전별 경고 차이 → 에러만 fail, 경고는 기록.

## Acceptance Criteria (G1 통과 시 freeze)
- [ ] **AC1 (Gymnasium 준수)**: `gymnasium.utils.env_checker.check_env(CritterEnv(), skip_render_check=True)`
  가 예외 없이 통과 (test).
- [ ] **AC2 (베이스라인 존재)**: `random_policy`·`greedy_policy` 가 패키지에서 import 가능, 임의 obs 에
  대해 유효 행동(0–5) 반환.
- [ ] **AC3 (spread 가드)**: 고정 held-out 시드 집합에서 `mean(greedy) > mean(random)` ∧
  `mean(random) > 0` ∧ `mean(greedy) ≤ target_catches` (env 가 자명하지도 불가능하지도 않음, test).
- [ ] **AC4 (일반화/결정론)**: 동일 시드+동일 정책 → 전체 trajectory (obs,reward 시퀀스) 완전 동일;
  다른 시드 → 다른 초기 obs (test). held-out 시드 평가가 `benchmark.py` 로 재현 가능.
- [ ] **AC5 (throughput)**: `test_throughput.py` 가 random 정책으로 ≥20,000 step 을 돌려 steps/s 를
  측정하고 **`rate >= 5_000` (steps/s/core) 를 단언**(boolean 가드 — 파국적 회귀만 잡는 보수적 floor).
  측정된 실제 수치는 report.md 에 DESIGN §4 목표(≥50k/s/core) 대비 기록.
- [ ] **AC6 (PPO 데모 재현)**: `scripts/train_ppo.py` 가 `[rl]` extra 하에 동일 held-out 시드 집합에서
  random 평균과 학습후 PPO 평균을 측정하고 **`trained_mean >= random_mean + 0.5` 를 단언**(미충족 시
  스크립트 exit≠0 — 수동 실행이지만 boolean 판정). 두 수치(+ 학습 곡선)를 report.md 에 캡처.
  core test suite·deps 에는 torch/sb3 **불포함**.
- [ ] **AC7 (툴체인 green)**: core 환경(torch 없이) 에서 `ruff check .` ∧ `mypy src` ∧ `pytest -q` ∧
  `python -m build` 모두 통과.
