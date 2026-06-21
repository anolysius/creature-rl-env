# Git 워크플로 — trunk-based + 단방향 sink 옵션

본 문서는 CritterGym git 머지 흐름의 narrative. 정책 SSOT 는 [`.claude/rules/85-git-policy.md`](../../../.claude/rules/85-git-policy.md), prefix 화이트리스트 SSOT 는 [`.claude/data/git-branch-prefixes.json`](../../../.claude/data/git-branch-prefixes.json).

## 기본 모델 — trunk-based

PRIMARY 모델은 단순하다: `feature/* · fix/* · hotfix/* · chore/* · docs/*` → PR → `main` (trunk).

```
    (source: 작업물)                       (trunk)
feature/*  ──┬────► PR ────────────────► main
fix/*      ──┤                             ▲
hotfix/*   ──┤                             │
chore/*    ──┤                             │ (trunk sync)
docs/*     ──┴───────────────────────────►┘ main → feature/* (merge 또는 rebase)
```

작업물은 source 브랜치에서 시작해 PR 을 거쳐 trunk 로 흐른다. trunk 는 source 로 sync 될 수 있다 (`main → feature/*`).

## (옵션) 단방향 sink — CI 통합 브랜치를 추가할 경우

나중에 CI 통합/스테이징 환경을 위한 통합 브랜치 (예: `qa/*`) 를 도입한다면, 그것은 **단방향 sink** 로 운용해야 한다. 작업물 → sink 만 흐를 수 있고, sink → 다른 어디로도 흐르지 않는다.

> **포팅 기본값**: shipped `git-branch-prefixes.json` 의 sink 카테고리는 **비어 있다**. 아래 sink 패턴은 통합 브랜치를 실제로 추가할 때만 활성화된다.

### 왜 단방향인가

통합 환경은 여러 작업이 모이는 곳이라, 다른 작업자의 미완성 변경·환경 디버그 commit·통합 전용 patch 가 섞인다. 통합 브랜치를 "트렁크의 mirror" 로 오인해 sync source 로 쓰면, 그 오염이 feature 브랜치로 역류해 PR diff 를 더럽힌다.

**예시 오염 패턴** (통합 브랜치를 `qa/*` 라 가정):

```
Merge branch 'qa/global' into feature/some-work
Merge branch 'qa/kr'    into feature/some-work
```

한 feature 브랜치가 통합 브랜치 양쪽을 흡수하면, 통합 환경에 모인 잡다한 변경이 같이 묻어들어온다.

**근본 원인**: 통합 브랜치의 본질이 "통합 검증 스냅샷" 인데, 이를 sync source 로 오인한 데서 발생.

**해결**: 통합 브랜치는 단방향 sink. 작업물 → sink 만 흐르고, sink → 어디로도 안 흐른다.

### sink 다이어그램

```
    (source: 작업물)                      (trunk)
feature/*  ──┬────► PR ────────────────► main
fix/*      ──┤                             │
hotfix/*   ──┤                             │ (sink 방향이라 합법)
chore/*    ──┤                             ▼
docs/*     ──┤                          qa/*  (통합 브랜치, 옵션)
             │                          ◄──────── (main → qa, sink 방향)
             │ 통합 검증                  (sink)
             ▼
         qa/* (sink)

         ❌ qa/* → 어떤 브랜치도 (역머지 금지)
         ✅ cherry-pick (-x) 만 escape hatch
```

**두 sink 는 서로 독립** — `main` 도 sink, `qa/*` 도 sink. source 가 양쪽에 각각 흐른다. 통합 검증과 main PR 은 병렬·독립이며, 코드 흐름은 별개다.

## 합법한 머지 흐름

(통합 sink 를 도입한 경우 기준. sink 미사용 시 trunk 행만 유효)

| from → to | 합법성 | 빈도 | 설명 |
|---|---|---|---|
| `feature/* → main` (PR) | ✅ | 자주 | source → trunk |
| `fix/*, hotfix/*, chore/*, docs/* → main` (PR) | ✅ | 다양 | source → trunk |
| `main → feature/*` | ✅ | 자주 | trunk sync (merge 또는 rebase) |
| `feature/* → qa/*` | ✅ | (옵션) | source → sink, 통합 검증 |
| `fix/*, hotfix/* → qa/*` | ✅ | (옵션) | source → sink |
| `main → qa/*` | ✅ | (옵션) | sink 발산 방지 sync (sink 방향) |
| **`qa/* → 어떤 브랜치도`** | ❌ **차단** | 0 | sink 위반 |
| **`qa/* → qa/*`** | ❌ **차단** | 0 | sink 끼리 cross 금지 |
| cherry-pick (`-x`) `qa/*` → `main` | ✅ | 예외 | escape hatch |

## Branch prefix 화이트리스트

