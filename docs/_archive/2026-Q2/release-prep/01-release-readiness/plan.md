---
slug: release-readiness
initiative: release-prep
status: active
started: 2026-07-06
acceptance_freeze: true
task_type: general
domains: [rl-env]
scope_paths:
  - .github/workflows/ci.yml
  - docs/CHANGELOG.md
  - README.md
extracted_to: []
supersedes: []
---

# release-readiness — 공개 전 준비 ① (CI 신설 + 이력 정리)

> 작성일: 2026-07-06 | 상태: 계획 | 마일스톤: **M3-EC5** (OSS 공개) Phase A-1

## 목표

사용자가 공개 게이트를 열었다. 공개 전 기술 준비 첫 슬라이스:
(1) **비밀 스캔** — 완료·통과 (이력 216 커밋 전수: 키 패턴 0, 비밀 파일 0, 데모
prototype 상수 2건은 의도된 예시; 저자 이메일 2건 공개됨은 사용자 인지).
(2) **CI 워크플로 신설** — pyproject 가 이미 설계한 대로 (core=numpy-only, jax=extra):
푸시/PR 마다 ruff·mypy·pytest·커뮤니티 제출 `--validate` 게이트. 커뮤니티 트랙 개시
(Phase D) 의 "CI 연결" 선행물이기도 함.
(3) **CHANGELOG 이력 정리** — 이미 머지된 task 들의 stale `_(commit pending)_` 마커
88건 제거 (공개 시 첫인상 = 감사 추적 문서).

## 작업 범위

| 파일 | 변경 | 영향 |
|---|---|---|
| `.github/workflows/ci.yml` (신규) | 2 job: **core** (py3.9+3.12 matrix — `.[dev]`, ruff/mypy/pytest[jax 테스트 auto-skip]/submissions validate loop) + **jax-parity** (py3.9 — `.[dev,jax]`, 전체 pytest=parity 포함) | 신규 (제품 코드 무변경) |
| `docs/CHANGELOG.md` | `_(commit pending)_`·`commit <pending>` 마커 제거 (내용 무변경) | 텍스트만 |
| `README.md` | CI 뱃지 1줄 (공개 후 자동 활성) | 텍스트만 |

## 검증 방법

- 로컬에서 CI 와 동일 커맨드 시퀀스 실행 (ruff·mypy·pytest·validate loop 전부 green)
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` (문법)
- README quickstart 스니펫 실측 (register→reset→step 동작)
- CHANGELOG 마커 grep 0건 + 그 외 diff 0 (마커 제거만)

## 리스크

| 리스크 | 대응 |
|---|---|
| CI 가 jax 테스트를 core job 에서 요구 | 기존 `pytest.importorskip("jax")` 패턴이 auto-skip — core job 은 numpy-only 로 통과 |
| py3.12 에서 core 의존성 비호환 | matrix 로 즉시 가시화; 실패 시 3.9 단독으로 축소 (README requires-python 정합) |
| CHANGELOG 정리가 내용을 건드림 | sed 치환은 마커 문자열만; diff 로 마커 외 변경 0 검증 |
| CI 첫 강제 시 기존 제출 파일 fail | **CI 작성 전** 로컬에서 validate loop 전수 선실행 → fail 0 확인 후 게이트 편입 |

커밋 단위: 단일 커밋 (준비물 원자 변경, 단독 PR). 후속 진입 조건: 본 task 머지 →
Phase A-2 `peer-facts-verify` → A-3 `paper-arena-update` → (사람) repo Public 전환.

## Acceptance Criteria (G1 freeze)

- **AC1 (CI)**: `.github/workflows/ci.yml` — core job(ruff·mypy·pytest·`community_submit.py --validate` 전 제출 파일 loop) + jax-parity job. YAML 문법 검증 + 로컬 동일-커맨드 시퀀스 green.
- **AC2 (CHANGELOG)**: pending 마커 88건 → 0건, 마커 외 diff 0.
- **AC3 (README)**: CI 뱃지 추가 + quickstart 스니펫 실측 통과.
- **AC4 (무회귀 + 제품 코드 무변경)**: `pytest -q` **통과 테스트 수 = 699, 실패 0**
  (baseline 정의: 현 main 의 pytest passed count); `git diff` 에 `src/**`·`tests/**`
  변경 **0 파일** (이 task 는 CI/문서만 건드림).
