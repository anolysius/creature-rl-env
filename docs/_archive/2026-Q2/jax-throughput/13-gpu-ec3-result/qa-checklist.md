# QA Checklist — gpu-ec3-result (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 동결.
> ⚠ M4-EC3 GPU 실측 기록 — 성공 = 정직한 기록(과대 금지)이지 "M4 전부 완성" 선언이 아니다.

## Acceptance Criteria (frozen at G1)

- [x] **AC1** ✅ — `gpu_bench.py` 기본 batch (1024,4096,16384,65536)→**(1024,4096,16384)** + 주석 3줄
  (b65536 free-T4 멈춤 사유). CPU `--quick` 무크래시(로직·시그니처 무변경, vmap≫numpy 유지). ruff clean.
- [x] **AC2 (실측 기록)** ✅ — milestones M4-EC3 **달성**(T4 overworld vmap **952.8M @b16384**, 95× EC;
  b1024 75.9M·b4096 271M) + 증거 task. jax-throughput.md §5 item3(미측정→**✅ measured**) +
  competitive-analysis "Speed" 행(JAX vmap ~950M GPU) + tradeoff "Speed" bullet(갭 해소). 수치=실측 일치.
- [x] **AC3 (정직 경계)** ✅ — 모든 기록에 overworld slice 한정·full-episode GPU 미측정(free T4 컴파일
  한계, CPU 22M/s로 EC 초과)·single run·free T4 명시. "M4 완전 달성"식 과대 0.
- [x] **AC4 (회귀 0)** ✅ — src 무변경. **442 passed**, 2 skipped, exit 0. mypy(28)·ruff·build clean.
- [x] **AC5** ✅ — INITIATIVE #13 행 추가 + CHANGELOG=task-end. milestones M4 EC1(hotpath 4/4 family)·
  EC2(parity 0)도 증거 task 포인터와 함께 ✅ 표기(아카이브·jax-throughput.md 입증 사실, 날조 아님).

## L1 이력
- round 1: plan-reviewer **APPROVE** / qa-verifier **2 SUGGEST**(AC4 "442" 명확화·경로 위치) → SUGGEST_CUTOFF.
  흡수: AC4에 "passing 테스트 수 442·2skip" + scope_paths 전체 경로 명시.

## 정직성 불변식
EC3는 "≥10M GPU vmap" — overworld 952M로 문자 그대로 충족이나 **overworld 한정·full-episode GPU 미측정·
free T4·single run** 경계를 숨기지 않음. EC1/EC2 표기는 아카이브·jax-throughput.md로 입증된 사실 반영(증거
동반). 헤드라인보다 정직성.
