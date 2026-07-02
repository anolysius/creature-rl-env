---
slug: hard-note-precision
initiative: monetization-surface
status: active
started: 2026-07-02
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/env_tier.py
  - tests/test_env_tier.py
  - docs/reference/env-tiers.md
  - scripts/list_env_tiers.py
  - site/index.html
  - site/index.ko.html
extracted_to: []
supersedes: []
mode: standard
task_type: general
---

# hard 티어 difficulty_note 정밀화 — 낡은 "recurrent OPEN" 서술 갱신 (monetization-surface #9)

> 작성일: 2026-07-02 | 상태: 계획 | #8 report 의 [SSOT 관찰] 후속 — note 는 SSOT 라 사이트에 원문
> 렌더되므로, 낡은 서술은 곧 사이트의 낡은 서술.

## 목표 (조사 결과 기반)

`hard` 티어 `difficulty_note` 의 "OPEN (unmeasured): difficulty for a SOTA/recurrent agent is
not yet established" 은 **작성 시점(#5, 6-30)에는 정확했으나 이제 과소 서술**: hard-benchmark
#3(memory-headroom)·#5(multitype-boss-headroom)가 **관련 grid16 config(5gym·420step·types8)에서
recurrent PPO 를 robust 측정**했다(oracle 의 ~43%(#3)·~32%±8%(#5) — 천장에 한참 미달). 이 티어의
*정확한* config(3gym·300step·types3)는 여전히 recurrent 미측정이고 SOTA 는 어디서도 미측정 — 이
구분을 note 에 정밀하게 반영한다. ff "~11–16%" 주장은 유지(scout 출처이나 #3 의 ff 11% 가 대역 지지).

파급(SSOT): note 는 `docs/reference/env-tiers.md`(2곳)·`scripts/list_env_tiers.py`(정직 print)·
**사이트 티어 섹션(#100, 원문 렌더)** 에 반영 — 전부 갱신+재빌드.

## 작업 범위 (수정 대상)

| 파일 | 변경 요지 |
|---|---|
| `src/critter_gym/env_tier.py` | `_HARD.difficulty_note` 재작성(아래 AC1 문구) — knob·다른 코드 무변경 |
| `tests/test_env_tier.py` | `test_hard_difficulty_note_is_honest` 강화: 기존 토큰("oracle"/"open") 유지 + "recurrent 관련-config 측정 언급" 검증 |
| `docs/reference/env-tiers.md` | 인트로 인용·표 행의 recurrent 서술 정합 |
| `scripts/list_env_tiers.py` | 정직 print 의 "SOTA/recurrent = OPEN" 줄 정밀화 |
| `site/*.html` | `--no-assets` 재빌드(SSOT 자동 반영) |

## Step

1. (Red→Green) note 재작성 + 테스트 강화. 2. reference·script 정합. 3. `--no-assets` 재빌드 +
전체 스위트.

## 리스크

| 리스크 | 완화 |
|---|---|
| 과대표현 반전(관련-config 측정을 이 config 측정처럼 서술) | note 가 "related, deeper config" 와 "this exact tier config is unmeasured" 를 명시 구분. |
| 기존 정직성 테스트 토큰 깨짐 | "oracle"·"open" 토큰 유지 확인(테스트가 강제). |
| site 결정론 | 재빌드 diff 는 note 문자열 치환분만(순수 텍스트). |

## Acceptance Criteria (G1 freeze)

1. `difficulty_note` 정밀화: ff ~11–16% 유지 + **"관련 deeper grid16 config(5gym·420step)에서
   recurrent PPO ~32–43% of oracle 로 측정(천장 미달)"** + **"이 정확한 티어 config 는 recurrent
   미측정, SOTA 는 미확립(OPEN) — SOTA-hard 주장 금지"** 3요소 모두 포함. knob 무변경.
2. 테스트: 기존 토큰("oracle"/"open") 유지 + recurrent 관련-config 언급("recurrent"+"related")
   검증 추가. SSOT-일치 사이트 테스트(#100)는 자동 정합(원문 비교).
3. `env-tiers.md`·`list_env_tiers.py` 정합 갱신. site 재빌드(원문 자동 반영, 자산 무변경).
4. 회귀 0(baseline 630), ruff clean, `mypy src/critter_gym/env_tier.py` Success(L1 SUGGEST 반영).
   CHANGELOG 1줄.
