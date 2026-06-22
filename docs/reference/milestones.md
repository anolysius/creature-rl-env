# CritterGym Milestones (reference)

> 제품 마일스톤의 **사실 SSOT**. 순서·근거 narrative 는 [roadmap.md](../explanation/roadmap.md) 참조.
> 상위 SSOT = [`DESIGN.md`](../../DESIGN.md) §6 (본 표는 그 Phase 를 *구체화*; 모순 시 DESIGN 우선).
> ⚠ `docs/harness/explanation/master-plan.md` 는 **하네스 도입 계획**(별개) — 제품 마일스톤 아님.

## 규율 (즉흥성 제거)

> **매 `/task-start` 는 "이 task 가 어느 마일스톤(M)의 어느 exit criterion(EC)을 전진시키는가"를 명시한다.
> task 는 *활성 마일스톤*의 미충족 EC 에서만 내려온다. 활성 M 의 EC 가 모두 충족되면 다음 M 으로 게이트.**
> task report 는 "M{n}-EC{k} 충족" 형태로 체크인해 진행도를 가시화한다.

활성 마일스톤: **M2** (M0·M1 완료).

## 마일스톤 표

| M | 이름 | 상태 | Goal | DESIGN |
|---|---|---|---|---|
| M0 | Foundation | ✅ done | 패키지+최소 env+검증 레이어 | §6 P1 |
| M1 | 고정월드 full subgoal chain | ✅ done | 절차생성 없이 단일 월드에서 catch→evolve→gym boss | §3.4–3.5 |
| M2 | Procgen + train/test (moat) | 🔵 active | 시드→절차 월드 + 절차 타입표; 일반화 측정 | §3.1 |
| M3 | 벤치마크 신뢰성 + 런치 | ⬜ pending | 베이스라인 4종 + 리더보드 + viz + writeup + OSS + 킬러 데모 | §5–6 P2 |
| M4 | Throughput (JAX) | ⬜ pending | spec 안정 후 핫패스 JAX 포팅 | §4 |
| M5 | 수익화 표면 | ⬜ pending | 비공개 held-out eval + 커스텀 env + Hub | §8 |

## Exit Criteria (마일스톤별)

### M0 — Foundation ✅
- [x] EC1: `gymnasium.make("CritterGym-v0")` 가 동작하는 env 반환
- [x] EC2: 베이스라인 spread 존재 (greedy > random > 0)
- [x] EC3: Gymnasium `check_env` 통과
- [x] EC4: throughput 회귀 가드 (실측 ~266k steps/s/core)
- 구성 task: `scaffolding`, `env-validation` (둘 다 archived)

### M1 — 고정월드 full subgoal chain ✅ done
- [x] EC1: 턴제 배틀 sub-MDP 동작 (타입 상성 데미지·스위치·아이템) — **고정** 타입표 *(`battle-system`)*
- [x] EC2: 진화가 long-horizon 투자 결정으로 동작 (level gated; 배틀 승리→레벨업→임계 자동 진화) *(`creature-evolution`)*
- [x] EC3: 배틀이 월드의 gated checkpoint 로 동작, catch+gym subgoal 이 `info["subgoals"]` 에 노출
  *(`gym-boss-progression`; evolve·최종보스는 EC2 와 함께 체인 확장)*
- [x] EC4: 각 subgoal 이 boolean-verifiable 리워드 (catch +1, gym 격파 +1; dense shaping 없음) *(`gym-boss-progression`)*
- [~] EC5: scripted 또는 PPO 가 (고정월드에서) ≥1 gym boss 격파; 에피소드 ≥1k 스텝.
  *(scripted 충족 — `gym-boss-progression`; PPO/풀 베이스라인은 후속. held-out 일반화는 M2)*
- 구성 task: `battle-system` ✅, `gym-boss-progression` ✅, `creature-evolution` ✅ / (선택 후속: `typechart-fixed`)

### M2 — Procgen + train/test (moat) 🔵 active
- [ ] EC1: 시드 → 절차 생성 region (맵·biome·spawn·gym 시퀀스)
- [ ] EC2: 시드 → 절차 생성 **내부정합 타입표** (infer-the-meta; 고정표 암기 방지)
- [ ] EC3: train/test 시드 분리, 누수 0; held-out 시드가 새 맵+새 타입표 생성
- [ ] EC4: PPO **train-vs-test 갭** 측정·리포트 (Procgen 관례)
- 구성 task(예정): `procgen-region`, `procgen-typechart`, `generalization-harness`

### M3 — 벤치마크 신뢰성 + 런치 ⬜
- [ ] EC1: 베이스라인 4종(random/scripted/PPO/recurrent) 점수표 (train+test 분리)
- [ ] EC2: 리더보드 포맷 + 재현 가능 configs (seeded, pinned)
- [ ] EC3: 측정 viz (학습곡선·일반화 갭·베이스라인 spread·시드 분포)
- [ ] EC4: arXiv writeup 초안
- [ ] EC5: OSS 공개 (MIT) + Prime Intellect Environments Hub 등록
- [ ] EC6: **킬러 데모** — "같은 에이전트 → unseen held-out 시드(새 맵+새 타입표) → 보스 격파" GIF
- 구성 task(예정): `baseline-suite`, `metrics-viz`, `killer-demo`, `arxiv-draft`, `oss-release`

### M4 — Throughput (JAX) ⬜
- [ ] EC1: 핫패스 JAX 포팅 (spec 안정 *후* — DESIGN §4)
- [ ] EC2: numpy ↔ JAX **parity 테스트** (동일 시드 동일 trajectory)
- [ ] EC3: ≥10M steps/s GPU (DESIGN §4 목표)
- 구성 task(예정): `jax-port`, `parity-tests`, `vectorized-bench`

### M5 — 수익화 표면 ⬜
- [ ] EC1: 비공개 held-out eval 세트 (재현 가능, un-gameable)
- [ ] EC2: 커스텀/고난도 env API
- [ ] EC3: Prime Intellect Hub 등록 + 공개 리더보드 운영
- 구성 task(예정): `private-evalset`, `custom-env-api`
