---
slug: v1-results-packaging
initiative: jax-throughput
status: active
started: 2026-06-25
mode: standard
task_type: general
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - README.md
  - docs/paper/critter-gym.md
  - docs/paper/README.md
  - scripts/reproduce_results.py
  - pyproject.toml
extracted_to: []
supersedes: []
---

# KR3 — 결과 패키징 / v1.0.0-rc 준비

> 작성일: 2026-06-25 | 상태: 계획 | milestone: M3 (런치 준비) + M4 결산

## 목표

흩어진 강한 결과(JAX 속도 + robust oracle-headroom + 4/4 family + 재현성)를 **front-facing 문서로
통합**하고, **1-command 재현 벤치**를 추가하고, **버전 1.0.0-rc**를 준비한다. **공개(OSS 리스팅·arXiv
제출·태그 push)는 사람 게이트 — 본 task는 그 직전까지만.**

핵심 통합 헤드라인 2개(자율런 KR1/KR2 산출):
1. **competitively fast** — JAX vmap 36–1047× numpy(CPU), **4/4 family(A/B/C/D) 전부 벡터화**.
2. **hard-and-learnable** — tuned PPO가 scripted oracle의 **21–28%만**(5-run robust), gap≈0(일반화),
   hard서 PPO<type_blind = capability ladder.

## 선행 조건

- main HEAD `c8e1375`, 415 tests green (2 skip). duel 포트 머지로 4/4 family 벡터화 완료.
- **현 stale 상태**: `README.md` "What it measures"가 throughput를 "266k steps/s/core"로만 기술(JAX vmap·
  4 family·PPO headroom 부재). `docs/paper/critter-gym.md` §2가 동일하게 stale, §8 conclusion이 "JAX port"를
  *future work*로 기술(이미 done). `docs/paper/README.md`(figure→source map)도 신규 결과 미반영.
- 기존 재현 도구: `scripts/bench_throughput.py`(throughput), `scripts/ppo_baseline.py`(PPO vs oracle headroom,
  `--runs N`). 1-command wrapper 부재.
- 버전: `pyproject.toml` `version = "0.0.1"`.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `README.md` | "What it measures"에 (1) JAX 속도(vmap 36–1047×·4/4 family) (2) hard-and-learnable headroom 헤드라인 추가. registered-env 표/positioning 유지. Release status에 1.0.0-rc·잔여 게이트(GPU·arXiv·OSS) 명시 | 중 (front-facing) |
| `docs/paper/critter-gym.md` | §2 throughput 갱신(numpy CPU + JAX vmap) + 신규 §"Throughput (JAX port)" + §4에 PPO oracle-headroom subsection + §5 "4 family 전부 벡터화" note + §8 conclusion("JAX port for throughput"→done) + §7 limitations(GPU 미측정) | 중 |
| `docs/paper/README.md` | figure→source map에 throughput·headroom·duel-parity 행 추가 | 소 |
| `scripts/reproduce_results.py` (신규) | **1-command 재현**: throughput 표(numpy/jax-single/jax-vmap) + headroom 표(PPO vs oracle, `--runs`) 재생성. `--quick`(CI/스모크 작은 config) / 전체 모드. honest framing(CPU·vmap-only·single/multi-run 라벨) 출력 | 중 |
| `pyproject.toml` | `version` `0.0.1` → `1.0.0rc1`. (태그 push·publish 안 함 — 버전 문자열만) | 소 |

### 영향 범위

- 전부 docs/scripts/메타 — **제품 코어(src/critter_gym) 무변경**. 회귀 위험 낮음. `reproduce_results.py`는
  기존 `bench_throughput`/`ppo_baseline`/`headroom`/`jax_env` 공개 API만 호출(신규 로직 최소).
- 버전 bump은 빌드 메타데이터만 — import/동작 무영향.

## Step별 계획

1. **(pre-freeze pilot)** `scripts/reproduce_results.py --quick` 프로토타입을 scratchpad에서 돌려 throughput·
   headroom 표가 실제로 생성되고 문서에 박을 수치 범위와 일치하는지 확인(falsify 시 수치 reframe).
