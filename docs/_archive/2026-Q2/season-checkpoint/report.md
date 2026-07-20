---
slug: season-checkpoint
initiative: null
status: completed
ended: 2026-07-19
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# 시즌 측정 체크포인트/이어받기 — 결과 보고서

수 시간짜리 LLM 시즌 측정의 전멸-재시작 문제 수리(사용자 승인 "1번부터").

- `score_submission_on_season(checkpoint=…)`: world마다 `{seed: clears}` 원자 flush(tmp+rename),
  재시작 시 완료 world 스킵. **None=기존 byte-identical**(테스트 고정). 의미 동일성 근거 =
  기존 계약(world마다 reset()·결정론 seed).
- `community_submit --llm`: `<out>.checkpoint.json` 자동 — 존재 시 "▶ resuming: n/N" 후 이어감,
  최종 JSON 후 삭제. caffeinate 팁 출력.
- 검증: 3 신규 테스트(default-불변·flush·재개 스킵+mean 동일) + fake-binary 카나리아로
  정상완주(삭제 확인)·중단→재개("resuming 1/2"→world 2만 실행) 실증. 794→**797**, ruff clean.
- L3 2/2 APPROVE(원자쓰기·None 게이트·fresh-only on_world 코드 정독 확인).

이제 sonnet(2-3.5h)·opus(3-5h) 측정이 중단-안전. 흡수 없음.
