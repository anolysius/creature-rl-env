---
slug: inference-floor-reframe
initiative: eval-product
status: completed
ended: 2026-06-30
extracted_to:
  - docs/paper/critter-gym.md
  - docs/explanation/competitive-analysis.md
changelog_entry: docs/CHANGELOG.md (eval-product 섹션)
---

# inference floor narrative reframe — 결과 보고서

## 요약

매치업 fix(#15) + baseline(#16) 위에서 돌린 **단일-run LLM 실측**(claude-opus-4-8, claude-cli,
보정 분포 n=8, max_steps=40)이 SE-rate **≈50%**(68 battle moves) — chart-blind floor(type_blind
≈27%)보다 위, 추론 proxy(infer ≈90%)·oracle(100%) 아래. 이로써 논문 §5·abstract·competitive-analysis
의 "robust 0% chart-blind floor" 단언을 **정직하게 reframe**: 이전 0% floor 는 상당 부분
**분포-validity 아티팩트**였고, 유효 분포 위에선 frontier LLM 이 **부분적이지만 실재하는 in-context
추론**을 보인다(과대/과소 reframe 없이).

## 계획 대비 실적

- ✅ **AC1** — §5: 도입부 "two→three stacked confounds", render·memory 사례 보존, 세 번째 층(매치업
  분포: oracle SE 100%→5-23% 붕괴, "추론 불가"와 "급소 부재" 혼동) 추가, 보정 분포 단일-run 실측 반영,
  "robustly remained at floor" 정정.
- ✅ **AC2** — §5 Honest scope + Abstract + competitive-analysis 에 단일 run·n=8·1 모델·proxy·
  step-cap 의존·"signal not verdict"·robust multi-run=follow-up 캡션. "correction not negation"(과소
  방지) + "partial, real / above chance, well below expert"(과대 방지).
- ✅ **AC3** — SE 50%/oracle 100%/infer 90%/type_blind 27%/probe 0%/inference_score 0.14 @ n=8
  max_steps=40 전반 일치. Abstract line 29 정정.
- ✅ **AC4** — docs-only(코드 0). §9 모순 0. L3 plan-reviewer+qa-verifier 2/2 APPROVE.

## 변경 파일

- `docs/paper/critter-gym.md` (+44/−22): Abstract line 29 + §5 frontier-LLM probe 단락(도입·세 번째
  confound·보정 분포 실측·Honest scope 3 limitations).
- `docs/explanation/competitive-analysis.md` (+1행 reframe): "monetizable eval" 행에 #15·#16·보정
  분포 단일-run 실측 + correction-not-negation.

## 발견된 이슈

- robustness run(--runs 3)이 세션/환경에서 중단(killed, 출력 0) → 사용자 결정으로 **단일-run 신호**로
  진행(명시 캡션). robust multi-run verdict 는 후속 seed.

## 흡수처 (extracted_to)

- `docs/paper/critter-gym.md`, `docs/explanation/competitive-analysis.md` — 둘 다 evergreen.
  cross-task 의존 없음(archive invariant). 실측 도구·band 는 #16 `docs/reference/inference-baseline.md`.

## 정직 경계

- 단일 run·1 모델·1 band·scripted-proxy·max_steps=40·claude-cli = 신호이지 verdict 아님.
- "LLM 추론 가능" 결론 아님(부분, 50%, expert 아님) / "여전히 0% floor" 도 아님(분포 정정 후 50%).
- 이전 측정(#11/#13/#14)은 *그 분포에선* 정확 — render·memory floor 제거는 유효. 매치업은 *세 번째* 층.
- arXiv 공개 자체는 사람 게이트(본 task 는 초안 정직성만).

## 의존
- #15(PR #84) ← #16(PR #85) ← 본 task(stacked). 파일 disjoint(paper/competitive-analysis vs 코드)=충돌 0.
