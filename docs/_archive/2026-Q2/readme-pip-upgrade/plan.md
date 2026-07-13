---
slug: readme-pip-upgrade
initiative: null
status: active
started: 2026-07-13
acceptance_freeze: true
task_type: general
domains: [docs]
scope_paths:
  - README.md
  - README.ko.md
extracted_to: []
supersedes: []
---

# README 설치 블록에 pip 업그레이드 1줄 (fresh-clone smoke 발견 수리)

## 목표

fresh-clone 퀵스타트 smoke(마케팅 전 체크리스트)에서 **신규 방문자 차단급 발견**:
stock macOS(python 3.9 동봉 pip 21.2.4)에서 README 첫 명령 `pip install -e .`가
**하드 에러**("editable mode currently requires a setuptools-based build" — PEP 660은
pip ≥ 21.3 필요). README가 명시한 최소 버전(Python 3.9)의 기본 환경에서 첫 명령이 죽음.

수리(2줄): en/ko README 설치 블록 맨 앞에 `python -m pip install -U pip` + 짧은 주석.
**smoke로 수리 유효성 이미 실증**: pip 업그레이드 후 설치→퀵스타트→커뮤니티 데모→validate
전 경로 green(fresh clone·fresh venv).

## Acceptance Criteria

- **AC1**: en/ko 설치 코드블록 첫 줄에 pip 업그레이드 명령 + 이유 주석(구식 pip은 editable
  설치 실패, pip ≥ 21.3 필요). 그 외 무변경.
- **AC2**: 791 green sanity(docs-only), CHANGELOG 1줄.
