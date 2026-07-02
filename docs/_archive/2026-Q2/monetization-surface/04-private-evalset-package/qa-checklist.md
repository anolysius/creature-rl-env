# QA Checklist — private-evalset-package (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-7)

- [ ] AC1 — `src/critter_gym/eval_package.py` 신규: `sign_payload`/`verify_signature`, `seed_commitment`, `EvalManifest`(+`build_manifest`/`to_json`/`from_json`/`verify_manifest`), `SignedCertificate`+`issue_certificate`/`verify_certificate`. stdlib-only, 신규 의존성 0.
- [ ] AC2 — 오염-불가: overlap>0 또는 train이 held-out 영역인 제출 → `issue_certificate`가 `ok=False` 발급, 부정 인증서도 서명 유효.
- [ ] AC3 — 위변조 검출: 서명된 인증서 필드 변조 → `verify_certificate` False; 서명된 매니페스트 필드 변조 → `verify_manifest` False.
- [ ] AC4 — 비밀 미노출: 매니페스트 JSON에 비밀 eval seed/offset 부재(문자열 부재 테스트), 커밋먼트로부터 seed 역산 불가.
- [ ] AC5 — `tests/test_eval_package.py` 신규: AC1-4 각각 커버(round-trip/위변조/오염/비밀미노출/커밋먼트무결성). 전체 스위트 회귀 0 (baseline 539 → 539+신규 all pass).
- [ ] AC6 — `scripts/package_sealed_eval.py`: seller→buyer→verify E2E 데모, 정상+오염 두 케이스 + 정직-scope 캡션, 무오류 실행.
- [ ] AC7 — 정직성: HMAC=shared-secret prototype 한계 코드·문서·데모 3중 명시. CHANGELOG 1줄 entry.

## Default DoD (pass-criteria)

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] `ruff check .` / `mypy src` 통과 (툴 존재 시; 없으면 report에 명시).
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
