# Initiative: hard-benchmark

> **절대 난이도** — "PPO/강한 agent가 oracle에 *못 닿는*" 진짜 hard benchmark. difficulty-scaling이
> *변별 분해능*(oracle−blind spread↑)과 *headroom robustness*(강한 baseline에도 21–41% plateau)를
> 입증했으나, gap register의 **"a hard benchmark" ❌(toy)**는 "강한/SOTA agent에도 hard"가 미해결로 남음.
> 본 이니셔티브 = env를 *구조적으로* 더 어렵게(부분관측·메모리·호라이즌·전략 깊이) 만들어 절대 난이도를 올린다.
>
> **마일스톤 SSOT**: roadmap.md · milestones.md. **활성: M3 신뢰성 자산** (난이도=신뢰성). 공개는 맨 마지막.

## 왜 지금 / 선행 결과

- **headroom-baseline-strength (difficulty-scaling #4)**가 진단(Q1) 완료: "hard-and-learnable" headroom이
  *cheap feedforward 스케일링(width/depth/budget)에 robust* — 약한-net 산물 아님, capacity/compute로 안 닫힘.
  **그러나 robust=cheap-scaling 한정**, recurrent/SOTA 미배제. → 절대 난이도(Q2)는 *spec 레버*가 필요.
- **부분관측 scout (2026-06-25)**: "시야 줄이기"(patch_radius↓ at fixed grid)는 **falsify**(feedforward 안
  나빠짐 + obs_dim 오염). 대신 **지도 크기/호라이즌**(grid16, 작은 고정 시야)이 강한 레버 신호 —
  feedforward PPO가 oracle의 **11–16%**(grid10 ~41% 대비 급락), oracle은 여전히 winnable(2.81).
  **단 entangled**(부분관측+호라이즌) + **feedforward only**(hard-but-learnable 미확인).

## 핵심 질문 (순서)

1. **메모리가 load-bearing인가?** (recurrent-baseline) — grid16의 난이도가 "hard-but-learnable"(메모리 있는
   agent는 더 잘함=진짜 능력)인지 "그냥 sparse-hard"(메모리 무관)인지. **recurrent vs feedforward** 대조.
2. (조건부) 메모리 load-bearing이면 → 호라이즌/부분관측을 깨끗이 분리한 hard config 정식화 + JAX 재포트.
3. (조건부) 강한 recurrent baseline의 oracle headroom 측정 (절대 난이도 = SOTA-class에도 hard 입증).

## 북극성 (CLAUDE.md 종속)

1. 능력 측정 복무. 2. RLVR(부분관측도 boolean subgoal 보존). 3. **procgen+seed split 비협상**(난이도 점도
   split·재현성·결정론 유지 — 부분관측이 결정론/RLVR 깨면 안 됨). 4. fast/vectorizable. 5. seeded·pinned.
   **정직성 > 헤드라인**(hard "입증" 과대 금지 — proxy·budget·seed 라벨).

## Task 목록

| # | slug | 상태 | 한 줄 |
|---|---|---|---|
| 1 | `recurrent-baseline` | ✅ done (→ `_archive/2026-Q2/hard-benchmark/01-recurrent-baseline/`) | **메모리는 load-bearing인가** — JAX에 GRU recurrent A2C 추가(feedforward 무변경), 부분관측 commit world(grid10·**5×5 view**·3 gyms)서 recurrent vs feedforward A2C를 matched greedy eval로 대조. **결과(3 seed)**: feedforward 18%(0.50/2.81) vs **recurrent 46%(1.29/2.81)** of oracle, memory effect **+0.79>max std 0.33 → LOAD-BEARING robust**. recurrent net이 *더 좁은데도*(h128<h256) ~2.5× → 이득=memory(capacity 아님). **Q1 정직 보정**: robust headroom=feedforward 한정, recurrence가 부분관측 headroom 크게 회복(18%→46%) → headroom 상당부분이 no-memory 한계. env가 메모리 agent 변별(벤치마크 virtue). **경계**: recurrent도 46%서 잔존(미해결), **A2C 한정**(recurrent PPO=후속·Q1 PPO 깨끗 연결 미확정), 3 seed·CPU·param-match 아님·oracle proxy. scout가 grid16(더 큰 지도)=A2C 학습불가 inconclusive 확인 → grid10/patch2가 sweet spot. 419→423(+4, 회귀 0). |
| 2 | `recurrent-ppo` | ✅ done (→ `_archive/2026-Q2/hard-benchmark/02-recurrent-ppo/`) | **recurrence가 *PPO* headroom을 닫는가** — #1은 A2C 내 메모리 효과만 보였으므로 Q1(PPO)과 깨끗이 연결. JAX에 **recurrent GRU PPO** 추가(`recurrent_replay`/`make_recurrent_ppo_rollout`/`recurrent_ppo_loss`/`train_recurrent_ppo`; feedforward/A2C/tuned-PPO/recurrent-A2C 전부 byte-identical). **고난도 sequence-preserving minibatch**: PPO의 시간축 셔플이 recurrence를 깨므로 **env축(B)만 셔플·T 보존·`h0`서 GRU 재생**. **correctness 먼저**(망가진 recurrent PPO=misleading): 결정론 게이트 2종 — (a) rollout logits==replay logits(tol 1e-4, ratio가 1서 시작), (b) **env-축 permutation 불변**(시간축 셔플 0 입증). **실측**(CPU·3 seed·250 iter, **Q1 exact default config** grid10·5×5·vary num_types8): feedforward PPO(h256) **24%(0.46±0.08/1.94)** vs **recurrent PPO(GRU h128) 53%(1.02±0.19)**, memory effect **+0.56>max std 0.19 → (a) recurrence-helps-PPO robust**. recurrent net이 *더 좁은데도* 2배+ → 이득=memory. **A2C 결과가 알고리즘 산물 아님 입증**(ff 18→24%, rec 46→53%; PPO가 양쪽 올려도 메모리 gap 유지). recurrent PPO도 **53%<oracle**(0.75·oracle 한참 아래) → **headroom-CLOSES(c) 미발동**(헤드라인 헤드룸 유지, 메모리가 일부만 회복으로 qualify·A2C+PPO robust). **경계**: PPO(SOTA 아님)·CPU·3 seed·single config·param-match 아님(의도적 더 좁음)·oracle proxy·A2C↔PPO는 config 다름(within-config gap만 읽기). 423→427(+4, 회귀 0). |

## 정직성 문화 (계승)

freeze 전 pilot이 전제 검증(falsify시 reframe — scout가 "시야 줄이기"를 이미 falsify). 사전약정 결정규칙으로
p-hacking 차단. recurrent 구현은 **correctness 먼저 입증**(망가진 recurrent=misleading "메모리 무용"). 다층
검증. proxy·budget·seed·CPU 라벨. 헤드라인보다 정직성.
