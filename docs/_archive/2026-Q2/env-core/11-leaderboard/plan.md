---
slug: leaderboard
initiative: env-core
status: active
started: 2026-06-21
acceptance_freeze: true
milestone: M3
exit_criteria: M3-EC2
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/leaderboard.py
  - src/critter_gym/generalization.py
  - src/critter_gym/scoreboard.py
  - tests/test_leaderboard.py
  - tests/test_generalization.py
  - tests/test_scoreboard.py
  - scripts/benchmark.py
  - scripts/train_ppo.py
extracted_to: []
supersedes: []
---

# leaderboard (M3-EC2)

> 작성일: 2026-06-21 | 상태: 계획

## 목표

**리더보드 포맷 + 재현 가능 configs(seeded, pinned)** 를 만든다 (M3-EC2). M3-EC1 의
`critter_gym.scoreboard` 점수표를 **랭킹된, 직렬화 가능한, 재현 가능한** 리더보드로 격상한다:

1. `critter_gym.leaderboard` 신설 — `BenchmarkSpec`(env config + eval 시드 수를 **핀 고정**한 재현
   단위) + `Leaderboard`(held-out 점수 내림차순 랭크, `to_markdown`/`to_json`) + `run_benchmark`.
2. **공개 점수 스키마 개명** — `GapReport.to_dict`/`ScoreTable` 의 키 `train_mean`/`test_mean` →
   `heldin_mean`/`heldout_mean`(+ `n_train`/`n_test` → `n_heldin`/`n_heldout`). 이 키들은 held-in
   **eval** 평균이라 "training-set 점수" 오독을 부른다(generalization-harness L3 forward-note,
   milestones M3-EC2 에 기록). **리더보드가 공개 스키마를 동결하기 직전인 지금이 개명 적기.**

이 리더보드가 viz(M3-EC3)·OSS 공개(M3-EC5)·킬러 데모(M3-EC6) 의 공개 산출물 포맷이 된다.

## 선행 조건

- ✅ M3-EC1 `baseline-suite` — `scoreboard.score_baselines`→`ScoreTable.to_dict`(베이스라인별 GapReport).
- ✅ M2-EC4 `generalization-harness` — `measure_generalization`/`GapReport.to_dict`(개명 대상 키).
- ✅ split API `train_seeds(n)`/`heldout_seeds(n)`(`TEST_SEED_OFFSET=1_000_000`).

## 개명 경계 (정확히 무엇을 바꾸나)

- **바꾼다 (공개 출력 키)**: `GapReport.to_dict()` 가 내는 dict 키 5종 →
  `{heldin_mean, heldout_mean, gap, n_heldin, n_heldout}`. 이를 읽는 모든 곳
  (`scoreboard.to_markdown`, `train_ppo.py`, 테스트 assertion) 동기 갱신. src/tests/scripts 어디에도
  `train_mean`/`test_mean` 키가 **남지 않음**(grep 0).
