# 인수인계서 — CritterGym 차별화(depth) 이니셔티브

> 다음 세션용. 목표 = **우리를 *남다르게* 만들 기능적 공백 3가지**를 메워 "공개할 *가치*가 있는" 1.0
> 수준으로. (지금도 *작동*은 하지만 — Procgen/Craftax/XLand 대비 must-use가 아님.)
> SSOT: `DESIGN.md`(특히 §3.1.1·§9·§10), `docs/reference/milestones.md`, `docs/explanation/roadmap.md`,
> `CLAUDE.md`(규율·하네스). 이 문서는 *왜·무엇을·어떻게*의 인수인계.

---

## 0. 오프닝 프롬프트 (새 세션에 붙여넣기)

> CritterGym(procgen creature-collection RL 벤치마크) 차별화 작업을 이어서 한다.
> 먼저 `docs/HANDOFF-differentiation.md` 와 `DESIGN.md` §3.1.1/§9/§10, `docs/reference/milestones.md` 를
> 읽어라. 미션 = 우리를 남다르게 만들 3 공백(추론 load-bearing / 장르 일반화 / 난이도 toy)을 메우는 것.
> 권장 시작 = **난이도+추론을 한 묶음으로**(아래 §3-A). 하네스 규율(매 task `/task-start`→L1→G1→TDD→
> L3→task-end, main 직접금지)을 지키고, **"X를 증명가능하게 만든다"류 acceptance 는 G1 freeze 전
> achievability pilot 으로 먼저 검증**하라(지난 task 의 교훈 — §4). 정직성 > 헤드라인.

---

## 1. 현재 상태 (한 줄)

M0·M1·M2 ✅, M3 부분(EC1 점수표·EC2 리더보드·EC3 viz·EC6 킬러데모 ✅ / EC4 arXiv·EC5 OSS 미완).
측정 스택 완성: `generalization`→`scoreboard`→`leaderboard`→`viz`, 렌더 `render`→`demo`. 128 tests,
numpy-only core + `[rl]`/`[viz]`/`[render]` extra. **정직한 한계 = 아래 3 공백.**

## 2. 미션 — 기능적 공백 3 (왜 중요한가)

우리 차별점(차별점≠해자, §9)은 **infer-the-meta + 증명가능한 일반화**인데, 둘 다 *기능적으로 비어 있음*:

| # | 공백 | 현 상태 | 왜 치명적 |
|---|---|---|---|
| 1 | **추론 load-bearing** | 숨은 타입표 *구조상* 존재하나 추론을 *강제 못 함* (typechart-depth 가 반증) | 헤드라인 novelty 가 속 빈 강정 |
| 2 | **장르 일반화 (B)** | instance-level(같은 생성기 시드)만. env-level split 없음 | "어떤 게임이라도" 미완 = 진짜 해자(②층) 미착수 |
| 3 | **난이도** | grid 6-10, 단순 배틀 → toy | gap≈0 이 "일반화 훌륭"이 아니라 "과제 쉬움"일 수 있음 |

**셋은 사실상 한 문제다:** "env 를 *충분히 어렵게* 만들어, 능력(추론·일반화)이 실제로 load-bearing·
측정가능하게." 난이도(3)가 substrate, 추론(1)·장르일반화(2)가 그 위 두 차별 능력.

## 3. 접근 (각 공백)

### A. 추론 load-bearing + 난이도 (1+3, 묶어서 — **권장 시작**)

**⚠ 반드시 §4 의 typechart-depth 실패 교훈을 먼저 읽어라 — 안 그러면 같은 벽을 친다.**

목표: *과거 배틀에서 메타를 추론*하는 정책이 *매번 시도(brute-force)*하는 정책을 **이긴다**를 측정으로 증명.
이미 ship 된 것(typechart-depth): 타입 풀 12, 보스 타입 에피소드 내 재출현(34/40), winnability 보장.
**아직 안 된 것: probing 을 *비싸게* 만들어 추론이 이기게.** 후보 메커니즘(실패한 것 + 미시도):
- (실패) **no-heal keystone** — switch 비용이 매치업 이득을 압도해 type-blind 가 1위가 됨(§4 pilot).
- (미시도, 유력) **틀린 타입 opener 가 same-battle 회복 불가** — 보스가 강해 첫 수 틀리면 그 배틀 패배.
  단 크리처 3마리 = 3 probe 문제 해결 필요(party 축소? 또는 wrong-move 가 즉시 KO).
- (미시도) **team-commit** — 잡은 크리처가 party 합류, 보스 *전에* 추론으로 타입 선택(= 전체 K×K 활용).
  더 크지만 가장 정통(전략+추론). typechart-depth 가 "다음 큰 증분"으로 명시 deferral.
**검증(필수)**: scripted 4-arm(oracle/type_blind/probe/infer) 의 **infer > probe** 게이트(numpy-only).
**freeze 전 pilot 으로 분리 달성 가능 먼저 확인**(§4). 안 되면 정직히 디스코프/방향전환.

### B. 장르 일반화 (2 — 더 큰 베팅, 진짜 해자 ②층)

