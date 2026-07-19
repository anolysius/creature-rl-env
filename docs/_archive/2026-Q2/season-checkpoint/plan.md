---
slug: season-checkpoint
initiative: null
status: active
started: 2026-07-19
acceptance_freeze: true
mode: standard
task_type: general
domains: [eval]
scope_paths:
  - src/critter_gym/community.py
  - scripts/community_submit.py
  - tests/test_community.py
extracted_to: []
supersedes: []
---

# 시즌 측정 체크포인트/이어받기 (사용자 승인 "1번부터 하자")

## 목표

수 시간짜리 LLM 시즌 측정(sonnet 2-3.5h·opus 3-5h)이 중간 실패(컴퓨터 꺼짐·quota 소진) 시
전부 증발하는 문제 수리. **의미 동일성 근거 확인됨**: `score_submission_on_season`이 world마다
`reset()` 호출(memory isolation 기존 계약) + 시드 결정론 → 끊어 돌려도 연속 실행과 동일.

1. `score_submission_on_season(..., checkpoint: Path|None=None)` (additive, None=기존
   byte-identical): 시작 시 checkpoint 로드→완료 seed 스킵, world 완료마다 `{seed: clears}`
   flush(임시파일+rename 원자 쓰기).
2. `community_submit --llm`: `<out>.checkpoint.json` 자동 사용 — 존재 시 재개(몇/몇 완료 출력),
   최종 JSON 성공 후 삭제. 실행 안내에 caffeinate 권장 명시.
3. 테스트(stub·quota 0): (a) checkpoint 없음=기존 결과 불변 (b) world마다 파일 flush
   (c) 중단→재개가 완료 world를 실제로 스킵(콜 카운트) (d) 연속 vs 끊김 재개 mean 동일
   (e) 성공 시 checkpoint 삭제.

## AC (freeze — 사용자 승인으로 G1)

- AC1: checkpoint=None 기본 경로 byte-identical(기존 테스트 무변경 green).
- AC2: 재개 의미 동일성 테스트(연속==끊김) + 스킵 실증(콜 카운트) + flush/삭제.
- AC3: 794 무회귀, ruff/mypy clean.
