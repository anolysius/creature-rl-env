---
slug: memory-headroom
initiative: hard-benchmark
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md           # Update (memory-headroom)
  - docs/explanation/competitive-analysis.md      # gap register "a hard benchmark" + matrix "Difficulty(absolute)"
  - docs/_active/hard-benchmark/INITIATIVE.md      # task #3 행
changelog_entry: docs/CHANGELOG.md (## hard-benchmark)
---

# Memory-agent headroom — is the env hard *even for a strong memory agent*? (결과 보고서)

## 요약 (수치 표)

deep partial-obs config (grid 16, **5×5 view**, 5 gyms, 420 steps; `hard_env_spec`),
matched greedy eval, CPU, **5 seed, 300 iters**:

| arm | held-out gym-clears | % of oracle (4.69) |
|---|---|---|
| feedforward PPO (h256) | 0.53 ± 0.44 | 11% |
| **recurrent PPO (GRU h128)** | **2.01 ± 1.05** | **43%** |
| opt-bound (mean+std) | **3.06** ≪ 0.75·oracle **3.52** | → **(a) hard-for-memory ROBUST** |
| oracle / type_blind | 4.69 (winnable) / 2.00 | scripted proxy |

**Verdict = (a) hard-for-memory-agent ROBUST** (사전약정 `classify_headroom(frac=0.75, k=1.0)` →
`hard-and-learnable`). **(b) memory-CLOSES 미발동** → 헤드라인 reframe 없음, 사람보고 stop 불요.

**의미**: 더 깊은 config가 *메모리 agent에게도* 더 hard — recurrent PPO가 grid10(53%)보다 *낮은*
43%만 회복하고 **절대 headroom은 훨씬 큼**(~2.7/4.69 gym 미달 vs grid10 ~0.9/1.94). memoryless feedforward
PPO는 11%로 더 floor. 메모리 여전히 load-bearing(rec−ff +1.49 ≈ 4× ff). → competitive-analysis
"Difficulty(absolute)" **❌toy → ◐**("현 baseline class엔, 메모리 agent 포함, hard").

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 상태 | 결과 |
|---|---|---|
| AC1 parity 게이트 | ✅ | grid16/5gym parity **0 mismatch** (15 테스트: random5+gym6+heldout2+shapes1+smoke1) |
| AC2 learnable+winnable | ✅ | oracle 4.69 winnable; recurrent PPO learns=True (5 seed 다수 branch a) |
| AC3 frozen 3-branch | ✅ | (a) hard-for-memory robust (opt-bound 3.06 ≤ 3.52); (b) 미발동 |
| AC4 회귀 0 | ✅ | 427→442 passed(+15), 2 skipped, exit 0; mypy 28 / ruff / build clean |
| AC5 정직 경계 + docs | ✅ | jax-throughput.md + competitive-analysis(gap+matrix) + INITIATIVE 갱신 |
| AC6 freeze 전 pilot | ✅ | --quick 2-run: parity0·학습·winnable·timing; 3→5 seed robust 굳힘 |

## 변경 파일 상세

**신규**:
- `tests/test_jax_hard_config_parity.py` — grid16/5gym parity(0 mismatch) + hard_env_spec shape + recurrent PPO smoke.
- `scripts/hard_benchmark_memory.py` — ff PPO vs rec PPO vs oracle @grid16, 사전약정 classify_headroom 판정.

**수정 (추가만 — 기존 경로 byte-identical)**:
- `src/critter_gym/jax_train.py` (+`hard_env_spec()` 헬퍼) — `difficulty_env_spec` 패턴, JaxEnvConfig
  config-driven(re-port 불요). 기존 spec/train/eval/PPO/recurrent 경로 무변경.
- `docs/explanation/jax-throughput.md`(Update) · `competitive-analysis.md`(gap register + matrix) ·
  `INITIATIVE.md`(#3 행).

## 발견된 이슈 (심각도)

- **(정직 경계, 중간)** **3 seed는 경계선**(rec 2.44±0.97, opt-bound 3.41 vs 임계 3.52, margin 0.11) →
  multi-seed 교정 문화대로 **5 seed로 재측정**(rec 2.01±1.05, opt-bound 3.06, margin 0.46)해 robust (a)로
  확정. 5 seed에서도 **std 1.05로 분산 큼**(long-horizon task의 seed별 학습 편차) — 보고에 명시.
- **(scout 한계, 낮음)** scratch scout는 numpy num_creatures(default 5) vs JAX region(6) 불일치였으나
  방향 신호용. 공식 config는 양쪽 num_creatures=6 일치(parity 0 검증).

## 흡수처 매핑 (extracted_to 상세)

- **jax-throughput.md** — memory-headroom Update: parity 게이트·실측·"메모리 agent에게도 hard"·정직 경계.
- **competitive-analysis.md** — gap register "a hard benchmark"(stronger/multi-run baseline ✅ + 메모리
  agent) + matrix "Difficulty(absolute)" ❌toy→◐.
- ADR 가치 없음(기존 config-driven 포트·classify_headroom·#1·#2 패턴 계승).

## 타입 체크 / 빌드 결과

- `mypy src`: Success, 28 files. `ruff check .`: passed. `build`: 1.0.0rc1 OK. `pytest`: 442 passed,
  2 skipped, exit 0 (회귀 0).

## 후속 (initiative)

recurrence axis(#1·#2)와 **메모리 agent 절대 난이도(#3)** settled. 남은 frontier: **더 깊은 절대
난이도**(다중타입 보스·전략 깊이) + **SOTA-class agent** 대비 측정(현 "강한 agent"=recurrent PPO는
baseline). family 확장. GPU·공개는 각각 하드웨어·사람 게이트.
