---
slug: obs-harmonization
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/env_family.py
  - src/critter_gym/envs/duel_env.py
  - src/critter_gym/envs/critter_env.py
  - src/critter_gym/genre_generalization.py
  - scripts/genre_learned_transfer.py
  - tests/**
extracted_to: []
supersedes: []
---

# obs 조화 (Observation Harmonization) — 4-family 공유 obs 스킴

> 작성일: 2026-06-23 | 상태: 계획

## 목표

4개 env family(A critter / B forage / C duel / D muster)가 **동일한 관측 공간(obs space)**
을 노출하도록 obs 스킴을 조화(harmonize)한다. 현재 duel(C)만 `player_charge`/`enemy_charge`
2키를 더해 13키를 노출하고 나머지 3 family는 11키(`REQUIRED_OBS_KEYS`)라, 단일 정책 네트워크
가 4 family를 한 번에 다룰 수 없다(`assert_obs_compatible`가 duel을 거부 → #26
`genre_learned_transfer`가 duel을 제외하고 train{A,B}→held-out{D}만 측정).

이 task는 **"전이하는 학습 정책" 이니셔티브의 선행(하드 블로커) 슬라이스**다. 목표는 전이 gap을
줄이는 게 *아니라*(그건 다음 task), duel을 포함한 4 family가 한 obs 공간을 공유하게 만들어
**4-family 학습 전이 실험을 가능케 하는 토대**를 까는 것이다.

### 마일스톤 매핑 (정직하게 명시)
- 이 작업은 활성 마일스톤 **M3**(공개 신뢰성)가 아니라 **M5 / moat 층2**(genre generalization
  surface, competitive-analysis 갭 register §5의 "more families + learned policy" 항목)의
  **enabler**다.
- CLAUDE.md의 엄격한 milestone-gating(M3 EC 먼저)을, 핸드오프의 사람-설정 방침
  ("**공개는 맨 마지막, 기능 준비 + 비교우위가 먼저**")이 의도적으로 override한다. 이 텐션을
  여기 명시하고 진행한다 — G1에서 사람이 이 override를 승인한다.

## 선행 조건
- 없음(이 task 자체가 다른 작업의 선행). 기존 4 family + `genre_generalization` 측정 스택,
  185 tests, env id 6종은 모두 존재.

## 작업 범위

### 핵심 설계 결정 — 조화 방식 (2안, L1/pilot로 정련)

**A. 공유 superset 키 + 마스킹 (추천)**
- `env_family`에 canonical obs 키 집합(`HARMONIZED_OBS_KEYS` = `REQUIRED_OBS_KEYS` ∪
  {`player_charge`, `enemy_charge`})를 SSOT로 선언.
- charge를 쓰지 않는 family(critter/forage/muster)는 두 키를 상수 0으로 노출(중립 패딩).
- 학습 네트워크는 모든 family에서 동일한 13키 Dict를 본다. duel만 실제 charge 값, 나머지는 0.
- 적용 지점은 **env 코어 최소 침습** — `env_family`에 `harmonize_obs_space()` /
  `harmonize_obs()` 헬퍼 또는 얇은 `HarmonizeObs` wrapper를 두고, *교차-family 단일 net이
  필요한 경로*(`genre_learned_transfer`의 `_MultiFamilyEnv`)에서 적용. env id 6종의 기본
  obs 공간은 변경 최소화(회귀 표면 최소).
- **왜 저회귀인가**: 기존 scripted 레퍼런스 정책(`duel_aware_policy` 등)은 이미
  `obs.get("enemy_charge", _ZERO)` 형태라, charge 키가 0으로 존재해도 **행동 불변**.

**B. family 계약 1급화** (대안 — 더 원칙적이나 더 침습)
- `CollectionRPGEnv` 계약 자체를 13키로 격상, 4 family 코어가 모두 13키를 직접 노출.
- `conforms`/`REQUIRED_OBS_KEYS` 의미 변경 → env id 6종 obs 공간 전부 변경 → 회귀 표면 큼.
- pilot에서 A안의 회귀/복잡도가 예상보다 크면 B안 재고.

→ **기본 A안으로 plan, pilot로 회귀 표면 검증 후 freeze.**

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/env_family.py` | `HARMONIZED_OBS_KEYS` SSOT + `harmonize_obs_space()`/`harmonize_obs()` 헬퍼(또는 wrapper) | 중 — 계약 모듈 |
| `scripts/genre_learned_transfer.py` | `assert_obs_compatible` 완화(조화 후 4 family 통과) + `_MultiFamilyEnv`가 조화된 obs 사용 + duel 포함 가능화 | 중 — 다음 task가 쓸 진입점 |
| `src/critter_gym/genre_generalization.py` | (필요 시) LOO/레퍼런스 정책이 조화 obs와 정합한지 점검 | 저 |
| `src/critter_gym/envs/duel_env.py` | (A안이면 거의 무변경 — 이미 13키) 점검만 | 저 |
| `src/critter_gym/envs/critter_env.py` | (A안이면 코어 무변경 — 헬퍼/wrapper가 패딩) 점검 | 저 |
| `tests/test_obs_harmonization.py` (신규) | 4 family 조화 obs 동일성·마스킹·무회귀 가드 | 신규 |

### 영향 범위 (import 그래프)
- `env_family` ← `genre_generalization`, `genre_learned_transfer`, 각 env. 헬퍼 추가는
  하위호환(기존 심볼 유지).
- env id 6종 registration/`check_env`: A안이면 기본 obs 불변이라 무회귀가 1순위 가드.

## Step별 계획
1. **(freeze 전 pilot)** A안 프로토타입: `env_family`에 조화 헬퍼 1개 + duel 포함 4 family를
   조화 obs로 묶어 `check_env`/단일 net 구성이 되는지, 기존 scripted 정책 점수가 *변하지
   않는지* 스모크. 회귀 표면(코어 변경 필요 여부) 실측 → A vs B 확정.
2. `HARMONIZED_OBS_KEYS` SSOT + 조화 헬퍼/ wrapper 구현(TDD: Red 먼저).
3. `assert_obs_compatible` 완화 + `_MultiFamilyEnv`가 조화 obs 사용, duel 포함 경로 가능화
   (단, 4-family 전이 *실험 실행*은 다음 task; 여기선 구성 가능성 smoke까지).
4. 신규 테스트: (a) 4 family 조화 obs 키 동일, (b) 비-duel family의 charge 키=0 마스킹,
   (c) duel charge 값 보존, (d) scripted 레퍼런스 정책 점수 무회귀, (e) env id 6종 무회귀.
5. DESIGN §3.1.1 + `genre_learned_transfer` 독스트링 갱신("obs 조화 완료 → 4-family 전이는
   다음 task").

## 검증 방법
- `python3 -m unittest` 전체(기존 185 + 신규) 무회귀.
- `mypy src` · `ruff check .` clean.
- 4 family 각각 `gymnasium.utils.env_checker.check_env` 통과(조화 obs 포함).
- scripted 레퍼런스 정책(`type_attacker`/`duel_aware`/`rush`/`muster`/`nav_toward_gyms`)
  점수가 조화 전후 동일(고정 seed) — 패딩이 행동을 안 바꿈을 수치로 증명.
- `[rl]` smoke: 4 family(duel 포함) `_MultiFamilyEnv` 구성 + `assert_obs_compatible` 통과
  (importorskip, 비-CI 실측 학습은 다음 task).

## 리스크
- **R1 회귀**: env 코어 obs 변경이 6 env id / 185 tests를 깸. → A안(코어 최소 침습) +
  무회귀를 1순위 acceptance. pilot로 코어 변경 필요 여부 사전 확인.
- **R2 마스킹이 학습을 오도**: 상수-0 charge 키가 비-duel family에서 학습 신호를 왜곡? →
  상수 피처는 무해(net이 무시 학습); 다음 task 실험에서 실측. 이 task 범위 밖.
- **R3 scope creep**: 4-family 전이 *실험*을 여기서 돌리고 싶은 유혹. → 명시적으로 **enabler
  까지만**, 실험은 다음 task. acceptance에 못 박음.
- **R4 A/B 방식 오선택**: pilot이 A안의 숨은 회귀를 드러내면 B안으로 reframe(정직).

## Acceptance Criteria (G1 통과 시 freeze)

> 성능/주장형이 아니라 **구조 변경 + 무회귀 + 정직 보고**로 freeze. "전이 gap을 줄였다"는
> 주장은 이 task의 acceptance가 **아니다**(다음 task).

- **AC1** `HARMONIZED_OBS_KEYS`가 `env_family`에 SSOT로 선언되고 4 family가 모두 동일한 obs
  Dict 키를 노출(조화 헬퍼/wrapper 적용 후).
- **AC2** 비-duel family(critter/forage/muster)의 `player_charge`/`enemy_charge`가 0으로
  마스킹되고, duel은 실제 charge 값을 보존(테스트로 증명).
- **AC3** 기존 scripted 레퍼런스 정책 점수가 조화 전후 **동일**(고정 seed) — 패딩 행동 불변.
- **AC4** env id 6종 + 기존 테스트 전부 무회귀(185 유지/증가), `check_env` 4 family 통과,
  `mypy`/`ruff`/`build` clean.
- **AC5** `assert_obs_compatible`가 duel 포함 4 family에 대해 통과하고, `_MultiFamilyEnv`가
  4 family(duel 포함) 조화 obs로 **구성 가능**(smoke; 실험 실행은 다음 task).
- **AC6** DESIGN §3.1.1 + 관련 독스트링이 "obs 조화 완료, 4-family 학습 전이는 다음 task"로
  정직하게 갱신. 마일스톤 override(M5 enabler, M3 공개보다 먼저) 기록.
- **AC7** CHANGELOG 1줄 append(rules/80 §F.5).
