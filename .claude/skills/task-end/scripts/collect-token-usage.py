#!/usr/bin/env python3
"""
collect-token-usage.py — Claude Code transcript JSONL 의 토큰 usage 실측 집계.

rules/80 §F (mode tiering ~25%) / §G (prompt cache ~30%/call) 추정치를
실측으로 검증하기 위한 파서 (task: rules80-token-savings-actuals, 2026-06-11).
v1 (collect-rules80-metrics.py) 의 상수 추정(SONNET_TOKENS_AVG 등)을 대체하는
별도 스크립트 — v1 은 무변경 유지.

데이터 원천 (로컬 전용, 커밋 금지):
  ~/.claude/projects/<project-slug>/<session-id>.jsonl            메인 세션
  ~/.claude/projects/<project-slug>/<session-id>/subagents/
      agent-*.jsonl                                               서브에이전트 호출
      agent-*.meta.json                                           {agentType, ...}

핵심 처리:
  - assistant 레코드의 message.usage 만 사용
    (input_tokens / cache_creation_input_tokens / cache_read_input_tokens / output_tokens)
  - ⚠ 동일 message.id 가 스트리밍 누적으로 다중 기록됨 → 전역 dedup (마지막 레코드 승)
  - 산출 JSON 은 집계값만 — 메시지 본문/프롬프트 raw 텍스트 일절 미포함 (커밋 안전)

cache hit rate (per call):
  cache_read / (cache_read + cache_creation + input)

no-cache 대비 비용 추정 (Anthropic 가격 모델: 5m cache write 1.25x, cache read 0.1x):
  baseline = input + cache_creation + cache_read   (전부 정가 input 이었을 경우)
  actual   = input + 1.25 * cache_creation + 0.1 * cache_read
  savings  = 1 - actual / baseline

usage:
  python3 collect-token-usage.py [--transcript-dir DIR] [--since YYYY-MM-DD]
                                 [--until YYYY-MM-DD] [--output PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

CACHE_WRITE_MULT = 1.25  # 5m ephemeral cache write (Claude Code 기본). 1h 은 2.0 — 한계로 명시
CACHE_READ_MULT = 0.10

PLAN_PATH_RE = re.compile(
    rb"docs/_(?:active|archive/[0-9]{4}-Q[0-9])/([A-Za-z0-9._/-]+?)/plan\.md"
)


def default_transcript_dir() -> Path:
    return Path.home() / ".claude" / "projects" / str(REPO_ROOT).replace("/", "-")


# ---------------------------------------------------------------- parsing


def extract_usage_calls(jsonl_path: Path, calls: dict) -> dict:
    """assistant 레코드의 usage 를 message.id 로 dedup 해 calls 에 누적 (마지막 레코드 승).

    calls: {message_id: {"input", "cache_creation", "cache_read", "output",
                         "model", "timestamp", "file_order"}}
    반환: 파일 단위 부가 정보 {"sidechain_ids": set, "order": [message_id 등장 순서]}
    """
    sidechain_ids = set()
    order: list[str] = []
    try:
        fh = jsonl_path.open("r", encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"⚠ open fail {jsonl_path}: {e}", file=sys.stderr)
        return {"sidechain_ids": sidechain_ids, "order": order}
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "assistant":
                continue
            msg = rec.get("message") or {}
            usage = msg.get("usage") or {}
            mid = msg.get("id")
            if not mid or not usage:
                continue
            if mid not in calls:
                order.append(mid)
            calls[mid] = {
                "input": int(usage.get("input_tokens") or 0),
                "cache_creation": int(usage.get("cache_creation_input_tokens") or 0),
                "cache_read": int(usage.get("cache_read_input_tokens") or 0),
                "output": int(usage.get("output_tokens") or 0),
                "model": msg.get("model") or "unknown",
                "timestamp": rec.get("timestamp") or "",
            }
            if rec.get("isSidechain"):
                sidechain_ids.add(mid)
    return {"sidechain_ids": sidechain_ids, "order": order}


def in_window(call: dict, since: str, until: str | None) -> bool:
    day = (call.get("timestamp") or "")[:10]
    if not day:
        return False
    if day < since:
        return False
    if until and day > until:
        return False
    return True


def read_agent_type(meta_path: Path) -> str:
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return meta.get("agentType") or "unknown"
    except (OSError, json.JSONDecodeError):
        return "unknown"


def attribute_task_slug(jsonl_path: Path) -> str | None:
    """세션 transcript 에 등장하는 plan.md 경로의 최빈 slug (best-effort)."""
    counts: dict[str, int] = defaultdict(int)
    try:
        data = jsonl_path.read_bytes()
    except OSError:
        return None
    for m in PLAN_PATH_RE.finditer(data):
        counts[m.group(1).decode("utf-8", "replace")] += 1
    if not counts:
        return None
    return max(counts, key=lambda k: counts[k])


def lookup_plan_mode(slug: str, repo_root: Path = REPO_ROOT) -> str | None:
    """slug (initiative/<slug> 포함 가능) 의 plan frontmatter mode: 조회 (best-effort)."""
    candidates = [repo_root / "docs" / "_active" / slug / "plan.md"]
    candidates += sorted(repo_root.glob(f"docs/_archive/*/{slug}/plan.md"))
    # archive 는 NN- prefix 가 붙음 — 마지막 path segment 에 suffix 매칭
    tail = slug.rsplit("/", 1)[-1]
    head = slug.rsplit("/", 1)[0] if "/" in slug else ""
    candidates += sorted(repo_root.glob(f"docs/_archive/*/{head or '*'}/[0-9][0-9]-{tail}/plan.md"))
    for p in candidates:
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r"^mode:\s*([\w-]+)", text, re.MULTILINE)
        if m:
            return m.group(1)
        return None  # plan 존재하나 mode 미기록 (구버전 plan)
    return None


# ---------------------------------------------------------------- aggregation


def summarize(calls: list[dict]) -> dict:
    """call 목록의 토큰 합계 + cache hit rate + no-cache 대비 비용 추정."""
    tot = {"calls": len(calls), "input": 0, "cache_creation": 0, "cache_read": 0, "output": 0}
    per_call_rates = []
    for c in calls:
        tot["input"] += c["input"]
        tot["cache_creation"] += c["cache_creation"]
        tot["cache_read"] += c["cache_read"]
        tot["output"] += c["output"]
        denom = c["input"] + c["cache_creation"] + c["cache_read"]
        if denom > 0:
            per_call_rates.append(c["cache_read"] / denom)
    denom = tot["input"] + tot["cache_creation"] + tot["cache_read"]
    tot["hit_rate_weighted"] = round(tot["cache_read"] / denom, 4) if denom else None
    tot["hit_rate_mean_per_call"] = (
        round(sum(per_call_rates) / len(per_call_rates), 4) if per_call_rates else None
    )
    if denom:
        actual = (
            tot["input"] + CACHE_WRITE_MULT * tot["cache_creation"] + CACHE_READ_MULT * tot["cache_read"]
        )
        tot["est_input_cost_savings_vs_nocache"] = round(1 - actual / denom, 4)
    else:
        tot["est_input_cost_savings_vs_nocache"] = None
    return tot


def collect(transcript_dir: Path, since: str, until: str | None) -> dict:
    calls: dict[str, dict] = {}  # 전역 dedup (세션 fork 로 동일 message 가 두 파일에 복제돼도 1회)
    call_src: dict[str, tuple] = {}  # message_id -> (kind, session, agent_type)
    first_call_flags: list[dict] = []  # subagent 별 첫 호출 cache_read>0 여부
    sidechain_in_main = 0

    main_files = sorted(transcript_dir.glob("*.jsonl"))
    for mf in main_files:
        session = mf.stem
        info = extract_usage_calls(mf, calls)
        for mid in info["order"]:
            if mid in info["sidechain_ids"]:
                call_src.setdefault(mid, ("sidechain-in-main", session, "unknown"))
                sidechain_in_main += 1
            else:
                call_src.setdefault(mid, ("main", session, None))

        sub_dir = transcript_dir / session / "subagents"
        if sub_dir.is_dir():
            for af in sorted(sub_dir.glob("agent-*.jsonl")):
                agent_type = read_agent_type(af.with_suffix("").with_name(af.stem + ".meta.json"))
                sub_info = extract_usage_calls(af, calls)
                for i, mid in enumerate(sub_info["order"]):
                    call_src[mid] = ("subagent", session, agent_type)
                    if i == 0 and in_window(calls[mid], since, until):
                        first_call_flags.append(
                            {"agent_type": agent_type, "cache_hit": calls[mid]["cache_read"] > 0}
                        )

    # 기간 필터
    kept = {mid: c for mid, c in calls.items() if in_window(c, since, until)}

    by_session: dict[str, dict] = defaultdict(lambda: {"main": [], "subagent": [], "sidechain": []})
    by_agent_type: dict[str, list] = defaultdict(list)
    for mid, c in kept.items():
        kind, session, agent_type = call_src.get(mid, ("main", "unknown", None))
        if kind == "main":
            by_session[session]["main"].append(c)
        elif kind == "subagent":
            by_session[session]["subagent"].append(c)
            by_agent_type[agent_type].append(c)
        else:
            by_session[session]["sidechain"].append(c)
            by_agent_type["sidechain-in-main"].append(c)

    sessions_out = []
    for session, groups in sorted(by_session.items()):
        all_calls = groups["main"] + groups["subagent"] + groups["sidechain"]
        if not all_calls:
            continue
        mf = transcript_dir / f"{session}.jsonl"
        slug = attribute_task_slug(mf) if mf.is_file() else None
        mode = lookup_plan_mode(slug) if slug else None
        sessions_out.append(
            {
                "session": session,
                "attributed_slug": slug,
                "mode": mode or ("unattributed" if not slug else "unknown"),
                "main": summarize(groups["main"]),
                "subagent": summarize(groups["subagent"]),
                "total": summarize(all_calls),
                "models": sorted({c["model"] for c in all_calls}),
            }
        )

    agents_out = {}
    for agent_type, lst in sorted(by_agent_type.items()):
        s = summarize(lst)
        flags = [f for f in first_call_flags if f["agent_type"] == agent_type]
        s["agent_invocations"] = len(flags)
        s["first_call_cache_hit"] = sum(1 for f in flags if f["cache_hit"])
        agents_out[agent_type] = s

    by_mode: dict[str, list] = defaultdict(list)
    for s in sessions_out:
        by_mode[s["mode"]].append(s)
    # mode 합계는 세션 total 의 단순 합 (call 재합산 대신 세션 summary 합)
    modes_out = {}
    for mode, lst in by_mode.items():
        agg = {"calls": 0, "input": 0, "cache_creation": 0, "cache_read": 0, "output": 0}
        for s in lst:
            for k in agg:
                agg[k] += s["total"][k]
        denom = agg["input"] + agg["cache_creation"] + agg["cache_read"]
        agg["hit_rate_weighted"] = round(agg["cache_read"] / denom, 4) if denom else None
        agg["tokens_per_session_avg"] = round(
            (denom + agg["output"]) / len(lst)
        ) if lst else None
        modes_out[mode] = {"sessions": len(lst), **agg}

    return {
        "transcript_dir": str(transcript_dir),
        "since": since,
        "until": until,
        "dedup": {
            "unique_api_calls": len(calls),
            "in_window_calls": len(kept),
            "sidechain_in_main_calls": sidechain_in_main,
        },
        "overall": summarize(list(kept.values())),
        "subagents_by_type": agents_out,
        "by_mode": modes_out,
        "sessions": sessions_out,
        "notes": [
            "집계값만 포함 — transcript raw 텍스트/프롬프트 미포함 (커밋 안전)",
            f"cache write 비용 {CACHE_WRITE_MULT}x (5m ephemeral 가정), read {CACHE_READ_MULT}x",
            "mode 매핑은 best-effort (transcript 내 plan.md 경로 최빈값) — 실패 시 unattributed",
        ],
    }


# ---------------------------------------------------------------- cli


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript-dir", type=Path, default=default_transcript_dir())
    ap.add_argument("--since", default="2026-06-01")
    ap.add_argument("--until", default=None)
    ap.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT
        / "docs/_artifacts/token-usage-actuals.json",
    )
    args = ap.parse_args()

    if not args.transcript_dir.is_dir():
        print(f"❌ transcript dir 없음: {args.transcript_dir}", file=sys.stderr)
        return 1

    result = collect(args.transcript_dir, args.since, args.until)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    o = result["overall"]
    print(f"기간: {args.since} ~ {args.until or '현재'}   (unique calls in window: {result['dedup']['in_window_calls']})")
    print(f"전체 hit rate (weighted): {o['hit_rate_weighted']}   no-cache 대비 입력비용 절감: {o['est_input_cost_savings_vs_nocache']}")
    print(f"{'agentType':<28}{'calls':>6}{'hit_w':>8}{'hit/call':>10}{'first-hit':>10}{'savings':>9}")
    for at, s in result["subagents_by_type"].items():
        fh = f"{s['first_call_cache_hit']}/{s['agent_invocations']}"
        print(f"{at:<28}{s['calls']:>6}{str(s['hit_rate_weighted']):>8}{str(s['hit_rate_mean_per_call']):>10}{fh:>10}{str(s['est_input_cost_savings_vs_nocache']):>9}")
    print(f"\nJSON: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
