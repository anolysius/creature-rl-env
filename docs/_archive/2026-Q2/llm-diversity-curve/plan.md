---
slug: llm-diversity-curve
initiative: null
status: active
started: 2026-07-09
acceptance_freeze: true
mode: standard
task_type: general
domains: [rl-env, eval]
scope_paths:
  - scripts/llm_diversity_curve.py
  - tests/test_llm_diversity_curve.py
extracted_to: []
supersedes: []
---

# LLM 다양성 곡선 — 난이도 다이얼은 불완전 추론자에게 보이는가 (돈 게이트 측정)

> 작성일: 2026-07-09 | 상태: 계획 | 단발 (사용자 승인된 quota 지출 측정)

## 목표

**두 scout이 남긴 핵심 미증명 조각을 돈으로 산다.** diversity-dial scout(#116)의 메타-발견:
scripted `infer` arm은 즉석-완벽 학습이라 **saturated** — scripted 밴드는 eval *검증*용이지 난이도
*calibration*은 불가. **난이도 곡선은 불완전 추론자(학습/LLM)에게만 보인다**는 가설이 돈 게이트로
남았다. 본 task = `boss_pool_size`(per-episode 타입 다양성) sweep을 **실제 LLM**(claude-cli, 사용자
구독 quota — 사용자가 방향 선택으로 승인)으로 재측정.

사전약정 질문: **per-episode 타입 다양성이 오르면 LLM의 추론 점수가 떨어지는가?** 떨어지면 =
"다이얼이 불완전 추론자에게 보인다" — 판매 티어 난이도 레버(boss_pool_size)의 실증 + scripted-밴드
한계 가설의 확증. 평평하면/역전이면 그대로 보고(falsify 환영).

**선행 결과가 주는 경고(정직)**: 이전 세션 Fable5 **아레나 추론 = 종결적 inconclusive** — LLM이
연속 전투에서 chart 추론을 명확히 못 보였다. 같은 일이 여기서도 나면(pool=1 최대-재발생에서도 blind
floor 수준) 곡선 자체가 측정 불가 — 이 경우를 위해 **floor 조기중단 게이트**를 사전약정해 quota를
보호한다.

## 비용 구조 (G1 승인 대상 — 명시)

- **호출 구조**: 매 env step = 1 LLM 호출(`claude -p` subprocess, 구독 quota·per-token 과금 없음,
  순차 실행 = rate-limit 친화). 1 world ≤ `max_steps`(140) 호출, 조기 클리어 시 감소.
- **게이트별 예산** (worst case):
  | 게이트 | 내용 | 호출 상한 |
  |---|---|---|
  | G-0 smoke | 1 world, pool=1 — 배선·지연·파싱 실패율 실측 | ≤140 |
  | G-1 앵커 | pool=1 × 4 worlds — floor 판정 | ≤560 |
  | G-2 본점 | pool=8 × 4 worlds (G-1 통과 시에만) | ≤560 |
  | G-3 중간(조건부) | pool=4 × 4 worlds (G-2에서 \|Δ\|≥margin 시에만) | ≤560 |
  | **합계** | | **≤1,820** (floor 중단 시 ≤700) |
- **wall-clock**: ~3–8s/호출 → 총 1.5–4h 추정. **background 실행**(진행 로그), 사용자 세션과 같은
  구독을 쓰므로 순차·단일 스트림 유지.

## 선행 조건

- main = 970e053 (#120 머지), 770 tests green. ✅
- 부품 전부 존재(src 무변경 조립): `SealedEvalSet(boss_pool_size=…)`(스레딩 검증됨) ·
  `BattleMemoryLLMAgent`(관찰 데미지 테이블 — 추론 지원 최강 정직 변형) · `claude_cli_complete`
  (timeout+retry) · `score_inference_telemetry`(win-독립 SE-rate) · `se_inference_score`(blind~oracle
  정규화) · `inference_baseline`(무료 scripted 앵커) · `_mean_distinct_types`(실측 x축) ·
  `_DIVERSITY_SEALED` config(grid8·8gym·140step·num_types12·boss 140/6/18).
- community/BenchmarkSpec 경로는 boss_pool_size 미노출 — 부적합 확인(설계 근거).
- StubLLM 테스트 패턴(tests/test_llm_eval.py) — quota 없이 메커니즘 검증 가능.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `scripts/llm_diversity_curve.py` (신규) | 게이트형 sweep 러너: pool점마다 sealed 조립→scripted 앵커(무료)→LLM telemetry→infer_score, G-0~G-3 게이트·예산 카운터·JSON 아티팩트 | 낮음 | **src 무변경** — 순수 조립 |
| `tests/test_llm_diversity_curve.py` (신규) | Stub-LLM 메커니즘 테스트(quota 0): pool 스레딩·게이트 분기·예산 카운트·출력 스키마 | 낮음 | CI-safe(claude 불요) |

### 영향 범위 (import 그래프)

- src 변경 0. 신규 스크립트는 eval_harness·llm_eval·inference_curve의 공개 API만 소비.
- 테스트는 StubLLM 주입으로 subprocess/network 0 — CI에서 결정론.

## Step별 계획

1. **테스트(Red→Green)** — 스크립트의 순수 로직을 함수로 분리해 stub 검증: (a) pool별 sealed에
   boss_pool_size 스레딩, (b) 게이트 분기(floor 중단/Δ판정/중간점 조건), (c) 예산 카운터, (d) 출력
   JSON 스키마(측정 재현 메타 포함).
2. **러너 조립** — `--smoke`(G-0만)·`--points`·`--worlds`(default 4) 플래그, 판정 전 사전약정 규칙
   출력, 진행 로그(호출 수·경과), 결과 JSON 저장(`docs/_active/.../results.json` → report에 박제).
3. **G-0 smoke 실행** — 1 world 실측: 호출 수·평균 지연·파싱 실패율 보고. 이상 시 중단·보고.
4. **본측정 (G-1→G-2→G-3)** — background, 사전약정 게이트대로. 결과 그대로 보고.

## 사전약정 (G1 freeze — 데이터 무관 불변)

- **config**(freeze): `_DIVERSITY_SEALED` mirror(master_seed 20260708·grid8·8gym·140step·
  num_types12·boss 140/6/18), **worlds/point=4**(비용; scripted 곡선의 8보다 작음 — 정직 라벨),
  agent=`BattleMemoryLLMAgent(window=8)`, provider=claude-cli(사용자 CLI 기본 모델, 라벨에 명기).
- **점수**(freeze): `score_inference_telemetry`의 SE-rate → `se_inference_score(llm, oracle, blind)`
  (같은 pool점의 무료 scripted 앵커로 정규화; 0=blind, 1=oracle). x축=실측 mean distinct types/world.
- **게이트**(freeze):
  - **G-1 floor 중단**: `llm_score(pool=1) < 0.10` → 측정 종료, verdict **FLOOR-SATURATED**("이
    모델/provider에겐 곡선 측정 불가 — 아레나 inconclusive와 정합") — 남은 예산 지출 금지.
  - **G-2 주판정**: `Δ = llm_score(pool=1) − llm_score(pool=8)`. `Δ ≥ 0.15` → **DIAL-VISIBLE**
    (다이얼이 불완전 추론자에게 보임 — SIGNAL). `Δ ≤ −0.15` → INVERTED(그대로 보고). else →
    FLAT/inconclusive(scripted와 같은 결론 — 그대로 보고).
  - **G-3 중간점**: G-2에서 `|Δ| ≥ 0.15`일 때만 pool=4 추가(모양 확인). 아니면 지출 금지.
  - **마진 근거**: 0.10/0.15는 정규화 점수(0~1) 위 사전 고정 — telemetry 표본(전투 move 수십)의
    단일-run 노이즈보다 큰 보수값. 확충해도 불변.
- **해석 규율**(freeze): **단일 run·4 worlds/point·1 모델·1 provider** — SIGNAL이지 measurement
  아님(오차막대 없음, LLM 확률적). 파싱 실패율 함께 보고. 헤드라인 금지. DIAL-VISIBLE이 나와도
  "LLM 일반"이 아니라 "이 모델·이 설정"으로 한정.

## 검증 방법

- `.venv/bin/python -m pytest -q` → 770 + 신규(stub 메커니즘) 무회귀 green.
- `.venv/bin/python -m ruff check .` clean (src 무변경 — mypy 대상 불변).
- `--smoke` 실측 보고(호출·지연·파싱 실패율) 후 본측정 진입 — G-0이 사실상 런타임 검증.
- 본측정 JSON 아티팩트 + report 박제.

## 리스크

- **R1 (quota 낭비)**: LLM이 아예 추론 못 하면 곡선 무의미. **완화**: G-1 floor 조기중단(≤700 호출로
  손절) — 아레나 inconclusive 선례를 정면 반영한 게이트.
- **R2 (wall-clock/hang)**: 시간당 수백 호출·수 시간. **완화**: claude_cli_complete의 timeout+retry
  기존 내장, background 실행 + 진행 로그, 게이트별 중간 저장(JSON append)으로 부분 결과 보존.
- **R3 (rate-limit 간섭)**: 측정과 본 세션이 같은 구독. **완화**: 순차 단일 스트림(병렬 0), 측정 중
  본 세션의 대형 LLM 작업 자제.
- **R4 (확률적 단일 run)**: LLM 응답 비결정 — 점수가 run마다 흔들림. **완화**: 보수 마진(0.15) +
  "SIGNAL, no error bars" 정직 라벨. 재현 메타(JSON) 박제로 후속 재측정 가능.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `scripts/llm_diversity_curve.py` 신규 — 게이트형 프로토콜(G-0~G-3)·예산 카운터·판정 전
  사전약정 규칙 출력·JSON 아티팩트. **src 무변경**(순수 조립).
- **AC2**: Stub-LLM 테스트가 pool 스레딩·게이트 분기(floor 중단/Δ/중간점 조건)·예산 카운트·출력
  스키마를 quota 0으로 커버. 770 무회귀, ruff clean.
- **AC3**: G-0 smoke(1 world) 완주 — 실측 호출 수·평균 지연·파싱 실패율 보고 후 본측정 진입.
- **AC4**: 본측정이 사전약정 게이트를 **그대로** 따름(FLOOR-SATURATED 조기중단 포함) — 사후 마진/
  grid 변경 0, 나온 branch 그대로 보고.
- **AC5**: 정직 라벨(단일 run·4 worlds/point·1 모델·1 provider·파싱 실패율·헤드라인 금지·모델 한정
  해석) 명시 + 결과 JSON·report 박제.
