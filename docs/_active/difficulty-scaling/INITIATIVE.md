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

(이후 task 는 /task-start 로 append — 조건부 예정: env 재설계[변별 난이도/oracle 천장 해소], family 확장)

## 다음 task
**task 1 종결 — gap≈0 이 multi-run rigor 에서 robust**(real-gap 미출현, held-in 비floor). 질문이 *gap* 에서
*hard* 로 이동: 현 난이도 knob(타입수·보스 stat)은 gap 도 안 만들고 능력 변별력도 약함(held-out~1.9/3).
- **다음(조건부)**: **env 재설계** — 변별력 있는 구조적 난이도(학습 정책이 쉽게 못 푸는: oracle 천장 해소 +
  깊은 추론 부하). 단 env 메커닉 변경 = **JAX 포트 재작업(jax-throughput R5)** → spec-stability 게이트 주의,
  착수 전 사람 결정.
- **또는 피벗**: (A) gap≈0 은 robust 입증됐으니, 변별-난이도 재설계는 큰 작업·JAX 재포트 동반이라 후순위로 두고
  다른 공개 전 leverage(예: RL 학습 데모, family 통합, 또는 M3 공개 준비)로 갈지 사람 결정 시점.
