# QA Checklist — tier-eval-bundle (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-8)

- [ ] AC1 — `src/critter_gym/eval_marketplace.py` 신규: `TierOffer`(+to_json/from_json), `SellerListing`(offer/issue 단일 진실원), `build_tier_offer`, `publish_catalog`, `issue_tier_certificate`, `verify_offer_certificate`, `bundle_honesty`. stdlib-only, 의존성 0, `eval_package`+`env_tier` 만 소비.
- [ ] AC2 — offer: `build_tier_offer`가 티어 sealed 매니페스트(서명·비밀 미노출)+difficulty 메타; `publish_catalog`가 티어별 서로 다른 커밋먼트 offer 리스트.
- [ ] AC3 — buyer 흐름: 정상 → `ok=True` 서명 유효; `verify_offer_certificate` 같은 티어·같은 seed 성공, 같은 티어+다른 seed 실패(confound 격리), 다른 티어 실패; `SellerListing` 재입력 불일치 방지.
- [ ] AC4 — 오염-불가 위임: 오염 → `ok=False` 미채점·서명 유효(eval_package 위임, 재구현 없음).
- [ ] AC5 — 정직성 travel: offer 가 `difficulty_note`("open" 포함)+`manifest.honest_scope`("prototype" 포함) 둘 다 노출(`bundle_honesty`+테스트).
- [ ] AC6 — `tests/test_eval_marketplace.py` 신규: AC1-5 커버, 전체 회귀 0 (baseline 578).
- [ ] AC7 — `scripts/tier_eval_bundle_demo.py`: catalog→선택→제출→인증서→검증(+바인딩실패·오염) E2E, 두 층 정직 캡션, 무오류.
- [ ] AC8 — 정직성: 두 층 note 유실 0. CHANGELOG 1줄 entry.

## Default DoD

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] `ruff check` / `mypy src/critter_gym/eval_marketplace.py` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
