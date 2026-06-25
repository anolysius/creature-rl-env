---
slug: recurrent-ppo
initiative: hard-benchmark
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md           # Update (recurrent-ppo)
  - docs/explanation/competitive-analysis.md      # gap register "robust learnability result" 행
  - docs/_active/hard-benchmark/INITIATIVE.md      # task #2 행 (이동 시 archive 로 따라감)
changelog_entry: docs/CHANGELOG.md (## hard-benchmark)
---

# Recurrent PPO — does memory close the *PPO* headroom under partial observability? (결과 보고서)

## 요약 (수치 표)

부분관측 Q1 `default` config (grid 10, **5×5 egocentric view**, vary num_types 8, 1–3 gyms),
matched greedy eval, CPU, **3 seed, 250 iters**:

| arm | held-out gym-clears | % of oracle (1.94) | learns (R1) |
|---|---|---|---|
| feedforward PPO (h256) | 0.46 ± 0.08 | 24% | ✅ |
| **recurrent PPO (GRU h128)** | **1.02 ± 0.19** | **53%** | ✅ |
| memory effect (rec − ff) | **+0.56** > max std 0.19 | — | **(a) LOAD-BEARING robust** |
| oracle / type_blind | 1.94 / 0.62 | (0.75·oracle = 1.45) | scripted proxy |

**Verdict = (a) recurrence-helps-PPO** (사전약정 규칙 `rec−ff > max(std)` 충족). rec PPO 53% <
0.75·oracle → **(c) headroom-CLOSES 미발동** (헤드라인 헤드룸 유지, 사람보고 stop 불요).

**핵심**: A2C에서 본 메모리 효과(#1: ff 18% vs rec 46%)가 **더 강한 PPO에서도 robust하게 재현**
(ff 18→24%, rec 46→53%; PPO가 양쪽을 올려도 메모리 gap 유지) → A2C 결과가 **알고리즘 산물이 아님**.
recurrent net이 *더 좁은데도*(h128 < h256) 2배+ → 이득 = **memory, not capacity** (non-vacuity).

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 상태 | 결과 |
|---|---|---|
| AC1 correctness 게이트 | ✅ | 4 테스트 통과: replay 정합(tol 1e-4) + env-축 permutation 불변(tol 1e-4) + loss finite + train smoke |
| AC2 학습 (R1) | ✅ | ff·rec PPO 3 seed 모두 `learning_verdict` branch "a" |
| AC3 사전약정 규칙 | ✅ | (a) recurrence-helps-PPO robust (+0.56 > 0.19); (c) 미발동 |
| AC4 회귀 0 | ✅ | 423→427 passed(+4), 2 skipped, exit 0; mypy 28 / ruff / build clean |
| AC5 정직 경계 + docs | ✅ | jax-throughput.md + competitive-analysis + INITIATIVE 갱신, 경계 라벨 명시 |
| AC6 freeze 전 pilot | ✅ | --quick 2-run: correctness 통과·학습 확인·timing 현실적, falsify 없음 |

## 변경 파일 상세

**신규**:
- `tests/test_jax_recurrent_ppo.py` (114 lines) — correctness 게이트 + smoke (importorskip, CI numpy-only).
- `scripts/recurrent_ppo_baseline.py` (123 lines) — 부분관측 ff vs rec PPO matched eval + 사전약정 규칙.

**수정 (추가만 — 기존 경로 byte-identical)**:
- `src/critter_gym/jax_train.py` (+187 lines, 파일 끝 "Recurrent (GRU) PPO" 섹션):
  `recurrent_replay`(loss·테스트 공유 GRU 재생) / `make_recurrent_ppo_rollout`(hidden 스레딩 + h0 노출 +
  last_value bootstrap) / `recurrent_ppo_loss`(env-축 minibatch clipped surrogate) /
  `train_recurrent_ppo`(env축만 셔플·T 보존·epochs).
- `docs/explanation/jax-throughput.md` (+32) — Update (recurrent-ppo).
- `docs/explanation/competitive-analysis.md` (+1/−1) — gap register 갱신.
- `docs/_active/hard-benchmark/INITIATIVE.md` (+1) — task #2 행.

## 발견된 이슈 (심각도)

- **(설계 결정, 낮음)** 구현은 `recurrent_a2c_loss`의 inline scan을 `recurrent_replay`로 *복제*했다
  (리팩터 아님) — recurrent-A2C 경로를 byte-identical로 유지(AC4)하기 위함. 의도적 중복.
- **(정직 경계, 중간)** A2C(#1)는 fixed-3-gym 변형(oracle 2.81), 본 task는 Q1 `default` vary'd
  1–3-gym(oracle 1.94)이라 **config가 다름** → cross-config 절대수치 비교 금지, **within-config
  ff-vs-rec gap만** 읽어야 함(docs에 명시). config를 Q1 default로 택한 이유 = "Q1 PPO headroom과의
  깨끗한 연결"이 본 task의 목적.

## 흡수처 매핑 (extracted_to 상세)

- **jax-throughput.md** — recurrent-ppo Update: 기술(sequence-preserving minibatch)·correctness 게이트·
  실측·정직 경계. M4/난이도 narrative의 살아있는 갱신.
- **competitive-analysis.md** — gap register "robust learnability result": recurrence axis가 A2C+PPO
  둘 다 settled로 갱신, 남은 frontier=deeper absolute difficulty.
- ADR 가치 별도 없음 (기존 jax_train 패턴·#1 결정규칙 계승, 새 아키텍처 결정 아님).

## 타입 체크 / 빌드 결과

- `mypy src`: Success, 28 files. `ruff check .`: All checks passed. `python -m build`: wheel/sdist
  1.0.0rc1 OK. `pytest tests/`: 427 passed, 2 skipped, exit 0 (회귀 0).

## 후속 (initiative)

recurrence axis는 이제 **A2C+PPO 둘 다 settled**. 남은 hard-benchmark frontier = **더 깊은 절대
난이도**(긴 호라이즌·다중타입 보스·강화된 부분관측)로 "메모리 agent에도 oracle headroom 잔존"을
키우기 — spec 변경 = JAX 재포트 동반. 또는 GPU 측정(M4-EC3, 하드웨어 게이트)·공개(사람 게이트).
