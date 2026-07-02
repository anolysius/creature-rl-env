---
slug: sealed-difficulty-levers
initiative: monetization-surface
status: completed
ended: 2026-07-01
extracted_to:
  - docs/reference/env-tiers.md
  - docs/reference/sealed-eval-packaging.md
  - docs/reference/tier-eval-bundle.md
changelog_entry: docs/CHANGELOG.md
---

# 정직성 갭 수리 — sealed eval 이 난이도 레버를 담게 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 추진 EC | M5-EC1/EC2 정직성 경화 (우리가 남긴 follow-up) |
| 수정 파일 | 3 코어(eval_harness/eval_package/env_tier) + 3 테스트 + 3 문서 |
| 신규 파일 | 0 (기존 수정) |
| 테스트 | 592 → **598** (+6, 회귀 0) |
| lint/type | ruff All checks passed · mypy Success |
| L3 리뷰 | **2/2 APPROVE** (qa APPROVE + plan-reviewer SUGGEST→docstring 반영) |
| 데모 | 3종(list_env_tiers·package_sealed_eval·tier_eval_bundle) 무오류 |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 결과 | 근거 |
|---|---|---|
| AC1 SealedEvalSet 레버 | ✅ | `patch_radius`(기본2)/`num_gyms`(기본3) param + 검증(patch≥0, gyms>0) + `env_factory` 전달. 기본값=CritterEnv 기본값 → byte-identical. |
| AC2 커밋먼트+매니페스트 | ✅ | `seed_commitment` material 에 두 레버(swap 방어); `EvalManifest`+`build_manifest` 가 두 레버 공개 노출(구매자 가시, 비밀 seed 미노출 유지). |
| AC3 env_tier | ✅ | `_SEALED_KNOBS`에 두 레버, `_SEALED_DROPPED`=(num_creatures,). `build_sealed` 튜닝 레버 전달; docstring 갱신. |
| AC4 회귀 0 | ✅ | 598 passed(기본값 보존), ruff/mypy clean, 3 데모 무오류. |
| AC5 정직 문서 | ✅ | env-tiers("faithful difficulty" 재작성, "less hard" 경고 제거) / sealed-eval-packaging(material 목록) / tier-eval-bundle(resolved knob) 갱신. 내장 hard 이미 충실 과대표현 없이. |
| AC6 테스트+CHANGELOG | ✅ | eval_harness/eval_package/env_tier 신규·갱신 테스트로 AC1-3 커버. CHANGELOG 1줄(본 task-end). |

## 변경 파일 상세

**수정(코어)**
- `eval_harness.py` — `SealedEvalSet` +patch_radius/num_gyms param + 검증 + `env_factory` 전달.
- `eval_package.py` — `seed_commitment` material +두 레버; `EvalManifest` +두 공개 필드; `build_manifest` payload +두 레버.
- `env_tier.py` — `_SEALED_KNOBS` +두 레버; `_SEALED_DROPPED`=(num_creatures,); `sealed_config`/`build_sealed` docstring.

**수정(테스트)**
- `test_eval_harness.py` — 하위호환(env patch=2/gyms=3), sealed env 튜닝 레버 반영, invalid 거부.
- `test_eval_package.py` — 커밋먼트 두 레버 바인딩, 매니페스트 두 레버 노출.
- `test_env_tier.py` — 옛 drop-test → 포함-검증 갱신, custom 티어 레버 sealed 도달, 모듈 docstring 정정.

**수정(문서·흡수)**
- `env-tiers.md`/`sealed-eval-packaging.md`/`tier-eval-bundle.md` — 정직성 갱신(살아있는 reference).

## 발견된 이슈 (심각도)

- **[정직성 정밀화]** 내장 hard 의 patch_radius/num_gyms(2/3)=기본값 → 내장 hard sealed 는 *이미 충실*했음. 이 fix 의 실질 효과는 **custom 티어**가 이 레버를 튜닝할 때. plan·문서·리뷰 모두 이를 과대표현 없이 반영("이제 hard 가 더 어렵다" 금지).
- **[low → 수정됨] L3 SUGGEST** — `test_env_tier.py` 모듈 docstring 이 "dropping num_gyms/patch_radius"로 stale → 실제 동작(num_creatures만 드롭)으로 정정.
- **[프로세스]** L3 qa-verifier 가 초기 BLOCK(AC5 문서 미완/AC6 CHANGELOG) — 메인 inline 이 문서 완료를 명시 안 해 발생한 false negative. 정정 사실(문서 3종 완료 + CHANGELOG=task-end 정상 순서) 전달 후 APPROVE. plan-reviewer 는 초기 빈 출력(stall) → 재호출로 정상 verdict(seeded proposal `plan-reviewer-verdict-first` 이 근본 대응).

## 타입 체크 / 빌드 결과

- `.venv/bin/python -m pytest` → 598 passed, 1 warning(기존 gymnasium, 무관).
- `ruff check` → All checks passed. `mypy`(3 코어) → Success.
- 3 데모 exit 0.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 무엇 |
|---|---|
| `docs/reference/env-tiers.md` | sealed tie-in "faithful difficulty" — 두 레버 반영·num_creatures만 드롭·내장 hard 이미 충실. |
| `docs/reference/sealed-eval-packaging.md` | seed_commitment material 목록에 두 레버. |
| `docs/reference/tier-eval-bundle.md` | 바인딩 계약 resolved-knob 목록에 두 레버. |
