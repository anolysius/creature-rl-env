# QA Checklist — inference-robust-correction (G1 freeze)

## Acceptance Criteria

- [x] **AC1 [정직-하향]** ✅ Abstract("partial inference signal" → "robust multi-run 은 inconclusive, near chart-blind floor; 단일 run 은 재현 안 됨") + §5 bullet("looked like partial ... but a robust three-run probe did not confirm it: 0.10±0.08 → inconclusive, LLM ≈14%") + Honest scope("current read is inconclusive ... single-run ≈50% did not survive"). "partial, real inference" 단언 제거.
- [x] **AC2 [설계 건강 명시]** ✅ 신규 §5 bullet "The design is validated even though the prediction failed" — infer arm robustly ≈89% → eval registers inference → LLM near-floor = real signal, not harness artifact + residual engagement/survival confound. competitive-analysis 동일. Abstract 도 "eval nonetheless validated: scripted inferrer robustly clears the band".
- [x] **AC3 [수치·caveat 정합]** ✅ 0.10±0.08 inconclusive·gym 0.04±0.08·infer 89%·LLM 14%·단일 50% 실측 일치; "single n=8 vs robust n=4 → floors 27% vs 6%·apples-to-apples n=8 multi-run follow-up" 명시.
- [x] **AC4 [무회귀]** ✅ docs-only(git diff src/tests/scripts 비어 있음). 잔여 stale overclaim 0(모든 "partial" 은 downgrade 문맥). L3 다음.

## Default pass-criteria

- [ ] CHANGELOG.md 1줄 entry (rules/80 §F.5).
- [ ] L3 (task-review) APPROVED (task-end 선결).
