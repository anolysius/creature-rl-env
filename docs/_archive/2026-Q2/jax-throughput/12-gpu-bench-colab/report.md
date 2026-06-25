---
slug: gpu-bench-colab
initiative: jax-throughput
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md           # §5 item 3 (GPU): local-Metal non-viability + Colab path
  - docs/_active/jax-throughput/INITIATIVE.md      # task #12 행
changelog_entry: docs/CHANGELOG.md (## jax-throughput)
---

# GPU throughput bench harness (Colab) + local-Metal 비가용 박제 — 결과 보고서

## 요약

M4-EC3(≥10M steps/s **GPU**)은 하드웨어 게이트. 이 세션에서 **로컬 Apple GPU(M5 Pro·macOS 26.5)
경로를 실측 → 비가용 확정**, GPU 측정은 **클라우드 NVIDIA(무료 Colab/Kaggle T4)** 로 라우팅. 본 task =
도구(import 가능 fused-scan bench + Colab 노트북) 제공 + 음성결과 박제. 측정 실행 = 사용자 Google 로그인(게이트).

**로컬 Metal 실측 (박제)**: jax-metal **0.1.0**(jax/jaxlib 0.4.26)·**0.1.1**(jax/jaxlib 0.4.34) 둘 다 —
`METAL(id=0)` device 인식·단순 op(vmap+scan+scatter+gather+where) 정확 실행 OK; 그러나 **fused
`lax.scan(vmap(env_step))`에서 둘 다 NSException 크래시**(Metal PJRT 플러그인 op-coverage 한계, 우리 코드
문제 아님). per-step bench는 ~23k steps/s(dispatch-bound, CPU보다 느림). → 로컬 Apple GPU는 JAX로 EC 측정 불가.

**gpu_bench.py CPU sanity** (fused scan, 측정 정확성 확인): overworld vmap **~480M/s** / full-episode env
**~22M/s** @batch1024 — 전부 >0·유한·vmap≫numpy. (참고: CPU fused scan이 이미 full-episode서 EC 10M 초과.)

## 계획 대비 실적

| AC | 상태 | 결과 |
|---|---|---|
| AC1 gpu_bench.py | ✅ | fused-scan bench, CPU sanity 통과(vmap≫numpy·유한·크래시0), ruff clean |
| AC2 colab notebook | ✅ | nbformat valid(15 cells), ruff clean, 표준 Colab 패턴 |
| AC3 Metal 박제 | ✅ | jax-throughput.md §5 갱신(둘 다 크래시·Colab 경로·재시도 금지) |
| AC4 회귀 0 | ✅ | src 무변경, 442 passed 불변, mypy(28)/ruff/build clean |
| AC5 정직 경계 | ✅ | notebook 미실행검증·공개전·EC=사용자회수 명시, INITIATIVE #12 |

## 변경 파일 상세

**신규**:
- `scripts/gpu_bench.py` — fused `lax.scan` rollout throughput(overworld + full-episode, batch 스윕,
  numpy/jax-single/jax-vmap). 기존 심볼만 import(src 무변경). CPU/CUDA 표준 동작; Metal만 크래시(박제됨).
- `scripts/colab_gpu_bench.ipynb` — 15-cell Colab 노트북(GPU 확인→clone[public+PAT]→`jax[cuda12]`+repo
  설치→bench+train throughput→복붙 요약). nbformat valid.

**수정 (docs만)**:
- `docs/explanation/jax-throughput.md` §5 item 3 — 로컬 Metal 비가용 + Colab 경로 박제.
- `docs/_active/jax-throughput/INITIATIVE.md` — task #12 행.

## 발견된 이슈

- **(도구 한계, 낮음)** notebook은 GPU 부재로 **로컬에서 완전 검증 불가** — bench 로직은 CPU sanity까지,
  notebook은 nbformat 유효성 + 표준 Colab 패턴까지만 보증. Colab 실제 실행은 사용자 몫(정직 명시).
- **(repo 공개 상태)** repo가 공개 전이라 notebook clone은 public URL + private PAT(getpass) 둘 다 안내.
- **(ruff·notebook)** ruff가 .ipynb 셀까지 검사 → 셀 import 정리(상단·분리·blank·noqa E402)로 clean 통과.

## 흡수처 매핑

- **jax-throughput.md §5** — GPU open-question을 "로컬 Metal 비가용(실측)·Colab 경로(도구 제공)·측정=사람
  게이트"로 갱신. 다음 세션이 로컬 Metal 재시도하는 비용 차단.
- ADR 가치 없음(도구 + 음성결과 기록, 새 아키텍처 결정 아님).

## 타입 체크 / 빌드 결과

- `mypy src`: Success, 28 files. `ruff check .`(incl ipynb): passed. `python -m build`: 1.0.0rc1 OK.
  `pytest`: 442 passed, 2 skipped, exit 0(src 무변경 회귀 0). `nbformat.validate`: valid, 15 cells.

## 후속

사용자가 Colab/Kaggle에서 `colab_gpu_bench.ipynb` 실행 → 출력 steps/s 회수 → M4-EC3(≥10M GPU)을 그 숫자로
정직 기록(달성/미달 그대로). 그 전까지 GPU EC는 미측정 상태 유지(과대 금지). 로컬 Metal은 비가용으로 종결.
