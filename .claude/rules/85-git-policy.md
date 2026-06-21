---
id: 85-git-policy
domain: lifecycle
version: 1.0.0
paths:
  - "**/*"
priority: 85
owner: process-owner
related:
  - rules/80-task-lifecycle.md
  - data/git-branch-prefixes.json
  - hooks/git-policy-guard.py
  - hooks/_lib/git_policy.py
last_reviewed: 2026-05-08
title: "Git 단방향 워크플로 정책 (trunk 우선 + prefix 화이트리스트 + 선택적 qa/* sink)"
tags:
  - git
  - branching
  - lifecycle
  - process
---

# Git 단방향 워크플로 정책

본 규칙은 [rules/80](80-task-lifecycle.md) §A.1 단방향 전진의 **git layer 구체화**. paths `**/*` (무조건 로드).

## 핵심 명제 (trunk 모델)

> **PRIMARY 모델: 작업물 (`feature/*`, `fix/*`, `hotfix/*`, `chore/*`, `docs/*`) → PR → `main` (trunk).** solo OSS 기본형 — 별도 integration 브랜치 없음 (`git-branch-prefixes.json` 의 sink 는 기본 비어 있음).

**OPTIONAL — integration 브랜치 (`qa/*`) 추가 시**:

> **나중에 `qa/*` 같은 integration 브랜치를 추가한다면, 그것은 단방향 sink 로 다룬다. 작업물만이 `qa/*` 로 흐를 수 있고, `qa/*` 에서 다른 어떤 브랜치로도 흐를 수 없다.**

이 경우 두 sink (`main`, `qa/*`) 는 서로 독립. 작업물이 양쪽에 각각 흐름:
- (`feature → qa/*`) — 통합 검증
- (`feature → PR → main`) — 코드 리뷰 + 머지

병렬 독립. integration 통과는 main 머지의 선행 조건일 뿐, 코드 흐름은 별개.

## 합법한 머지 흐름

PRIMARY (trunk) 행은 항상 적용. `qa/*` sink 행은 integration 브랜치를 도입했을 때만 의미 있음.

| from → to | 합법성 | 빈도 | 비고 |
|---|---|---|---|
| `feature/* → main` (PR) | ✅ | 자주 | source → trunk (PRIMARY) |
| `fix/*, hotfix/*, chore/*, docs/* → main` (PR) | ✅ | 다양 | source → trunk (PRIMARY) |
| `main → feature/*` | ✅ | 자주 | trunk sync (merge 또는 rebase) |
| `feature/* → qa/*` | ✅ (sink 도입 시) | — | source → sink (통합 검증) |
| `fix/* → qa/*` | ✅ (sink 도입 시) | — | source → sink |
| `hotfix/* → qa/*` | ✅ (sink 도입 시) | — | source → sink |
| `main → qa/*` | ✅ (sink 도입 시) | — | trunk → sink (sink 발산 방지 sync) |
| **`qa/* → 어떤 브랜치도`** | ❌ **차단** | 0 | sink 위반 |
| **`qa/* → qa/*`** | ❌ **차단** | 0 | sink 끼리 cross 금지 |
| cherry-pick (`-x`) `qa/*` → `main` | ✅ | 예외 | escape hatch |

## Branch prefix 화이트리스트

SSOT — [`.claude/data/git-branch-prefixes.json`](../data/git-branch-prefixes.json).

| 카테고리 | prefix | 머지 source 가능? | 머지 target 가능? |
|---|---|---|---|
| **source** (작업물) | `feature/`, `fix/`, `hotfix/`, `chore/`, `docs/` | ✅ | ✅ (PR 통해) |
| **sink** (통합, optional) | `qa/` | ❌ | ✅ |
| **trunk** | `main` | ⚠️ (sync 만) | ✅ (PR 통해) |
| **special** (예외) | `backup/`, `renovate/`, `archive/` | (검증 skip) | (검증 skip) |
| **forbidden** (정규화 대상) | `qa-*` (slash 없는), `dev`, 단어 단독 | — | — |

기본값: sink 는 비어 있음 (trunk-only). `qa/` 는 integration 브랜치를 도입할 때만 등록.

신규 브랜치 생성 시 forbidden 패턴 매칭 → 차단 (선택적 로컬 git hook + Claude Code PreToolUse hook).

