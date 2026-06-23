# QA 체크리스트 — learnability-precision

## 영향도
- 측정 전용 모듈(`learnability.py`)·`[rl]` 스크립트·테스트·DESIGN. env/obs/step 무변경.
- `run_episode` float→`EpisodeOutcome`는 내부 호출(`arm_mean`/`measure_learnability`)만 갱신; 공개 `measure_learnability` 시그니처+combined 필드 보존.

## 회귀 가드
- [x] 전체 174 passed/2 skipped (171→174, 회귀 0)
- [x] `measure_learnability` 시그니처 무회귀(combined heldin/heldout 보존)
- [x] `arm_mean` combined-return mean 무회귀(기존 `test_infer_beats_probe_through_the_action_ux` pass)
- [x] PPO `[rl]` smoke 무회귀(`test_ppo_learnability_smoke`, seed param 추가)
- [x] mypy(21)/ruff/build clean
- [x] honesty 가드 무회귀

## 엣지 케이스
- [x] arm은 CATCH 안 함 → return == gyms+evolutions 정확(분리 입증)
- [x] `infer` arm stateful memory가 seed마다 fresh(`partial(reference_arm,a)` per seed)
- [x] `--runs` band guard: band≤0 방어(`≈ probe/blind` fallback)
- [x] gym-clear ceiling(num_gyms) — 천장 압축 confound DESIGN 명시
- [x] oracle==infer 구분불가 — DESIGN 명시(추론 suffices지 load-bearing 증명 아님)

## 정직성
- [x] gym-clear-only = signal, 성능 freeze 아님
- [x] 3 caveat(ceiling/oracle==infer/단일config·N·다중run[rl]) DESIGN 명시
- [x] 다중run은 [rl]/비CI, 단일run 완화지 제거 아님
