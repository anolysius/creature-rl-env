#!/usr/bin/env python3
"""
detect-review-profile.py — task-review skill 의 reviewer 라우팅 분기 결정.

3 profile (deterministic):
  code           — source 코드/스타일 변경 ≥1 → plan-reviewer + qa-verifier (default)
  docs-only      — 모든 변경 파일이 .md/.json/.txt/.yaml/docs/ 하위 + 코드/스타일 0 → plan-reviewer + qa-verifier
  harness-tooling — task_type=harness + .py/.sh/.json/.md ≥1 + 코드/스타일 0 → plan-reviewer + qa-verifier

reviewer 는 모든 profile 에서 @plan-reviewer + @qa-verifier (이 하네스가 보장하는
2 generic reviewer). 도메인 전용 reviewer agent 를 추가하면 PROFILE_REVIEWERS 에
매핑해 확장할 수 있다.

분류 룰 (priority 순):
  1. plan frontmatter manual `review_profile:` 명시 → 그대로 사용 (override)
  2. 변경 파일 모두 (.md ∪ .json ∪ .txt ∪ .yaml ∪ docs/) + 코드/스타일 0 → docs-only
  3. plan task_type=harness + (.py ∪ .sh ∪ .json ∪ .md) ≥1 + 코드/스타일 0 → harness-tooling
  4. else → code (default)

usage:
  python3 detect-review-profile.py <plan-path> [--diff-files file1 file2 ...]
  python3 detect-review-profile.py <plan-path>      # git diff HEAD 자동 사용

stdout (JSON):
  {"profile": "...", "reviewers": [...], "matched_rule": "...", "reasoning": "..."}
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

CODE_STYLE_EXTS = {".ts", ".tsx", ".js", ".jsx", ".css", ".scss", ".sass", ".less", ".vue", ".svelte"}
# 순수 docs ext (위치 무관 docs 분류)
PURE_DOCS_EXTS = {".md", ".txt"}
# 순수 harness ext (위치 무관 — docs/ 하위라도 harness)
PURE_HARNESS_EXTS = {".py", ".sh"}
# 위치 의존 ext (docs/ 하위 → docs, 외부 → harness)
AMBIGUOUS_EXTS = {".json", ".yaml", ".yml", ".toml"}

PROFILE_REVIEWERS = {
    "code": ["@plan-reviewer", "@qa-verifier"],
    "docs-only": ["@plan-reviewer", "@qa-verifier"],
    "harness-tooling": ["@plan-reviewer", "@qa-verifier"],
}


def parse_plan_frontmatter(plan_path: Path) -> dict:
    if not plan_path.exists():
        return {}
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        # simple key: value (no nested)
        match = re.match(r"^([\w_-]+):\s*(.*)$", line)
        if match:
            key, val = match.group(1), match.group(2).strip()
            fm[key] = val
        # scope_paths list (next lines starting with `  - `)
    # extract scope_paths list
    scope_match = re.search(r"^scope_paths:\s*\n((?:\s+-\s+.+\n)+)", m.group(1) + "\n", re.MULTILINE)
    if scope_match:
        items = re.findall(r"^\s+-\s+(.+)$", scope_match.group(1), re.MULTILINE)
        fm["scope_paths"] = [s.strip() for s in items]
    return fm


def get_git_diff_files(repo_root: Path) -> List[str]:
    """git diff HEAD --name-only — uncommitted + staged 변경 파일."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "HEAD", "--name-only"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
            return files
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def classify_files(files: List[str]) -> dict:
    """파일 목록을 카테고리 별 집계.

    분류 우선순위:
      1. CODE_STYLE_EXTS (.ts/.tsx/.js/.css/.scss/...) → code_style (위치 무관)
      2. PURE_HARNESS_EXTS (.py/.sh) → harness (위치 무관 — docs/ 하위라도 harness)
      3. PURE_DOCS_EXTS (.md/.txt) → docs (위치 무관)
      4. AMBIGUOUS_EXTS (.json/.yaml/.yml/.toml):
         - docs/ 하위 → docs
         - 외부 → harness
      5. 그 외 docs/ 하위 → docs
      6. else → other

    핵심 결정:
      - `.py` 는 위치 무관 harness (예: docs/.../scripts/measure.py 도 harness)
      - `.json` 은 위치별 분기 (docs/.../*.json = docs, .claude/data/*.json = harness)
    """
    code_style = []
    docs = []
    harness = []
    other = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        in_docs_dir = f.startswith("docs/")
        if ext in CODE_STYLE_EXTS:
            code_style.append(f)
        elif ext in PURE_HARNESS_EXTS:
            harness.append(f)
        elif ext in PURE_DOCS_EXTS:
            docs.append(f)
        elif ext in AMBIGUOUS_EXTS:
            if in_docs_dir:
                docs.append(f)
            else:
                harness.append(f)
        elif in_docs_dir:
            docs.append(f)
        else:
            other.append(f)
    return {"code_style": code_style, "docs": docs, "harness": harness, "other": other}


def detect_profile(
    plan_fm: dict,
    diff_files: List[str],
) -> Tuple[str, str, str]:
    """반환: (profile, matched_rule, reasoning)."""
    # Rule 1: manual override
    manual = plan_fm.get("review_profile", "").strip()
    if manual:
        if manual in PROFILE_REVIEWERS:
            return manual, "rule1_manual", f"plan frontmatter review_profile: {manual}"
        else:
            # invalid manual → fall through to auto detection
            pass

    classified = classify_files(diff_files)
    code_count = len(classified["code_style"])
    docs_count = len(classified["docs"])
    harness_count = len(classified["harness"])
    other_count = len(classified["other"])

    # Rule 2: docs-only — 모든 변경이 docs 분류 + 코드/스타일/harness/other 모두 0
    if code_count == 0 and harness_count == 0 and other_count == 0 and docs_count > 0:
        return "docs-only", "rule2_docs_only", f"docs ext only ({docs_count} files), 코드/스타일/harness 0"

    # Rule 3: harness-tooling — task_type=harness + harness ext ≥1 + 코드/스타일 0
    task_type = plan_fm.get("task_type", "").strip()
    if task_type == "harness" and code_count == 0 and harness_count > 0:
        return "harness-tooling", "rule3_harness_tooling", f"task_type=harness, harness ext {harness_count} files, 코드/스타일 0"

    # Rule 4: code (default)
    return "code", "rule4_code_default", f"코드/스타일 {code_count} files OR fallback"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_path")
    ap.add_argument("--diff-files", nargs="*", default=None, help="명시 파일 목록 (지정 X 시 git diff HEAD 자동)")
    ap.add_argument("--repo-root", default=None)
    args = ap.parse_args()

    plan_path = Path(args.plan_path).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else plan_path.parents[3] if len(plan_path.parents) >= 4 else Path.cwd()

    plan_fm = parse_plan_frontmatter(plan_path)
    if args.diff_files is not None:
        diff_files = args.diff_files
    else:
        diff_files = get_git_diff_files(repo_root)

    profile, rule, reasoning = detect_profile(plan_fm, diff_files)
    reviewers = PROFILE_REVIEWERS[profile]

    out = {
        "plan": str(plan_path.relative_to(repo_root)) if str(plan_path).startswith(str(repo_root)) else str(plan_path),
        "profile": profile,
        "reviewers": reviewers,
        "matched_rule": rule,
        "reasoning": reasoning,
        "diff_files_count": len(diff_files),
        "task_type": plan_fm.get("task_type", "(unset)"),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
