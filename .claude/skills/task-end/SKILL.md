---
name: task-end
description: |
  작업 완료 후 결과 보고서 + qa-checklist 생성 + evergreen 흡수 + CHANGELOG.md
  1줄 auto-append + active→archive 이동 (NN- prefix 자동 부여, ADR-0014).
  사용자가 "리포트", "작업 완료", "QA 체크리스트", "/task-end" 호출 시 트리거.
argument-hint: ""
context: inline
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
domain: lifecycle
---

# Task End (작업 마감 + archive 이동)

작업 완료 시 다음을 자동 수행한다 (다이어그램 단계 7):

1. report.md 생성 (계획 대비 실적 + 흡수 trace)
2. qa-checklist.md 생성 (영향도 분석)
3. **evergreen 흡수** — 살아있는 결정·정보를 explanation/how-to/reference/ADR 로 추출
4. **CHANGELOG.md 1줄 auto-append**
5. **active → archive 이동** (NN- prefix 자동 부여)

## 선결 조건 (rules/80 단방향 전진)

본 skill 은 **L3 (`/task-review`) APPROVED 후에만 호출**. 순서 강제 — master 9-step 의 `6. /task-review → 7. /task-end` 흐름.

이유:
- `/task-end` 는 active → archive 이동 (`git mv`) 이 포함됨 — 사실상 비가역 단계
- L3 가 BLOCK 일 때 archive 이동 후라면 역방향 mv 필요 → `rules/80 A.1 단방향 전진` 위반
- L3 미수행 / 미통과 후 archive 이동 시 BLOCK 권장 (Phase 5 strict 격상 시 강제)

**예외**: read-only QA / docs-only task 등 G2 acceptance 가 산출물 존재 여부로 자동 충족되는 경우, `/task-verify` 는 skip 가능. 단 `/task-review` 는 skip 금지 — diff 검토는 필수.

## 입력

```
/task-end
```

별도 인자 없이 호출. 현재 plan.md frontmatter + git diff + 대화 컨텍스트에서 정보 자동 수집.

## 문서 경로 (Diátaxis 구조 — ADR-0014)

```
Before (active):
docs/_active/[<initiative>/]<slug>/
├── plan.md          ← /task-start 가 생성
└── report.md        ← 본 skill 이 생성

After /task-end (archive):
docs/_archive/{YYYY-Q}/<initiative>/NN-<slug>/    ← 이니셔티브 안 (NN- prefix 자동)
docs/_archive/{YYYY-Q}/<slug>/                    ← 단발 (prefix 없음)
```

## 수행 절차

### 1. plan 식별 + 변경사항 수집

- `docs/_active/**/plan.md` 중 frontmatter `slug` 가 본 task 와 매칭하는 것 찾기
- frontmatter 에서 `initiative`, `slug`, `domains`, `scope_paths` 읽기
- `git diff --stat HEAD~{N}` 등으로 변경 파일 수집 (커밋 전이면 unstaged/staged)

### 2. report.md 생성

`docs/_active/[<initiative>/]<slug>/report.md` 작성:

```yaml
---
slug: {slug}
initiative: {name|null}
status: completed
ended: YYYY-MM-DD
extracted_to:                 # ⭐ 흡수 trace (필수)
  - docs/{domain}/explanation/...
  - docs/{domain}/how-to/...
  - docs/decisions/00NN-...
changelog_entry: docs/CHANGELOG.md#L{n}
---
```

본문 섹션:
```markdown
# {제목} — 결과 보고서

## 요약 (수치 표)
## 계획 대비 실적 (✅/⚠️/❌)
## 변경 파일 상세 (신규/수정)
## 발견된 이슈 (심각도)
## 흡수처 매핑 (extracted_to 상세)
## 타입 체크 / 빌드 결과
```

### 3. qa-checklist.md 생성

`docs/_active/[<initiative>/]<slug>/qa-checklist.md` 작성 (영향도 + 회귀 + 엣지 케이스).

### 4. ⭐ Evergreen 흡수 검사 (핵심)

본 task 가 살아있는 결정·정보를 만들었는가? 다음 4가지 질문:

1. **새 설계 narrative** 가 생성되었나? → `docs/{domain}/explanation/<topic>.md`
2. **새 절차/runbook** 이 생성되었나? → `docs/{domain}/how-to/<topic>.md`
3. **새 명세/표/체크리스트** 가 생성되었나? → `docs/{domain}/reference/<topic>.md`
4. **새 결정 (ADR-worthy)** 이 있나? → `docs/decisions/00NN-<title>.md`

각 답이 yes 면:
- 해당 evergreen 파일을 *별도로 작성*하거나, plan/report 본문 일부를 발췌해 git mv 또는 새 파일로 추출
- frontmatter `extracted_to:` 에 경로 명시

