---
slug: metrics-viz
initiative: env-core
status: active
started: 2026-06-22
acceptance_freeze: true
milestone: M3
exit_criteria: M3-EC3
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/viz.py
  - src/critter_gym/leaderboard.py
  - tests/test_viz.py
  - scripts/benchmark.py
  - scripts/train_ppo.py
  - pyproject.toml
extracted_to: []
supersedes: []
---

# metrics-viz (M3-EC3)

> 작성일: 2026-06-22 | 상태: 계획

## 목표

**측정 viz** 를 만든다 (M3-EC3) — 4종 차트: **학습곡선 · 일반화 갭 · 베이스라인 spread · 시드 분포**.
이건 **게임 월드 렌더링이 아니라 연구자용 메트릭 플롯**이다(고객=RL 연구자, CLAUDE.md 북극성:
art·juice 최저). 방금 만든 `scoreboard`/`leaderboard`/`generalization` 의 데이터를 그래프로 그린다.

핵심 격리 패턴(generalization·baseline·leaderboard 와 동일): **plot-ready 데이터 정형은 numpy-only**
(core CI 가 검증), **matplotlib 드로잉은 `[viz]` optional extra 뒤로** 지연 import 격리. core/CI 는
matplotlib 없이도 viz 모듈 import + 데이터 헬퍼 테스트가 돈다.

## 선행 조건

- ✅ M3-EC1/EC2 — `scoreboard.ScoreTable`(베이스라인별 `GapReport`, `.test.returns` per-seed),
  `leaderboard.Leaderboard`. 갭/​spread/​시드분포 데이터원.
- ✅ `generalization.EvalResult.returns` — held-out per-seed 리턴(시드 분포 데이터).
- 학습곡선 데이터원 = `scripts/train_ppo.py` 가 이미 산출하는 per-chunk held-in/held-out 평균 시계열
  (본 task 에서 `LearningCurve` 컨테이너로 표준화).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/viz.py` | **신규** | 높음 (신규 공개 viz API) | 데이터 헬퍼(numpy-only) + plot 함수(지연 matplotlib) |
| `src/critter_gym/leaderboard.py` | 수정 | 낮음 | `Leaderboard.from_score_table(spec, table)` 분리 — ScoreTable 1회로 board+plot 공유(중복 평가 회피) |
| `tests/test_viz.py` | **신규** | 중 | core: 데이터 헬퍼+import순수성 / `[viz]` smoke: Figure·savefig |
| `scripts/benchmark.py` | 수정 | 낮음 | ScoreTable 1회 산출 → 리더보드 + `--plot DIR` 4종 차트(있을 때), graceful |
| `scripts/train_ppo.py` | 수정 | 낮음 | per-chunk 시계열을 `LearningCurve` 로 표준화 + `[viz]` 시 학습곡선 저장 (실제 데이터원) |
| `pyproject.toml` | 수정 | 낮음 | `[viz]` extra = matplotlib (core/dev 무변) |

### 영향 범위 (import 그래프)

- `viz.py` → import `scoreboard.ScoreTable`, `generalization.EvalResult`(타입), numpy.
  **matplotlib 은 plot 함수 내부 지연 import**(모듈은 matplotlib 없이 import 가능) +
  `matplotlib.use("Agg")`(headless). 측정 모듈(generalization/scoreboard/leaderboard)은 viz·matplotlib
  **미import**(import 순수성 테스트로 가드 — 의존 방향 단방향).
- `benchmark.py` → `viz` 의 plot 함수 지연 사용(없으면 안내, 비차단).
- 기존 `env`·`region`·측정 스택 **무수정**.

## Step별 계획

### Step 1 — `viz.py` 데이터 헬퍼 (numpy-only) [RED→GREEN]

matplotlib 불요 — `ScoreTable`/`EvalResult` 에서 plot-ready 배열 추출 + 학습곡선 컨테이너:

```python
@dataclass(frozen=True)
class LearningCurve:
    timesteps: tuple[int, ...]
    heldin_means: tuple[float, ...]
    heldout_means: tuple[float, ...]

