# QA Checklist — jax-hotpath-foundation (G1 freeze 대상) · M4-EC1/EC2 토대

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.
> 원칙: 성능 수치가 아니라 **측정 + 정직 feasibility verdict** 로 freeze (pilot 이 AC7 분기 (a) 로 확정).

## Acceptance Criteria
- [ ] AC1 (JAX overworld 포트): `src/critter_gym/jax_overworld.py` 신규 — overworld step(move+catch/
      contact-collect+battle 진입 flag, battle 제외)의 functional JAX 포트가 family A·B 커버, `jax.jit`
      컴파일 성공. (pilot 입증; 불가 판명 시 그 사실 입증=충족)
- [ ] AC2 (parity): `tests/test_jax_parity.py` — 동일 seed+동일 action 시퀀스에서 JAX overworld 가 numpy
      overworld 와 trajectory(agent_pos·caught·reward·battle진입 step) 동일. battle 진입 전까지 범위 명시.
      `importorskip("jax")` 로 CI numpy-only 보존.
- [ ] AC3 (bench 하네스): `scripts/bench_throughput.py` — numpy overworld steps/s 베이스라인 +
      (jax 환경) single/vmap steps/s 정직 출력(환경·batch·기기 라벨; "이득은 vmap 에서, single 은 느림"
      framing 명시). 수치는 report 에 기록(단일 측정=헤드라인 아님).
- [ ] AC4 (extra 격리): `pyproject.toml` 에 `[jax]` extra 추가, 코어 deps numpy-only 유지.
      `pip install` 기본은 numpy-only(무회귀).
- [ ] AC5 (회귀 0): 기존 199 tests green(jax 미설치 CI 포함), mypy/ruff/build clean. 기존 `CritterEnv`/
      `ForageEnv` 런타임·obs·action 무변경(포트는 격리 복제).
- [ ] AC6 (feasibility verdict): report 에 박제 — (i) jit OK/NG (ii) parity OK/NG (iii) CPU vmap speedup
      방향·비율 (iv) battle 포트 난이도 예측 (v) 후속 권고. speedup 음수/이득없음도 정직 결론.
- [ ] AC7 (사전약정 결정규칙): pilot 결과로 freeze 분기 — pilot 이 **분기 (a)** 확정(jit OK ∧ parity 맞음)
      → 본 scope 진행. (b 슬라이스축소 / c reframe 은 미발동.) 어느 분기든 정직 보고가 DoD.
- [ ] AC8 (툴체인 green): ruff ∧ mypy src ∧ pytest(jax 환경) ∧ build.