#### Mode 별 분기 (rules/80 §F mode tiering)

| Mode | Evergreen 흡수 | INITIATIVE.md 갱신 |
|---|---|---|
| 🟢 quick-fix | **skip 가능** (4가지 질문 모두 no) — 단 사용자 명시 ADR 가치 발견 시 작성 | 1줄 sequence 추가 또는 lifecycle 우회 표기 |
| 🟡 standard | 4가지 질문 검사 (현재 정책) | NN- prefix + sequence 추가 + extracted_to 누적 |
| 🔴 heavy | standard + cross-vertical 영향 평가 의무 | standard + 후속 vertical 영향 표 |

quick-fix 의 archive 이동도 무조건 수행 (lifecycle invariant) — 단 minimal report.md (요약 표 + 한 줄).

**Invariant**: archive 안의 task 는 다른 task 를 참조하지 않는다. cross-task 의존성은 evergreen 으로만. 이 규칙이 깨지면 흡수 부실 → 추가 추출.

### 5. CHANGELOG.md 1줄 auto-append (모든 mode 강제 — rules/80 §F.5 audit minimum)

`docs/CHANGELOG.md` 의 `## {YYYY}-Q{N}` 섹션 아래 (없으면 신규 생성), Keep a Changelog 규약대로 4 카테고리 (Added/Changed/Fixed/Removed) 중 하나 선택. **mode 별 template 분기**:

#### 🟢 quick-fix mode

```markdown
- **YYYY-MM-DD** — `<slug>` (quick-fix): <한 줄 요약>. <commit hash>.
```

archive 링크 생략 가능 (단 archive 폴더 자체는 invariant 으로 생성). minimal entry — audit trace 의 minimum.

#### 🟡 standard mode (현재 default)

```markdown
- **YYYY-MM-DD** — [<slug>](_archive/{YYYY-Q}/[<initiative>/]NN-<slug>/): 한 줄 요약. 핵심 수치. 추출처 ADR-00NN, evergreen 링크.
```

#### 🔴 heavy mode

```markdown
- **YYYY-MM-DD** — [<slug>](_archive/{YYYY-Q}/[<initiative>/]NN-<slug>/): standard narrative + cross-vertical 영향 표.
```

모든 mode 에서 entry 1줄 minimum **무조건** 강제 (rules/80 §F.5 audit trail floor).

### 5.5. ✅ 종료 Gate Summary Card + 사용자 confirm (rules/80 §H)

