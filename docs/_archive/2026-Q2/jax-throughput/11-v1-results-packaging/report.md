---
slug: v1-results-packaging
initiative: jax-throughput
status: completed
ended: 2026-06-25
extracted_to:
  - README.md                          # "What it measures" 2 헤드라인 + Release status 1.0.0-rc
  - docs/paper/critter-gym.md          # §2 + 신규 §6 Throughput + §4 PPO headroom + §5/§8/§9
  - docs/paper/README.md               # figure→source map 신규 행
  - scripts/reproduce_results.py       # 1-command 재현 harness (살아있는 도구)
changelog_entry: docs/CHANGELOG.md
---

# KR3 결과 패키징 / v1.0.0-rc 준비 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 1-command 재현 | `scripts/reproduce_results.py [--quick] [--runs N]` (throughput + headroom 두 표, 라이브) |
| 통합 헤드라인 | (1) JAX vmap 27–1047× numpy·4/4 family parity 0 (2) hard-and-learnable PPO 21–28% of oracle (5-run robust) |
| 버전 | `0.0.1` → **`1.0.0rc1`** (build→`critter_gym-1.0.0rc1` wheel+sdist) |
| 제품 코어 | **무변경** (docs/scripts/메타만) |
| 무회귀 | pytest exit=0 (415 green, src 무변경) · mypy(28) · ruff clean |
| 공개 행위 | **수행 안 함** (OSS 리스팅·arXiv 제출·태그 push = 사람 게이트) |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 1-command 재현 스모크 + honest framing | ✅ | `reproduce_results.py --quick` exit=0, throughput+headroom 두 표, CPU·vmap-only·oracle proxy 라벨 |
| AC2 README 두 헤드라인 + Release status 1.0.0-rc + 잔여 게이트 | ✅ | "What it measures"에 competitively-fast/4-family/hard-and-learnable; Release status에 GPU·arXiv·OSS 명시 |
| AC3 paper JAX throughput + PPO headroom 통합 + conclusion 정정 + source map | ✅ | §2 갱신·신규 §6 Throughput·§4 headroom subsection·§5 note·§8 limitations·§9 conclusion(JAX done); paper/README 4 신규 행 |
| AC4 version 1.0.0rc1 + build | ✅ | `pyproject.toml` 1.0.0rc1, build이 1.0.0rc1 아티팩트 생성 |
| AC5 무회귀 + 정직성 fabricate 0 | ✅ | pytest exit=0·mypy·ruff clean; 수치 라이브 재생성(pilot 검증), 모든 주장에 caveat |
| AC6 공개 안 함 | ✅ | 태그 push·OSS 리스팅·arXiv 제출 없음; README가 "공개=사람 결정" 명시 |

## 변경 파일 상세

**신규**
- `scripts/reproduce_results.py` (+80): `bench_throughput.py`+`ppo_baseline.py` subprocess 오케스트레이션,
  `--quick`/`--runs N`, honest framing 배너, 수치 하드코딩 없음.

**수정**
- `README.md`: "What it measures"에 JAX 속도·4/4 family·hard-and-learnable headroom 3개 항목 추가 + 재현
  명령 블록 + Release status(1.0.0-rc + GPU/arXiv/OSS 잔여 게이트).
- `docs/paper/critter-gym.md`: §2 throughput 갱신 + 신규 **§6 Throughput: a parity-proven JAX port**(parity
  표·multiplier 표·4 family·trains·honest boundary) + §4 PPO oracle-headroom subsection(표·R1/R2/R3) + §5 note
  + §8 limitations(GPU·PPO baseline) + §9 conclusion(JAX done) + §7/§8/§9 renumber.
- `docs/paper/README.md`: figure→source map에 numpy/JAX throughput·parity·headroom 4 행 + status 갱신.
- `pyproject.toml`: version 1.0.0rc1.

## 발견된 이슈 (심각도)

- **(정직 결정) 1.0.0-rc 성숙도** — GPU(M4-EC3)·arXiv(M3-EC4)·OSS(M3-EC5) 미충족. "rc=release candidate,
  공개는 사람 게이트"로 정직 프레이밍, Release status에 잔여 3 게이트 명시. pyproject version 문자열만 변경(태그/
  publish 안 함). 과대 아님.
- **(설계) --quick vs full 수치 차이** — quick(작은 예산·1-run)은 headroom %가 헤드라인(5-run 21–28%)보다
  낮음. 스크립트가 수치를 라이브 재생성하고 quick은 작은 예산이라고 배너에 명시 → fabricate 아님.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 내용 |
|---|---|
| `README.md` | front-facing 헤드라인 2개 + 재현 명령 + Release status (살아있는 진입점) |
| `docs/paper/critter-gym.md` §6/§4 | JAX throughput + PPO headroom 살아있는 paper narrative |
| `docs/paper/README.md` | figure→source 추적 map (재현성 SSOT) |
| `scripts/reproduce_results.py` | 1-command 재현 harness (살아있는 도구) |

ADR 가치 결정 없음(기존 결과의 패키징·정직 프레이밍 — 새 아키텍처 결정 아님).

## 타입 체크 / 빌드 결과

- `mypy src` — Success: no issues found in 28 source files.
- `ruff check .` — All checks passed (신규 script 포함).
- `pytest -q` — exit=0 (415 passed, 2 skipped; src 무변경 무회귀).
- `python -m build` — Successfully built critter_gym-1.0.0rc1 wheel + sdist.
- `scripts/reproduce_results.py --quick` — exit=0, 두 표 재생성.
