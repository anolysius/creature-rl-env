# CritterGym Product Roadmap (explanation — *왜*)

> 마일스톤의 사실·exit criteria 표 = [milestones.md](../reference/milestones.md). 본 문서는 *순서와 근거*.
> 상위 SSOT = [`DESIGN.md`](../../DESIGN.md) §6. 본 문서는 그 4-Phase 를 검증 가능한 마일스톤으로 구체화.

## 두 "플랜"의 구분 (혼동 방지)

| 문서 | 무엇 | 답하는 질문 |
|---|---|---|
| `docs/harness/explanation/master-plan.md` | **하네스** 도입 계획 | "AI 가 이 코드베이스를 *어떻게 작업*하나" (lifecycle/hooks/skills) |
| **본 roadmap.md + milestones.md** | **제품** 마일스톤 | "제품이 *무엇을 향해* 가나" (env 기능·벤치마크·런치) |

master-plan 의 "Phase 1/2/3" 은 *하네스* 단계(이미 완료)다. 제품 단계와 무관.

## 왜 마일스톤이 필요했나

DESIGN §6 로드맵은 고수준("Phase 1 = full subgoal chain + procgen")이라, 매 작업이 *대화에서 즉흥*으로
정해져 task 에 휘둘리는 문제가 있었다. 해법은 **검증 가능한 exit criteria 를 가진 마일스톤** — task 가
거기서 *내려오는* backbone. 우리의 RLVR 문화(boolean 완료 기준)를 로드맵에도 적용한 것.

## 규율 (이 문서의 핵심 산출)

> **매 `/task-start` 는 "어느 마일스톤(M)의 어느 exit criterion(EC)을 전진시키는가"를 명시한다.
> task 는 활성 마일스톤의 미충족 EC 에서만 내려온다. 활성 M 의 EC 가 모두 충족되면 다음 M 게이트.**

- "다음에 뭐?" → 활성 M 의 미충족 EC 를 본다 (발명 X).
- 각 task report 가 "M{n}-EC{k} 충족" 으로 체크인 → 진행도 가시화.
- 성능·viz·OSS 의 *타이밍*이 박혀 있어 "지금 X 해야 하나?" 즉흥 논쟁이 사라진다 (답은 해당 M).

이 규율은 [CLAUDE.md](../../CLAUDE.md) "Task lifecycle" 섹션에도 포인터로 박혀 auto-load 컨텍스트에서 강제된다.

## 순서 근거 (왜 이 순서인가)

### M1 (고정월드) 을 M2 (procgen) 보다 먼저
절차생성을 켜기 전에 **게임 메커니즘(배틀·진화·보스 체인)을 단일 결정론 월드에서 먼저** 만든다.
디버깅·결정론 검증이 쉽고, procgen 은 "이미 동작하는 메커니즘"에 난수 월드를 끼우는 일이라 위험이
작다. 역순(procgen 먼저)이면 메커니즘 버그와 생성 버그가 뒤엉켜 진단 불가.

### 성능(JAX)은 M4 로 지연 — 조기 최적화 회피
DESIGN §4 가 "speed = 채택 게이트"라 했으나 단서가 붙는다: ***spec 안정 후* 핫패스 포팅**. 이유:
- 이미 numpy 로 **~266k steps/s/core** (목표 50k 의 5배) — 개발·중간 학습엔 충분.
- JAX 의 250배 가속은 *수십억 스텝* 규모에서 의미. env 가 자주 바뀌는 M1–M2 에 포팅하면 매번 재작성.
- 따라서 env 기능이 안정된 뒤(M4) 포팅하고, parity 테스트로 numpy 동치 보장.

### OSS·writeup·마케팅을 M3 런치로 묶음
첫인상은 한 번뿐이다. "점 줍기 env"를 일찍 공개하면 약하다. **콘텐츠(M1)+moat(M2)+결과가 있은 뒤**
writeup·OSS·viz·킬러 데모를 *한 묶음*으로 런치한다 (DESIGN §6 Phase 2).

## 킬러 데모 정의 (마케팅 수단)

포켓몬 레드 AI 영상처럼 가시적 데모가 채택의 force multiplier 다 — 단, **포켓몬 레드를 따라 하지 않고
그게 *구조적으로 못 하는* 것을 보여준다**:

> **같은 에이전트를, 한 번도 본 적 없는 held-out 시드(새 맵 + 새 타입 상성표)에 떨어뜨렸더니
> 그래도 보스를 깬다.**

포켓몬 레드는 ROM 이 하나라 "암기 아니냐"를 못 떨친다. 우리의 generalization 장면은 연구자에게 신뢰가
가면서 동시에 트윗감이다 — 우리 moat 그 자체. M2 의 held-out 측정이 이 데모의 토대(M3-EC6).

## 현재 위치

M0 완료(`scaffolding`, `env-validation`). **활성 = M1.** 다음 task 는 M1 의 미충족 EC 에서 — 권장
시작점은 `battle-system`(M1-EC1, 턴제 배틀이 진화·보스의 선행).
