---
slug: board-haiku-seed
initiative: null
status: active
started: 2026-07-13
acceptance_freeze: true
mode: standard
task_type: general
domains: [eval, site]
scope_paths:
  - src/critter_gym/llm_eval.py
  - scripts/community_submit.py
  - tests/test_llm_eval.py
  - community/submissions/season1-claude-haiku-4-5-claude-cli.json
  - site/index.html
  - site/index.ko.html
extracted_to: []
supersedes: []
---

# CLI 모델 선택 배선 + Haiku 4.5 리더보드 씨딩 (구독 quota, API 0원)

## 목표

사용자 승인: Haiku 4.5를 **구독 quota로**(API 결제 없이) 시즌 시험지에 돌려 커뮤니티 리더보드에
등재. CLI의 `--model` 지원은 1콜로 실측 확인됨. 필요한 배선(~10줄, additive):

1. `llm_eval.claude_cli_complete`에 `model: str | None = None` — argv에 `--model <id>` 추가.
2. `community_submit.py`에 `--cli-model`·`--cli-bin` 플래그(기본 None/"claude" = 기존 동작
   byte-identical) + `_build_llm_agent` 스레딩 + reproduce 문자열에 기록(재현 정직성).
3. **본측정**: season 1 공개 seed 8 worlds, BattleMemory(w=8) — 기존 조직자 예시와 동일 표준
   설정, `--model-name "claude-haiku-4.5 (claude-cli)"` → JSON 산출 →
   `community/submissions/` 커밋(=보드 등재, 사용자 이번 승인) → 사이트 재빌드로 행 표시.

## 비용 (G1 승인 대상)

- **≤1,600 콜**(8 worlds × 200 steps, 조기 클리어 시 감소) — **구독 quota, API 지출 0**.
- wall-clock ~1.5–3.5h(CLI 프로세스 기동이 지배), background 순차 단일 스트림.

## 선행 조건

- CLI `--model claude-haiku-4-5-20251001` 실측 OK(1콜). `shutil.which`는 절대경로도 통과.
- `_build_llm_agent`(community_submit.py:74-76)가 `claude_cli_complete()` 무인자 호출 — 배선 지점.
- 제출 스키마·검증기·시즌 seed 분리는 기존(#10 community-leaderboard) 그대로 — 산출 JSON은
  `--validate`로 자가 검증, `self_reported: true` 강제.

## 작업 범위 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `src/critter_gym/llm_eval.py` | `claude_cli_complete(model=None)` — argv 조건 추가, 기본 None=기존 byte-identical | **중** |
| `scripts/community_submit.py` | `--cli-model`/`--cli-bin` + 스레딩 + reproduce 기록 | 낮음 |
| `tests/test_llm_eval.py` | fake 실행파일(args echo)로 model 스레딩 계약 테스트(quota 0·CI-safe) | 낮음 |
| `community/submissions/season1-claude-haiku-4-5-claude-cli.json` (신규) | 본측정 산출(=보드 등재) | 낮음 |
| `site/index*.html` | 재빌드(커뮤니티 행 추가 — 데이터 반영일 뿐 카피 무변경) | 낮음 |

## Step별 계획

1. **테스트(Red→Green)** — fake binary(sh 스크립트, 받은 argv를 stdout으로)로: (a) model=None →
   argv에 `--model` 없음, (b) model 지정 → `--model <id>` 포함, (c) prompt는 `-p`로 전달.
2. **배선** — llm_eval + community_submit.
3. **카나리아(quota 0, L1 SUGGEST 반영)** — fake binary(`--cli-bin <fake>` + `--cli-model test`)로
   `community_submit --llm` 1-world 실행: argparse→스레딩→에이전트 조립 전 경로를 실 콜 없이 검증
   (fake 응답은 fallback 파싱 → 점수 무의미하나 배선 검증 목적, 산출물 폐기).
4. **본측정(background)** — season1 8 worlds Haiku, 산출 JSON `--validate` 확인.
5. **등재** — JSON 커밋 + `build_site --no-assets` 재빌드 → 보드 행 확인.

**커밋 단위(L1 SUGGEST 반영)**: 단일 브랜치/PR, 2커밋 — ①배선+테스트 ②측정 산출 JSON+사이트
재빌드(등재는 원자적으로 한 PR에서 리뷰 가능).

## 사전약정 (freeze)

- 설정: season 1·**n_worlds 8**·BattleMemory(window 8)·provider claude-cli·model
  `claude-haiku-4-5-20251001`·binary `~/.local/bin/claude`(shim 회피). **단일 run** —
  나온 점수 그대로 등재(재측정으로 유리한 run 고르기 금지). 점수가 낮아도(0 포함) 그대로 —
  낮은 점수는 보드의 변별력 증거이지 실패가 아님.
- 라벨: `claude-haiku-4.5 (claude-cli)` + JSON reproduce에 cli-model 포함.

## 리스크

- **R1 (quota)**: ≤1,600콜. 완화: 사용자 승인 대상 명시, 진행 로그(world당 1줄), 세션과 순차 공유.
- **R2 (파싱/에러 응답 오염)**: Haiku가 형식을 덜 지키면 fallback(WAIT) 비율↑ → 점수 하락으로
  정직 반영(그 자체가 측정). CLI 에러 문자열이 응답으로 새는 경우는 timeout+retry 기존 처리.
- **R3 (기존 경로 회귀)**: model=None 기본값이 기존 argv와 byte-identical — 테스트로 고정.

## Acceptance Criteria (G1 freeze)

- **AC1**: `claude_cli_complete(model=...)` 계약 테스트(quota 0) — None=기존 argv 불변,
  지정 시 `--model <id>` 포함. 기존 스위트 무회귀(791+), ruff/mypy clean.
- **AC2**: `community_submit --cli-model/--cli-bin` 스레딩 + reproduce 문자열 기록.
- **AC3**: 본측정 완주(season1·8w·BattleMemory·단일 run) — 산출 JSON `--validate` VALID,
  점수 그대로 등재(사후 재측정 0).
- **AC4**: JSON 커밋 + 사이트 재빌드로 보드에 haiku 행 표시(en/ko), 카피 무변경(데이터 행만).