def spread_data(table) -> tuple[list[str], list[float]]:        # (names, heldout means)
def gap_data(table) -> tuple[list[str], list[float], list[float]]:  # names, heldin, heldout
def seed_distribution_data(table) -> dict[str, tuple[float,...]]:   # name -> held-out per-seed returns
```

### Step 2 — `viz.py` plot 함수 (지연 matplotlib, Agg) [GREEN]

```python
def plot_baseline_spread(table) -> "Figure":        # held-out 평균 막대(랭크순)
def plot_generalization_gap(table) -> "Figure":     # baseline 별 held-in vs held-out 그룹막대
def plot_seed_distributions(table) -> "Figure":     # held-out per-seed 분포(box/hist)
def plot_learning_curve(curve: LearningCurve) -> "Figure":  # held-in·held-out 2선 vs timesteps
def save_all(table, outdir, curve=None) -> list[str]:        # 편의 — 파일 경로들 반환
```

- 각 함수 첫 줄에서 `import matplotlib; matplotlib.use("Agg")` 지연 — display 불요(서버/CI 안전).
- Figure 만 반환(savefig 는 호출부) → 테스트가 axes/내용 검증 가능.

### Step 3 — `tests/test_viz.py` [RED→GREEN]

- **core(numpy-only)**: `spread_data`/`gap_data`/`seed_distribution_data` 정확성(이름·값 매핑,
  per-seed 길이) + `LearningCurve` 구성. `viz` 모듈이 matplotlib 미import(top-level) — import 순수성.
- **`[viz]` smoke**(`importorskip("matplotlib")`): 각 plot 함수가 Figure 반환 + 기대 axes/artist 수
  (예: spread = 막대 N개, gap = 그룹막대, 학습곡선 = 2선); `save_all` 이 tmp 에 PNG(비어있지 않음) 저장.
  core CI 에선 skip(matplotlib 미설치) → numpy-only 순수성 무손상.
- **측정 모듈 순수성**: `generalization`/`scoreboard`/`leaderboard` 가 `matplotlib`/`viz` 미import.

### Step 4 — 통합: `leaderboard` 분리 + `benchmark.py --plot` + `train_ppo` 곡선 + `pyproject` [GREEN]

- `leaderboard.py`: `Leaderboard.from_score_table(spec, table)` classmethod 추출(랭킹 로직 이전);
  `run_benchmark` 은 `score_baselines`→`from_score_table` 위임(동작 무변, 무회귀).
- `benchmark.py`: ScoreTable 을 **1회** 산출(`score_baselines`) → `Leaderboard.from_score_table` 로
  출력 + `--plot <dir>` 시 같은 table 로 `viz.save_all(table, dir, curve=None)` (per-seed 분포 포함).
  중복 평가 없음. matplotlib 미설치 시 안내 + skip(비차단).
- `train_ppo.py`: 기존 per-chunk held-in/held-out 평균 루프를 `LearningCurve` 로 누적(실제 데이터원);
  `[viz]` 설치 시 `plot_learning_curve(curve)` 저장. 개명 키(heldin/heldout) 기반.
- `pyproject.toml`: `[project.optional-dependencies]` 에 `viz = ["matplotlib>=3.7"]`.

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build`.
- `python scripts/benchmark.py --plot /tmp/cg`(+`[viz]`) 수동 — 4 PNG 생성 육안 확인(데모).
- 기존 92 tests 무회귀 + 신규 test_viz.py(core green, `[viz]` smoke skip-or-pass).

## 리스크

| 리스크 | 완화 |
|---|---|
| matplotlib 의존이 core CI 오염 | 지연 import + `[viz]` extra 격리 + import 순수성 테스트(측정 모듈·viz top-level) |
| display 없는 CI/서버에서 plot crash | `matplotlib.use("Agg")` headless 백엔드 강제 |
| viz 테스트가 vacuous(Figure 생성만 확인) | axes/artist 수·savefig 파일 비어있지 않음까지 검증 |
| 학습곡선이 합성 데이터로만 검증돼 실제 산출 안 됨 | `train_ppo.py` 가 실제 학습 루프에서 `LearningCurve` 누적+저장(데이터원); core 테스트는 합성으로 plot 함수 검증(이중 보장) |
| `benchmark --plot` 가 시드분포에 필요한 per-seed 데이터 못 얻음(run_benchmark=means만) | `from_score_table` 분리로 ScoreTable(per-seed `report.test.returns`) 직접 보유 → 시드분포 차트 가능 |
| 측정→viz 역의존(스택 오염) | 의존 방향 단방향(viz→측정만); 측정 모듈 순수성 테스트로 강제 |
| "게임 렌더링"으로 scope 확대 오인 | 본 task 는 메트릭 플롯만 — 월드 픽셀/GIF 는 render 도메인·M3-EC6(별개) |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/viz.py` 가 4종 EC3 차트 plot 함수 제공 — `plot_baseline_spread`,
   `plot_generalization_gap`, `plot_seed_distributions`, `plot_learning_curve`(+`save_all`) —
   각 matplotlib `Figure` 반환.
2. **numpy-only 격리** — `viz` 모듈이 top-level 에서 matplotlib 미import(지연 import); 측정 모듈
   (`generalization`/`scoreboard`/`leaderboard`)은 `matplotlib`/`viz` 미import. import 순수성 테스트.
3. **데이터 헬퍼 numpy-only** — `spread_data`/`gap_data`/`seed_distribution_data`/`LearningCurve` 가
   matplotlib 없이 동작·테스트(core CI). per-seed 분포는 held-out `EvalResult.returns` 에서 추출.
4. **headless** — plot 함수가 `Agg` 백엔드 사용(display 불요, CI/서버 안전).
5. **`[viz]` smoke** — `importorskip("matplotlib")` 테스트가 각 plot 함수의 Figure 내용(기대 axes/
   artist 수) + `save_all` 의 PNG 파일 생성(비어있지 않음) 검증; core CI 에선 skip. `matplotlib` 이
   `[viz]` extra 에 추가됨.
6. **단일 평가 통합** — `Leaderboard.from_score_table(spec, table)` 분리로 `run_benchmark` 무회귀;
   `benchmark.py --plot DIR` 가 **1회 산출한 ScoreTable** 로 리더보드 + 4종 차트(시드분포 포함)를
   생성(중복 평가 없음), matplotlib 미설치 graceful; ruff 통과.
7. **학습곡선 실제 데이터원** — `train_ppo.py` 가 per-chunk 시계열을 `LearningCurve` 로 누적하고
   `[viz]` 설치 시 학습곡선을 저장(합성 데이터 아닌 실제 학습 산출물). 개명 키 기반.
8. `mypy src` · `ruff check .` · `pytest -q` · `python -m build` 통과 + 기존 92 tests 무회귀.
