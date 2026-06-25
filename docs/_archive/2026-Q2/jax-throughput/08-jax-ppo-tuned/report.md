---
slug: jax-ppo-tuned
initiative: jax-throughput
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md       # PPO baseline + headroom Update
  - DESIGN.md                                # §3.1.1 tuned-PPO headroom (hard side)
  - docs/explanation/competitive-analysis.md # gap register "a hard benchmark" 데이터점
changelog_entry: docs/CHANGELOG.md
---

# tuned PPO 베이스라인 + oracle-headroom 정량화 — 결과 보고서

## 요약 (수치 표)

| config | PPO held-out gym-clear | oracle | type_blind | PPO/oracle | gap(in−out) | A2C-lite | R2 | R3 |
|---|---|---|---|---|---|---|---|---|
| default(3 gym) | 0.59 | 1.84 | 0.59 | **32%** | +0.12 | 0.78 | PPO 2.53≥0.78 | hard-and-learnable |
| hard(8 gym) | 1.06 | 7.28 | 2.03 | **15%** | −0.09 | 1.88 | PPO 2.56≥1.88 | hard-and-learnable |

- 전체 테스트 360 → **365**(+5, 회귀 0), 2 skipped. mypy(27)/ruff/build clean.
- A2C `train`/`evaluate`·`jax_env` **무변경**(PPO는 추가 API).

## 계획 대비 실적 (✅/⚠️/❌)

AC1–AC8 전부 ✅ (qa-checklist 1:1 대조). 핵심: AC1 proper PPO(GAE+clip+epochs+adv-norm), AC2 gae
property 3종 + evaluate_gym_clears, AC3 headroom default+hard, AC4 R2 PPO≥A2C, AC7 freeze 전 pilot
(falsify 0, R1/R2/R3 데이터 전 고정).

## 변경 파일 상세

**수정**:
- `src/critter_gym/jax_train.py` (+221): `PPOConfig` + `gae`(순수, reverse scan, value bootstrap)
  + `make_ppo_rollout`(value·logp_old 수집 + bootstrap last_value) + `ppo_loss`(clipped surrogate +
  adv-norm + value MSE + entropy) + `train_ppo`(GAE→K epoch×minibatch jit update + Adam) +
  `evaluate_gym_clears`(final gyms_defeated, oracle와 동일 지표) + `_DEFAULT_PPO_CONFIG` singleton.
  A2C 경로 무변경.

**신규**:
- `tests/test_jax_ppo.py` (+109): gae property(numpy ref·γ1λ1↔MC·λ0↔1-step TD) + train_ppo 학습
  smoke(R1) + gym-clears 범위.
- `scripts/ppo_baseline.py` (+135): default+hard config PPO vs A2C vs oracle headroom 보고(R1/R2/R3).

## 발견된 이슈 (심각도)

- **[정보·marketing] capability ladder 선명** — hard config서 tuned PPO(1.06) < 비추론 type_blind
  (2.03) < oracle(7.28). 현 tuned-PPO-baseline은 oracle이 쓰는 추론을 못 깸 = "hard-and-learnable"의
  실측 증거(벤치마크 결과 표 실체). R3 reframe 미발동(PPO ≪ 0.75×oracle).
- **[정보] A2C-lite hard서 거의 붕괴**(0.06~1.88) vs PPO robust — env가 RL 방법을 변별(PPO≫A2C).
- **[caveat] single-run·작은 net·CPU·200 iter·oracle proxy** — headroom은 *이 예산* 기준. multi-run
  rigor + 강한 baseline은 후속(difficulty-scaling 이니셔티브).

## 흡수처 매핑 (extracted_to)

- `jax-throughput.md` — PPO baseline + headroom Update(표 + capability ladder + caveat).
- `DESIGN.md` §3.1.1 — tuned-PPO headroom("hard" side measured).
- `competitive-analysis.md` — gap register "a hard benchmark"에 headroom 데이터점.
- ADR 가치: 없음(jax_train 확장, 신규 결정 아님). INITIATIVE task 8 행으로 충분.

## 타입 체크 / 빌드 결과

`mypy src` Success(27). `ruff check .` passed. `pytest` 365 passed/2 skipped. `python -m build` 성공.
