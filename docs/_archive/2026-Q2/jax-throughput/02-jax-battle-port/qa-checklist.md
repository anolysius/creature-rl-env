# QA Checklist — jax-battle-port (G1 freeze 대상) · M4-EC1/EC2

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.
> 원칙: 성능 아닌 **측정 + 정직 feasibility verdict**로 freeze (pilot 이 AC7 분기 (b) 확정).

## Acceptance Criteria
- [ ] AC1 (JAX battle 포트): `src/critter_gym/jax_battle.py` 신규 — commit-mode 챔피언 battle step
      (move-vs-move + eff damage + faint→terminal)의 functional JAX 포트가 `jax.jit` 컴파일 성공.
- [ ] AC2 (parity): `tests/test_jax_battle_parity.py` — numpy `Battle(commit_mode=True)`와 동일 초기
      state + 동일 action 시퀀스에서 trajectory(champ_hp·boss_hp·active·winner·turn·done) **동일**.
      fixed + vary 차트 다수 config. `importorskip("jax")` CI numpy-only 보존.
- [ ] AC3 (산술 정확 일치): damage `max(1, floor(power·atk/def·eff))` + **hp 클램프 `max(0,·)`**(take_damage
      미러링) + 속도 타이(A 우선) + faint 타이밍 + max_turns truncation 경계가 numpy 와 정확 일치 — parity 가드.
- [ ] AC4 (bench): `scripts/bench_throughput.py` 에 battle step numpy vs jax single/vmap steps/s 행 추가,
      정직 framing(이득=vmap) 유지.
- [ ] AC5 (회귀 0): 기존 210 tests green(jax 미설치 CI 포함), mypy/ruff/build clean. 기존 `battle.py`/
      `creatures.py`/`types.py` 무변경(포트는 격리 복제). 코어 numpy-only.
- [ ] AC6 (feasibility verdict): report 박제 — (i) jit OK/NG (ii) parity OK/NG (iii) vmap speedup 방향
      (iv) 포트 범위(commit-mode; full 은 후속 `jax-battle-full`) (v) 후속 권고(jax-env-integration).
- [ ] AC7 (사전약정 결정규칙): pilot 이 **분기 (b)** 확정 → commit-mode 포트 + full 후속 분리. 정직 보고가 DoD.
- [ ] AC8 (툴체인 green): ruff ∧ mypy src ∧ pytest ∧ build.
