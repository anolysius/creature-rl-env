# QA Checklist — llm-eval-run (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 동결.
> ⚠ eval-product #3 — 실제 LLM 비용-제한 러너. 실행=사용자 로컬(키=사용자·채팅 금지). 러너는 stub로 CI 검증.

## Acceptance Criteria (frozen at G1)

- [x] **AC1 (step 상한)** ✅ — `SealedEvalSet(max_steps=N)`→env_factory가 CritterEnv max_steps=N. 테스트:
  max_steps=8서 에피소드 ≤8스텝 / 기본 200 그대로(env.max_steps==200). 기존 #1/#2 무회귀.
- [x] **AC2 (러너)** ✅ — `scripts/llm_eval_run.py`: argparse(model/worlds/max-steps/num-types/master-seed) +
  예상 콜 수+⚠️ 비용 경고 + `LLMAgent(anthropic_complete(model))`→봉인 set `score_agent`→frac_of_oracle·
  oracle·blind·cleared/caught 출력. ruff clean. 키/SDK 없을 때 명확 ImportError 확인.
- [x] **AC3 (회귀 0 + 보안/정직)** ✅ — SealedEvalSet 기본(max_steps=200) byte-identical. 461→**463 passed**
  (+2), mypy 30·ruff·build clean. 러너 키 인자 안 받음(SDK env)·docstring "🔑 키 채팅/커밋 금지" + 정직 경계
  (작은 probe·step 상한·proxy oracle·단일 run). claude-api 준수(claude-opus-4-8 기본·thinking 생략).
- [x] **AC4 (task-end 산출)** ✅ — INITIATIVE #3 + CHANGELOG = task-end.

## L1 이력
- round 1: plan-reviewer **APPROVE** / qa-verifier **APPROVE** → APPROVED.

## 정직성 불변식
실제 LLM run은 사용자 로컬·키 필요·비용 발생 — 러너는 *도구*(상한+경고)이지 측정 결과 아님. 결과 해석은
작은 표본·step 상한·proxy oracle·단일 run noise 경계 동반. 키는 채팅/로그 금지(SDK env). 과대 0.
