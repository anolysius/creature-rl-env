---
slug: generalization-harness
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
milestone: M2
exit_criteria: [M2-EC4]
extracted_to:
  - docs/reference/milestones.md       # M2-EC4 [x] + M2 → done, 활성 M3 게이트
  - docs/explanation/roadmap.md         # 현재 위치 → M2 완료
changelog_entry: docs/CHANGELOG.md
---

# Report — generalization-harness (train-vs-test 일반화 갭 측정) · M2-EC4 ✅ → **M2 완성**

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약

**M2(procgen + train/test, 우리 moat)의 마지막 EC.** 정책-비의존 **numpy-only** 측정 하네스
`critter_gym.generalization` 를 신설해 Procgen 관례의 일반화 갭(`gap = train_mean − test_mean`)을
측정한다. 학습은 train 시드, 평가는 held-in(training-region, **학습 시드와 disjoint**) + held-out
(test-region, 새 맵 + 새 타입표) 양쪽. 측정 로직은 torch/sb3 의존이 전혀 없어 core CI 가 항상 검증하고,
PPO 학습은 `[rl]` extra 뒤 `scripts/train_ppo.py` 한 소비자로 격리. Acceptance **9/9**, **81 tests green**
(기존 71 + 신규 10, 회귀 0), ruff/mypy/build/check_env(fixed+procgen) 통과.

## 계획 대비 실적

| AC | 내용 | 결과 |
|---|---|---|
| AC1 | 정책-비의존 하네스 (`evaluate`/`measure_generalization`/`GapReport.to_dict`/`format_report`/`split_train_pool`) | ✅ |
| AC2 | numpy-only (torch/sb3 미import, import 순수성 테스트) | ✅ |
| AC3 | split API + 누수0 호출부 가드 (양방향 ValueError), 하드코딩 50_000 제거 | ✅ |
| AC4 | 결정론 (고정 seed → 고정 return) | ✅ |
| AC5 | procgen 변형(`vary=True`, 새 맵+새 타입표) 위 측정 | ✅ |
| AC6 | held-in ∩ 학습 = ∅ (`split_train_pool` disjoint+total boolean 테스트) | ✅ |
| AC7 | 리포트 계약 (`to_dict` 키 5종 + `format_report` 수치 포함, numpy-only CI) | ✅ |
| AC8 | `train_ppo.py` 하네스 소비자화 + `target_catches` dead-bug 정정 + `vary=True`, `[rl]` 격리 | ✅ |
| AC9 | mypy/ruff/pytest/build 통과 + 기존 71 무회귀 | ✅ |

## 변경 파일 상세

| 파일 | 종류 | 내용 |
|---|---|---|
| `src/critter_gym/generalization.py` | 신규 | numpy-only 측정 하네스 (rollout/evaluate/EvalResult/split_train_pool/GapReport/measure_generalization/format_report) |
| `tests/test_generalization.py` | 신규 | baseline 정책으로 하네스 검증 10건 (결정론·disjointness·누수가드·import순수성·리포트계약) |
| `scripts/train_ppo.py` | 리팩터 | 하네스 소비자화. `target_catches` dead-kwarg(실행 시 TypeError) 정정, split API + `vary=True` + `_SeededReset`(학습을 learn 풀로 한정) 도입 |

## 발견된 이슈 (해소)

- **(중) `train_ppo.py` dead-bug**: 기존 `CFG = dict(..., target_catches=3, ...)` 는 `CritterEnv`
  시그니처에 없는 kwarg → `CritterEnv(**CFG)` 실행 시 **TypeError**. `[rl]` 미설치라 CI 미검출.
  L1(reviewer A)이 plan 단계에서 포착 → AC8 로 정정 강제. 유효 시그니처로 재구성 완료.
- **(중) 시드 split 불일치**: 기존 `HELDOUT = range(50_000, …)` 는 `TEST_SEED_OFFSET=1_000_000`
  기준으로 사실 **train 영역**(held-out 아님) + `vary=False`(타입표 변형 미적용). split API +
  `vary=True` 로 정정 (AC3/AC5/AC8).
- **(낮) held-in 낙관편향 리스크**: L1(reviewer B) BLOCK — held-in/학습 disjointness 가 prose 에만.
  `split_train_pool` 헬퍼 + AC6 boolean 테스트로 구조적 강제 → 해소.

## L3 리뷰 + 후속 노트

L3 ≥2 reviewer **APPROVED**. 비차단 SUGGEST 중 2건 즉시 흡수(headline 갭 테스트 비공허화,
`measure_generalization` 호출부 disjointness 계약 docstring). 1건은 **M3 forward 노트로 이월**:

> **`GapReport.to_dict()` 키 `train_mean` 재검토** — 의미는 held-in(학습과 disjoint) **eval** 평균이라
> "training-set 점수"로 오독 소지. M2-EC4 frozen 계약이라 본 task 에선 docstring 으로 의미 명시만.
> **M3 리더보드 스키마(M3-EC2)가 공개 동결되기 전** `heldin_mean`/`heldout_mean` 로 개명(또는 alias) 검토.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 내용 |
|---|---|
| `docs/reference/milestones.md` | M2-EC4 [x], M2 상태 → done, 활성 마일스톤 M3 게이트 |
| `docs/explanation/roadmap.md` | "현재 위치" → M2 완료(moat 4 EC 충족), 다음 = M3 |
| `INITIATIVE.md` (env-core) | task #8 행 추가 + "다음 task" → M3 |

## 툴체인 결과

- `pytest -q` → **81 passed** (71→81, 회귀 0)
- `ruff check .` → All checks passed
- `mypy src` → Success (11 files)
- `python -m build` → wheel + sdist OK
- `check_env` (CritterGym-v0 + CritterGym-procgen-v0) → OK
