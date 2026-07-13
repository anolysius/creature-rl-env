---
slug: readme-pip-upgrade
initiative: null
status: completed
ended: 2026-07-13
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# README pip 업그레이드 1줄 — 결과 보고서

fresh-clone 퀵스타트 smoke(마케팅 전 체크리스트)가 잡은 **신규 방문자 차단 요인** 수리.

- **발견(실측 재현)**: stock macOS python3.9(동봉 pip 21.2.4)에서 README 첫 명령
  `pip install -e .` 하드 에러 — PEP 660 editable은 pip ≥ 21.3 필요, repo는 pyproject-only.
- **수리**: en/ko 설치 블록 첫 줄 `python -m pip install -U pip` + 이유 주석 (+4줄, 그 외 0).
- **유효성 실증**: 업그레이드 후 fresh clone·fresh venv에서 설치→README 퀵스타트→커뮤니티
  데모(0.75 산출)→`--validate` VALID exit 0 — 방문자 전 경로 green.
- 791 green sanity. L3 2/2 APPROVE(주석의 기술 서술·en/ko 대응·pyproject-only 사실 확인).

흡수 없음(docs 2줄).
