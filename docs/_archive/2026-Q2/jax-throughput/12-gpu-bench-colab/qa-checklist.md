# QA Checklist — gpu-bench-colab (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ M4-EC3(GPU) enabler — 측정 도구 + 로컬 Metal 비가용 박제. EC 달성 자체는 사용자 Colab 회수(게이트).
> ⚠ 성공 = 동작하는 도구 + 정직한 음성결과 기록이지 "EC 달성"이 아니다.

## Acceptance Criteria (frozen at G1)

- [x] **AC1** ✅ — `scripts/gpu_bench.py`: fused `lax.scan` rollout throughput(overworld + full-episode,
  batch 스윕, numpy/jax-single/jax-vmap 3행). **CPU 로컬 sanity**: overworld vmap **~480M/s**·full-episode
  **~22M/s** @b1024, **전부 >0·유한·vmap≫numpy**, 크래시 0. ruff clean. 기존 jax_overworld/jax_env/jax_train
  심볼만 import(`mypy src` clean; scripts는 repo 관례상 mypy-게이트 밖, standalone import-untyped는 무관).
- [x] **AC2** ✅ — `scripts/colab_gpu_bench.ipynb`: **nbformat.validate 통과**(15 cells, ruff clean). 셀:
  GPU 확인(`nvidia-smi`) → 토큰(getpass, private용) → repo clone(public+PAT) → `pip install "jax[cuda12]"`
  +repo 설치 → backend 확인 → `gpu_bench.py` 실행 → train throughput(`train_ppo`) → 복붙용 요약.
- [x] **AC3 (로컬 Metal 비가용 박제)** ✅ — jax-throughput.md §5(item 3)에 실측 박제(jax-metal 0.1.0[0.4.26]·
  0.1.1[0.4.34] 둘 다 METAL 인식·단순 op OK·**fused lax.scan(vmap) NSException 크래시**·per-step ~23k/s)
  + "GPU=클라우드 NVIDIA(Colab) 경로" + "do not re-attempt local Metal".
- [x] **AC4 (회귀 0)** ✅ — src 무변경. **442 passed**(불변), 2 skipped, exit 0. mypy(28)·ruff·build clean.
- [x] **AC5 (정직 경계)** ✅ — notebook docstring/README cell에 GPU 미실행 검증(CPU sanity까지)·repo 공개전
  (clone 안내)·EC 달성=사용자 Colab 회수 후 별도 기록 명시. INITIATIVE #12 행 추가.

## L1 이력
- round 1: plan-reviewer **2 SUGGEST**(import 모듈 경로 명시 / AC1 "합리적" 정량화) / qa-verifier **APPROVE**
  → SUGGEST_CUTOFF. 흡수: 선행조건에 import 심볼·파일 명시 + AC1을 ">0·유한·대형batch vmap≥numpy"로 정량화.

## 정직성 불변식
이번 로컬 Metal 실측은 **음성결과(비가용)**지만 숨기지 않고 박제(다음 세션 비용 절감). notebook은 GPU 없이
로컬 완전검증 불가 → 그 한계 명시(CPU sanity까지만 보증). EC 달성 주장 0 — 도구 제공 + 음성결과 기록까지.
