# QA Checklist — inference-floor-reframe (G1 freeze)

## Acceptance Criteria

- [x] **AC1 [정직-정정]** ✅ §5: (a) render·memory 두 floor 사례연구 보존(도입부 "three stacked confounds"로 갱신) (b) 세 번째 validity 층=매치업-broken 분포(oracle SE 100%→5-23% 붕괴; 0%가 "추론 불가"와 "급소 부재"를 뒤섞음) 추가 (c) 보정 분포 단일-run 실측(SE 50% vs type_blind 27%/infer 90%/oracle 100%) 반영 (d) "robustly remained at chart-blind floor" → "substantially a distribution-validity artifact / partial inference"로 정정.
- [x] **AC2 [정직 캡션]** ✅ §5 Honest scope + Abstract + competitive-analysis 에 "single run·n=8·1 model·1 band·proxy·step-cap dependent·signal not verdict·robust multi-run verdict는 follow-up" 명시. "correction not negation" 명시(과소 reframe 방지). "partial, real / above chance, well below expert"(과대 방지).
- [x] **AC3 [수치 정합]** ✅ paper+competitive-analysis 전반 SE 50%/oracle 100%/infer 90%/type_blind 27%/probe 0%/inference_score 0.14 @ n=8 max_steps=40 일치(#16 band). Abstract line 29 정정.
- [x] **AC4 [무회귀]** ✅ docs-only(코드 0 — git diff src/tests/scripts 비어 있음). §9 모순 0. L3 다음 단계.

## Default pass-criteria

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5).
- [ ] L3 (task-review) APPROVED (task-end 선결).
