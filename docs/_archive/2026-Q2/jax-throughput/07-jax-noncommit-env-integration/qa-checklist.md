# QA Checklist — jax-noncommit-env-integration (G1 freeze)

> G1 통과 시점에 동결된 acceptance. task-verify(G2)·task-review(L3)가 이 목록과 1:1 대조.
> Frozen: 2026-06-25. Mode: standard.

## Acceptance (frozen → 결과)

- [x] **AC1** ✅: `make_jax_env(JaxEnvConfig(commit=False))`가 non-commit full-episode env step 생성
  (overworld + SWITCH/force-switch/party-wipe). jit 컴파일 — `test_jit_compiles` pass.
- [x] **AC2 (비협상 게이트)** ✅: numpy `CritterEnv(commit_battles=False)` 대비 **parity 0 mismatch** —
  13 obs 키 + reward + term + trunc, full 에피소드, fixed+vary, random+gym-clearing+switch-heavy+
  never-attack(패배) 정책, seed 배터리. **32 passed** (`test_jax_noncommit_env_parity.py`).
- [x] **AC3 (무회귀)** ✅: 360 passed(328+32), 2 skipped. commit parity(18)/difficulty/standalone
  full-battle 무회귀. default-config(commit=True) byte-identical(commit 경로 무변경).
- [x] **AC4** ✅: vmap 배치 처리; numpy 139k/s · jax vmap **5.08M(b=1024)=36× / 8.35M(b=16384)=60×**
  (CPU·single·vmap-only 정직).
- [x] **AC5** ✅: jit이 non-commit step 컴파일 — `test_jit_compiles`/`test_vmap_batches` pass.
- [x] **AC6 (정직 범위)** ✅: docs에 CPU·single·family A·vmap-only·potion inert·battle-trunc edge 라벨.
- [x] **AC7 (사전약정 pilot)** ✅: freeze 전 가정 검증(보스 항상-MOVE·trunc 비발산·switch 순서 구분) +
  parity 배터리 0 mismatch + non-vacuity 가드. 미러 불가 mismatch 0 → reframe 불요.
- [x] **AC8** ✅: mypy(27)/ruff/pytest(360)/build clean. jax-throughput.md(§4+§5)·INITIATIVE·DESIGN §4
  갱신. CHANGELOG 1줄 — task-end append.

## Default pass-criteria (harness)

- [ ] 신규/변경 코드에 테스트 동반 (TDD Red→Green).
- [ ] L3 multi-reviewer APPROVED (task-end 선결 조건).
- [ ] feature 브랜치 → PR (main 직접 금지).
