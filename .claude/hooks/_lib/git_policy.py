"""Git branch policy classification + intent parsing.

rules/85-git-policy.md 의 SSOT 구현. git-policy-guard.py (PreToolUse) 와
scripts/githooks/pre-push (로컬 git hook) 양쪽이 본 모듈 사용.

분류는 .claude/data/git-branch-prefixes.json 을 SSOT 로 함 — 본 모듈은 로직만.
"""
from __future__ import annotations

import json
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


BranchKind = Literal["source", "sink", "trunk", "special", "forbidden"]


def _project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3]


def load_prefixes(path: Path | None = None) -> dict:
    p = path or (_project_root() / ".claude/data/git-branch-prefixes.json")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def classify_branch(name: str, prefixes: dict | None = None) -> BranchKind:
    """branch 명을 5 카테고리로 분류.

    matching: 첫 / 로 split. main 은 slash 없는 단일 단어로 trunk 단독.
    forbidden_patterns 가 source/sink/trunk/special 보다 우선 (정규화 대상이라).
    """
    px = prefixes or load_prefixes()

    for pat in px.get("forbidden_patterns", []):
        if re.match(pat, name):
            return "forbidden"

    if name in px.get("trunk", []):
        return "trunk"

    if "/" in name:
        prefix = name.split("/", 1)[0]
        if prefix in px.get("source", []):
            return "source"
        if prefix in px.get("sink", []):
            return "sink"
        if prefix in px.get("special", []):
            return "special"

    return "forbidden"


@dataclass
class MergeIntent:
    """git merge / git pull 의 source ref."""
    source_ref: str
    raw: str


@dataclass
class PushIntent:
    """git push 의 target remote ref (refspec 의 dst)."""
    remote: str
    target_ref: str
    raw: str


@dataclass
class Violation:
    kind: Literal["sink_source", "forbidden_prefix"]
    detail: str
    suggestion: str


def _strip_remote(ref: str) -> str:
    """origin/feature/x → feature/x. tags/v1 → v1 같은 표준화."""
    parts = ref.split("/", 1)
    if len(parts) == 2 and parts[0] in ("origin", "upstream"):
        return parts[1]
    return ref


def parse_merge_intent(command: str) -> MergeIntent | None:
    """`git merge X` / `git merge --no-ff X` / `git pull X` 패턴 인식.

    `git pull` (인자 없음) 은 현재 upstream 머지 — source 가 명시 안 됐으니 None.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if len(tokens) < 2 or tokens[0] != "git":
        return None

    sub = tokens[1]
    if sub not in ("merge", "pull"):
        return None

    args = [t for t in tokens[2:] if not t.startswith("-")]

    if sub == "pull":
        if len(args) < 2:
            return None
        source = args[1]
    else:
        if not args:
            return None
        source = args[0]

    return MergeIntent(source_ref=_strip_remote(source), raw=command)


def parse_push_intent(command: str) -> PushIntent | None:
    """`git push origin <ref>` / `git push origin <local>:<remote>` 패턴 인식.

    `git push` 단독은 current branch 의 upstream 으로 push — None 반환 (target 명시 안 됨).
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if len(tokens) < 2 or tokens[0] != "git" or tokens[1] != "push":
        return None

    args = [t for t in tokens[2:] if not t.startswith("-")]
    if len(args) < 2:
        return None

    remote, refspec = args[0], args[1]
    target = refspec.split(":", 1)[1] if ":" in refspec else refspec
    return PushIntent(remote=remote, target_ref=_strip_remote(target), raw=command)


def parse_cherry_pick(command: str) -> bool:
    """`git cherry-pick` 패턴은 escape hatch — 통과."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    return len(tokens) >= 2 and tokens[0] == "git" and tokens[1] == "cherry-pick"


def is_violation(
    intent: MergeIntent | PushIntent,
    current_branch: str | None = None,
    prefixes: dict | None = None,
) -> Violation | None:
    """정책 위반 판정.

    - MergeIntent: source 가 sink kind 면 위반 (current_branch 가 sink 면 OK — qa 끼리 cross 만 별도)
    - PushIntent: target_ref 가 forbidden kind 면 위반
    """
    px = prefixes or load_prefixes()

    if isinstance(intent, MergeIntent):
        source_kind = classify_branch(intent.source_ref, px)
        if source_kind == "sink":
            current_kind = classify_branch(current_branch, px) if current_branch else None
            if current_kind == "sink":
                return Violation(
                    kind="sink_source",
                    detail=f"qa/* → qa/* cross 머지 ({intent.source_ref} → {current_branch})",
                    suggestion="qa 끼리 cross 금지. 필요한 commit 은 cherry-pick -x 으로.",
                )
            return Violation(
                kind="sink_source",
                detail=f"qa/* sink 위반 ({intent.source_ref} → {current_branch or '?'})",
                suggestion=(
                    "허용: feature/* → qa/*, main → qa/*. "
                    "필요한 commit 은 git cherry-pick -x <qa-commit> 로."
                ),
            )
        return None

    if isinstance(intent, PushIntent):
        target_kind = classify_branch(intent.target_ref, px)
        if target_kind == "forbidden":
            return Violation(
                kind="forbidden_prefix",
                detail=f"forbidden brand prefix push ({intent.target_ref})",
                suggestion=(
                    "허용 prefix: feature/, fix/, hotfix/, chore/, docs/ (작업물) / "
                    "qa/ (환경) / main (trunk). brand 정규화 후 재시도."
                ),
            )
        return None

    return None