## AI 행동 규칙 (Claude Code PreToolUse)

[`.claude/hooks/git-policy-guard.py`](../hooks/git-policy-guard.py) 가 PreToolUse Bash matcher 에서 다음 패턴 차단:

| 명령 패턴 | 처리 |
|---|---|
| `git merge qa/*` (현재 브랜치가 qa/* 가 아닐 때) | **BLOCK** — sink 위반 |
| `git pull qa/*` | **BLOCK** — sink 위반 |
| `git checkout <feature>; git merge qa/*` | **BLOCK** — 현재 브랜치 검사 |
| `git push origin <forbidden-prefix>` | **BLOCK** — prefix 위반 |
| `git cherry-pick -x <qa-commit>` | ✅ 통과 — escape hatch |
| `git merge feature/x` (현재 qa/* 일 때) | ✅ 통과 — source → sink |
| `git merge main` (현재 qa/* 또는 feature/* 일 때) | ✅ 통과 — trunk sync |

**OVERRIDE**: `HARNESS_GIT_POLICY_OVERRIDE=1` env 시 hook 통과 + stderr 경고. 사용자 명시 의도로 정책 우회.

추가로 `git-policy-guard.py` 와 짝을 이루는 커밋 시점 가드 ([`harness-commit-guard.py`](../hooks/harness-commit-guard.py) + [`harness-commit-intent-record.py`](../hooks/harness-commit-intent-record.py)) 가 Claude Code 의 commit 의도를 기록·검사한다.

## 로컬 git hook 강제 (optional — 이 포트에 미포함)

아래 로컬 git hook (`pre-push` / `pre-merge-commit` / `pre-commit` / `install.sh`) 은 **이 포트에 포함되지 않았다**. git-policy CONCEPT 만 유지한다. 동일한 BLOCK 의미는 이 포트에 **포함된** Claude Code PreToolUse 강제 ([`git-policy-guard.py`](../hooks/git-policy-guard.py)) 가 담당한다. 나중에 사람이 실행하는 git (CLI / IDE / GUI) 까지 cover 하려면 아래 패턴으로 로컬 git hook 을 추가할 수 있다 (optional).

검증 의도 (참고용 — 파일 미포함):

1. push 되는 history 안에 `Merge branch 'qa/*' into <not-qa>` 머지 commit 검출 → 차단
2. push 되는 신규 브랜치 prefix 검사 (forbidden 패턴) → 차단
3. `HARNESS_GIT_POLICY_OVERRIDE=1` env 시 통과 + 경고

git 의 hook fire 규칙이 비대칭이라 로컬 git hook 을 추가한다면 두 단계가 보완하는 형태가 된다 — clean merge 는 `pre-merge-commit`, 충돌 resolution + commit / `git merge --squash` + commit 은 `pre-commit` (git 공식: "If the merge cannot be carried out automatically, ... [pre-merge-commit] hook will not be executed, but the 'pre-commit' hook will").

**방어 정합성** (현 포트 기준):

| Layer | 강제 | 포함 여부 | 시점 | 대상 |
|---|---|---|---|---|
| 1 | Claude Code PreToolUse (`git-policy-guard.py`) | ✅ 포함 | Claude Code git 명령 직전 | Claude 가 부르는 명령 |
| 2 | 로컬 git hook (`pre-merge-commit` / `pre-commit`) | ⛔ 미포함 (optional) | 로컬 commit 직전 | CLI + GUI tool |
| 3 | 로컬 git hook (`pre-push`) | ⛔ 미포함 (optional) | git push 시점 | history 검사 (최종 방어선) |

**한계** — 로컬 git hook 을 추가하더라도 `git commit --no-verify` / `git merge --no-verify` / `git push --no-verify` / `git config --unset core.hooksPath` 등으로 우회 가능. **`rebase` 도중 충돌 resolution + `git rebase --continue`** 는 hook fire 패턴이 git 버전별 차이 가능. 서버측 강제 (GitHub branch protection) 는 별도 task.

## Escape hatch — cherry-pick

(integration 브랜치 도입 시) `qa/*` 에서 발견한 진짜 hotfix 가 main 으로 가야 할 때:

```bash
git checkout main
git cherry-pick -x <qa-commit-sha>
# commit message 자동 첨부: "(cherry picked from commit <sha>)"
```

`-x` 플래그 강제 — origin commit 추적 가능. AI hook 은 cherry-pick 패턴을 escape hatch 로 인식해 통과시킴.

## 위반 시 처리

hook 위반 시 stderr 출력 형식:

```
[git-policy BLOCK] qa/* sink 위반 — qa/integration → feature/x

본 정책 (rules/85): qa/* 는 단방향 sink.
  허용: feature/* → qa/*, main → qa/*
  금지: qa/* → 어떤 브랜치도

해결책:
  1. 정말 필요한 commit 만 cherry-pick: git cherry-pick -x <qa-commit>
  2. 사용자 명시 OVERRIDE: HARNESS_GIT_POLICY_OVERRIDE=1 git merge ...
  3. 이번 변경의 의도가 main 에 들어가야 한다면 새 feature 브랜치에서 PR

세부: docs/harness/explanation/git-branching-model.md
```

## 본 규칙이 다루지 않는 것 (out of scope)

| 항목 | 처리 |
|---|---|
| PR 미경유 main 직행 금지 (`Merge branch '<x>'` main) | 별도 task (팀 공유 후) |
| GitHub branch protection (서버측 강제) | 별도 task |
| merge commit vs squash 정책 | 현재 운용 유지 |
| rebase vs merge sync 권장 | contributor guide 영역 |
| force-push 정책 | settings.deny 이미 적용 |
| Branch lifetime SLA / stale 정리 | 별도 task |
| 기존 브랜치 정규화 (`qa-render-fix` → `fix/render-qa` 등) | 별도 마이그 task |

## 검증 메커니즘

| 검증 | 시점 | 포함 여부 | 대상 |
|---|---|---|---|
| `git-policy-guard.py` | PreToolUse Bash | ✅ 포함 | Claude Code 가 실행하는 git 명령 |
| `harness-commit-guard.py` + `harness-commit-intent-record.py` | PreToolUse / 기록 | ✅ 포함 | Claude Code commit 의도 기록·검사 |
| `_lib/git_policy.py` 단위 테스트 | CI / 로컬 (`python3 -m unittest`) | ✅ 포함 | 분류·파싱·위반 판정 라이브러리 |
| 로컬 git hook (`pre-merge-commit` / `pre-commit` / `pre-push`) | 로컬 commit / push 직전 | ⛔ 미포함 (optional) | CLI + GUI tool, 사람이 실행하는 git |
| frontmatter `domain:` 검사 | PostToolUse | (project-specific hook, if configured) | 본 rule 의 `domain: lifecycle` 통과 |
| broken link 검사 | PostToolUse | (project-specific hook, if configured) | 사람용 문서 broken link 0 |

## 변경 이력

| 일자 | 버전 | 변경 |
|---|---|---|
| 2026-05-08 | 1.0.0 | 초안. trunk 우선 (source → PR → main) + 선택적 qa/* sink + prefix 화이트리스트 + Claude Code AI hook. out-of-scope 7건 명시. |
| 2026-05-08 | 1.1.0 | (origin 하네스) 로컬 git hook 단계 확장 — clean merge 시 commit 생성 직전 차단, Tier 1 (MERGE_MSG) + Tier 2 (MERGE_HEAD + name-rev qa/* refs) 2단 추출, worktree 안전 (`git rev-parse --git-path`). 본 포트에는 로컬 git hook 미포함 — Claude Code PreToolUse 강제만 유지. |
| 2026-05-08 | 1.2.0 | (origin 하네스) 충돌 resolution + commit / `--squash` 경로까지 로컬 git hook cover. 본 포트에는 로컬 git hook 미포함 (optional). 도그푸딩 발견 학습 사례. |
| (port) | 1.3.0 | CritterGym 포트 적응 — PRIMARY 모델을 trunk (source → PR → main) 로 재구성, qa/* sink 는 integration 브랜치 도입 시의 OPTIONAL 패턴으로 강등 (기본 sink 비어 있음). 로컬 git hook (`pre-push`/`pre-merge-commit`/`pre-commit`/`install.sh`) 미포함 명시 — Claude Code PreToolUse (`git-policy-guard.py`) 만 강제. OVERRIDE 환경변수 `SAZO_GIT_POLICY_OVERRIDE` → `HARNESS_GIT_POLICY_OVERRIDE`. 커머스·환경 specifics 제거. |
