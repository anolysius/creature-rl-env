---
slug: leaderboard
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
milestone: M3
exit_criteria: [M3-EC2]
extracted_to:
  - docs/reference/milestones.md       # M3-EC2 [x] + forward-note "개명 완료"
changelog_entry: docs/CHANGELOG.md
---

# Report — leaderboard (리더보드 포맷 + 재현 configs) · M3-EC2 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약

M3-EC2. M3-EC1 의 점수표를 **랭킹된·직렬화·재현 가능한** 리더보드로 격상하는 numpy-only
`critter_gym.leaderboard` 신설 — `BenchmarkSpec`(env config + eval 시드 수 **핀 고정** 재현 단위) +
`Leaderboard`(held-out 평균 내림차순 랭크, `to_markdown`/`to_json` canonical) + `run_benchmark`.
동시에 **공개 점수 스키마 개명** 완료 — generalization-harness L3 forward-note 이행: `train_mean`/
`test_mean` → `heldin_mean`/`heldout_mean`(+ `n_heldin`/`n_heldout`), 리터럴 잔존 0(grep). 이 리더보드가
viz(M3-EC3)·OSS(M3-EC5)·킬러데모(M3-EC6) 의 공개 산출물 포맷. Acceptance **8/8**, **92 passed/1
skipped**(86→92, 회귀 0).

## 계획 대비 실적

| AC | 내용 | 결과 |
|---|---|---|
| AC1 | 리더보드 포맷 (`BenchmarkSpec`+`Leaderboard`+`run_benchmark`, `to_markdown`/`to_json`) | ✅ |
| AC2 | 개명 완료 (키 5종 + 리터럴 `train_mean`/`test_mean` grep=0, 산문 포함) | ✅ |
| AC3 | numpy-only (leaderboard/scoreboard/generalization torch/sb3 미import) | ✅ |
| AC4 | 재현성 (동일 spec+결정론 정책 → 동일 `to_json`; spec embed round-trip) | ✅ |
| AC5 | 랭킹 (held-out 내림차순 + rank 1..N + 결정적 tie-break) | ✅ |
| AC6 | 누수 가드 상속 (held-in⊂train영역, held-out⊂test영역) | ✅ |
| AC7 | benchmark.py 리더보드 소비자 + 재현 spec 헤더 + graceful | ✅ |
| AC8 | mypy/ruff/pytest/build 통과 + 기존 86 무회귀 | ✅ |

## 변경 파일 상세

| 파일 | 종류 | 내용 |
|---|---|---|
| `src/critter_gym/leaderboard.py` | 신규 | `BenchmarkSpec`(핀 고정 eval 프로토콜) + `Leaderboard`(랭크, `to_json` sort_keys+spec embed, `to_markdown`) + `run_benchmark`(held-out 내림차순, 결정적 tie-break gap/name) |
| `src/critter_gym/generalization.py` | 수정 | `to_dict` 키 개명 + `gap`/`format_report`/module docstring 동기화 |
| `src/critter_gym/scoreboard.py` | 수정 | `to_markdown` 키 읽기 + docstring 동기화 |
| `scripts/benchmark.py` | 리팩터 | `run_benchmark` 소비자 + `BenchmarkSpec` + 재현 spec 헤더; learn 풀=train_seeds(start=n_heldin) 로 heldin eval 과 disjoint |
| `scripts/train_ppo.py` | 수정 | 개명 키 본문+docstring 동기화 |
| `tests/test_leaderboard.py` | 신규 | 6건 — 랭킹·재현성·spec round-trip·split·import순수성 |
| `tests/test_generalization.py`, `tests/test_scoreboard.py` | 수정 | 개명 키 assertion |

## 설계 결정 — 개명 경계

**공개 출력 키만** 개명(`heldin_mean`/`heldout_mean` — held-in/held-out *eval* 평균임을 정직히 표현).
**시드 분할 API**(`measure_generalization(train_seeds=, test_seeds=)`, `GapReport.train`/`.test`)는
유지 — 그건 실제 train/test 시드 split 을 가리켜 정확. 혼동은 *점수 키*에만 있었으므로 범위 최소화.
개명은 단일 위임(`GapReport.to_dict`)이라 추가 부채 없음.

## L3 리뷰 + 흡수

L3 ≥2 reviewer **APPROVED**. 비차단 SUGGEST 중 재현성·정직성 직결 2건 즉시 흡수:
1. `BenchmarkSpec` 가 정책 RNG(stochastic 정책·SB3 seed)는 핀 못함 → docstring 을 "환경/프로토콜을
   핀, 결정론 정책에서 재현 보장"으로 정밀화(과대주장 제거).
2. held-out 동점 시 stable-sort(dict 순) 의존 → 결정적 2차 키(gap asc, name) 추가 — 랭킹이 정책
   dict 순서에 무관하게 재현.
보류 1건(benchmark.py `# type: ignore[arg-type]` — mypy 비검사 스크립트의 cosmetic).

## 흡수처 매핑 (extracted_to)

| 흡수처 | 내용 |
|---|---|
| `docs/reference/milestones.md` | M3-EC2 [x]; forward-note 를 "개명 완료(heldin/heldout)"로 갱신 |

## 툴체인 결과

- `pytest` → **92 passed, 1 skipped**(`[rl]` smoke; 86→92, 회귀 0)
- `ruff check .` → clean · `mypy src` → Success (13 files) · `python -m build` → OK
- `grep -rn "train_mean\|test_mean" src tests scripts` → 0 (개명 완료)
- `python scripts/benchmark.py` (sb3 미설치) → 랭크 리더보드(scripted #1 by held-out) + 재현 spec 헤더 + throughput, graceful
