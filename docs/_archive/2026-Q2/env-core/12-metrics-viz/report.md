---
slug: metrics-viz
initiative: env-core
status: done
started: 2026-06-22
ended: 2026-06-22
mode: standard
result: passed
milestone: M3
exit_criteria: [M3-EC3]
extracted_to:
  - docs/reference/milestones.md       # M3-EC3 [x]
changelog_entry: docs/CHANGELOG.md
---

# Report — metrics-viz (측정 메트릭 플롯) · M3-EC3 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약

M3-EC3. **측정 viz** 4종 차트(학습곡선·일반화 갭·baseline spread·시드 분포)를 그리는
`critter_gym.viz` 신설 — **게임 월드 렌더링이 아니라 연구자용 메트릭 플롯**(고객=RL 연구자).
방금 만든 `scoreboard`/`leaderboard`/`generalization` 데이터를 입력으로. 격리 패턴 계승:
**plot-ready 데이터 정형은 numpy-only**(core CI 검증), **matplotlib 드로잉은 함수 내부 지연 import +
`[viz]` optional extra**. 측정 모듈은 viz/matplotlib 을 import 하지 않아 의존 방향 단방향(viz→측정).
Acceptance **8/8**, **102 passed/1 skipped**(92→102, 회귀 0).

## 계획 대비 실적

| AC | 내용 | 결과 |
|---|---|---|
| AC1 | 4종 차트 plot 함수(+`save_all`), 각 Figure 반환 | ✅ |
| AC2 | numpy-only 격리 (viz top-level matplotlib 미import; 측정 모듈 matplotlib/viz 미import) | ✅ |
| AC3 | 데이터 헬퍼 numpy-only (`spread_data`/`gap_data`/`seed_distribution_data`/`LearningCurve`) | ✅ |
| AC4 | headless (`Agg` 백엔드) | ✅ |
| AC5 | `[viz]` smoke (Figure 내용 + PNG 비어있지 않음, core skip) + `matplotlib` extra | ✅ |
| AC6 | 단일 평가 통합 (`from_score_table` 무회귀; `benchmark --plot` 1회 ScoreTable) | ✅ |
| AC7 | 학습곡선 실제 데이터원 (`train_ppo.py` `LearningCurve` 누적+저장) | ✅ |
| AC8 | mypy/ruff/pytest/build 통과 + 기존 92 무회귀 | ✅ |

## 변경 파일 상세

| 파일 | 종류 | 내용 |
|---|---|---|
| `src/critter_gym/viz.py` | 신규 | 데이터 헬퍼(numpy-only) + 4종 plot 함수(지연 matplotlib, `Agg`) + `save_all` + `LearningCurve` 컨테이너 |
| `src/critter_gym/leaderboard.py` | 수정 | `Leaderboard.from_score_table(spec, table)` classmethod 분리; `run_benchmark` 위임(무회귀) |
| `scripts/benchmark.py` | 수정 | ScoreTable 1회 산출 → 리더보드 + `--plot DIR`(per-seed 분포 포함), graceful |
| `scripts/train_ppo.py` | 수정 | per-chunk 시계열 → `LearningCurve` 누적 + `--plot` 시 학습곡선 저장(실제 데이터원) |
| `tests/test_viz.py` | 신규 | 10건 — 데이터 헬퍼·import순수성(core) + Figure 내용·savefig(`[viz]` smoke) |
| `pyproject.toml` | 수정 | `[viz]` extra = matplotlib; mypy override 에 `matplotlib.*` |

## 설계 결정

- **지연 import** — matplotlib 을 plot 함수 내부에서만 import → viz 모듈은 matplotlib 없이 import
  가능, core CI 가 데이터 헬퍼를 numpy-only 로 검증. `[viz]` 미설치 시 smoke 는 skip(순수성 무손상).
- **단방향 의존** — 측정 모듈(generalization/scoreboard/leaderboard)은 viz/matplotlib 미import.
  import 순수성 테스트로 강제.
- **단일 평가** — L1 SUGGEST 흡수: `from_score_table` 분리로 `benchmark --plot` 가 ScoreTable 1회
  (per-seed `report.test.returns`)로 리더보드 + 시드분포 차트 모두 생성(중복 평가 회피).
- **실제 학습곡선** — L1 SUGGEST 흡수: `train_ppo.py` 가 합성이 아닌 실제 학습 루프에서
  `LearningCurve` 누적+저장(producer wiring).

## L3 리뷰 + 흡수

L3 ≥2 reviewer **APPROVED**. 비차단 SUGGEST 1건(시드분포 smoke 가 `len(axes)==1` 만 검증 → AC5 의
per-chart artist 약속 미달) 즉시 흡수 — baseline 당 box 슬롯을 xticklabel 로 검증.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 내용 |
|---|---|
| `docs/reference/milestones.md` | M3-EC3 [x] (구성 task `metrics-viz` ✅) |

## 툴체인 결과

- `pytest` → **102 passed, 1 skipped**(`[rl]` smoke; 92→102, 회귀 0)
- `ruff check .` → clean · `mypy src` → Success (14 files) · `python -m build` → OK
- `python scripts/benchmark.py --plot DIR` → 3 PNG(spread/gap/seed-dist) 비어있지 않게 생성 확인
  (학습곡선은 `train_ppo.py --plot` [rl]+[viz] 경로)
