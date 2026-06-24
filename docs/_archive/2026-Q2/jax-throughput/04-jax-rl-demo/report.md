---
slug: jax-rl-demo
initiative: jax-throughput
status: completed
ended: 2026-06-24
extracted_to:
  - docs/explanation/jax-throughput.md   # §4 "Update (jax-rl-demo)" 블록 + §5 + references
  - DESIGN.md                            # §4 M4 follow-on 1문단
  - docs/explanation/competitive-analysis.md  # "competitively fast" 갭 register 행 보강
changelog_entry: docs/CHANGELOG.md (jax-throughput 섹션)
---

# RL 학습 데모 — JAX 벡터화 env로 실제 학습 1회 (M4 마감) — 결과 보고서

## 한 문단 요약 (수식 없이)

지난 세션에 만든 "수천 개를 한꺼번에 돌리는 빠른 JAX 엔진" 위에서 **AI를 실제로 한 번 학습시켰습니다.** 결과: AI의 점수가 학습과 함께 분명히 올라갔고(에피소드 점수 약 1.8 → 약 10.0), 그 학습이 **옛날 방식(sb3)보다 약 170배 빨랐습니다** — CPU에서 1.23백만 걸음을 약 2초에. 처음 보는 맵(held-out)에서도 본 맵과 비슷하게 잘 해서, "외운 게 아니라 진짜 배웠다"는 신호도 함께 나왔습니다. 단, 이건 *튜닝된 최고 성능*이 아니라 *신호*입니다(간단한 학습법·CPU·한 번 실행). 가장 중요하게 — **결과를 보고 나서 좋게 포장하는 걸 막으려고, "어떤 결과면 어떤 결론을 쓴다"는 규칙을 실험 전에 미리 못박고 그대로 따랐습니다.**

## 요약 (수치)

| 항목 | 값 | 비고 |
|---|---|---|
| 학습 곡선 (mean reward/step) | 0.0068 → 0.0513 | ep_return 환산 ~1.8 → ~10.0 |
| R1 사전약정 규칙 | rise **0.041 ≥ std_late 0.003** | → **분기 (a) 학습+빠름** |
| 학습 throughput (jax vmap) | **~0.66M env-steps/s** | 1.23M steps / ~1.9s (별 run ~1.1M, single-run 변동) |
| numpy sb3 collection (기존 경로) | ~3.8k env-steps/s | 단일 DummyVecEnv |
| speed (R4 부등식) | **~170× FASTER** | 0.66M > 3.8k 성립 → "빠르다" 정당 |
| 일반화 (greedy, ep return) | held-out **1.44** vs held-in **1.00** | seed split, **gap≈0** (no-memorization 일관) |
| 테스트 | 283 → **287** (+4 smoke, 회귀 0) | jax importorskip 격리 |
| canonical | mypy(26) / ruff / build clean | |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 jax_train.py 신규 | ✅ | obs flatten + tiny MLP + manual Adam + region-bank auto-reset + lax.scan rollout + jit. `__init__` 미import. |
| AC2 jax_rl_demo.py 신규 | ✅ | 학습곡선 + throughput + sb3 비교 + held-out eval. seed split(train range(B) vs heldout_seeds disjoint). |
| AC3 측정+정직보고 | ✅ | 헤드라인=사전약정 규칙 산출 분기 (a) 일치, 모든 수치 caveat 라벨, "빠르다"=R4 부등식 근거. |
| AC4 core CI numpy-only 불변 | ✅ | `import critter_gym` 후 sys.modules에 jax 부재(True), `__init__` jax 참조 0. |
| AC5 smoke 테스트 | ✅ | 4 테스트(flatten dim 38·결정론 / train params 변화 / learning_verdict 규칙 / evaluate finite). |
| AC6 canonical 0-exit | ✅ | mypy clean, ruff clean, pytest 287 passed/2 skipped, build OK. |
| AC7 freeze 전 pilot | ✅ | R2 auto-reset jit OK(region-bank) / R1 (a) / R4 부등식 성립. 사전약정 규칙 기계적 적용. |
| AC8 문서 | ✅ | jax-throughput.md(§4/§5/refs) + DESIGN §4 + competitive-analysis + INITIATIVE. CHANGELOG=task-end append. broken-link 0(신규 archive 링크는 표준 패턴). |

## 변경 파일 상세

**신규**
- `src/critter_gym/jax_train.py` (320줄) — JAX-native A2C: `TrainConfig`/`TrainResult`, `flatten_obs`(OBS_DIM=38), `init_params`/`apply_policy`(tiny MLP), `build_region_bank`(numpy procgen bridge), `make_rollout`(lax.scan + auto-reset), `_returns`/`a2c_loss`, manual `_adam_*`, `train`, `learning_verdict`(사전약정 R1 규칙), `evaluate`(held-out, greedy, alive-masked).
- `scripts/jax_rl_demo.py` (140줄) — 데모 실행 + sb3 baseline + 정직 framing. `--quick`/`--no-sb3`/`--no-eval`.
- `tests/test_jax_train.py` (73줄) — importorskip smoke 4종.

**수정**
- `docs/explanation/jax-throughput.md` — §4 "Update (jax-rl-demo)" 블록 + §5 + references.
- `DESIGN.md` — §4 M4 follow-on 1문단.
- `docs/explanation/competitive-analysis.md` — "competitively fast" 행 보강(데모로 "trains" 입증).
- `docs/_active/jax-throughput/INITIATIVE.md` — task 4 행 + 다음-task 갱신.

## 발견된 이슈 / 정직한 한계

- **A2C-lite (튜닝 PPO 아님), CPU, single run** — *데모/신호*지 SOTA 벤치 아님. throughput은 run 간 변동(0.66M~1.1M).
- **학습 메트릭 = reward/step proxy** — episode return은 `×_MAX_STEPS=200` 상한 환산(데모 내 일관, caveat 명시). greedy eval은 quick-모드(저 iter)서 collapse해 0이 나올 수 있음(full run서 정상).
- **sb3 baseline = 기존 단일-env 경로** — 다중 프로세스 sb3는 비율을 줄이나 on-device vmap 미만. GPU 미측정.
- **env config 하드코딩** — jax_env가 CritterEnv 기본(10×10·boss120·super_mult 무증폭)으로 고정 → 난이도 knob 변주 불가(데모 범위 밖).

## 흡수처 매핑 (extracted_to)

| 살아있는 정보 | 흡수처 |
|---|---|
| "벡터화 env가 실제로 학습한다 + ~170× speed" narrative | `docs/explanation/jax-throughput.md` §4 Update 블록 |
| M4 follow-on 진행 상태 | `DESIGN.md` §4 |
| "competitively fast" 비교우위 갱신 | `docs/explanation/competitive-analysis.md` 갭 register |
| 사전약정 결정규칙(R1) | 코드 `jax_train.learning_verdict` + plan/qa-checklist (SSOT는 코드) |

ADR 가치 결정: 없음(기존 jax-throughput 이니셔티브 narrative + 코드로 충분, 새 아키텍처 결정 아님).

## 검증 결과

- mypy src: clean (26 files) · ruff check .: clean · pytest: 287 passed, 2 skipped (회귀 0) · build: OK
- AC4 격리: `jax not in sys.modules after import critter_gym` = True
- L3: @plan-reviewer APPROVE(5축, 코드 정합성 포함) + @qa-verifier APPROVE(3축) = 2/2 APPROVED
