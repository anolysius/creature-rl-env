---
slug: private-evalset-package
initiative: monetization-surface
status: completed
ended: 2026-07-01
extracted_to:
  - docs/reference/sealed-eval-packaging.md
changelog_entry: docs/CHANGELOG.md
---

# 비공개 held-out eval 세트 판매 패키지 (monetization-surface #4) — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 추진 EC | M5-EC1 (비공개 held-out eval — 재현 가능·un-gameable) |
| 신규 파일 | 3 (`eval_package.py`, `test_eval_package.py`, `package_sealed_eval.py`) + evergreen 1 |
| 기존 파일 수정 | 0 (additive) |
| 테스트 | 539 → **556** (+17, 회귀 0) |
| lint/type | ruff All checks passed · mypy Success |
| L3 리뷰 | **2/2 APPROVE** (plan-reviewer + qa-verifier) |
| 신규 의존성 | 0 (stdlib `hashlib`/`hmac`/`json`) |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 결과 | 근거 |
|---|---|---|
| AC1 공개 API | ✅ | `sign_payload`/`verify_signature`, `seed_commitment`, `EvalManifest`(+`build_manifest`/`to_json`/`from_json`/`verify_manifest`/`manifest_self_check`), `SignedCertificate`+`issue_certificate`/`verify_certificate` 구현. stdlib-only. |
| AC2 오염-불가 | ✅ | 오염 제출(overlap>0 또는 train이 held-out) → `ok=False` 미채점, 부정 인증서 서명 유효 (`test_contaminated_submission...`). |
| AC3 위변조 검출 | ✅ | 인증서/매니페스트 필드 변조 → `verify_*` False (`test_*_tamper_*`). L1 SUGGEST 반영: 매니페스트도 서명. |
| AC4 비밀 미노출 | ✅ | 매니페스트 JSON 에 seed/offset 문자열 부재, 커밋먼트=64-hex one-way (`test_manifest_hides_*`, `test_commitment_does_not_leak_*`). |
| AC5 테스트 회귀0 | ✅ | 신규 17 테스트, 전체 556 passed. |
| AC6 E2E 데모 | ✅ | `package_sealed_eval.py` seller→buyer→verify, 정상+오염 2케이스 + 정직-scope 캡션, exit 0. |
| AC7 정직성 | ✅ | HMAC=shared-secret 한계 모듈 docstring·`HONEST_SCOPE`·데모 3중 명시. CHANGELOG 1줄. |

## 변경 파일 상세

**신규**
- `src/critter_gym/eval_package.py` — 서명 코어(canonical SSOT + HMAC) → seed 커밋먼트 → 서명 매니페스트 → 서명 인증서. `eval_harness` 만 import(단방향).
- `tests/test_eval_package.py` — 4단계 계단식 17 테스트 (서명/커밋먼트/매니페스트/인증서 각 정상+실패 경로).
- `scripts/package_sealed_eval.py` — E2E 데모 (build_site.py 규율: 순수 흐름 + `main()` guard, stdout only).

**흡수(evergreen)**
- `docs/reference/sealed-eval-packaging.md` — 공개 API 표 + 4 보장 + 정직-scope + 후속(사람 게이트).

## 발견된 이슈 (심각도)

- **[low] 프로세스** — plan-reviewer 가 L3 에서 verdict 없이 tool 호출만 반복 stall (2회 MALFORMED). verdict-first(`VERDICT:` 첫 줄 강제) 프롬프트로 3번째 시도에서 정상 APPROVE 획득. retro 큐에 `plan-reviewer-verdict-first` 제안 적재(사람 결재 대기).
- **[nuance, non-blocking] 보안** — public config 가 공개되므로 seed space 가 작으면 이론상 commitment brute-force 여지. `HONEST_SCOPE`("prototype, 실제=비대칭/서버측")가 이미 스코프를 좁혀 다룸 → 후속 사람-게이트 task 대상.

## 타입 체크 / 빌드 결과

- `.venv/bin/python -m pytest` → 556 passed, 1 warning(기존 gymnasium env_checker, 무관).
- `ruff check` → All checks passed. `mypy src/critter_gym/eval_package.py` → Success.
- `python scripts/package_sealed_eval.py` → exit 0, 전 케이스 출력.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 무엇 |
|---|---|
| `docs/reference/sealed-eval-packaging.md` | 판매 패키징 공개 API·4 보장·정직-scope — archive 와 무관하게 살아있는 참조. |
