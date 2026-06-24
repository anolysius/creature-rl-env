# QA Checklist — difficulty-gap-rigor (G1 freeze 대상) · M3 신뢰성/(A)

> G1 통과 시 freeze. task-verify(G2)·task-end 가 1:1 대조.
> 원칙: 측정 + 정직 보고로 freeze. 결론은 multi-run. 사전약정 임계로 사후 편향 차단.

## 사전약정 (freeze) — classify_gap 임계, 데이터 보기 전 고정
`floor=0.3`, `k=1.0`. heldin<0.3→inconclusive / gap_mean>1.0·gap_std→real-gap /
|gap_mean|≤1.0·gap_std→gap≈0-signal / gap_mean<-1.0·gap_std→inconclusive. gap_std=**std-across-runs**.
확정 budget: **100k timesteps × 5 runs × d0/d1/d2**.

## Acceptance Criteria
- [ ] AC1: `scripts/difficulty_generalization.py` 에 `train_and_gap_multirun`(N run → gap mean ±
      std-across-runs) + `--runs N` CLI. 기존 `train_and_gap` 유지(무회귀).
- [ ] AC2: 사전약정 `classify_gap(gap_mean, gap_std, heldin_mean)` 순수함수 — gap≈0-signal/real-gap/
      inconclusive, 임계 floor=0.3·k=1.0(위 고정값).
- [ ] AC3: `tests/test_difficulty_generalization.py` — multi-run smoke(tiny, importorskip) + `classify_gap`
      결정론 단위 테스트(3 라벨 경계, numpy-only).
- [ ] AC4: 실측(background, 100k×5runs) — d0/d1/d2 gap **mean ± std-across-runs** + 각 점 classify 라벨
      report 기록. single 아닌 multi-run.
- [ ] AC5: 정직 verdict report 박제 — #24 약한신호 대비 multi-run 결과(robust gap≈0/real-gap/inconclusive)
      + env 재설계 필요성 함의. std-across-runs 병기, 과대 금지.
- [ ] AC6: 회귀 0 — 281 tests green, mypy/ruff/build clean, core numpy-only. DESIGN §3.1.1 갱신.
- [ ] AC7: 사전약정 분기 — 재측정 결과를 classify 임계로 verdict 분기(a robust gap≈0 / b real-gap=hard
      benchmark / c inconclusive). 어느 분기든 정직 보고가 DoD.
- [ ] AC8: 툴체인 green (ruff ∧ mypy src ∧ pytest ∧ build).