2. `scripts/reproduce_results.py` 작성 — `--quick`(작은 batch/iter, 빠른 스모크) + full 모드, 두 표 출력.
3. README "What it measures" 헤드라인 2개 통합 + Release status에 1.0.0-rc·잔여 게이트.
4. paper: §2 + 신규 throughput 섹션 + §4 headroom + §5/§7/§8 갱신.
5. paper/README.md source map 행 추가.
6. pyproject version → 1.0.0rc1.
7. G2(mypy·ruff·pytest·build) + reproduce_results.py --quick 실행 확인.

## Pilot 결과 박제 (2026-06-25, freeze 전)

scratchpad `reproduce_results_proto.py --quick`(기존 `bench_throughput.py`+`ppo_baseline.py` subprocess
오케스트레이션):
- **두 표 모두 에러 없이 재생성** + honest framing 라벨 보존(CPU·vmap-only·single jit slower·oracle proxy).
- throughput: overworld 58× / commit-battle 1088× / non-commit-full-battle 454× / full-env 27× / non-commit
  full-env 35× (quick config, b=1024) — 아카이브 multiplier 범위와 일치.
- headroom(quick·1-run): default PPO 13%·hard 18% of oracle, verdict **`hard-and-learnable`** 양 config.
  full `--runs 5`가 헤드라인 21–28%로 수렴(quick은 작은 예산이라 낮음 — 정직). **수치는 라이브 재생성**(하드코딩
  없음) → fabricate 불가.
- **falsify 없음** → plan 그대로 freeze. 실제 script는 `Path(__file__).parent`로 scripts dir 해석(proto의
  하드코딩 경로 제거).

## 검증 방법

- `python scripts/reproduce_results.py --quick` 가 에러 없이 두 표를 출력(스모크).
- 문서의 모든 정량 주장이 측정/아카이브 근거와 일치(과대 금지) — paper/README source map으로 추적가능.
- mypy(src 무변경이라 영향 적음; 신규 script는 src 밖이나 일관 위해 lint) · ruff · pytest(415 무회귀) · build(1.0.0rc1 wheel).

## 리스크

- **과대주장**: front-facing 문서에서 vmap-only·CPU·single/multi-run·oracle=scripted proxy 한계 흐릴 위험.
  → 모든 헤드라인에 honest caveat 동반(기존 정직성 문화 계승). pilot이 수치 재현으로 fabricate 차단.
- **1.0.0-rc 성숙도 주장**: GPU(M4-EC3)·arXiv(M3-EC4)·OSS(M3-EC5) 미충족. → "rc=release candidate, 공개는
  사람 게이트"로 정직 프레이밍, Release status에 잔여 게이트 명시. 태그/publish 안 함.
- **reproduce 시간**: full headroom(5-run PPO)은 수 분. → `--quick`로 CI/스모크 분리, full은 옵션.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1** `scripts/reproduce_results.py --quick`가 throughput 표(numpy/jax-single/jax-vmap row) + headroom 표
  (PPO vs oracle, frac/verdict)를 에러 없이 출력하고, honest framing 라벨(CPU·vmap-only·run 수)을 동반.
- **AC2** README "What it measures"가 두 헤드라인(JAX 속도 36–1047×·4/4 family / hard-and-learnable 21–28% of
  oracle robust)을 정직 caveat과 함께 통합. Release status에 1.0.0-rc + 잔여 게이트(GPU·arXiv·OSS=사람) 명시.
- **AC3** `docs/paper/critter-gym.md`가 JAX throughput + PPO headroom을 본문에 통합(§2/신규 §/§4/§5/§7/§8),
  conclusion의 "JAX port=future"가 done으로 정정. `docs/paper/README.md` source map에 신규 행.
- **AC4** `pyproject.toml` version = `1.0.0rc1`, `python -m build`가 1.0.0rc1 아티팩트 생성. 태그/publish **안 함**.
- **AC5** 무회귀 + 정직성: pytest 415 green(src 무변경), mypy/ruff clean. **모든 정량 주장이 측정/아카이브 근거와
   일치**(fabricate 0) — pilot 재현으로 입증. 과대주장 0.
- **AC6** 공개 행위(OSS 리스팅·arXiv 제출·git tag push)는 **수행하지 않음** — 사람 게이트 직전 정지.
