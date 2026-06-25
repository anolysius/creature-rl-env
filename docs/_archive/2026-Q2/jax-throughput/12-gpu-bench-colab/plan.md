---
slug: gpu-bench-colab
initiative: jax-throughput
status: active
started: 2026-06-25
acceptance_freeze: true
domains: [rl-env]
mode: standard
task_type: general
scope_paths:
  - scripts/colab_gpu_bench.ipynb
  - scripts/gpu_bench.py
  - docs/explanation/jax-throughput.md
  - docs/_active/jax-throughput/INITIATIVE.md
extracted_to: []
supersedes: []
---

# GPU throughput bench harness (Colab) + local-Metal non-viability 박제 (M4-EC3 enabler)

> 작성일: 2026-06-25 | 상태: 계획

## 목표

M4-EC3(≥10M steps/s **GPU**)은 하드웨어 게이트로 미측정. 이 세션에서 **로컬 Apple GPU(M5 Pro, Metal)
경로를 jax-metal로 실측**한 결과 비가용으로 확인됨(아래). 따라서 GPU 측정의 신뢰 경로 = **클라우드 NVIDIA
GPU**(무료 Colab/Kaggle T4). 본 task = (1) 사용자가 **맥에서 Colab을 열어 클릭만으로** GPU throughput을 찍을
수 있는 **bench 아티팩트**(notebook + import 가능한 bench 모듈) 제작, (2) 이번 **로컬 Metal 실측(비가용)**을
docs에 음성 결과로 박제(다음 세션 반복 시도 방지). 측정 실행 자체는 사용자 Google 로그인(게이트).

**로컬 Metal 실측 (이 세션, 박제 대상)**: M5 Pro + macOS 26.5. jax-metal **0.1.0**(jax/jaxlib 0.4.26) ·
**0.1.1**(jax/jaxlib 0.4.34) 둘 다 — METAL device 인식·단순 op(vmap+scan+scatter+gather+where) 정확 실행
OK; 그러나 **fused `lax.scan(vmap(env_step))` 패턴(공정 GPU 측정·학습에 필요)에서 둘 다 NSException 크래시**
(Metal PJRT 플러그인 한계, 우리 코드 문제 아님). per-step bench는 돌지만 ~23k steps/s(dispatch-bound, CPU보다
느림). → 로컬 Apple GPU는 JAX로 EC 측정 불가.

## 선행 조건

- bench 대상 코드 존재(이 세션 확인, 전부 `src/critter_gym/`): `jax_overworld.py`(`overworld_step`/
  `state_from_region`/`OverworldState`) · `jax_env.py`(`make_jax_env`/`JaxEnvConfig`) ·
  `jax_train.py`(`train_ppo`/`make_ppo_rollout` = fused `lax.scan` rollout 패턴). 전부 device-agnostic(순수
  jnp/lax/vmap) → GPU 백엔드만 있으면 그대로 동작. **gpu_bench.py는 이 기존 심볼만 import**(부재 시 AC1
  CPU-sanity가 즉시 실패 = 결함 조기 검출).
- 기존 `scripts/bench_throughput.py`는 **per-step python 루프**(dispatch-bound) — GPU엔 불리. 본 task의
  bench는 **fused `lax.scan` rollout** throughput(GPU-공정)을 측정.
- 코드 변경 없음(측정 도구 추가만). repo는 공개 전이므로 notebook은 private repo clone(token) 경로 안내 포함.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `scripts/gpu_bench.py` | 신규 | 저 | import 가능한 **fused-scan throughput** bench(overworld + full-episode env, batch 스윕; numpy/jax-single/jax-vmap 정직 3행). CPU에서도 동작(로컬 sanity) → GPU서 그대로 큰 숫자. |
| `scripts/colab_gpu_bench.ipynb` | 신규 | 저 | Colab notebook: GPU 확인(`nvidia-smi`/`jax.devices()`) → repo clone(public/PAT 안내) → `pip install jax[cuda12]` + repo → `gpu_bench.py` 실행 + train throughput → 복붙용 요약 출력. |
| `docs/explanation/jax-throughput.md` | Update 추가 | 저(docs) | §5 GPU 항목에 **로컬 Metal 비가용 실측** + Colab 경로 박제. |
| `docs/_active/jax-throughput/INITIATIVE.md` | task 행 추가 | 저(docs) | 본 task 1행. |

### 영향 범위

- `gpu_bench.py`는 신규 독립 스크립트(import: jax_overworld/jax_env/jax_train의 *기존* 심볼만). src 무변경
  → 전체 테스트 회귀 0. notebook은 실행 아티팩트(테스트 대상 아님).

## Step별 계획

> 커밋 경계: lifecycle 끝(L3 APPROVED 후) 1 커밋(이 프로젝트 관례).

