# QA 체크리스트 — family-d-muster

## 영향도
- `MusterEnv`는 `CritterEnv` 서브클래스(`_step_overworld`만 override). family A/B/C 소스 무변경.
- `genre_generalization.py`·`registration.py`는 *추가*만(레퍼런스 정책 2종 / 등록 1종). 기존 API 보존.

## 회귀 가드
- [x] 전체 181 passed/2 skipped (174→181, 회귀 0)
- [x] family A/B/C 무변경(서브클래스 + additive 등록)
- [x] 2-family + LOO API 무회귀(`test_two_family_pairwise_api_unregressed`·`test_leave_one_out_measures_three_families` pass)
- [x] check_env 6 gym id 통과(+muster)
- [x] mypy(22)/ruff/build clean, honesty 가드 무회귀

## 엣지 케이스
- [x] CATCH 성공 시에만 버프(빈 타일 CATCH는 0)
- [x] 버프가 live party 참조로 Battle 데미지에 흐름(엔진 무변경)
- [x] obs `caught`로 수집 진행 판단(특권접근 없음, family-agnostic 정책)
- [x] rush_policy 절대 CATCH 안 함(순수 직행) — D에서 floor 보장
- [x] 난이도 confound: within-family 대조로 통제(같은 config, 정책만 변주)

## 정직성
- [x] 헤드라인 = within-family 대조(난이도 confound된 raw LOO gap 아님), DESIGN 명시
- [x] family A muster ≤ rush(수집 step 낭비) — "≈" 아닌 방향 정정(L3 반영)
- [x] 4 family도 토대지 장르 일반화 증명 아님(DESIGN)
- [x] N=12 단일 run = signal