목표: *구조-상이* 수집형 RPG env **여러 개** + **environment-level held-out split**(train env 패밀리
{A,B,C} → test unseen 패밀리 D). 이게 "수집형 RPG 장르 일반화" 주장의 진짜 바 = **M5 커스텀 환경과 동일**.
- 두 번째 *구조 다른* env(다른 배틀 시스템/수집/진행 메커닉, 단 공유 obs/action 인터페이스 또는 어댑터).
- 공통 평가 API(이미 `generalization`/`leaderboard` 가 정책-비의존이라 재사용 가능).
- 측정: train env(들)로 학습 → held-out env 에서 일반화 갭. gap≈0 이면 "장르 일반화" 정직히 주장.
- **규모 큼** — 이니셔티브급. (A) 보다 임팩트 크지만 비용도 큼.

### C. 난이도 단독 (3) — A 에 흡수 권장 (별도로 잘 안 함)

## 4. ⚠ 지난 세션 핵심 교훈 (typechart-depth, archive 15) — *재현 금지*

- **K↑ 단독은 brute-forceable**: 플레이어 3타입 고정 + 보스 K타입 → "3개 다 때려보고 best" 로 추론 없이 풀림.
- **에피소드 내 타입 재출현 없으면 cross-gym 추론 무의미**(원래 0/40 → 풀 추출로 34/40 고침).
- **no-heal keystone 역효과**: pilot `type_blind 0.76 > probe 0.74 > oracle 0.72 > infer 0.64` —
  switch 가 턴을 소모(보스 공짜 공격)해, 보스가 약하면 안 바꾸고 패는 게 이김 → **타입지식이 손해**.
- **결론**: 추론 load-bearing = battle-economy 재설계 연구 문제. 매 층(K→재출현→경제) 풀면 다음이 나옴.
- **프로세스 교훈(retro `pilot-before-freeze`, deferred)**: "X 를 *증명가능하게* 만든다"류 acceptance 는
  **G1 freeze 전 pilot 으로 achievability 먼저 검증**. typechart-depth 는 2 round L1 + 구현 후 pilot 에서야
  구조적 불가 발견 → 디스코프. (이 retro 제안 `seed` 하면 L1/task-start 가이드에 박을 수 있음.)
- **정직성 작동 사례**: 안 되는 걸 *증명하고* DESIGN §3.1.1 에 future work 로 정직히 기록 + 코드 honesty
  가드 테스트. 헤드라인보다 정직성 우선 — 이 문화 유지.

## 5. 권장 순서

1. **(A) 추론 load-bearing + 난이도** — 우리 *기존* 차별점을 *작동*시킴. §4 교훈 위에서. 묶음 1 증분.
   - 단, **freeze 전 pilot 필수**. 분리 못 만들면 (B) 로 피벗하거나 정직히 보류.
2. **(B) 장르 일반화** — 진짜 해자 ②층. 이니셔티브급. (A) 가 막히면 오히려 (B) 가 더 정직한 차별화일 수도.
3. 그 후 **1.0 OSS 런치**(EC5)+**writeup**(EC4) — 차별 기능 하나가 *작동*한 뒤.

> 개인 의견(지난 세션): (A) 가 막히는 게 구조적이라면(§4), **(B) 가 더 확실한 차별화**일 수 있다. (A) 에
> 무한 튜닝 쏟기 전에, (B) 두 번째 env 설계로 "장르 일반화" 를 *진짜로* 보여주는 게 moat 에 더 부합.

## 6. 코드 포인터

- env 코어/배틀 경제: `src/critter_gym/envs/critter_env.py`(reset/battle entry/heal), `battle.py`,
  `party.py`(스타터·보스 stat), `creatures.py`.
- 타입/차트: `src/critter_gym/types.py`(ElementType 15, generate_typechart 임의 K),
  `region.py`(num_types·active subset·winnability·보스 풀 재출현).
- 측정(정책-비의존, 재사용): `generalization.py`/`scoreboard.py`/`leaderboard.py`/`viz.py`.
- 데모/렌더: `render.py`(rgb_array+save_gif), `demo.py`(record_episode).
- scripted 정책 참고: `tests/test_gym_battle.py` `_scripted_action`(type-aware), 지난 pilot 4-arm 로직은
  archive 보고서(`docs/_archive/2026-Q2/env-core/15-typechart-depth/report.md`)에 수치만 남음(스크립트는 /tmp, 삭제됨).
- known follow-up: `render.py:save_gif` 가 imageio 설치 dev 에서 mypy overload(core CI 무관) — 별도 수정.

## 7. 하네스 메모

- 매 task `/task-start "<slug>" --initiative=env-core` → L1(plan-reviewer ×2, **opus**, sonnet 529 회피)
  → G1 → TDD → G2 → L3 → task-end. main 직접 commit 금지(feature 브랜치→PR). co-author 트레일러.
- 개발은 `.venv`(ruff/mypy/pytest/build). 무거운 학습 deps 는 extra.
- retro 큐 `.claude/retro/proposals.md` 에 `pilot-before-freeze`(deferred) 대기.