| 카테고리 | prefix | 예시 |
|---|---|---|
| **source** (작업물) | `feature/`, `fix/`, `hotfix/`, `chore/`, `docs/` | `feature/reward-shaping`, `fix/reset-seed` |
| **sink** (통합, 옵션 — shipped 기본 비어 있음) | `qa/` | `qa/integration` |
| **trunk** | `main` | `main` |
| **special** (예외) | `backup/`, `renovate/`, `archive/` | `backup/temp`, `renovate/configure` |
| **forbidden** (정규화 대상) | `qa-*` (slash 없는), `dev`, 단어 단독 | `qa-reset-fix` (→ `fix/reset-qa`) |

신규 브랜치가 forbidden 패턴 매칭 시 push 단계에서 차단된다.

## 방어 — git-policy-guard.py (Claude Code PreToolUse)

본 포트에 포함된 enforcement 는 **Claude Code 의 PreToolUse hook 한 종류**다: [`git-policy-guard.py`](../../../.claude/hooks/git-policy-guard.py). Claude 가 git 명령을 호출하기 직전에 정책을 검사한다.

> **로컬 git hooks (`scripts/githooks/*` — pre-merge-commit / pre-commit / pre-push)** 는 **본 포트에 포함되지 않았다 (optional, not included in this port)**. 이들은 CLI/GUI tool 까지 cover 하는 서버측 아닌 추가 layer 였으나, 현재 포트는 `git-policy-guard.py` (Claude Code 명령 표면) 만 보장한다. 필요하면 후속으로 로컬 hook layer 를 추가할 수 있다.

### git-policy-guard.py 가 차단하는 패턴

`.claude/hooks/git-policy-guard.py` (PreToolUse Bash matcher) 가 다음을 차단한다 (sink 활성 시):

| 명령 | 처리 |
|---|---|
| `git merge qa/*` (현재 브랜치가 qa/* 가 아닐 때) | BLOCK |
| `git pull qa/*` | BLOCK |
| `git push origin <forbidden-prefix>` | BLOCK |
| `git cherry-pick -x <sink-commit>` | ✅ 통과 (escape) |

위반 시 stderr 에 정책 인용 + 해결책 + OVERRIDE 안내가 출력된다.

## Escape hatch — cherry-pick

sink 에서 발견한 진짜 hotfix 가 main 으로 가야 할 때:

```bash
git checkout main
git cherry-pick -x <sink-commit-sha>
# commit message 자동 첨부: "(cherry picked from commit <sha>)"
```

`-x` 플래그 강제 — origin commit 추적 가능. git-policy-guard.py 는 cherry-pick 을 escape 로 인식한다.

## OVERRIDE — 사용자 명시 우회

정책상 차단되지만 우회가 정당한 경우 (긴급 상황, 정책 자체 갱신 작업 등):

```bash
HARNESS_GIT_POLICY_OVERRIDE=1 git merge qa/integration
HARNESS_GIT_POLICY_OVERRIDE=1 git push origin qa-test
```

stderr 에 경고 + 통과. 사용 후 환경변수 비활성 권장.

## 한계

`git-policy-guard.py` 는 **Claude Code 가 호출하는 git 명령만** cover 한다. 사람이 CLI/GUI 로 직접 머지하면 이 hook 은 발동하지 않는다:

| 우회 방법 | 효과 |
|---|---|
| 사람이 CLI/GUI 로 직접 `git merge` | git-policy-guard.py 미발동 (Claude 명령이 아님) |
| `HARNESS_GIT_POLICY_OVERRIDE=1` | 명시적 우회 |
| 로컬 githooks 미포함 | CLI/GUI tool surface 미보호 (본 포트 한계) |

진짜 강제는 **GitHub branch protection (서버측)** 만 보장한다. 그건 별도 task 영역이다.

## 본 정책이 다루지 않는 것 (out of scope)

| 항목 | 처리 |
|---|---|
| PR 미경유 main 직행 금지 | 별도 task (팀 공유 후) |
| GitHub branch protection (서버측) | 별도 task |
| merge commit vs squash | 현재 운용 유지 |
| rebase vs merge sync 권장 | contributor guide 영역 |
| 로컬 githooks layer (pre-merge-commit / pre-commit / pre-push) | optional, 본 포트 미포함 — 필요 시 후속 추가 |
| Branch lifetime SLA / stale 정리 | 별도 task |

## 관련 문서

- 정책 SSOT (rule): [`.claude/rules/85-git-policy.md`](../../../.claude/rules/85-git-policy.md)
- prefix 화이트리스트 SSOT: [`.claude/data/git-branch-prefixes.json`](../../../.claude/data/git-branch-prefixes.json)
- AI hook: [`.claude/hooks/git-policy-guard.py`](../../../.claude/hooks/git-policy-guard.py)
- task lifecycle 부모: [`rules/80-task-lifecycle.md`](../../../.claude/rules/80-task-lifecycle.md) §A.1 단방향 전진
</content>
