---
slug: board-discoverability
initiative: null
status: active
started: 2026-07-13
acceptance_freeze: true
mode: standard
task_type: general
domains: [site]
scope_paths:
  - scripts/build_site.py
  - tests/test_build_site.py
  - site/index.html
  - site/index.ko.html
extracted_to: []
supersedes: []
---

# 보드 발견성 수리 — "Leaderboard" 제목 충돌 제거 + 커뮤니티 점프 링크

## 목표 (사용자 실사용 발견·명시 승인)

프로젝트 소유자가 모델 행을 **두 번** 못 찾음 = 방문자는 100% 못 찾음. 원인: ① 1번 섹션 제목이
"Leaderboard"인데 모델 없음(내장 baseline 표) ② 진짜 모델 표는 9/9 맨 끝. 사용자가 아래 3항목
제안에 "응 고쳐줘"로 명시 승인(=G1, freeze 기록):

1. 1번 섹션 제목: "Built-in baselines — generalization check"(ko: "내장 baseline — 일반화 검증")
   — "Leaderboard" 단어 충돌 제거.
2. 1번 표 아래 점프 링크 1줄: "Looking for submitted models (LLMs)? → Community leaderboard ↓"
   (`#community` 앵커, en/ko).
3. Community 섹션에 `id="community"` 앵커.

## AC (freeze)

- AC1: 위 3항목 en/ko 반영, 그 외 카피·수치 무변경. 기존 "Community leaderboard" 헤딩 유지
  (backward-compat 테스트 보존).
- AC2: 신규 테스트 — 앵커 존재 + 점프 링크(en/ko) + 새 제목. 793 무회귀, ruff clean.
- AC3: 재빌드 후 라이브 반영 확인(머지 후).