archive 이동(### 6, 비가역 `git mv`)은 **사람 hard 게이트**다. 직전에 **종료 카드**를 제시하고 confirm 받는다. 자유 텍스트 "종료할까요?" 금지 — 긴 컨텍스트에서 무엇을 확정하는지 상실 방지.

1. helper 로 종료 카드 조립 — 소분류(`--row`)의 `impact` 자리에 plan 대비(일치/편차) 권장, `--results` 는 G1 의 **모든 AC** 를 키로. `--proposals-file` 로 retro 제안 큐 surface (rules/80 §I):
   ```bash
   python3 .claude/skills/_lib/gate_summary_card.py end \
     --plan docs/_active/<slug>/plan.md \
     --qa   docs/_active/<slug>/qa-checklist.md \
     --row '{"domain":"<도메인>","sub":"<한 일 한 줄>","impact":"일치|➕편차(흡수)"}' \
     --results '{"AC1":"pass","AC2":"pass","AC3":"unverified"}' \
     --proposals-file .claude/retro/proposals.md
   ```
   `results` status enum: `pass`(✅) / `unverified`(⚠️ 미검증) / `fail`(❌ 실패).
2. stdout 의 카드(헤더 앵커 / 승인 대상 1줄 / 한 일 표 / ✅ acceptance 결과 1:1 대조 / **🔁 제안된 개선**(pending 있을 때) / 명시 옵션)를 그대로 출력.
3. 사용자 `[1] 종료` → ### 6 archive 이동 진행. `[2] 보류` → 미검증/실패 항목 먼저 처리 (archive 이동 중단).
4. **proposals 결재 (rules/80 §I)** — "🔁 제안된 개선" 블록이 있으면 사용자가 항목별 결재. 결과를 큐에 반영:
   ```bash
   python3 .claude/skills/_lib/retro_proposals.py set-status \
     --file .claude/retro/proposals.md --id <id> --status seeded|dismissed|deferred
   ```
   `seeded` 는 후속 task 로 (다음 `/task-start` scope). **자동 적용 금지 — 사람 결재만** (§I.1 불변식).

> 주인공(acceptance 결과)은 G1 카드에서 freeze 한 acceptance 를 그대로 다시 띄워 ✅/⚠️/❌ 로 대조 — "시작 때 약속한 것 = 끝낼 때 확인하는 것" 을 닫는다. 결과 미지정 AC 는 helper 가 '미검증' + 경고로 표기 (1:1 대조 불완전 신호).

### 6. active → archive 이동 (NN- prefix 자동)

#### 6a. 이니셔티브 결정

- `initiative` frontmatter 가 있으면 → `docs/_archive/{YYYY-Q}/<initiative>/`
- 없으면 (단발) → `docs/_archive/{YYYY-Q}/`

#### 6b. NN- prefix 결정 (이니셔티브 있을 때만)

`docs/_archive/{YYYY-Q}/<initiative>/INITIATIVE.md` 의 sequence 표 또는 기존 폴더 `NN-` 들을 보고 다음 번호 할당:
- 첫 task: `01-`
- 기존 `01-` ~ `05-` 있으면: `06-`
- 2자리 zero-padded (`01-`, `02-` ... `99-`)

INITIATIVE.md 없으면 사용자에게 신규 생성 권유 (이니셔티브 narrative + sequence 표).

#### 6c. git mv 실행

```bash
git mv docs/_active/[<initiative>/]<slug>/ docs/_archive/{YYYY-Q}/<initiative>/NN-<slug>/
# 또는 단발이면
git mv docs/_active/<slug>/ docs/_archive/{YYYY-Q}/<slug>/
```

> **가드** ([`task-end-archive-guard.py`](../../hooks/task-end-archive-guard.py), PreToolUse Bash): archive 이동 시 (1) `NN-` prefix 충돌 (2) 기존 INITIATIVE.md 덮어쓰기 (3) 비어있지 않은 task 폴더 덮어쓰기 를 결정론적으로 BLOCK. 기존 `NN-` 들을 확인해 다음 빈 번호를 쓰고, INITIATIVE.md 는 append. 우회는 `HARNESS_ARCHIVE_GUARD_OVERRIDE=1`.

### 7. INITIATIVE.md 갱신 (해당 시)

이동 후 해당 이니셔티브의 INITIATIVE.md sequence 표에 본 task 1행 추가, `extracted_to` 누적.

### 8. 완료 안내

1. archive 경로 알림
2. CHANGELOG.md 라인 번호 알림
3. evergreen 흡수처 표 (extracted_to)
4. **다음 단계**: 사용자 검토 + commit + push (단계 8 — 사용자 수동)

> ⛔ **커밋·푸시는 본 skill 범위 밖.** task-end 는 **archive 이동 + CHANGELOG append 까지만** 수행한다. 종료 카드 `[1] 종료` 는 archive 이동 승인일 뿐 **커밋 승인이 아니다**. `git commit`/`git push` 는 **사용자가 별도로 명시 요청**할 때만 실행한다 (글로벌 지침 "Commit or push only when the user asks"). 무단 커밋은 [`harness-commit-guard.py`](../../hooks/harness-commit-guard.py) (PreToolUse Bash) 가 결정론 차단 — 직전 사용자 발화에 커밋 인가 신호가 없으면 BLOCK. 우회 `HARNESS_ALLOW_COMMIT=1`.
> 동작 주의: 인가는 **가장 최근 사용자 발화** 기준(매 발화 덮어쓰기). "커밋해줘" 후 다른 일반 발화가 끼면 인가가 false 로 갱신돼 차단되므로, 커밋·푸시는 사용자의 커밋 요청 발화에 **바로 이어서** 실행한다.

## 중요 원칙

- **선결 조건**: `/task-review` (L3) APPROVED 후에만 호출 — master 9-step 6 → 7 순서 강제
- **흡수 규율 강제**: report.md 의 `extracted_to:` 비어 있으면 사용자에게 "정말 살아있는 결정 없나?" 재확인. archive 가 evergreen 으로 부터 단절되어야 함
- frontmatter 에서 initiative 읽기 — slug 만 있으면 단발
- INITIATIVE.md 없는 이니셔티브 → 사용자 신규 생성 prompt
- G2 통과 후 호출 권장 (`/task-verify` PASS 후) — read-only / docs-only 는 skip 가능
- commit 은 사용자 수동 — 본 skill 은 git mv 까지만. **커밋·푸시는 사용자 명시 요청 시에만** (harness-commit-guard.py 가 무단 커밋 BLOCK)

## 다이어그램 매핑

본 Skill 은 [process-diagram.md](../../../docs/harness/process-diagram.md) 의 **단계 7 작업 마감 + archive 이동**.
완료 후 단계 8 (사용자 검토 + 커밋 + 푸쉬) 사용자 수동.
