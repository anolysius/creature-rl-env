---
slug: tier-eval-bundle
initiative: monetization-surface
status: completed
ended: 2026-07-01
extracted_to:
  - docs/reference/tier-eval-bundle.md
changelog_entry: docs/CHANGELOG.md
---

# 판매-표면 통합 캡스톤 — 티어 eval 번들 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 추진 EC | M5-EC1 + M5-EC2 결합 (판매 표면 end-to-end) |
| 신규 파일 | 3 (`eval_marketplace.py`, `test_eval_marketplace.py`, `tier_eval_bundle_demo.py`) + evergreen 1 |
| 기존 파일 수정 | 0 (additive, 조합-전용) |
| 테스트 | 578 → **592** (+14, 회귀 0) |
| lint/type | ruff All checks passed · mypy Success |
| L3 리뷰 | **2/2 APPROVE** (plan-reviewer SUGGEST→docstring 정밀화 반영 + qa-verifier APPROVE) |
| 신규 의존성 | 0 (stdlib) |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 결과 | 근거 |
|---|---|---|
| AC1 공개 API | ✅ | `TierOffer`(+to_json/from_json), `SellerListing`(.create/.offer/.issue_certificate), `build_tier_offer`, `publish_catalog`, `issue_tier_certificate`, `verify_offer_certificate`, `bundle_honesty`. stdlib-only, `eval_package`+`env_tier`만 소비. |
| AC2 offer | ✅ | `build_tier_offer`가 서명·비밀 미노출 매니페스트+difficulty 메타; `publish_catalog`가 티어별 distinct 커밋먼트(`test_catalog_offers_have_distinct_commitments`). |
| AC3 buyer 흐름 | ✅ | 정상→`ok=True` 서명 유효; 바인딩 same-tier·same-seed 성공 / **same-tier+diff-seed 실패**(seed confound 격리) / diff-tier 실패; `SellerListing` 재입력 불일치 방지. |
| AC4 오염 위임 | ✅ | 오염 제출 → `ok=False` 미채점·서명 유효. `eval_package.issue_certificate` 위임(재구현 0줄). |
| AC5 정직 travel | ✅ | `bundle_honesty`가 difficulty_note("open")+manifest.honest_scope("prototype") 둘 다 노출(`test_bundle_honesty_exposes_both_notes`). |
| AC6 테스트 회귀0 | ✅ | 신규 14 테스트, 전체 592 passed. |
| AC7 데모 | ✅ | `tier_eval_bundle_demo.py` catalog→선택→제출→인증서→검증(+바인딩실패·오염), 두 층 캡션, exit 0. |
| AC8 정직성 | ✅ | 두 층 note 유실 0(코드·데모). CHANGELOG 1줄. |

## 변경 파일 상세

**신규**
- `src/critter_gym/eval_marketplace.py` — TierOffer·SellerListing·offer/cert 조합·bundle_honesty. `eval_package`+`env_tier`만 import(조합-전용, 재구현 0).
- `tests/test_eval_marketplace.py` — 14 테스트 (offer round-trip·catalog·바인딩 3종(seed confound 격리 포함)·오염 위임·변조·정직 travel).
- `scripts/tier_eval_bundle_demo.py` — seller→buyer E2E 데모.

**흡수(evergreen)**
- `docs/reference/tier-eval-bundle.md` — 버퍼 흐름·공개 API·**바인딩 계약(커밋먼트=resolved knob+seed, not label)**·정직-scope. #4/#5 reference 를 잇는 캡스톤 문서.

## 발견된 이슈 (심각도)

- **[insight] 바인딩=resolved knob, not label** — 구현 중 테스트가 드러냄: 두 티어를 구분 knob(grid_size 등)까지 동일 오버라이드하면 sealed 설정이 붕괴해 커밋먼트가 같아짐 → 바인딩됨. 이는 올바른 동작(커밋먼트는 티어 이름이 아니라 해석된 knob+seed 에 바인딩). 테스트 헬퍼가 구분 knob 을 오버라이드하지 않도록 정정 + reference 문서에 계약 명문화.
- **[low → 수정됨] docstring 정밀도 (L3 SUGGEST)** — `verify_offer_certificate` docstring 이 "same tier"로 표현해 라벨 검사처럼 읽힐 소지 → "same resolved knobs (not the tier label)"로 정밀화.

## 타입 체크 / 빌드 결과

- `.venv/bin/python -m pytest` → 592 passed, 1 warning(기존 gymnasium, 무관).
- `ruff check` → All checks passed. `mypy src/critter_gym/eval_marketplace.py` → Success.
- `python scripts/tier_eval_bundle_demo.py` → exit 0, 전 케이스 출력.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 무엇 |
|---|---|
| `docs/reference/tier-eval-bundle.md` | 캡스톤 buyer 흐름·공개 API·바인딩 계약·정직-scope — archive 무관 살아있는 참조. |
