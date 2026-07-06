# Initiative: release-prep

> **M3-EC5 OSS 공개 준비** — 사용자가 공개 게이트를 연 시점(2026-07-06)부터의 공개 전
> 기술 준비 트랙. 이전 quick-fix 2건(onboarding-guides, paper-eval-product-section)은
> 이니셔티브 폴더 이전 시기라 CHANGELOG 에만 기록됨.
>
> **Phase 지도**: A-1 CI+이력 정리 → A-2 피어 사실 [verify] 검증 → A-3 논문 §5 아레나
> 반영 → (사람) B repo Public+Pages → C arXiv/PyPI → D 커뮤니티 트랙 개시.

## Task 목록

| # | slug | 상태 | 한 줄 |
|---|---|---|---|
| 2 | `peer-facts-verify` | ✅ done (→ `_archive/2026-Q2/release-prep/02-peer-facts-verify/`) | **피어 사실 검증 + 약관 + Pages 준비** — [verify] 전수 종결(4피어 1차 자료·4병렬), 정직 하향 3건(XLand one-notch 폐기 등), 4피어 모두 sealed-eval 제품 없음 확정. 약관: 수치 공개 OK / 구독 배치 GRAY(소규모+API 선호). pages.yml(사람 토글 전 no-op). molt.church=홍보 부적합. 699/0. L3 2/2. |
| 1 | `release-readiness` | ✅ done (→ `_archive/2026-Q2/release-prep/01-release-readiness/`) | **공개 전 준비 ① CI 신설 + 이력 정리** — 비밀 스캔 통과(이력 216커밋 전수: 키 0·비밀 파일 0; 저자 이메일 2건 공개는 사용자 인지). `.github/workflows/ci.yml`: core job(py3.9+3.12, numpy-only — ruff/mypy/pytest[jax auto-skip]/커뮤니티 제출 --validate 게이트) + jax-parity job(py3.9, 전체 parity). CHANGELOG stale pending 마커 88건 제거(marker-only diff 증명). README CI 뱃지+quickstart 실측. 제품 코드 0 파일, 699/0. 후속 체크: 첫 실제 CI 런 mypy green 확인. L3 2/2. |
