---
slug: diversity-dial
initiative: null
status: active
started: 2026-07-08
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/region.py
  - src/critter_gym/envs/critter_env.py
  - src/critter_gym/eval_harness.py
  - src/critter_gym/inference_curve.py
  - scripts/diversity_dial.py
  - tests/test_diversity_dial.py
  - tests/test_inference_curve.py
extracted_to: []
supersedes: []
---

# diversity-dial — per-episode 타입 다양성이 진짜 추론-난이도 다이얼인가 (scout)

> 작성일: 2026-07-08 | inference-difficulty-curve 후속. num_types 반증 → 진짜 다이얼 검증.

## 목표

직전 scout 가 반증: num_types(차트 크기)는 다이얼이 아니다 — 재발생 pool
(`max(2, n_gyms//2)`)이 월드당 distinct 보스타입을 ~2로 캡해 재방문을 ~2로 고정하기 때문.
**진짜 다이얼 후보 = per-episode 타입 다양성(pool 크기).** 이걸 깨끗이 격리해 측정한다:

고정 num_gyms(예산)에서 pool 을 1→8 로 키우면 재방문이 8→1 로 줄어 첫-만남 추론자가
"미리 학습한 매치업" 비율이 떨어진다 → 추론이 진짜 어려워진다. pool=1(1타입·8재방문)이면
infer 가 거의 oracle, pool=8(8타입·1회씩)이면 infer 가 거의 floor 이어야 한다.

**opt-in env knob** `boss_pool_size` (기본 None = 현 공식 = **byte-identical**;
boss_secondary/strict_battle 선례). scout 는 scripted-only·결정론·무료.

## 사전선언 해석 (데이터 전)

- **양성(단조 하락)**: pool(다양성)↑ → infer_score↓ → per-episode 다양성 = **calibrated
  추론-난이도 다이얼** = 강한 결과("눈금 있는 계측기"·마케팅 헤드라인·판매 티어 축).
- **음성(평평)**: 다양성도 다이얼 아님 → 정직 falsify, 그대로 보고.
- 곡선 x축은 knob 이 아니라 **실측 mean distinct-types/world**(knob 이 다양성을 실제로
  올렸는지 동반 검증). 헤드라인 금지·1 seed·scripted proxy·학습/LLM 앵커=후속(돈 게이트).

## 작업 범위 (영향도)

| 파일 | 변경 | 등급 |
|---|---|---|
| `region.py` | `generate_region(..., boss_pool_size=None)` — None=현 `max(2,n_gyms//2)` 그대로(byte-id), 설정 시 `min(exploitable, boss_pool_size)` | 낮음(opt-in, 기본 무변경) |
| `envs/critter_env.py` | `boss_pool_size` kwarg → reset 에서 generate_region 전달 | 낮음(기본 None) |
| `eval_harness.py` | `SealedEvalSet(boss_pool_size=None)` → env_factory 전달 | 낮음(기본 None) |
| `inference_curve.py` | `diversity_curve(pool_grid, *, sealed_kwargs)` — pool 별 infer score + 실측 distinct-types/world + 앵커/winnable | additive |
| `scripts/diversity_dial.py` (신규) | 곡선 출력·사전선언 규칙·정직 라벨 | 도구 |
| `tests/test_diversity_dial.py` (신규) | byte-identity(None=현 region 불변) + pool knob 이 distinct 타입 증가시킴 + 곡선 결정론/구조 | +테스트 |
| `tests/test_inference_curve.py` | 기존 num_types 곡선 결정론 회귀(무변경 확인) | +assert |

JAX 범위밖: JAX env 는 numpy `Region.gyms`(이미 타입 결정됨)를 소비 — knob 미설정 config(파리티 테스트)는 region 불변이라 parity 무영향. JaxEnvConfig 무변경.

## Step별 계획

1. **Red**: test_diversity_dial — (a) `boss_pool_size=None` region == 기존(byte-id, 고정 seed) (b) `boss_pool_size=1` → 월드 distinct 타입=1, 큰 값 → 증가 (c) `diversity_curve` 결정론·구조·정규화. inference_curve 결정론 회귀.
2. **Green(env)**: region.py knob(None 분기 byte-id) + critter_env/eval_harness 플러밍.
3. **Green(curve)**: inference_curve.py `diversity_curve` + 실측 distinct-types 계측.
4. **Scout 실행**: `scripts/diversity_dial.py` — num_gyms 고정·num_types=12, pool ∈ {1,2,4,8} 곡선 + 사전선언 규칙. 결과 report 기록(방향은 결과보고, AC 아님).
5. 문서/CHANGELOG (task-end). 양성이면 evergreen `docs/reference/inference-difficulty-dial.md`.

커밋 단위: 단일 커밋. **PR base = feature/inference-difficulty-curve** (스택; #114 머지 후 GitHub 자동 retarget).

## 검증 방법

- `.venv/bin/python -m pytest -q` (전체 713+신규, 회귀 0)
- `mypy src` · `ruff check .`
- 기존 parity 테스트 무회귀(knob 기본 None=byte-id)
- scout 출력 report 기록

## 리스크

| 리스크 | 대응 |
|---|---|
| knob 이 default RNG 스트림 바꿈(byte-id 깨짐) | None 분기 = 기존 코드 그대로; byte-identity 테스트로 고정 |
| pool > exploitable 타입 수 | `min(len(exploitable), pool)` 클램프 |
| 다양성↑인데 revisit 외 confound | x축=실측 distinct-types; num_gyms·경제 고정으로 다양성만 변화 |
| JAX parity 회귀 | knob 미설정 config 는 region byte-id → parity 무영향; 기존 parity 테스트로 확인 |

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1 (opt-in knob, byte-id)**: `generate_region(boss_pool_size=None)` == 기존 region
  (고정 seed byte-identical 테스트) + 기존 전체/파리티 테스트 회귀 0. 설정 시
  `min(exploitable, pool)` 로 pool 크기 제어 (distinct-types 증가 테스트).
- **AC2 (플러밍)**: `CritterEnv(boss_pool_size=...)` 와 `SealedEvalSet(boss_pool_size=...)`
  가 generate_region 까지 전달 — 설정 시 월드 distinct 보스타입이 pool 로 제어됨(테스트).
- **AC3 (다양성 곡선 API)**: `diversity_curve(pool_grid)` 가 pool 별 infer inference_score +
  oracle/type_blind 앵커 + **실측 mean distinct-types/world** + winnable 을 결정론 반환
  (단위 테스트: 결정론·구조·oracle≥blind·score∈[0,1]).
- **AC4 (scout + 정직 라벨 — 측정 가능)**: `scripts/diversity_dial.py` 실행이 **exit 0** 로
  pool 별 (실측 distinct-types/world, infer inference_score, oracle/blind) 행을 출력하고,
  출력에 **다음 문자열이 데이터 앞에 존재**한다(검증: 스크립트 실행 캡처 grep) —
  (a) 사전선언 결정 규칙("monotone"/"dial"/"falsify" 취지), (b) "scripted"·"1 seed"·
  헤드라인-금지("do NOT headline") 라벨, (c) 학습/LLM 앵커=후속 언급. **곡선의 수치 방향
  (단조↓ or 평평)은 결과보고이지 gate 아님** — 어느 쪽이든 report 에 그대로 기록.
- **AC5 (무회귀·결정론)**: 전체 713+신규 회귀 0, mypy/ruff clean, 결정론.
