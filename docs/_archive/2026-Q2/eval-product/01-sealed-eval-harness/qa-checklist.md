# QA Checklist — sealed-eval-harness (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 동결.
> ⚠ M5 enabler 프로토타입 — 성공 = moat 메커니즘의 *동작하는 코드 데모*이지 "제품 완성/고객/매출"이 아니다.

## Acceptance Criteria (frozen at G1)

- [x] **AC1 (봉인 held-out)** ✅ — `_eval_seeds()` 전부 `is_held_out`(≥1M, sealed base=1.1M); 같은
  master_seed→동일 블록·다른→다른 블록. 3 테스트 통과(`test_eval_seeds_*`).
- [x] **AC2 (오염 가드 — moat 핵심)** ✅ — `verify_sealed`: clean→ok=True·overlap0 / 겹침→ok=False·
  overlap>0(leak 검출) / 구역 밖→ok=False. 3 테스트 통과. demo: leak 시도 overlap=16 검출·거부.
- [x] **AC3 (RLVR 검증 채점)** ✅ — `score_agent` verifiable subgoal만(mean_gyms/cleared/caught/evolved
  rate/frac_of_oracle). 실측 demo: oracle 1.88(100%) > type_blind 0.94(50%) > random 0.38(20%), 모든
  rate∈[0,1]. 테스트로 oracle>random·rate bound 입증. hand-tuned 0.
- [x] **AC4 (제출 인터페이스)** ✅ — `Agent` Protocol `act(obs)->int`(runtime_checkable) + EnvPolicy(scripted)
  둘 다 `score_agent` 수용. demo가 oracle/type_blind/random 제출→scorecard end-to-end.
- [x] **AC5 (회귀 0 + 정직 경계)** ✅ — 기존 src 무변경(신규 모듈만). **442→450 passed**(+8), 2 skip.
  mypy **29** clean·ruff·build clean. 모듈 docstring·INITIATIVE·demo에 "프로토타입·in-process 봉인·단일
  머신·numpy·hosted 제품/고객/공개 아님" 경계 명시. CHANGELOG=task-end.

## L1 이력
- round 1: plan-reviewer **APPROVE** / qa-verifier **APPROVE** → APPROVED.

## 정직성 불변식
프로토타입=기능 토대 데모(hosted 제품·고객·매출 아님). 봉인=in-process 컨벤션(실제 제품은 서버측 secret seed
+ 제출 샌드박스 필요)·단일 머신·numpy·단일 config. RLVR 검증 채점만(hand-tuned 0). 오염 가드가 "테스트로
학습 못 함"을 *검증 가능*하게 — moat의 핵심을 과장 없이 코드로 입증.