1. **(green)** `scripts/gpu_bench.py` 작성 — fused `lax.scan` rollout throughput 함수(overworld·full-episode,
   batch (1024,4096,16384,65536)), numpy baseline, jit-single, vmap row. `--quick` 옵션. CPU서 로컬 실행해
   sanity(숫자 합리·크래시 0) 확인.
2. **(green)** `scripts/colab_gpu_bench.ipynb` 작성 — 셀: (a) 설명+사용법 markdown, (b) GPU 확인,
   (c) repo clone(public URL + private는 PAT `getpass` 안내), (d) `pip install "jax[cuda12]"` + `pip install -e`,
   (e) `python scripts/gpu_bench.py` 실행, (f) train throughput(`train_ppo` 짧은 run의 env-steps/s),
   (g) 복붙용 요약. **유효 JSON**(nbformat)으로 작성.
3. **(green)** docs 박제 — jax-throughput.md §5 GPU 항목 갱신(로컬 Metal 비가용 + Colab 경로) + INITIATIVE 행.
4. **(verify)** `gpu_bench.py` ruff/mypy clean + CPU 로컬 실행 무크래시. notebook nbformat 유효성 검증.
   기존 테스트 전체 green(회귀 0).

## 검증 방법

- `scripts/gpu_bench.py`: ruff·mypy clean, CPU 로컬 실행 시 유한 합리적 steps/s 출력(크래시 0).
- `scripts/colab_gpu_bench.ipynb`: `python -c "import nbformat; nbformat.read(...)"` 유효성 + `nbformat.validate` 통과.
- 전체 pytest green(442 유지) — src 무변경 회귀 0.
- mypy(28)·ruff·build clean.

## 리스크

- **R1 notebook이 Colab서 실제로 안 돎**(검증 못 함 — GPU 없음). **완화**: bench 로직(`gpu_bench.py`)을 CPU서
  로컬 실행해 검증(GPU는 같은 코드를 더 빠르게 돌릴 뿐). notebook은 표준 Colab 패턴(clone+pip+run)만 사용.
  clone 경로는 public/PAT 둘 다 안내(repo 비공개 대비).
- **R2 fused-scan이 어떤 백엔드서 op 미지원**. **완화**: CPU/CUDA는 fused scan 표준 지원(Metal만 크래시였음).
  CPU 로컬 실행으로 패턴 자체 정상 확인.
- **R3 측정 결과 EC 미달 가능**(T4가 약함·full-episode 분기). **완화**: 정직 보고 — EC는 사용자가 Colab 숫자
  회수 후 별도 기록. 본 task는 *도구+로컬 음성결과 박제*이지 EC 달성 주장 아님.

## Acceptance Criteria (G1 통과 시 freeze)

> freeze 대상 = 결과 아닌 산출물·검증 기준.

- **AC1**: `scripts/gpu_bench.py` 존재 — fused `lax.scan` rollout throughput(overworld + full-episode env,
  batch 스윕, numpy/jax-single/jax-vmap 정직 3행). **CPU 로컬 실행 시 크래시 0**, 모든 행이 **>0·유한**,
  그리고 **대형 batch(≥4096)서 vmap row ≥ numpy row**(벡터화 우위 — 음수/0/NaN/inf 또는 vmap<numpy면
  bench 결함). ruff·mypy clean. (기존 `jax_overworld`/`jax_env`/`jax_train` 심볼만 import.)
- **AC2**: `scripts/colab_gpu_bench.ipynb` 존재 — **유효 nbformat**(`nbformat.validate` 통과). 셀 구성:
  GPU 확인 → repo clone(public + PAT 안내) → `jax[cuda12]`+repo 설치 → `gpu_bench.py` 실행 → train
  throughput → 복붙용 요약. 표준 Colab 패턴만(외부 자율 검증 불가는 정직 명시).
- **AC3 (로컬 Metal 비가용 박제 — 정직 음성결과)**: jax-throughput.md §5 GPU 항목에 이번 실측(jax-metal
  0.1.0·0.1.1 둘 다 fused-scan 크래시·per-step 느림·METAL 인식은 됨) + "GPU 측정=클라우드 NVIDIA(Colab)
  경로" 기록. 다음 세션이 로컬 Metal 재시도 안 하도록.
- **AC4 (회귀 0)**: src 무변경. 전체 테스트 442 유지, mypy(28)·ruff·build clean.
- **AC5 (정직 경계)**: notebook은 *미실행 검증*(GPU 없어 로컬선 CPU만 sanity)·repo 공개 전(clone 경로 안내)·
  EC 달성은 사용자 회수 후 별도 기록임을 명시. INITIATIVE 행 추가.
