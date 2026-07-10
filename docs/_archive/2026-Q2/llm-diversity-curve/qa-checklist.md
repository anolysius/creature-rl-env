# QA Checklist — llm-diversity-curve (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.
> **사전약정(config·worlds/point·마진·게이트 분기·해석 규율)은 freeze 후 데이터와 무관하게 불변.**

## Acceptance (plan AC 1-5)

- [ ] AC1 — `scripts/llm_diversity_curve.py` 신규: 게이트형 프로토콜(G-0~G-3)·예산 카운터·판정 전 사전약정 규칙 출력·JSON 아티팩트. **src 무변경**(순수 조립).
- [ ] AC2 — Stub-LLM 테스트가 pool 스레딩·게이트 분기(floor 중단/Δ/중간점 조건)·예산 카운트·출력 스키마를 quota 0으로 커버. 770 무회귀, ruff clean.
- [ ] AC3 — G-0 smoke(1 world) 완주 — 실측 호출 수·평균 지연·파싱 실패율 보고 후 본측정 진입.
- [ ] AC4 — 본측정이 사전약정 게이트를 그대로 따름(FLOOR-SATURATED 조기중단 포함) — 사후 마진/grid 변경 0, 나온 branch 그대로 보고.
- [ ] AC5 — 정직 라벨(단일 run·4 worlds/point·1 모델·1 provider·파싱 실패율·헤드라인 금지·모델 한정 해석) + 결과 JSON·report 박제.

## 사전약정 (freeze)

- **config**: `_DIVERSITY_SEALED` mirror(master_seed 20260708·grid8·8gym·140step·num_types12·boss 140/6/18), worlds/point=4, agent=BattleMemoryLLMAgent(window=8), provider=claude-cli(CLI 기본 모델 라벨 명기).
- **점수**: telemetry SE-rate → `se_inference_score(llm, oracle, blind)` (같은 pool의 무료 scripted 앵커 정규화). x축=실측 mean distinct types/world.
- **게이트**: G-0 smoke(1 world·pool=1) → G-1 pool=1×4w: `score<0.10`→**FLOOR-SATURATED 종료** → G-2 pool=8×4w: `Δ≥0.15`→DIAL-VISIBLE / `Δ≤−0.15`→INVERTED / else FLAT → G-3 pool=4×4w는 `|Δ|≥0.15`시만.
- **예산 상한**: ≤1,820 호출(worst), floor 중단 시 ≤700.
- **해석 규율**: 단일 run·SIGNAL·오차막대 없음·모델 한정("이 모델·이 설정")·헤드라인 금지.

## Default DoD

- [ ] 전체 테스트 green, 회귀 0. `ruff check .` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
