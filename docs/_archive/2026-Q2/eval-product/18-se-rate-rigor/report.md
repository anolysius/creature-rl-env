---
slug: se-rate-rigor
initiative: eval-product
status: completed
ended: 2026-06-30
extracted_to: []
changelog_entry: docs/CHANGELOG.md (eval-product 섹션)
---

# SE-rate robustness — 결과 보고서

## 요약

#17 헤드라인(LLM SE-rate ≈50%, 단일 패스)을 robust verdict 로 격상하는 **도구**를 추가했다. 신규
`se_inference_score(submission_se, oracle_se, blind_se)` 가 SE-rate 를 [0,1](blind=0/oracle=1)로
정규화 → inference_score 와 *같은 frame* → 러너가 `--runs N` 시 N회 telemetry 의 정규화 SE 를
**기존 사전약정 `classify_inference`(임계 frozen)**로 묶어 robust SE verdict 출력. 유료 N-run 실행은
사용자 로컬.

## 계획 대비 실적

- ✅ **AC1** — `se_inference_score` 결정론(oracle→1.0·blind→0.0·mid→(0,1)·span≤0→0.0·clamp). 2 테스트.
- ✅ **AC2** — 러너 `--telemetry`: telemetry 를 `n_runs=max(1,runs)`회 → runs>1 robust SE verdict / runs=1 단일 + 무회귀(1 call).
- ✅ **AC3** — 정규화 SE = inference_score span 공식 mirror(같은 frame) → `classify_inference` frozen 임계 재사용, 새 임계 0. 분류기 재사용 테스트(oracle→infers·type_blind→at-floor).
- ✅ **AC4** — pytest **523 passed**(520+3), 회귀 0. score_agent/telemetry 본문 무변경=byte-identical. mypy/ruff/build clean.
- ✅ **AC5** — docstring + 러너 출력에 "scripted-proxy·유료 N-run=사용자 로컬·신호이지 verdict 아님·same max_steps".

## 변경 파일

- `src/critter_gym/eval_harness.py` (+17): `se_inference_score`(추가 함수, read-only normalizer).
- `scripts/llm_eval_run.py` (+25/−3): `--telemetry` 가 telemetry N회 + 정규화 + runs>1 robust SE verdict. runs=1 무회귀.
- `tests/test_eval_harness.py` (+40): 앵커·band·분류기 재사용 3 테스트.

## 발견된 이슈

- 정규화 SE 자체가 max_steps 의존(blind floor 가 step-cap 민감 → 같은 LLM SE 50% 가 ms=40 정규화
  0.32 / ms=200 0.46). 러너가 band+submission 을 같은 sealed(같은 max_steps)서 계산하므로 일관 —
  docstring 에 "same max_steps" 경고(#16 계승).

## 흡수처 (extracted_to)

- 없음 — 새 evergreen 없음. 도구·정직 경계는 코드 docstring + #16 `inference-baseline.md` 참조.

## 정직 경계

- robust verdict 도 **scripted-proxy band·1 모델·proxy** = 신호이지 능력 verdict 아님.
- 정규화 SE 는 inference_score 와 동일 [0,1] frame → frozen 임계 transfer by construction(새 임계 0=p-hacking 회피).
- 유료 N-run LLM 실행은 평가자 로컬. 전투 모델 재설계·공개는 사람 게이트.
