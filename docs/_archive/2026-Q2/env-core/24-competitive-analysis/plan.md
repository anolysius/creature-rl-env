---
slug: competitive-analysis
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - docs/explanation/competitive-analysis.md
extracted_to: []
supersedes: []
---

# 경쟁(OSS 벤치마크) 비교 분석 — 갭 탐지기 (공개 전 선결)

> 작성일: 2026-06-23 | 상태: 계획

## 목표

공개 전, **다른 오픈소스 RL 벤치마크 대비 CritterGym이 무엇이 낫고/못한지** 정직하게 분석하는 living 문서.
**이중 목적**: (1) 공개·논문의 비교 분석 섹션 토대, (2) **갭 탐지기** — *우리가 주장 못 하는 지점*을
명시적으로 드러내 다음 기능 작업 우선순위(난이도/속도/family)를 도출. (사용자 방침: 공개는 맨 마지막,
기능 준비 + 비교 분석이 먼저.)

비교 대상(OSS): **Procgen**, **Craftax**(/Crafter), **XLand-MiniGrid**, **NetHack(NLE)/MiniHack** —
DESIGN의 정직 포지셔닝(Procgen/Craftax/XLand가 동류, Pokémon은 메타포)을 따른다.

**핵심 원칙(정직성 = 자산)**: 마케팅 금지. **peer가 우리보다 나은 축을 먼저, 분명히** 적는다(Craftax 속도,
Procgen 성숙도·채택, NetHack 난이도). 우리 수치는 코드/논문 근거. **peer 사실은 학습지식 기반이라 불확실분은
"공개 전 1차 출처 검증 필요(verify)" 라벨** — 날조·과신 금지. 결론은 *주장*이 아니라 *갭 register*.

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `docs/explanation/competitive-analysis.md` (신규) | (1) 비교 축 정의 (2) 기능/능력 매트릭스(CritterGym × peers) (3) 축별 정직 트레이드오프 산문(우리 우위/열위) (4) **갭 register**(주장 못 하는 것 → 필요한 기능) (5) peer 사실 verify-list | 신규, docs-only |

## 비교 축 (잠정 — 산문은 정직 트레이드오프)

| 축 | CritterGym(근거) | peer 강자 |
|---|---|---|
| 일반화 측정(procgen + train/test split) | ✅ + **rule-value 랜덤화**(seed별 숨은 타입표) | Procgen(layout), XLand(ruleset) — 더 성숙 |
| "썩지 않는 eval"(regenerable held-out) | ◐ property 있음(DESIGN §9 층1) | 대부분 정적/포화 — *우리 distinctive* |
| 장기 horizon | ✅ subgoal chain | Procgen/Crafter 짧음 / NetHack 김 |
| 전략·추론(infer-the-meta load-bearing) | ✅ scripted gate 실증 | peer 대개 없음 — *distinctive* |
| RLVR(boolean subgoal) | ✅ | 대개 shaped/achievement |
| 장르(env-level) 일반화 | ◐ **토대(4 family)** — 증명 아님 | XLand meta-RL(task dist) 더 큼 |
| 속도/throughput | numpy ~266k/s/core | **Craftax/XLand JAX GPU 압도적** — *우리 열위* |
| 성숙도/채택 | ❌ 0(미공개) | Procgen/NetHack 광범위 채택 — *우리 열위* |
| 난이도 | toy(gap≈0 쉬움) | **NetHack/Crafter 훨씬 어려움** — *우리 열위* |

## Step별 계획

1. **축·매트릭스 작성** — 위 축으로 매트릭스 + 각 셀 한 줄. 우리 셀은 코드/논문 근거, peer 셀은 정성+verify 라벨.
2. **트레이드오프 산문** — 축별로 *우위/열위 모두* 정직 서술. "우리가 다 낫다" 금지.
3. **갭 register** — "주장 못 하는 것" 목록 → 각 갭에 *필요 기능*(난이도 스케일·JAX·family 확장·multi-run) 매핑. = 다음 기능 우선순위 입력.
4. **peer verify-list** — 불확실한 peer 사실(속도 수치·라이선스·날짜 등)을 1차 출처 검증 대상으로 명시.
5. **L3 리뷰** — 정직성(열위 명시)·우리 수치 정확성·peer 과신 0.

## 검증 방법

- 우리 정량은 논문(`docs/paper/`)·DESIGN과 일치(날조 0).
- peer 주장은 정성 또는 verify 라벨(과신·날조 0). "우리가 더 낫다"가 *전 축*인 곳 없음(열위 축 분명).
- 갭 register가 기능 갭→필요 기능 매핑 제공(갭 탐지기 목적 충족).
- broken-link 0. 제품 코드·테스트 무변경(181 passed 불변).

## 리스크

1. **마케팅·과대(비교 유혹)** → peer 우위 먼저 명시 + L3 정직성 축 + DESIGN §9 자기평가 준수.
2. **peer 사실 오류**(학습지식 한계) → 불확실분 verify 라벨, 정성 위주, 정밀 수치 회피.
3. **갭 register가 형식적** → 각 갭에 *구체 필요 기능* 매핑(난이도/JAX/family/multi-run) 강제.

## Acceptance Criteria (G1 통과 시 freeze)

> *정직한 비교 + 갭 register*로 freeze. 마케팅·우위 주장 아님.

- **AC1** — `docs/explanation/competitive-analysis.md` 신규: 비교 축 정의 + **기능/능력 매트릭스**(CritterGym × Procgen/Craftax/XLand/NetHack) + 축별 트레이드오프 산문 + 갭 register + peer verify-list 섹션 완비.
- **AC2** — **정직 열위 명시**: peer가 우월한 축(Craftax/XLand 속도, Procgen/NetHack 성숙·채택, NetHack/Crafter 난이도)을 분명히 기술. "전 축 우위" 서술 0.
- **AC3** — 우리 정량/능력 주장이 논문·DESIGN과 **일치**(날조 0): (A) 측정/(B) 토대지 증명 아님/속도 numpy/난이도 toy 등 현 상태 정직 반영.
- **AC4** — peer 사실은 **정성 또는 verify 라벨**(불확실 수치 과신 금지). "공개 전 1차 출처 검증" 대상 명시. **속도 축은 basis 명시 필수**(우리=numpy CPU/core 측정 vs peer=JAX GPU 공개치는 단위·하드웨어 상이 → 동일 행 직접 수치 비교 금지, basis 라벨 또는 정성 서술; L1 accuracy reviewer 반영).
- **AC5** — **갭 register**: 우리가 *주장 못 하는 것* 목록 + 각 갭→필요 기능(난이도 스케일·JAX·family 확장·multi-run·채택) + **해당 갭이 푸는 마일스톤 EC**(예: 난이도→"hard-and-gap≈0", JAX→throughput, family→M5 genre) 매핑(L1 honesty reviewer 반영). 다음 기능 우선순위 입력.
- **AC6** — 무회귀: 제품 코드·테스트 무변경(181 passed 불변), broken-link 0. docs-only → `/task-verify` skip 가능, `/task-review`(L3) 필수.
