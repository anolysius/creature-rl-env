#!/usr/bin/env python3
"""
domain: lifecycle
retro_proposals — 자가정화 제안 큐(.claude/retro/proposals.md) read/write SSOT.

rules/80 §I (Self-Retro). 실수 신호 감지 시 개선안 초안을 큐에 append, task-end
종료 카드에서 pending 을 surface, 사람 결재 결과를 set_status 로 반영.
**적용은 항상 사람 게이트** — 본 모듈은 큐 조작만, 어떤 가드도 자동 적용하지 않는다.

큐 라인 포맷:
  - [<status>] <id> | <date> | <trigger> | <summary> | <proposal>

CLI:
  python3 .claude/skills/_lib/retro_proposals.py list-pending --file .claude/retro/proposals.md
  python3 .claude/skills/_lib/retro_proposals.py append --file <f> --id <id> --date <d> \\
    --trigger manual-revert --summary "..." --proposal "..."
  python3 .claude/skills/_lib/retro_proposals.py set-status --file <f> --id <id> --status seeded

Module import:
  from retro_proposals import append, list_pending, list_all, set_status, parse_line
"""
import argparse
import re
import sys

STATUSES = ("proposed", "seeded", "dismissed", "deferred")
TRIGGERS = ("manual-revert", "hook-block-override", "user-correction", "no-progress", "task-seed")

LINE_RE = re.compile(
    r"^- \[(?P<status>\w+)\]\s*(?P<id>[^|]+?)\s*\|\s*(?P<date>[^|]+?)\s*\|\s*"
    r"(?P<trigger>[^|]+?)\s*\|\s*(?P<summary>[^|]+?)\s*\|\s*(?P<proposal>.+?)\s*$"
)


def parse_line(line: str):
    """큐 라인 1개 → dict, 비매칭이면 None."""
    m = LINE_RE.match(line.rstrip())
    if not m:
        return None
    return m.groupdict()


def _render_line(d: dict) -> str:
    return (
        f"- [{d['status']}] {d['id']} | {d['date']} | {d['trigger']} | "
        f"{d['summary']} | {d['proposal']}"
    )


def list_all(text: str) -> list:
    """큐 텍스트에서 모든 제안 dict 추출 (등장 순)."""
    out = []
    for line in text.splitlines():
        d = parse_line(line)
        if d:
            out.append(d)
    return out


def list_pending(text: str) -> list:
    """status == 'proposed' 만."""
    return [d for d in list_all(text) if d["status"] == "proposed"]


def append(text: str, id: str, date: str, trigger: str, summary: str,
           proposal: str, status: str = "proposed") -> str:
    """큐 끝에 제안 1줄 추가한 새 텍스트 반환. 동일 id 존재 시 그대로(중복 방지)."""
    if any(d["id"] == id for d in list_all(text)):
        return text  # idempotent — 동일 id 재적재 안 함
    line = _render_line({
        "status": status, "id": id, "date": date,
        "trigger": trigger, "summary": summary, "proposal": proposal,
    })
    body = text.rstrip("\n")
    return f"{body}\n{line}\n"


def set_status(text: str, id: str, new_status: str) -> str:
    """id 의 status 를 변경한 새 텍스트 반환. id 없으면 원본 그대로."""
    if new_status not in STATUSES:
        raise ValueError(f"invalid status: {new_status}")
    out_lines = []
    for line in text.splitlines():
        d = parse_line(line)
        if d and d["id"] == id:
            d["status"] = new_status
            out_lines.append(_render_line(d))
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main(argv=None):
    p = argparse.ArgumentParser(description="retro proposals 큐 조작 (rules/80 §I)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("list-pending", "list-all"):
        s = sub.add_parser(name)
        s.add_argument("--file", required=True)
    a = sub.add_parser("append")
    a.add_argument("--file", required=True)
    for f in ("id", "date", "trigger", "summary", "proposal"):
        a.add_argument(f"--{f}", required=True)
    a.add_argument("--status", default="proposed")
    st = sub.add_parser("set-status")
    st.add_argument("--file", required=True)
    st.add_argument("--id", required=True)
    st.add_argument("--status", required=True)
    args = p.parse_args(argv)

    text = _read(args.file)
    if args.cmd in ("list-pending", "list-all"):
        items = list_pending(text) if args.cmd == "list-pending" else list_all(text)
        for d in items:
            print(f"{d['id']} [{d['status']}] — {d['summary']} → {d['proposal']}")
    elif args.cmd == "append":
        _write(args.file, append(text, args.id, args.date, args.trigger,
                                 args.summary, args.proposal, args.status))
    elif args.cmd == "set-status":
        _write(args.file, set_status(text, args.id, args.status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