- **안 바꾼다 (시드 분할 API)**: `measure_generalization(train_seeds=, test_seeds=)` 파라미터,
  `GapReport.train`/`.test` 내부 필드 — 이건 **train/test 시드 split** 을 가리켜 정확한 ML 어휘.
  혼동은 *점수 키*에만 있었으므로 출력 키만 고친다(범위 최소화).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/leaderboard.py` | **신규** | 높음 (신규 공개 포맷) | `BenchmarkSpec`+`Leaderboard`+`run_benchmark` (numpy-only) |
| `src/critter_gym/generalization.py` | 수정 | 중 (공개 계약) | `to_dict` 키 개명 + 관련 docstring |
| `src/critter_gym/scoreboard.py` | 수정 | 낮음 | `to_markdown` 의 키 읽기 동기화 |
| `tests/test_leaderboard.py` | **신규** | 중 | 랭킹·재현성·직렬화·import순수성 |
| `tests/test_generalization.py` | 수정 | 낮음 | 개명 키 assertion |
| `tests/test_scoreboard.py` | 수정 | 낮음 | 개명 키 assertion |
| `scripts/benchmark.py` | 수정 | 낮음 | 리더보드 출력 소비자화 |
| `scripts/train_ppo.py` | 수정 | 낮음 | 개명 키 읽기 동기화 |

### 영향 범위 (import 그래프)

- `leaderboard.py` → import `scoreboard.{score_baselines, ScoreTable}`,
  `region.{train_seeds, heldout_seeds}`, `envs.critter_env.CritterEnv`. **torch/sb3 미import**.
- `benchmark.py` → import `leaderboard.{BenchmarkSpec, run_benchmark}`; PPO/recurrent 는 지연 import
  유지(graceful). `train_ppo.py` 는 개명 키만 동기화(기능 무변).
- 기존 `env`·`region`·`battle`·`typechart` **무수정**.

## Step별 계획

### Step 1 — 공개 점수 스키마 개명 [RED→GREEN]

- `generalization.py` `GapReport.to_dict` 키: `train_mean→heldin_mean`, `test_mean→heldout_mean`,
  `n_train→n_heldin`, `n_test→n_heldout`. `gap` 유지. docstring 의 forward-note 를 "개명 완료"로 갱신.
- 읽기 동기화 (**전 reader 명시 — 리터럴 grep=0 강제**):
  - `generalization.format_report()` (동일 파일 L164-173, `d['train_mean']`/`d['test_mean']` 읽음 — **2번째 in-file reader**)
  - `generalization.py` 산문 docstring 의 `train_mean - test_mean` 표현
  - `scoreboard.to_markdown` (`d['train_mean']`/`d['test_mean']`) + 그 docstring
  - `scripts/train_ppo.py` 본문(L105-106) **+ module docstring L9 의 산문 `test_mean`**
  - `tests/test_generalization.py`, `tests/test_scoreboard.py` assertion
- 가드: `grep -rn "train_mean\|test_mean" src tests scripts`(archive 제외) = **0** (산문 포함 — 리터럴
  잔존 0 까지). 새 키 `heldin_mean`/`heldout_mean` 로 일괄 치환됨을 의미.

### Step 2 — `leaderboard.py` (numpy-only) [RED→GREEN]

```python
@dataclass(frozen=True)
class BenchmarkSpec:
    grid_size: int; num_creatures: int; num_gyms: int; max_steps: int; patch_radius: int
    n_heldin: int; n_heldout: int            # 고정 eval 시드 수 (vary=True 항상)
    def env_factory(self) -> Callable[[], CritterEnv]: ...
    def heldin_eval_seeds(self) -> tuple[int,...]:  return tuple(train_seeds(self.n_heldin))
    def heldout_eval_seeds(self) -> tuple[int,...]: return tuple(heldout_seeds(self.n_heldout))
    def to_dict(self) -> dict: ...           # 재현용 — 리더보드에 직렬화

DEFAULT_SPEC = BenchmarkSpec(...)            # 핀 고정 기본 벤치마크

@dataclass(frozen=True)
class LeaderboardEntry:
    rank: int; name: str; heldin_mean: float; heldout_mean: float; gap: float

@dataclass(frozen=True)
class Leaderboard:
    spec: BenchmarkSpec
    entries: tuple[LeaderboardEntry, ...]    # heldout_mean 내림차순
    def to_markdown(self) -> str: ...         # | rank | baseline | held-in | held-out | gap |
    def to_json(self) -> str: ...             # {spec, entries} canonical (정렬된 키, 재현)

def run_benchmark(spec, policies) -> Leaderboard:
    """score_baselines 로 점수표 산출 → held-out 평균 내림차순 랭크."""
