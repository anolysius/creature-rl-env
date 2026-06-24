# QA Checklist — jax-rl-demo (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록과 1:1 대조.

## Acceptance Criteria

- [ ] **AC1** — `src/critter_gym/jax_train.py` 신규: JAX-native 최소 학습 루프(obs flatten + tiny MLP policy/value + optimizer + region-bank/fixed-horizon auto-reset + lax.scan rollout + jit update). `import jax` 모듈, 코어 numpy-only 보존(`__init__` 미import).
- [ ] **AC2** — `scripts/jax_rl_demo.py` 신규: 학습 1회 → 학습 곡선(iter별 mean episode return) + 학습 rollout throughput(env-steps/s) + numpy/sb3 동예산 wall-clock 정직 비교 + framing. seed split 유지(train bank vs held-out).
- [ ] **AC3** — 측정+정직 보고(성능 freeze 아님). 보고 헤드라인이 **사전약정 결정규칙** 산출 분기((a)/(b)/(c))와 일치 + 모든 수치 caveat 라벨 동반. "빠르다"는 R4 부등식 성립 시에만.
- [ ] **AC4** — core CI numpy-only 불변(구조적): import 후 `sys.modules`에 jax 부재(또는 `__init__.py` jax_train import 0) + jax 미설치 가정 `pytest -q`=283 green(신규 importorskip skip).
- [ ] **AC5** — `tests/test_jax_train.py`(importorskip) smoke: 몇 iter 실행 / params pytree 값 변화 / 리턴 finite / obs-flatten 결정론+차원(고정 D). 학습 품질 CI 비주장.
- [ ] **AC6** — canonical 0-exit: `mypy src` · `ruff check .` · `pytest -q` · `python -m build`. (AC4=격리 구조, AC6=도구 통과 — 분리.)
- [ ] **AC7** — freeze 전 pilot로 R1·R2·R4 측정 → 사전약정 결정규칙이 헤드라인 분기 기계적 확정. (a) falsify 시 (b)/(c) reframe. pilot 결과·적용 규칙·확정 분기 report 박제.
- [ ] **AC8** — 문서: jax-throughput.md(§4/§5) + DESIGN §4 + competitive-analysis "competitively fast" 행 + CHANGELOG + INITIATIVE 갱신. broken-link 0.

## 사전약정 결정규칙 (freeze — 데이터 보기 전 고정)

- **R1 → (a)vs(b)**: `mean_late(마지막 20% iter) − mean_early(초기 20% iter) ≥ std_late` 이면 (a)"학습+빠름", 아니면 (b)"throughput 헤드라인 + 학습 partial".
- **R2 → (c)**: region-bank 인덱스 reset이 `jax.jit` 아래 tracer/concretization 에러 없으면 region-bank, 에러 시 (c) fixed-horizon 후퇴.
- **R4 speed**: "빠르다"는 `vmap rollout env-steps/s > numpy sb3 collection env-steps/s`(동일 환경수·머신) 성립 시에만 주장. 미성립 시 정직 철회 보고.
