---
slug: inference-floor-reframe
initiative: eval-product
status: active
started: 2026-06-30
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
review_profile: docs-only
scope_paths:
  - docs/paper/critter-gym.md
  - docs/explanation/competitive-analysis.md
extracted_to: []
supersedes: []
depends_on: [matchup-validity (#15, PR #84), inference-baseline (#16, PR #85)]
---

# inference floor narrative reframe — 보정 분포 위 부분-추론 실측 정직 반영 (docs-only)

> 작성일: 2026-06-30 | 상태: 계획 | 마일스톤: M3-EC4(arXiv 초안 정직성)

## 목표

현재 논문 §5 와 competitive-analysis 는 "render·memory 두 confound 제거 후에도 frontier LLM
(claude-opus-4-8)이 **SE-rate 0% / inference_score 0.00 으로 robust 하게 chart-blind floor 에 머문다
= 깨끗한 능력 신호(하네스 artifact 아님)**"라고 단언한다. 그러나 **세 번째 validity 아티팩트**가
있었다: 매치업-broken 분포(매치업 fix #15 이전)는 world 마다 super-effective 무브 존재를 보장하지
못해(oracle SE-rate 자체가 world 수에 따라 5–23% 로 붕괴), "추론 못 함"과 "쓸 급소 무브가 없음"을
**뒤섞었다**. 매치업을 보장한 보정 분포 위 **단일 run 실측**: claude-opus-4-8 SE-rate **50%**
(68 battle moves, n=8, max_steps=40) — chart-blind floor(type_blind **27%**)보다 **명확히 위**,
추론 proxy(infer **90%**)·전문가(oracle **100%**) 아래. inference_score 0.14, gym-clears 1.38(oracle
의 65%).

→ 정직 reframe: 이전 "robust 0% floor" 는 **상당 부분 분포-validity 아티팩트**였고, 매치업을 보장한
유효 분포 위에선 frontier LLM 이 **부분적이지만 실재하는 in-context 추론**(blind 위·expert 아래)을
보인다. 단, **단일 run·N=8·1 모델·1 config·scripted-proxy band·claude-cli·max_steps=40 = 신호이지
verdict 아님**. robustness(--runs/반복)는 후속 seed.

이는 **공개 narrative(arXiv 초안 §5) 정직 정정** — 과대 reframe("LLM 추론 가능!") 금지, 과소
reframe(0% floor 유지) 금지. *정직성 > 헤드라인.*

## 선행 조건

- #15 `matchup-validity`(PR #84): 보정 분포(모든 boss 에 SE 무브 보장).
- #16 `inference-baseline`(PR #85): 보정 분포 위 4-arm scripted band + 러너 full band + max_steps 경고.
- 실측(이 세션, claude-cli 단일 run): SE 50% vs band(oracle 100%/infer 90%/type_blind 27%/probe 0%).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `docs/paper/critter-gym.md` | §5 frontier-LLM probe 단락 reframe(세 번째 validity 아티팩트=매치업 분포 추가 + 보정 분포 부분-추론 실측) + Abstract line 29("robust chart-blind floor") 정정 + §9 limitations 정합 | **중** (공개 narrative) |
| `docs/explanation/competitive-analysis.md` | "monetizable eval" 행에 매치업 validity(#15)+baseline(#16)+보정 분포 부분-추론 실측 정직 반영 | 중 |

### 영향 범위

- 코드 변경 0(docs-only). 측정 도구·env 무변경.
- 논문 §5/abstract/§9 의 내부 정합(SE-rate 0%→부분, "robust floor" 서술) 유지.
- competitive-analysis 의 누적 narrative(#5~#16) 연속성 유지.

## Step별 계획 (docs-only, TDD 없음)

1. §5 frontier-LLM probe 단락: "두 stacked floor(render·memory)" 사례연구 **보존**(여전히 유효) +
   **세 번째 validity 이슈(매치업-broken 분포)** 추가: 이전 0% 가 "추론 불가"와 "급소 무브 부재"를
   뒤섞었음을 명시. 보정 분포 단일-run 실측(SE 50% vs blind 27%/oracle 100%/infer 90%) 반영.
   "robustly remained at chart-blind floor" → "보정 분포 위 부분 추론(단일 run 신호)"로 정정.
2. Abstract line 29("a robust chart-blind floor") → 정직 정정(보정 분포 위 부분-추론 신호 / 단일 run).
3. §9 limitations: max_steps 의존 band·단일 run·robustness 후속 명시(필요 시).
4. competitive-analysis "monetizable eval" 행: #15·#16·보정 분포 실측 한 단락 추가(정직 캡션).

## 검증 방법

- 수치 정합: §5/competitive-analysis 의 모든 수치가 실측 출력(SE 50%/band) + #16 band 와 일치.
- 정직 캡션 존재: "단일 run·1 모델·proxy band·max_steps=40·신호이지 verdict 아님·robustness 후속" 명시.
- 과대/과소 reframe 부재(plan-reviewer + qa-verifier 판정).
- broken-link 0(evergreen 참조 invariant).

## 리스크

| 리스크 | 완화 |
|---|---|
| 과대 reframe("frontier LLM 추론 가능") | 단일 run·부분(50%, expert 아님)·"신호이지 verdict 아님" 명시. plan/L3 가 과대주장 0 검증. |
| 옛 0% 측정 폄하(이전 task 부정) | 이전 측정은 *그 분포에선* 정확했음 명시 — render·memory floor 제거는 여전히 유효 사례연구. 매치업은 *세 번째* 층(distribution validity)으로 추가, 이전 결론 *정정*이지 *부정* 아님. |
| 3단 PR 스택(#84→#85→이번) | 파일 disjoint(paper/competitive-analysis vs 코드)=충돌 0. 머지 순서대로. |
| 공개물 변경 | arXiv 공개 자체는 사람 게이트 — 본 task 는 초안 정직성만(공개 X). |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[정직-정정]** §5 frontier-LLM probe 단락이 (a) render·memory 두 floor 사례연구 보존 (b) **세 번째
   validity 이슈=매치업-broken 분포**(0% 가 "추론 불가"와 "급소 부재"를 뒤섞음) 추가 (c) 보정 분포
   단일-run 실측(SE 50% vs type_blind 27%/infer 90%/oracle 100%) 반영 (d) "robust 0% floor" 단언 정정.
2. **[정직 캡션]** §5 + Abstract + competitive-analysis 에 "단일 run·N=8·1 모델·1 config·scripted-proxy
   band·max_steps=40·신호이지 verdict 아님·robustness 후속 seed" 명시. 과대("추론 가능 결론")·과소
   ("여전히 0% floor") reframe 부재.
3. **[수치 정합]** 인용 수치가 실측 출력 + #16 band 와 일치(SE 50%/oracle 100%/infer 90%/type_blind
   27%/probe 0% @ n=8, max_steps=40). Abstract line 29 정정.
4. **[무회귀]** docs-only(코드 0). broken-link 0. L3(docs-only profile) APPROVED.
