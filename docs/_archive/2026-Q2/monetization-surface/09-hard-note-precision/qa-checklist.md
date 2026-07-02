# QA Checklist — hard-note-precision (G1 freeze)

## Acceptance (plan AC 1-4)

- [ ] AC1 — `difficulty_note` 3요소: ff ~11–16% 유지 + "related deeper grid16 config(5gym·420step)에서 recurrent PPO ~32–43% of oracle 측정(천장 미달)" + "이 정확한 티어 config 는 recurrent 미측정·SOTA 미확립(OPEN)·SOTA-hard 주장 금지". knob 무변경.
- [ ] AC2 — 테스트: 기존 토큰("oracle"/"open") 유지 + "recurrent"+"related" 언급 검증 추가. #100 SSOT-일치 테스트 자동 정합.
- [ ] AC3 — `env-tiers.md`·`list_env_tiers.py` 정합 갱신 + site `--no-assets` 재빌드(자산 무변경).
- [ ] AC4 — 회귀 0(baseline 630), ruff clean, mypy Success. CHANGELOG 1줄.

## Default DoD

- [ ] 전체 테스트 green. L3 APPROVED. CHANGELOG append.
