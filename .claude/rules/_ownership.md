---
title: ""
domain: meta
tags:
  - rules-meta
  - lifecycle
aliases: []
created: 2026-04-17
updated: 2026-04-17 02:17:34 +09:00
---



# rules/ 소유권과 수정 절차
이 폴더의 각 `*.md` 파일은 Claude Code의 **Path-scoped Rules**로 작동한다(가이드 §10). 사용자가 파일을 편집/생성할 때 매칭 경로에 한해 자동 로드되며, 메인 에이전트에만 전파된다. 서브에이전트에는 전파되지 않으므로 `agents/*.md` 본문에 핵심 규칙을 중복 임베드한다.



# 책임자 맵
| 파일 | 책임자 | 변경 PR 리뷰 필수 |
| --- | --- | --- |
| `80-task-lifecycle.md` | process-owner | 프로세스 오너 승인 |
| `85-git-policy.md` | process-owner | 프로세스 오너 승인 |
| `_ownership.md` | process-owner | 프로세스 오너 승인 |



# 충돌 해소 원칙
- `priority` 숫자가 **낮을수록 우선** (0이 최상위)
- 무조건 로드 (`paths` 생략) 규칙이 경로 한정 규칙보다 우선
- 경로별 Rules는 paths 매칭 시에만 로드, priority 순으로 충돌 해소
- 예: 가상의 `05-foundational` (priority 5) > `80-task-lifecycle` (80) > `85-git-policy` (85)
- 규칙 간 직접 충돌 발생 시 `_ownership.md`에 책임자 등록 후 결정



# 새 Rule 추가 절차
1. 다음 이름 규칙으로 파일 생성: `{priority}-{id}.md` (예: `70-performance.md`)
2. 프론트매터 필수 5필드: `id`, `version`, `paths`(또는 생략=무조건), `priority`, `owner`
3. 데이터 의존 규칙은 `data/*.json` 참조만. 매핑 값을 rules에 복붙하지 않는다.
4. 변경 이력은 본 `_ownership.md` 하단에 한 줄 기록.



# 변경 이력
- 2026-04-17 : rules/ 디렉토리 초기 생성
- (port) : CritterGym 포트 — 책임자 맵을 포팅된 규칙 (80, 85, _ownership) 으로 한정, DS 전용 규칙 항목 제거
