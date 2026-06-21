#!/usr/bin/env python3
"""
collect-rules80-metrics.py — rules/80 freeze 기간 메트릭 수집.

수집 항목 (deterministic):
  1. rules/80 churn — git log .claude/rules/80-task-lifecycle.md 의 minor commit count + 시간 stamp
  2. lifecycle metrics — .claude/.session-log/*.json 의 L1/L2/L3 round + no-progress + 토큰 추정
  3. task-level metrics — docs/_archive/{YYYY-Q}/<initiative>/ 의 completed task count + effort (started↔ended)
  4. threshold violations — rules/80 D 의 200k tokens / 10+ agents / L2 max 5

usage:
  python3 collect-rules80-metrics.py [--output PATH] [--initiative NAME]

stdout: 사람용 표. JSON 결과는 --output (default: _artifacts/baseline-metrics.json).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parents[4]
RULES_FILE = REPO_ROOT / ".claude" / "rules" / "80-task-lifecycle.md"
SESSION_LOG_DIR = REPO_ROOT / ".claude" / ".session-log"
ARCHIVE_DIR = REPO_ROOT / "docs" / "_archive"

# 토큰 추정 상수 (실제 Anthropic API 응답 추출은 향후 향상)
SONNET_TOKENS_AVG = 5000
HAIKU_TOKENS_AVG = 3000
OPUS_TOKENS_AVG = 10000

# 임계값 (rules/80 §D)
THRESHOLD_TOKENS = 200_000
THRESHOLD_AGENT_CALLS = 10
THRESHOLD_L2_OUTER = 5


def collect_churn() -> dict:
    """git log 로 rules/80 의 변경 빈도 측정."""
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", "--oneline", "--", str(RULES_FILE.relative_to(REPO_ROOT))],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return {"error": f"git log rc={result.returncode}", "commits": []}
        commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return {
            "file": str(RULES_FILE.relative_to(REPO_ROOT)),
            "total_commits": len(commits),
            "commits": commits[:20],  # latest 20
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"error": f"{type(e).__name__}: {e}", "commits": []}


def collect_freeze_status() -> dict:
    """rules/80 frontmatter 의 freeze_until + 현재 freeze 위반 여부."""
    if not RULES_FILE.exists():
        return {"freeze_until": None, "violations": []}
    text = RULES_FILE.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {"freeze_until": None, "violations": []}
    fm = m.group(1)
    freeze_match = re.search(r"^freeze_until:\s*[\"']?([0-9-]+)[\"']?\s*$", fm, re.MULTILINE)
    freeze_until = freeze_match.group(1) if freeze_match else None

    # freeze_until 명시 후 commit 0 검증 (freeze_marker 추가 commit 자체 제외 — 본 정밀화 후속 task)
    violations = []
    reason_match = re.search(r"^freeze_reason:\s*[\"']?(.*?)[\"']?\s*$", fm, re.MULTILINE)
    return {
        "freeze_until": freeze_until,
        "freeze_reason": reason_match.group(1) if reason_match else None,
        "violations": violations,
    }


def collect_lifecycle_metrics() -> dict:
    """`.session-log/*.json` 에서 L1/L2/L3 round + no-progress + 토큰 추정."""
    if not SESSION_LOG_DIR.is_dir():
        return {"sessions": [], "aggregate": {"l1_rounds": 0, "l2_iterations": 0, "l3_rounds": 0, "no_progress": 0}}

    sessions = []
    for log_file in sorted(SESSION_LOG_DIR.glob("*.json")):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({"date": log_file.stem, "summary": _summarize_session(data)})
        except (OSError, json.JSONDecodeError) as e:
            sessions.append({"date": log_file.stem, "error": f"{type(e).__name__}: {e}"})

    aggregate = {
        "l1_rounds": sum(s.get("summary", {}).get("l1_rounds", 0) for s in sessions),
        "l2_iterations": sum(s.get("summary", {}).get("l2_iterations", 0) for s in sessions),
        "l3_rounds": sum(s.get("summary", {}).get("l3_rounds", 0) for s in sessions),
        "no_progress": sum(s.get("summary", {}).get("no_progress", 0) for s in sessions),
        "agent_calls_estimated": sum(s.get("summary", {}).get("agent_calls_estimated", 0) for s in sessions),
    }
    return {"sessions": sessions, "aggregate": aggregate}


def _summarize_session(data: dict) -> dict:
    """session-log 한 entry 의 lifecycle 메트릭 추출. 형식이 알려져 있지 않을 수 있음 — best-effort."""
    summary = {
        "l1_rounds": 0,
        "l2_iterations": 0,
        "l3_rounds": 0,
        "no_progress": 0,
        "agent_calls_estimated": 0,
        "tokens_estimated": 0,
    }
    if isinstance(data, dict):
        # 알려진 keys (project-specific session-report hook 출력 형식 가정, 있을 때)
        metrics = data.get("session_metrics", data)
        summary["l1_rounds"] = metrics.get("iterations", {}).get("L1", 0) if isinstance(metrics.get("iterations"), dict) else 0
        summary["l2_iterations"] = metrics.get("iterations", {}).get("L2-outer", 0) if isinstance(metrics.get("iterations"), dict) else 0
        summary["l3_rounds"] = metrics.get("iterations", {}).get("L3", 0) if isinstance(metrics.get("iterations"), dict) else 0
        summary["no_progress"] = metrics.get("no_progress_count", 0) or 0
        agent_calls = metrics.get("agent_calls", {})
        if isinstance(agent_calls, dict):
            summary["agent_calls_estimated"] = sum(v for v in agent_calls.values() if isinstance(v, int))
        summary["tokens_estimated"] = metrics.get("total_tokens", 0) or 0
    return summary


def collect_task_metrics(initiative: str = None) -> dict:
    """archive 의 completed task 수 + effort 추정."""
    if not ARCHIVE_DIR.is_dir():
        return {"completed_tasks": [], "total": 0}

    tasks = []
    pattern = "*/" + (f"{initiative}/" if initiative else "") + "*/plan.md"
    for plan_file in ARCHIVE_DIR.glob(pattern):
        try:
            text = plan_file.read_text(encoding="utf-8", errors="replace")
            fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
            if not fm_match:
                continue
            fm = fm_match.group(1)
            slug = (re.search(r"^slug:\s*(\S+)", fm, re.MULTILINE) or [None, None])[1]
            initiative_val = (re.search(r"^initiative:\s*(\S+)", fm, re.MULTILINE) or [None, None])[1]
            started = (re.search(r"^started:\s*([0-9-]+)", fm, re.MULTILINE) or [None, None])[1]
            tasks.append({
                "slug": slug,
                "initiative": initiative_val,
                "started": started,
                "archive_path": str(plan_file.parent.relative_to(REPO_ROOT)),
            })
        except OSError:
            continue
    return {"completed_tasks": sorted(tasks, key=lambda t: t.get("started") or ""), "total": len(tasks)}


def detect_threshold_violations(lifecycle: dict) -> list:
    """rules/80 §D 임계값 위반 검출."""
    violations = []
    agg = lifecycle.get("aggregate", {})
    if agg.get("tokens_estimated", 0) > THRESHOLD_TOKENS:
        violations.append({
            "kind": "tokens_200k_plus",
            "value": agg["tokens_estimated"],
            "threshold": THRESHOLD_TOKENS,
        })
    if agg.get("agent_calls_estimated", 0) > THRESHOLD_AGENT_CALLS:
        violations.append({
            "kind": "agent_10_plus",
            "value": agg["agent_calls_estimated"],
            "threshold": THRESHOLD_AGENT_CALLS,
        })
    if agg.get("l2_iterations", 0) > THRESHOLD_L2_OUTER:
        violations.append({
            "kind": "L2_max_5",
            "value": agg["l2_iterations"],
            "threshold": THRESHOLD_L2_OUTER,
        })
    return violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=None, help="JSON 출력 경로 (default: _artifacts/baseline-metrics.json)")
    ap.add_argument("--initiative", default=None, help="task 메트릭 필터링 — 특정 initiative만")
    args = ap.parse_args()

    out_path = Path(args.output) if args.output else (
        REPO_ROOT / "docs" / "_active" / "harness-stabilization" / "rules80-freeze-metrics" / "_artifacts" / "baseline-metrics.json"
    )

    churn = collect_churn()
    freeze_status = collect_freeze_status()
    lifecycle_metrics = collect_lifecycle_metrics()
    task_metrics = collect_task_metrics(initiative=args.initiative)
    threshold_violations = detect_threshold_violations(lifecycle_metrics)

    out = {
        "collected_at": datetime.utcnow().isoformat() + "Z",
        "freeze_status": freeze_status,
        "churn": churn,
        "lifecycle_metrics": lifecycle_metrics,
        "task_metrics": task_metrics,
        "threshold_violations": threshold_violations,
        "constants": {
            "SONNET_TOKENS_AVG": SONNET_TOKENS_AVG,
            "HAIKU_TOKENS_AVG": HAIKU_TOKENS_AVG,
            "OPUS_TOKENS_AVG": OPUS_TOKENS_AVG,
            "THRESHOLD_TOKENS": THRESHOLD_TOKENS,
            "THRESHOLD_AGENT_CALLS": THRESHOLD_AGENT_CALLS,
            "THRESHOLD_L2_OUTER": THRESHOLD_L2_OUTER,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"=== rules/80 freeze metrics (collected {out['collected_at']}) ===")
    print(f"freeze_until: {freeze_status.get('freeze_until')}")
    print(f"churn (rules/80 commits): {churn.get('total_commits', 0)}")
    print(f"sessions sampled: {len(lifecycle_metrics.get('sessions', []))}")
    print(f"  L1 rounds: {lifecycle_metrics['aggregate'].get('l1_rounds', 0)}")
    print(f"  L2 iterations: {lifecycle_metrics['aggregate'].get('l2_iterations', 0)}")
    print(f"  L3 rounds: {lifecycle_metrics['aggregate'].get('l3_rounds', 0)}")
    print(f"  no_progress: {lifecycle_metrics['aggregate'].get('no_progress', 0)}")
    print(f"completed tasks ({args.initiative or 'all'}): {task_metrics.get('total', 0)}")
    print(f"threshold violations: {len(threshold_violations)}")
    print()
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
