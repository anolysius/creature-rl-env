---
slug: custom-env-api
initiative: monetization-surface
status: completed
ended: 2026-07-01
extracted_to:
  - docs/reference/env-tiers.md
changelog_entry: docs/CHANGELOG.md
---

# 커스텀/고난도 env 티어 API (monetization-surface #5) — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 추진 EC | M5-EC2 (커스텀/고난도 env API) |
| 신규 파일 | 3 (`env_tier.py`, `test_env_tier.py`, `list_env_tiers.py`) + evergreen 1 |
| 기존 파일 수정 | 0 (additive) |
| 테스트 | 539 → **561** (+22, 회귀 0) |
| lint/type | ruff All checks passed · mypy Success |
| L3 리뷰 | **2/2 APPROVE** (plan-reviewer BLOCK→수정→APPROVE + qa-verifier APPROVE) |
| 신규 의존성 | 0 (stdlib) |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 결과 | 근거 |
|---|---|---|
| AC1 공개 API | ✅ | `TierSpec`(+to_json/from_json), `validate_tier_spec`, `register_tier`/`tier_names`/`get_tier`, `make_tier_env`/`tier_env_factory`, `sealed_config`/`build_sealed`. stdlib-only, eval_package 미import. |
| AC2 curated 프리셋 | ✅ | `standard`+`hard` 내장 등록, 둘 다 검증 통과 (`test_presets_pass_guard`). |
| AC3 검증 가드 | ✅ | 비정상·unwinnable knob `ValueError` 거부. `make_tier_env`/`register_tier`/`build_sealed` 모두 가드 재적용(우회 없음 — L3 BLOCK 수정). |
| AC4 결정론·구별 | ✅ | 같은 seed reset 동일, hard≠standard knob, override 반영+거부. |
| AC5 정직 메타 | ✅ | `hard` `difficulty_note`=실측(PPO ~11–16% of oracle, oracle winnable)+"SOTA/recurrent open" (`test_hard_difficulty_note_is_honest`). |
| AC6 sealed tie-in | ✅ | `build_sealed` 지원 서브셋 전달, `sealed_config` 가 num_gyms/patch_radius/num_creatures 드롭(문서+테스트). descriptor round-trip. |
| AC7 테스트 회귀0 | ✅ | 신규 22 테스트, 전체 561 passed. |
| AC8 데모 | ✅ | `list_env_tiers.py` 목록·메타·커스텀(통과+거부)·정직 캡션, exit 0. |
| AC9 정직성 | ✅ | 난이도 실측 한정+open 명시(코드·데모). CHANGELOG 1줄. |

## 변경 파일 상세

**신규**
- `src/critter_gym/env_tier.py` — TierSpec + 검증 가드 + curated 레지스트리(standard/hard) + 팩토리 + sealed tie-in. `critter_env`/`eval_harness` 만 import(단방향, eval_package 미import).
- `tests/test_env_tier.py` — 22 테스트 (가드/프리셋/결정론/정직메타/sealed 드롭/가드-우회 방지).
- `scripts/list_env_tiers.py` — 데모 (build_site 규율: 순수 + main() + stdout).

**흡수(evergreen)**
- `docs/reference/env-tiers.md` — 공개 API 표 + 프리셋 + sealed 드롭 규칙 + 정직-scope.

## 발견된 이슈 (심각도)

- **[med → 수정됨] 가드 우회 (L3 BLOCK)** — 초기 `build_sealed` 가 overrides 를 `validate_tier_spec`
  없이 `SealedEvalSet` 로 직행 → `build_sealed(name, grid_size=-1)` 등 가드 우회 가능 + `num_creatures`
  조용한 드롭. **수정**: overrides 를 tier-knob/sealed-only 분리 후 tier-knob 은 재검증, `_SEALED_DROPPED`
  에 num_creatures 추가·문서화, 테스트 2개 추가. 재리뷰 APPROVE.
- **[low] 프로세스** — plan-reviewer 가 L1/일부 L3 첫 호출에서 빈 출력 stall(이 브랜치는 #94 의
  verdict-first 개선 미포함). 재호출로 정상 verdict 획득. #94 seeded proposal(`plan-reviewer-verdict-first`)
  이 근본 대응 — 별도 신규 제안 불필요.

## 타입 체크 / 빌드 결과

- `.venv/bin/python -m pytest` → 561 passed, 1 warning(기존 gymnasium, 무관).
- `ruff check` → All checks passed. `mypy src/critter_gym/env_tier.py` → Success.
- `python scripts/list_env_tiers.py` → exit 0, 전 케이스 출력.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 무엇 |
|---|---|
| `docs/reference/env-tiers.md` | 티어 API 공개 표·프리셋·sealed 드롭 규칙·정직-scope — archive 무관 살아있는 참조. |
