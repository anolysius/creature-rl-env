---
slug: arxiv-writeup
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - docs/paper/**
extracted_to: []
supersedes: []
---

# arXiv writeup 초안 (M3-EC4) — 결과를 정직하게 글로

> 작성일: 2026-06-23 | 상태: 계획

## 목표

활성 마일스톤 **M3의 미충족 EC4**(arXiv writeup) 전진: 지금까지의 측정 인프라 + 결과를 **arXiv 논문 초안**으로
패키징. (A) 인스턴스 일반화(procgen seed split) + infer-the-meta load-bearing + learnability + (B) 장르 일반화
토대(4 family) — 모두 *측정+정직 보고* 자산을 글로. **docs-only**(제품 코드 무변경).

**핵심 원칙(정직성 = 자산)**: 모든 수치는 **코드/측정에 근거**(날조 금지). 결과를 *signal*로, 한계를 *한계*로
서술. Pokémon 경쟁 주장 금지(plain-language 메타포). Procgen/Craftax/XLand-MiniGrid 대비 정직 포지셔닝.
(B)는 토대지 증명 아님 명시. 헤드라인보다 정직성.

**EC 매핑**: M3-EC4. (docs-only → `/task-verify` skip, `/task-review` 필수: 수치 정확성·정직성 diff 검토.)

## 선행 조건

- 인용할 측정/모듈 (전부 main 머지됨): `generalization`(A), `test_reasoning_gate`(#16), `learnability`(#17/#19),
  `genre_generalization`+family A–D(#18·battle-system-family·family-d-muster), `scoreboard`/`leaderboard`/`viz`/`demo`.
- DESIGN.md §3.1.1(정직 scope SSOT), milestones.md, CHANGELOG(수치 출처).
- 킬러 데모 수치(M3-EC6): held-in 40% vs held-out 45% 보스격파, gap≈0. throughput ~266k steps/s/core.

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `docs/paper/critter-gym.md` (신규) | arXiv 논문 초안(markdown): abstract / intro+positioning / env design(obs/action/RLVR/procgen) / 측정 결과(A 인스턴스·load-bearing·learnability·B 장르 토대) / related work / honest limitations / conclusion | 신규, docs-only |
| `docs/paper/README.md` (신규) | 초안 상태·재현 포인터(어느 모듈/테스트가 각 수치 산출) | 신규 |

## Step별 계획

1. **수치 수집** — 코드/리포트에서 인용 수치 확정(아래 "인용 수치 표"). 날조 0.
2. **초안 작성** — 섹션별 markdown. 각 결과에 *측정 출처*(모듈/테스트) 각주.
3. **정직성 패스** — Pokémon 비경쟁 / (B) 토대지 증명 아님 / 모든 caveat(단일run·N·confound·천장) 명시.
4. **재현 포인터** — `docs/paper/README.md`에 수치↔모듈/테스트 매핑.
5. **L3 리뷰** — 수치 정확성(코드 대조) + 정직성(과대표현 0) + 포지셔닝.

## 인용 수치 표 (코드 근거 — 날조 금지)

| 주장 | 수치 | 출처 |
|---|---|---|
| (A) 인스턴스 일반화 gap≈0 | held-in 40% vs held-out 45% 보스격파(killer demo) | CHANGELOG M3-EC6, `scripts/killer_demo.py` |
| throughput | ~266k steps/s/core (목표 50k의 5배) | env-validation 리포트 |
| infer load-bearing(#16) | Gate0 oracle 1.00≫type_blind 0.52; Gate1 infer 0.84>probe 0.47 (42 seeds) | `tests/test_reasoning_gate.py` |
| learnability(#17/#19) | gym-clear-only oracle/infer 4.19≫type_blind 1.81>probe 1.06; PPO≈infer | `critter_gym.learnability`, #19 |
| (B) family C skill-structural | A-tuned gap +3.9 vs C-appr +0.2 (held-out duel) | `genre_generalization`, #18 battle-system-family |
| (B) family D skill-structural | muster 1.42≫rush 0.00 on D; muster≤rush on A | family-d-muster |
| (B) family B forgiving | A-tuned gap≈0 (collection 축 관대) | #18 |

## 검증 방법

- 모든 인용 수치가 위 출처와 일치(L3 reviewer가 코드 대조).
- broken-link 0(evergreen 참조 규율).
- 과대표현 0: Pokémon 비경쟁·(B) 토대·caveat 명시(L3 정직성 축).
- docs-only → 코드 테스트 무영향(181 passed 불변).

## 리스크

1. **수치 날조/드리프트** → 인용 수치 표 + 재현 포인터로 출처 고정, L3가 코드 대조.
2. **과대표현**(arXiv 유혹) → 정직성 패스 + L3 정직성 축 + DESIGN §3.1.1 scope 준수.
3. **scope creep**(논문이 끝없이 커짐) → 초안(draft) 범위로 한정, 제출용 LaTeX·실험 추가는 후속.

## Acceptance Criteria (G1 통과 시 freeze)

> *정직한 초안 산출 + 수치 출처 근거*로 freeze. 제출/peer-review 아님.

- **AC1** — `docs/paper/critter-gym.md` 초안: abstract / intro+positioning / env design / 측정 결과(A·load-bearing·learnability·B) / related work / limitations / conclusion 섹션 완비.
- **AC2** — 모든 정량 주장이 "인용 수치 표"의 코드/측정 출처와 **일치**(날조 0). 각 결과에 측정 출처 명시. **CI-재현 가능(test-frozen gate/assert)** vs **run-derived 평균**(예: load-bearing 1.00/0.52/0.84/0.47은 run 값; 테스트는 Gate0≥0.20·Gate1≥0.10만 동결) 구분 라벨. throughput은 출처(env-validation 리포트 경로/벤치 스크립트) 고정(L1 accuracy/honesty reviewer 반영).
- **AC3** — **정직 포지셔닝**: Pokémon = plain-language 메타포(비경쟁), Procgen/Craftax/XLand 대비 정직 벤치마킹(related work).
- **AC4** — **honest limitations 섹션**: (B) 4 family도 토대지 장르 일반화 증명 아님 / 단일run·N modest / family D 난이도 confound·within-family 대조 / learnability 천장·oracle==infer / 절대성능 향상 여지 — 모두 명시.
- **AC5** — `docs/paper/README.md` 재현 포인터(수치↔모듈/테스트 매핑) + broken-link 0.
- **AC6** — docs-only 무회귀: 제품 코드·테스트 무변경(181 passed 불변). M3-EC4 전진(초안 산출; 제출은 후속). **lifecycle: docs-only → `/task-verify` skip 가능하나 `/task-review`(L3) 필수**(diff 검토 — 수치 정확성·정직성).
