# Initiative: difficulty-scaling

> (A) "**hard-and-gap≈0**" — env 가 toy 라 gap≈0 의 능력예측력이 약하다(DESIGN §3.1.1). 난이도를 *키우면서*
> seed split 을 유지해 (A) 를 "toy-and-gap≈0" → "hard-and-gap≈0" 으로 끌어올린다. 갭 register
> (competitive-analysis §5) "a hard benchmark" 항목.
>
> **마일스톤 SSOT**: [roadmap.md](../../explanation/roadmap.md) · [milestones.md](../../reference/milestones.md).
> **활성 마일스톤: M3**(벤치마크 신뢰성). (A) 정밀화는 M3 신뢰성 자산. 공개는 맨 마지막(방침).

## 왜 지금

- M4(JAX 속도) 핵심 입증 완료(jax-throughput #40·#41·#42, family A 벡터화 env). 갭 register 의 *다른* 최우선
  축 = 난이도. "competitively fast" 는 크게 메웠고, "a hard benchmark" 가 남은 큰 신뢰성 갭.
- **#24(difficulty-generalization)가 남긴 honest limit**: 난이도 점 3종의 gap 이 전부 큰 per-seed std 안 =
  *약한 증거*(저예산 40k·단일run 이라 작은 real gap 을 0 과 구분 못 함). gap≈0 "입증"이 아니라 신호였음.
- 난이도는 **다차원**(num_types=추론난이도↑·blind grinding↓ / 보스 stat=cliff / scripted oracle 천장 ~0.6
  [3 스타터 vs 12 타입]) — #24 가 "깨끗한 단조 scripted 사다리"를 falsify.

## 두 갈래 (순서 중요)

1. **측정 정밀화 먼저**(difficulty-gap-rigor): #24 의 약한 신호를 multi-run + 예산↑ + 사전약정 결정규칙으로
   rigor 화. **결과가 갈림길**: (a) hard 점서도 gap≈0 robust → env 이미 "hard-enough-and-gap≈0" 신호(재설계
   덜 시급) / (b) real gap 출현(난이도↑서 gap 커짐) → **env 가 hard benchmark**(Procgen 식 train→test 갭) =
   그 자체로 (A) 결과 / (c) held-in 이 floor → 정책 무능(generalist-mediocrity 아날로그) = 예산/정책 필요.
2. **env 재설계(후속, 조건부)**: rigor 가 재설계 필요성을 가린 뒤에만. 스타터 다양화로 oracle 천장 해소 등 —
   단 env 메커닉 변경 = **JAX 포트 재작업(jax-throughput R5)**. spec-stability 게이트 주의.

## 북극성 (CLAUDE.md 종속)
1. 능력 측정 복무 — 난이도도 *측정 정밀도*를 위해. 2. RLVR. 3. procgen + seed split 비협상(난이도 점도 split
유지). 4. fast/vectorizable. 5. seeded·pinned. **정직성 > 헤드라인**(gap≈0 "입증" 과대 금지).

## Task 목록
| # | slug | 상태 | 한 줄 |
|---|---|---|---|
| 1 | `difficulty-gap-rigor` | ✅ done (→ `_archive/2026-Q2/difficulty-scaling/01-difficulty-gap-rigor/`) | #24 약한신호 rigor 화 — `classify_gap`(사전약정 floor=0.3·k=1.0) + `train_and_gap_multirun`(std-**across-runs**) + `--runs N`. **실측**(100k,5run): held-in 비floor(1.10/1.21/1.54) + 세 점 모두 **`gap≈0-signal`**(d2 −0.40±0.90), #24 대비 robust 업그레이드. **real-gap 미출현**. **분기 (a)**: gap-correctness 문제 아님 → "hard-and-gap≈0"의 *hard*(변별 난이도)가 미해결 = 재설계 동기 재정의. std 난이도와 함께 커짐(d2 0.90). env 무변경. 281→283(+2), clean |
| 2 | `difficulty-dynamic-range` | ✅ done (→ `_archive/2026-Q2/difficulty-scaling/02-difficulty-dynamic-range/`) | *hard* 쪽 — **변별 분해능↑(동적 범위)**. `discriminating-difficulty` slug pilot이 "oracle 천장/스타터 다양화"를 **falsify**(winnability 정상·변별 이미 +1.0/gym·다양화는 토너먼트 구조상 무력·재출현↓ 금지) → 확실한 레버=gym 수. `region.generate_region(min_gyms=None)` opt-in(기본 무회귀) + `critter_env min_gyms` + `difficulty_generalization --resolution/--range-gap`. **실측**(scripted, held-out, 사전약정 규칙): oracle−type_blind spread **+1.31(3)→+2.56(5)→+4.88(8)** 단조↑, winnability 0.88 → **`resolution-up`**. 학습 gap@8(PPO 60k,3run): −0.19±0.60=**`gap≈0-signal`**(분해능↑하며 일반화 유지, PPO 1.67≪oracle 7.06=headroom 큼). **범위 밖 정직 명시**: "PPO 못 푸는 hard-benchmark"는 future work. JAX 재포트 후속(R5). 287→294(+7), mypy(26)/ruff/build clean |

| 3 | `ppo-headroom-rigor` | ✅ done (→ `_archive/2026-Q2/difficulty-scaling/03-ppo-headroom-rigor/`) | **tuned PPO oracle-headroom을 multi-run robust로** — `jax-ppo-tuned`의 single-run "PPO가 oracle의 15–32%"를 ≥5-run + 사전약정 std rule로 굳힘(과거 single-run 노이즈 4회 교정 학습). 신규 `src/critter_gym/headroom.py` `classify_headroom`(순수·**numpy-only CI**, frac=0.75·k=1.0 데이터 전 고정: mean+k·std≤frac·oracle→`hard-and-learnable`/mean−k·std≥→`ppo-closes`/else `inconclusive`) + `ppo_baseline.py --runs` robust verdict. **실측**(CPU·5-run): default PPO **0.52±0.06=oracle 1.84의 28%**(낙관상한 0.58≪임계 1.38), hard PPO **1.52±0.28=oracle 7.28의 21%**(낙관상한 1.80≪5.46) → 양 config **`hard-and-learnable` robust**(seed 노이즈 아님 입증). gap≈0(+0.20/+0.12)·R2 PPO≥A2C·hard서 PPO<type_blind 유지. **ppo-closes 미발동**(reframe 불요). 정직: 5-run·작은net·CPU·이 예산·oracle proxy. 365→372(+7 headroom 단위, CI numpy-only), mypy(28)/ruff/build clean. jax-throughput.md(robust 갱신)+DESIGN §3.1.1 갱신 |

| 4 | `headroom-baseline-strength` | ✅ done (→ `_archive/2026-Q2/difficulty-scaling/04-headroom-baseline-strength/`) | **강한 baseline에도 oracle headroom이 살아남나? (절대 난이도 진단 Q1)** — 헤드라인 "hard-and-learnable"(PPO≈oracle 21–28%)가 *tiny MLP·짧은 훈련* 산물인지 진짜 난이도인지 진단. `jax_train`에 **default-preserving depth 노브**(depth=1 byte-identical) 추가 → capacity×budget 스윕(width 64→256·depth 1→2·budget i600→4000≈20M steps·3 seed)의 **best**를 강한 baseline으로 사전약정 3-branch 판정. **결과 = (a) headroom-ROBUST**: best strong PPO가 oracle의 **41%(default)/25%(hard)**에서 **plateau**(opt-bound ≪ 0.75·oracle), tiny 대비 non-vacuous. **핵심 정직 발견**: depth 1→2는 **하락**·budget은 i600서 plateau(i4000도 안 나음) → **병목은 capacity/compute 아님**(transfer-capacity-budget 재현). non-vacuity 가드가 깊은 net의 공허한 robust(d2 0.33<tiny 0.56)를 포착. **경계(과대 금지)**: robust=*cheap feedforward 스케일링 한정*, recurrent/대형/better-algo/HP-튜닝 **미배제**, oracle=scripted proxy, 3 seed·CPU. **함의**: headroom 실재·약한-net 산물 아님 → 현 baseline class엔 trivially toy 아님(헤드라인 강화); "SOTA agent에도 hard"는 미해결 → **Q2(부분관측 등 spec 레버)가 더 강한 agent 대비 절대 난이도엔 여전히 동기**. **⚠ 후속 보정([`hard-benchmark/recurrent-baseline`](../hard-benchmark/INITIATIVE.md)): robust=*feedforward* 한정이 맞았음 — recurrent(GRU) A2C가 부분관측(5×5 view)서 feedforward 18%→recurrent 46% of oracle 회복(메모리 load-bearing robust). 즉 headroom 상당부분이 *no-memory* 한계였고 recurrence가 크게 회복(단 46%서 잔존). "robust headroom"은 feedforward 한정으로 읽어야 함.** 415→419(+4 depth 테스트, 회귀 0), mypy(28)/ruff/build clean. jax-throughput.md(PPO robust 갱신)+competitive-analysis(gap register) 갱신. Acceptance AC1–AC5 |

(이후 task 는 /task-start 로 append — 예정: **Q2 더 깊은 hard-benchmark**[부분관측 등 spec 레버·별도 이니셔티브급·JAX 재포트 동반], family 확장)

## Pilot 발견 박제 (2026-06-24, `discriminating-difficulty` slug — pilot이 메커닉 falsify → 정리됨)

"oracle 천장(스타터 다양화로 해소)"이 변별을 막는다는 진단을 freeze 전 pilot이 **반증**(measure_learnability,
d2_hard, held-out, gym-clear-only):
- **winnability 정상**: oracle 2.06 ≈ 에피소드당 실제 gym 수(vary 평균 ~2.0) → oracle은 *존재하는 gym 거의 다 클리어*.
  "천장 ~0.6"은 max(num_gyms=3) 대비 분수였을 뿐, 실제 gym 평균 2개라 천장 아님.
- **변별 이미 존재**: oracle 2.06 vs type_blind 1.06 = **spread +1.0/gym**. probe 0.88.
- **스타터 다양화는 무력**: 랜덤 토너먼트 차트에선 *고정 챔피언 하나가 상대의 ~절반을 우연히 카운터*(FIRE ~50%).
  보스 풀을 12종으로 넓혀도 blind 0.46/gym 유지, spread 0.35→0.54로 *미미*. RPS 구조가 다양화를 무력화.
- **재출현↓는 금지**: 차트가 seed별 생성이라 in-episode 재출현이 없으면 추론 자체가 불가(매 보스가 미지 타입) →
  infer≈probe로 moat 붕괴. **추론 난이도 레버는 "재출현↓"가 아니다.**

**→ 진짜 변별 레버 (확실)**: **동적 범위** — gym 수를 늘리고/안정화(현 평균 2 → 분해능↑, oracle−blind 절대
spread↑). 추론 구조(재출현 유지)는 보존. "PPO가 oracle에 못 닿게 하는" 더 깊은 hard-benchmark는 한 task 범위 밖.

## 다음 task
**task 1·2 종결** — gap≈0 robust(rigor) + 변별 **분해능↑**(동적 범위, `resolution-up`, gap≈0 유지). *hard* 쪽의
*분해능* 레버는 해소. 남은 후보:
- **`jax-difficulty-report`** (jax-throughput R5): `jax_env` _MAX_GYMS 가변화 재포트 — 동적 범위 검증됐으니 JAX
  벡터화로 고-gym 학습/측정 가속.
- **더 깊은 hard-benchmark** (별도 이니셔티브급, 본 task 범위 밖 명시): "PPO가 oracle에 못 닿는" 변별 —
  다중타입 보스·부분관측·전략 깊이. 큰 연구.
- **또는 피벗**: M4 완전성(jax-battle-full)·family 통합·공개 준비 등.
