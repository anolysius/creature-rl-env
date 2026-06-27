---
slug: gpu-ec3-result
initiative: jax-throughput
status: completed
ended: 2026-06-26
extracted_to:
  - docs/reference/milestones.md                  # M4 EC1/EC2/EC3 ✅ (GPU measured)
  - docs/explanation/jax-throughput.md            # §5 item 3 (GPU measured)
  - docs/explanation/competitive-analysis.md       # "Speed" matrix row + tradeoff bullet
  - docs/_active/jax-throughput/INITIATIVE.md       # task #13 행
changelog_entry: docs/CHANGELOG.md (## jax-throughput)
---

# M4-EC3 GPU 실측 기록 — 결과 보고서

## 요약

`gpu-bench-colab`이 만든 Colab bench를 **사용자가 무료 NVIDIA T4서 실행** → **M4-EC3(≥10M steps/s GPU)
실측 달성**. 기록 + bench 기본 배치 상한 정직 수정.

**실측 (NVIDIA T4, fused `lax.scan` rollout, overworld slice)**:

| 행 | steps/s | vs EC |
|---|---|---|
| numpy single | 49,196 | — |
| jax single (jit scan) | 63,621 | 1.29× numpy |
| jax vmap (b1024) | 75,913,589 | 7.6× EC |
| jax vmap (b4096) | 271,352,874 | 27× EC |
| **jax vmap (b16384)** | **952,819,777** | **95× the ≥10M EC** |

→ **M4-EC3 달성** (GPU vmap ≈9.5억 steps/s, batch 단조 스케일). M4 EC1(hotpath 4/4 family 포트)·
EC2(parity 0)도 이니셔티브 입증 사실로 milestones에 ✅ 갱신(doc lag 정직화).

## 계획 대비 실적

| AC | 상태 | 결과 |
|---|---|---|
| AC1 batch 상한 하향 | ✅ | (..,16384,65536)→(..,16384) + 주석, CPU --quick 무크래시, ruff clean |
| AC2 실측 기록 | ✅ | milestones M4-EC3 달성 + jax-throughput.md §5 + competitive-analysis Speed 행/bullet |
| AC3 정직 경계 | ✅ | overworld 한정·full-episode GPU 미측정(free T4)·single run·free T4 명시 |
| AC4 회귀 0 | ✅ | src 무변경, 442 passed, mypy(28)/ruff/build clean |
| AC5 INITIATIVE/EC | ✅ | #13 행 + M4 EC1/EC2/EC3 ✅(증거 포인터) |

## 변경 파일 상세

**수정**:
- `scripts/gpu_bench.py` — 기본 `batches` 65536 제거(→1024/4096/16384) + 주석(b65536 free-T4 멈춤 사유).
  로직·함수 시그니처 무변경(회귀 0).
- `docs/reference/milestones.md` — M4 `⬜`→`🟢`, EC1·EC2·EC3 ☑ + 실측·증거 task.
- `docs/explanation/jax-throughput.md` — §5 item 3: GPU "미측정"→"✅ measured"(T4 952.8M, 경계 동반).
- `docs/explanation/competitive-analysis.md` — matrix "Speed" 행 + tradeoff "Speed" bullet(채택-게이트 갭 해소).
- `docs/_active/jax-throughput/INITIATIVE.md` — #13 행 + M4 EC 상태.

## 발견된 이슈

- **(정직 수정)** bench 기본 b65536이 무료 T4를 멈추게 함(65536 procgen 빌드 + 메모리 한계 thrashing·
  full-episode OOM) → 기본에서 제외(16384가 이미 ~950M로 throughput 포화). VRAM 충분 시 명시 전달 가능.
- **(경계)** full-episode env GPU 수치는 분기 많은 step의 free-T4 컴파일이 너무 느려 미확보 — 단 CPU
  full-episode 22M/s로 EC 이미 초과 → GPU도 초과 자명. 정밀 full-episode GPU 수치는 better-HW minor 후속.

## 흡수처 매핑

- milestones M4(EC1/EC2/EC3 ✅), jax-throughput.md §5(GPU measured), competitive-analysis(Speed 갭 해소).
- ADR 가치 없음(측정 결과 기록 + 1줄 default 수정).

## 타입 체크 / 빌드 결과

- `mypy src`: 28 files clean. `ruff check .`: passed. `build`: 1.0.0rc1 OK. `pytest`: 442 passed, 2 skipped.

## 후속

- (선택·better-HW) full-episode GPU 정밀 수치, b65536+ 대형 배치(VRAM 충분 시).
- M4는 사실상 완료. 남은 프로젝트 게이트: 공개(M3-EC4/EC5·사람), M5 eval 제품(전략·사람).
