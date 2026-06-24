# QA Checklist — jax-env-integration (G1 freeze 대상) · M4-EC1/EC2

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.
> 원칙: 성능 아닌 **측정 + 정직 feasibility verdict**로 freeze (pilot 이 AC7 분기 (a) 목표 확정).

## Acceptance Criteria
- [ ] AC1 (통합 env step): `src/critter_gym/jax_env.py` 신규 — `(state, action) → (state, obs, reward, term,
      trunc)` 이 overworld + commit-battle 을 `lax.cond` mode dispatch 로 합성, `jax.jit` 컴파일.
- [ ] AC2 (parity): `tests/test_jax_env_parity.py` — numpy `CritterEnv(commit_battles=True)`와 동일 seed +
      동일 action 시퀀스에서 full-episode trajectory 동일(reward·terminated·truncated + obs). fixed + vary
      seed. `importorskip("jax")` CI numpy-only 보존.
- [ ] AC3 (vmap): batched full-episode rollout 동작(leading batch dim 보존) — RL 루프 소비 형태.
- [ ] AC4 (bench): `scripts/bench_throughput.py` 에 full env step numpy vs jax single/vmap steps/s 행 추가,
      정직 framing(이득=vmap) 유지.
- [ ] AC5 (회귀 0): 기존 263 tests green(jax 미설치 CI 포함), mypy/ruff/build clean. 기존 numpy env 무변경
      (포트는 격리 복제). 코어 numpy-only.
- [ ] AC6 (feasibility verdict): report 박제 — (i) jit (ii) parity 범위·OK/NG (iii) vmap speedup 방향
      (iv) 포트 범위(family A commit-mode; obs 범위; 미포함분) (v) 후속 권고.
- [ ] AC7 (사전약정 결정규칙): pilot 이 **분기 (a) 목표** 확정(composition+evolution+스칼라obs+reward+term
      parity 입증) → full obs(local_patch 포함) 목표; 무거우면 (b) local_patch 후속 분리. 정직 보고가 DoD.
- [ ] AC8 (툴체인 green): ruff ∧ mypy src ∧ pytest ∧ build.
