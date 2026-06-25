# QA Checklist — ppo-headroom-rigor (G1 freeze)

> Frozen: 2026-06-25. Mode: standard.

## 사전약정 결정규칙 (데이터 전 고정 — held-out gym-clear, k=1.0, frac=0.75)

- `mean(PPO) + k·std ≤ frac × oracle` → **`hard-and-learnable`** (낙관 상한도 oracle 75% 미만).
- `mean(PPO) − k·std ≥ frac × oracle` → **`ppo-closes`** → reframe·정지.
- 그 외 → **`inconclusive`** (robust 판정 불가, run/budget↑ 권고).

## Acceptance (frozen → 결과)

- [x] AC1 ✅: `headroom.py` `classify_headroom`(frac=0.75·k=1.0) + `HeadroomVerdict`. numpy-only.
- [x] AC2 ✅: `test_headroom.py` 7 passed — 3 verdict 경계 + ratio + custom frac/k + 빈입력/oracle≤0 가드.
- [x] AC3 ✅: `--runs 5` default 0.52±0.06=oracle 1.84의 28% / hard 1.52±0.28=7.28의 21%, 양 config `hard-and-learnable` robust.
- [x] AC4 ✅: 372 passed(365+7), jax_train/jax_env 무변경, headroom.py numpy-only CI 포함.
- [x] AC5 ✅: 5-run mean±std·CPU·작은 net·이 예산·oracle proxy 라벨(docs).
- [x] AC6 ✅: pilot이 classify property 7 + multi-run 입증, 임계 고정. ppo-closes 미발동(reframe 불요).
- [x] AC7 ✅: mypy(28)/ruff/pytest(372)/build clean + 문서(jax-throughput.md·DESIGN·INITIATIVE) + CHANGELOG.

## Default pass-criteria
- [ ] 신규 코드 테스트 동반. L3 APPROVED. feature→PR.
