---
slug: baseline-suite
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
milestone: M3
exit_criteria: [M3-EC1]
extracted_to:
  - docs/reference/milestones.md       # M3-EC1 [x]
changelog_entry: docs/CHANGELOG.md
---

# Report — baseline-suite (4-베이스라인 train+test 점수표) · M3-EC1 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약

M3(벤치마크 신뢰성 + 런치)의 첫 EC. M2 의 `critter_gym.generalization` 갭 하네스를 **N-베이스라인**으로
확장하는 얇은 numpy-only 레이어 `critter_gym.scoreboard` 신설 — 베이스라인마다 `measure_generalization`
을 1회씩 돌려 **train(held-in)/test(held-out)/gap** 을 한 표로 모은다(`ScoreTable.to_markdown`/`to_dict`).
점수표 빌더는 torch/sb3 무의존(core CI 가 random+scripted 2종으로 상시 검증, spread 가드 보존), 학습
베이스라인(PPO·recurrent)은 `[rl]` extra 뒤 `scripts/benchmark.py` 소비자로 격리. 이 점수표가 리더보드
(M3-EC2)·viz(M3-EC3)·킬러 데모(M3-EC6)의 데이터 토대. Acceptance **9/9**, **86 passed/1 skipped**
(`[rl]` smoke), 81→86 회귀 0.

## 계획 대비 실적

| AC | 내용 | 결과 |
|---|---|---|
| AC1 | 정책-비의존 빌더 (`score_baselines`→`ScoreTable`, `to_markdown`/`to_dict`) | ✅ |
| AC2 | numpy-only (torch/sb3/sb3_contrib 미import) | ✅ |
| AC3 | split 누수 가드 상속 (measure_generalization 위임) | ✅ |
| AC4 | 결정론 (결정론 정책+고정 seeds → 동일 표) | ✅ |
| AC5 | 벤치마크 유효성 (scripted test_mean > random + 0.5 spread) | ✅ |
| AC6 | 리포트 계약 (`to_markdown` 수치 + `to_dict`={이름:{train_mean,…}}) | ✅ |
| AC7 | benchmark.py CI-검증 (scoreboard 리팩터 + dead-bug 3종 정정 + graceful 2행) | ✅ |
| AC8 | `[rl]` smoke (PPO+RecurrentPPO lazy-import 4종 표, importorskip) + `sb3-contrib` 추가 | ✅ |
| AC9 | mypy/ruff/pytest/build 통과 + 기존 81 무회귀 | ✅ |

## 변경 파일 상세

| 파일 | 종류 | 내용 |
|---|---|---|
| `src/critter_gym/scoreboard.py` | 신규 | numpy-only N-베이스라인 점수표 빌더 (`score_baselines`/`ScoreTable`/`BaselineRow`). seeds 를 tuple materialize 해 정책별 동일 split 보장(iterable 소진 회피), split 누수 가드는 `measure_generalization` 위임 |
| `tests/test_scoreboard.py` | 신규 | 6건 — 표 형태·계약·spread(margin)·결정론·누수가드·import순수성 + `[rl]` smoke(PPO/RecurrentPPO importorskip) |
| `scripts/benchmark.py` | 리팩터 | 4종 train+test 표 소비자. dead-bug 3종 정정, `_SeededReset` 로 학습 learn 풀 한정, sb3 미설치 graceful(core 2행) |
| `pyproject.toml` | 수정 | `[rl]` extra 에 `sb3-contrib>=2.0` (RecurrentPPO) |

## 발견된 이슈 (해소)

- **(중) `benchmark.py` dead-bug**: `CritterEnv().target_catches` 는 env 에 없는 **속성** → 실행 시
  AttributeError. `range(50_000)`(사실 train 영역) "held-out" 오칭, `vary=False`. 모두 scoreboard +
  split API + `vary=True` 로 정정 (AC7). train_ppo.py(M2-EC4)에 이어 동일 부류 마지막 잔존 스크립트 정리.

## L3 리뷰 + 흡수

L3 ≥2 reviewer **APPROVED**. 비차단 SUGGEST 1건(spread 가드가 8-seed bare `>` → drift flicker
가능) 즉시 흡수 — 표본 16 + margin 0.5 로 강화. 키 네이밍 부채는 단일 위임(GapReport.to_dict)으로
유지돼 새 부채 없음(M3-EC2 에서 일괄 개명 가능, milestones forward-note 기존 기록).

## 흡수처 매핑 (extracted_to)

| 흡수처 | 내용 |
|---|---|
| `docs/reference/milestones.md` | M3-EC1 [x] (구성 task `baseline-suite` ✅) |

## 툴체인 결과

- `pytest` → **86 passed, 1 skipped**(`[rl]` smoke; 81→86, 회귀 0)
- `ruff check .` → All checks passed · `mypy src` → Success (12 files) · `python -m build` → OK
- `python scripts/benchmark.py` (sb3 미설치) → core 2행 표(scripted 5.75 ≫ random 1.0 held-out) + throughput, graceful