```

- **랭킹 기준 = held-out(test-region) 평균 내림차순** — 이 벤치마크의 headline 은 *unseen 월드
  일반화 성능*이라 held-out 점수로 줄세운다.
- split 누수 가드는 `score_baselines`→`measure_generalization` 에서 상속.

### Step 3 — `leaderboard.py` 테스트 (numpy-only) [RED→GREEN]

- `run_benchmark(DEFAULT_SPEC_small, {random, scripted})` → 2-entry 리더보드; **scripted 가 random
  보다 상위 랭크**(held-out 기준 spread → 랭킹으로 보존).
- 랭크 단조: entries 가 heldout_mean 내림차순 + rank 1..N 연속.
- **재현성**: 같은 spec + 결정론 정책 → 동일 `to_json`(canonical) — boolean.
- `to_json` 이 spec(재현 핀) + entries 를 포함하고 round-trip 파싱 가능; `heldin_mean`/`heldout_mean`
  키 노출(개명 검증).
- import 순수성: `leaderboard` 가 torch/sb3 미import(소스 정적 검사).
- 누수 가드 상속: held-in eval 시드가 training-region, held-out 이 test-region.

### Step 4 — `benchmark.py` 리더보드 소비자화 [GREEN]

- `run_benchmark(spec, baselines)` → `Leaderboard.to_markdown()`(랭크 표) + spec 헤더(재현 정보)
  출력. PPO/recurrent graceful 유지. throughput 라인 유지.

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build`.
- `python scripts/benchmark.py`(+`[rl]`) 수동 — 랭크된 리더보드 + spec 헤더 육안 확인(데모).
- 기존 86 tests 무회귀(개명 동기화 포함) + 신규 test_leaderboard.py green.

## 리스크

| 리스크 | 완화 |
|---|---|
| 개명 누락(일부 `train_mean` 잔존)으로 KeyError | Step 1 grep=0 가드 + 테스트 키 assertion |
| `to_json` 비결정 직렬화로 재현성 깨짐 | `sort_keys=True` + 고정 float 포맷, 재현성 boolean 테스트 |
| leaderboard 가 viz(M3-EC3) 침범 | 텍스트 markdown/JSON 만 — 차트/이미지 없음(EC3 경계 유지) |
| BenchmarkSpec 가 재현에 불충분(누락 핀) | env config + 시드 수 전부 spec 에 + `to_json` 에 직렬화, round-trip 테스트 |
| 개명이 M2 archive 산출물과 불일치 | M2 archive 문서는 historical(불변) — 코드 계약만 전진; milestones forward-note "개명 완료"로 갱신 |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/leaderboard.py`(numpy-only) 가 `BenchmarkSpec`(핀 고정 재현 단위) +
   `Leaderboard`(`to_markdown`/`to_json`) + `run_benchmark(spec, policies)` 제공.
2. **공개 점수 스키마 개명 완료** — `GapReport.to_dict` 키 = `{heldin_mean, heldout_mean, gap,
   n_heldin, n_heldout}`; src/tests/scripts(archive 제외) 어디에도 리터럴 `train_mean`/`test_mean`
   잔존 0(`grep -rn`, 산문 docstring 포함). 모든 읽기 지점(특히 `format_report`·`to_markdown`·
   `train_ppo` 본문+docstring) 동기 갱신.
3. **numpy-only** — `leaderboard`/`scoreboard`/`generalization` 모두 torch/sb3 미import(import 순수성).
4. **재현성** — 동일 `BenchmarkSpec` + 결정론 정책 → 동일 `to_json`(canonical, `sort_keys`); spec 가
   `to_json` 에 직렬화돼 round-trip 파싱 가능 (boolean 테스트).
5. **랭킹 정확** — `Leaderboard.entries` 가 held-out 평균 **내림차순** + `rank` 1..N 연속;
   scripted 가 random 보다 상위(spread → 랭킹 보존).
6. **split 누수 가드 상속** — `run_benchmark` 가 `score_baselines`/`measure_generalization` 경유라
   held-in eval ⊂ training-region, held-out ⊂ test-region (가드 재사용).
7. `scripts/benchmark.py` 가 `run_benchmark` → 랭크된 `to_markdown` + 재현 spec 헤더 출력;
   sb3 미설치 graceful; ruff 통과.
8. `mypy src` · `ruff check .` · `pytest -q` · `python -m build` 통과 + 기존 86 tests 무회귀.
