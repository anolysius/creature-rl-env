# QA 체크리스트 — battle-system-family (family C / DuelEnv)

## 영향도 분석
- **신규 격리**: `DuelEnv`는 `CritterEnv` 서브클래스, 배틀 경로만 override. family A(`CritterEnv`)·family B(`ForageEnv`) 소스 **무변경**.
- **공유 인프라 변경**: `genre_generalization.py`는 새 함수/정책 *추가*만 — 기존 `GenreGapReport`/`measure_genre_generalization` 시그니처 보존.
- **core CI**: numpy/stdlib만(배틀 시스템). `[rl]`/`[viz]`/`[render]` extra 무영향.

## 회귀 가드
- [x] 전체 스위트 171 passed/2 skipped (160→171, 회귀 0)
- [x] family A 무회귀 — `test_family_a_battle_unchanged_by_family_c`(동일 시드 byte-identical, 결정론)
- [x] 2-family genre API 무회귀 — `test_two_family_pairwise_api_unregressed`
- [x] check_env 5 gym id 통과(fixed/procgen/commit/forage/duel)
- [x] honesty 가드 무회귀 — `test_source_does_not_overclaim_learned_inference`
- [x] mypy(21)/ruff/build clean

## 엣지 케이스
- [x] obs가 overworld/battle 양쪽에서 observation_space에 포함(extra charge 키 항상 존재) — `observation_space.contains(obs)`
- [x] duel charge가 battle 진입/종료 시 0으로 리셋(reset + 배틀 이탈)
- [x] duel turn cap(40)에서 미결착 시 loss로 종료(무한 GUARD/CHARGE 교착 방지)
- [x] GUARD가 적 ATTACK 무효화, charge가 데미지 배율(메커닉 단위 테스트)
- [x] 타입-무관: fresh ATTACK = attack×(1+0), 차트 곱 없음
- [x] 결정론/RLVR: 보스 고정 패턴, 랜덤 없음 → 재현성

## 정직성 점검
- [x] gap은 *signal*으로 보고(threshold/proof 아님)
- [x] 3 family = 토대 강화지 장르 일반화 증명 아님(DESIGN §3.1.1 명시)
- [x] 캐비엣(결정론 보스+charge-in-obs readability, N=12 단일 run) DESIGN·report에 명시
