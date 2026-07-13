---
slug: board-haiku-seed
initiative: null
status: completed
ended: 2026-07-13
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# CLI 모델 선택 배선 + Haiku 4.5 보드 씨딩 — 결과 보고서

## 요약

| 항목 | 결과 |
|---|---|
| 배선 | `claude_cli_complete(model=…)`(None=기존 argv byte-identical) + `--cli-model/--cli-bin` + reproduce 기록 |
| 카나리아 | fake binary, **quota 0** — argparse→스레딩→채점→VALID 전 경로 2회 검증 |
| **본측정** | Haiku 4.5·season1·8 worlds·BattleMemory(w8)·구독 quota·단일 run — 클리어 2/1/0/0/1/1/2/1 → **mean 1.0** |
| 보드 | scripted 0.750 < **haiku 1.0** — en/ko 순위표에 행 등재(사전약정대로 점수 그대로) |
| 테스트 | 791 → **793**(+2 계약), ruff clean, mypy 신규 clean |

## L3에서 잡힌 결함 (프로세스 가치 실증)

plan-reviewer **BLOCK**: reproduce 문자열이 `--cli-model`만 기록, `--cli-bin` 누락 — freeze가
명시한 binary(shim 회피)가 재현 커맨드에서 은폐됨(AC2 위반). **수리**: 비기본 cli-bin 조건부
append + 카나리아 재검증 + 기측정 JSON의 reproduce를 실제 실행 커맨드로 **출처 정정**(점수·스키마
필드 무변경 — 사전약정의 "단일 run 그대로" 유지). 재리뷰 APPROVE.

## 사전약정 준수

설정 freeze 일치(season1·8w·BattleMemory·모델 id·실바이너리), 단일 run 그대로 등재(재측정 0),
낮지 않은 점수였지만 원칙은 동일 — 몇 점이든 그대로. `--validate` VALID.

## 흡수처 매핑

흡수 없음. 후속(선택): fable-5 행은 이제 **개발 0**으로 같은 커맨드(모델 미지정=CLI 기본)로 가능.
