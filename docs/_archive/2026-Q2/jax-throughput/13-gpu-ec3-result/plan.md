---
slug: gpu-ec3-result
initiative: jax-throughput
status: active
started: 2026-06-26
acceptance_freeze: true
domains: [rl-env]
mode: standard
task_type: general
scope_paths:
  - scripts/gpu_bench.py
  - docs/explanation/jax-throughput.md
  - docs/explanation/competitive-analysis.md
  - docs/reference/milestones.md
  - docs/_active/jax-throughput/INITIATIVE.md
extracted_to: []
supersedes: []
---

# M4-EC3 GPU 실측 기록 + bench 배치 상한 정직 수정

> 작성일: 2026-06-26 | 상태: 계획

## 목표

직전 task(`gpu-bench-colab`)가 만든 Colab bench를 **사용자가 무료 T4 GPU에서 실행** → **M4-EC3
(≥10M steps/s GPU) 실측 확보**. 이 측정값을 docs에 정직하게 기록하고("GPU 미측정" → "달성"), bench의
기본 배치 상한이 무료 T4를 멈추게 한 점(b65536)을 정직하게 수정한다.

**실측 (사용자 Colab, NVIDIA T4, fused `lax.scan` rollout — overworld slice)**:

| 행 | steps/s |
|---|---|
| numpy single | 49,196 |
| jax single (jit scan) | 63,621 (1.29× numpy) |
| **jax vmap (batch=1024)** | **75,913,589** |
| **jax vmap (batch=4096)** | **271,352,874** |
| **jax vmap (batch=16384)** | **952,819,777** (≈9.5억/s, **95× the ≥10M EC**) |

→ **M4-EC3 달성**(GPU vmap이 ≥10M을 95× 초과, batch와 함께 단조 스케일). **정직 경계**: overworld slice
한정(full-episode env는 분기 많은 step이 무료 T4서 컴파일이 너무 느려 깔끔한 GPU 수치 미확보 — 단 CPU서
이미 22M/s로 EC 초과 → GPU도 초과 자명, 정밀 수치는 더 좋은 HW의 minor 후속); single-run·free T4·overworld.

## 선행 조건

- `gpu-bench-colab` done: `scripts/gpu_bench.py` + `scripts/colab_gpu_bench.ipynb` 존재.
- 사용자가 Colab T4서 실행해 위 overworld 수치 산출(b65536 + full-episode는 T4 한계로 미완 — 정직 반영).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `scripts/gpu_bench.py` | 기본 batch 상한 **65536→16384** (1줄) + docstring 1줄(무료 T4 b65536 한계 주석) | 저 | b65536이 무료 T4 멈춤 → 기본에서 제외(정직 수정). `--quick` 무영향. 로직 무변경. |
| `docs/reference/milestones.md` | M4 EC3 ☑+실측 / EC1·EC2도 충족 표기(이니셔티브로 입증됐으나 doc lag) / M4 status | 저(docs) | 측정값·증거 task 명시 |
| `docs/explanation/jax-throughput.md` | §5 item 3 GPU "미측정"→"실측 달성"(T4 수치) + §4 GPU 라인 | 저(docs) | 정직 경계 동반 |
| `docs/explanation/competitive-analysis.md` | "Speed/throughput" 행 GPU 실측 반영 | 저(docs) | peer 대비 GPU 수치 |
| `docs/_active/jax-throughput/INITIATIVE.md` | task 행 추가 + M4 EC3 상태 | 저(docs) | |

### 영향 범위

- `gpu_bench.py` batch 상한 변경은 **기본 실행 범위만 축소**(로직·함수 시그니처 무변경) → 회귀 0.
  docs는 사실 기록. src 무변경 → 전체 테스트 442 유지.

## Step별 계획

> 커밋 경계: lifecycle 끝 1 커밋(관례).

1. **(green)** `gpu_bench.py` 기본 `batches`에서 65536 제거(→ (1024,4096,16384)) + 주석 1줄. CPU 로컬
   `--quick`·기본 실행 무크래시 재확인.
2. **(green)** docs 기록 — milestones M4-EC3(실측·증거) + EC1/EC2 충족 표기, jax-throughput.md §5 item3
   + §4, competitive-analysis "Speed" 행, INITIATIVE 행.
3. **(verify)** ruff·mypy(src)·pytest(442)·build clean. 수치 정합(보고=실측).

## 검증 방법

- 전체 pytest 442 green(src 무변경). mypy(28)·ruff·build clean. gpu_bench.py CPU `--quick` 무크래시.
- docs 수치가 실측(overworld T4 75.9M/271M/952.8M)과 정확히 일치, 경계(overworld 한정·free T4·single run) 명시.

## 리스크

- **R1 과대기록**: overworld GPU만으로 "M4 완전 달성" 과장. **완화**: EC3는 "≥10M GPU vmap"이라 overworld
  952M로 *문자 그대로 충족*. 단 full-episode GPU 미측정·free T4·single run·overworld 한정을 **명시**.
- **R2 EC1/EC2 표기**: 이니셔티브로 입증됐으나 milestones doc은 미갱신. **완화**: EC1(hotpath 포트 4/4
  family)·EC2(parity 0)는 jax-throughput.md·아카이브로 입증된 사실 → 증거 task 포인터와 함께 표기(날조 아님).

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `gpu_bench.py` 기본 batch 상한 16384로 하향(b65536 제거) + 주석. CPU `--quick`·기본 실행
  크래시 0(로직·시그니처 무변경). ruff clean.
- **AC2 (실측 기록)**: milestones M4-EC3을 **달성**으로 갱신 + 실측값(T4 overworld vmap 952.8M @b16384,
  95× EC) + 증거(`gpu-bench-colab`/`gpu-ec3-result`). jax-throughput.md §5 item3(GPU 미측정→실측) +
  competitive-analysis "Speed" 행 반영.
- **AC3 (정직 경계)**: 모든 기록에 **overworld slice 한정·full-episode GPU 미측정(free T4 컴파일 한계,
  CPU 22M로 EC 이미 초과)·single run·free T4** 경계 명시. 과대 0.
- **AC4 (회귀 0)**: src 무변경. **passing 테스트 수 442 유지**(현재 통과 수), 2 skip. mypy(28 files)·
  ruff·build clean. (scope_paths의 `competitive-analysis.md`=`docs/explanation/`, `INITIATIVE.md`=
  `docs/_active/jax-throughput/` — frontmatter scope_paths에 전체 경로 명시됨.)
- **AC5**: INITIATIVE 행 추가 + CHANGELOG append. EC1/EC2는 증거와 함께 표기(이니셔티브 입증 사실).
