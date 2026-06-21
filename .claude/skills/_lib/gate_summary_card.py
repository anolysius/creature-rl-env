#!/usr/bin/env python3
"""
domain: lifecycle
gate_summary_card — 사람 hard 게이트(G1·task-end) 직전 "작업 요약 카드" 조립기.

rules/80 §H (Gate Summary Card) 의 5블록 골격을 plan frontmatter + qa-checklist 에서
deterministic 하게 조립한다 (LLM 미호출). 소분류(변경 단위) 한 줄 설명만 호출자가 보강.

5블록 (rules/80 §H.2):
  1. 헤더 앵커  2. 승인 대상 1줄  3. 대분류→소분류 표(≤5행)
  4. 게이트별 주인공 (G1=freeze될 acceptance / end=acceptance 결과 1:1 대조)
  5. 명시 옵션

사용처:
  - task-evaluate (Decision.APPROVED) → build_g1_card
  - task-end (archive 이동 confirm 직전) → build_end_card

CLI (메인이 Bash 로):
  python3 .claude/skills/_lib/gate_summary_card.py g1 \\
    --plan docs/_active/<slug>/plan.md \\
    --qa   docs/_active/<slug>/qa-checklist.md \\
    --yes  "acceptance freeze + 구현 시작" \\
    --row '{"domain":"lifecycle","sub":"§H 신설","impact":"1 file"}'
  → stdout: 카드 문자열

Module import:
  from gate_summary_card import build_g1_card, build_end_card, parse_frontmatter, extract_acceptance
"""
import argparse
import json
import re
import sys

MAX_TABLE_ROWS = 5  # rules/80 §H.2 블록3 — 표 ≤5행

# end 카드 acceptance 결과 status enum (rules/80 §H.2 블록4)
RESULT_MARK = {
    "pass": ("x", "✅"),
    "unverified": (" ", "⚠️ 미검증"),
    "fail": (" ", "❌ 실패"),
}


def parse_frontmatter(plan_text: str) -> dict:
    """plan.md frontmatter 에서 slug / initiative / domains 추출 (yaml 의존 없이 regex)."""
    fm = {}
    m = re.search(r"^---\s*\n(.*?)\n---\s*\n", plan_text, re.DOTALL)
    if not m:
        return fm
    body = m.group(1)
    slug = re.search(r"^slug:\s*(.+?)\s*$", body, re.MULTILINE)
    if slug:
        fm["slug"] = slug.group(1).strip()
    init = re.search(r"^initiative:\s*(.+?)\s*$", body, re.MULTILINE)
    if init:
        v = init.group(1).strip()
        fm["initiative"] = None if v in ("null", "~", "") else v
    dom = re.search(r"^domains:\s*\[(.*?)\]\s*$", body, re.MULTILINE)
    if dom:
        fm["domains"] = [d.strip() for d in dom.group(1).split(",") if d.strip()]
    else:
        fm["domains"] = []
    return fm


def extract_acceptance(qa_text: str) -> list:
    """qa-checklist.md 의 '## Acceptance' 섹션에서 체크리스트 항목 추출.

    반환: [{"id": "AC1", "text": "...", "checked": bool}, ...]
    id 는 'AC<n>' 토큰이 있으면 사용, 없으면 순번 부여.
    """
    items = []
    # '## Acceptance' 헤더부터 다음 '## ' 헤더 전까지
    m = re.search(r"^##[^\n]*Acceptance[^\n]*\n(.*?)(?=^##\s|\Z)", qa_text, re.DOTALL | re.MULTILINE)
    section = m.group(1) if m else qa_text
    n = 0
    for line in section.splitlines():
        cm = re.match(r"^\s*-\s*\[([ xX])\]\s*(.+?)\s*$", line)
        if not cm:
            continue
        n += 1
        checked = cm.group(1).lower() == "x"
        text = cm.group(2).strip()
        idm = re.match(r"^(AC\d+)\b\s*(.*)$", text)
        if idm:
            ac_id, rest = idm.group(1), idm.group(2).strip()
        else:
            ac_id, rest = f"AC{n}", text
        items.append({"id": ac_id, "text": rest or text, "checked": checked})
    return items


def _detail_link(fm: dict, kind: str) -> str:
    """plan.md / report.md 상대 링크 라벨."""
    return "plan.md" if kind == "plan" else "report.md"


def _table(rows: list) -> list:
    """대분류→소분류 표 (블록3). ≤5행, 초과 시 '…외 N건' 행 추가."""
    out = ["| 대분류(도메인) | 소분류 | 영향 |", "|---|---|---|"]
    shown = rows[:MAX_TABLE_ROWS]
    for r in shown:
        out.append(f"| {r.get('domain','—')} | {r.get('sub','—')} | {r.get('impact','—')} |")
    if len(rows) > MAX_TABLE_ROWS:
        out.append(f"| … | 외 {len(rows) - MAX_TABLE_ROWS}건 (상세는 링크) | … |")
    return out


def build_g1_card(plan_text: str, qa_text: str, what_yes: str, rows: list) -> str:
    """G1 카드 — 앞을 봄. 주인공 = freeze 될 acceptance.

    what_yes: 승인 시 일어나는 일 (예: 'acceptance freeze + 구현 시작').
    rows: [{"domain","sub","impact"}, ...] — 소분류는 호출자 보강.
    """
    fm = parse_frontmatter(plan_text)
    acs = extract_acceptance(qa_text)
    lines = []
    # 블록1 헤더 앵커 + 블록2 승인 대상 1줄
    lines.append(f'## 🚦 G1 승인 요청 — "{what_yes}"')
    lines.append("")
    lines.append(f"**승인 대상**: YES → {what_yes}.")
    lines.append("")
    # 블록3 표
    lines.append(f"**설계 요약** (상세 → `{_detail_link(fm, 'plan')}`)")
    lines.append("")
    lines.extend(_table(rows))
    lines.append("")
    # 블록4 주인공 — freeze 될 acceptance
    lines.append("**🔒 freeze 될 Acceptance**")
    if acs:
        for a in acs:
            lines.append(f"- [ ] {a['id']} {a['text']}")
    else:
        lines.append("- [ ] (qa-checklist 에 Acceptance 항목 없음 — 확인 필요)")
    lines.append("")
    # 블록5 명시 옵션
    lines.append("**승인?** [1] GO (freeze) │ [2] 보완 후 재평가 │ [3] 취소")
    return "\n".join(lines)


def _proposals_block(pending: list) -> list:
    """종료 카드의 '🔁 제안된 개선' 블록 (rules/80 §I). pending 비면 빈 리스트(블록 생략).

    pending: [{"id","summary","proposal", ...}, ...] (retro_proposals.list_pending 결과).
    적용은 사람 게이트 — 블록은 결재 surface 일 뿐 auto-apply 0.
    """
    if not pending:
        return []
    out = ["", f"**🔁 제안된 개선 {len(pending)}건** (이번 세션 감지 — 적용은 사람 결재)"]
    for d in pending[:MAX_TABLE_ROWS]:
        out.append(f"- `{d.get('id','?')}`: {d.get('summary','')} → {d.get('proposal','')}")
    if len(pending) > MAX_TABLE_ROWS:
        out.append(f"- … 외 {len(pending) - MAX_TABLE_ROWS}건")
    out.append("결재: 항목별 [seed] task 로 / [dismiss] 폐기 / [defer] 보류")
    return out


def build_end_card(plan_text: str, qa_text: str, rows: list, results: dict,
                   pending: list = None) -> str:
    """종료 카드 — 뒤를 봄. 주인공 = acceptance 결과 (G1 freeze 와 1:1 대조).

    rows: [{"domain","sub","impact"}, ...] — 'impact' 자리에 plan 대비(일치/편차) 권장.
    results: {ac_id: 'pass'|'unverified'|'fail'} — G1 의 모든 AC 를 키로 가져야 1:1 대조 성립.
    pending: retro 제안 큐의 pending 목록 (rules/80 §I). None/빈 리스트면 블록 생략(무회귀).
    """
    fm = parse_frontmatter(plan_text)
    acs = extract_acceptance(qa_text)
    lines = []
    lines.append('## ✅ task-end 승인 요청 — "archive 이동 + CHANGELOG append"')
    lines.append("")
    lines.append("**승인 대상**: YES → active → archive 이동 + CHANGELOG 1줄 append (비가역).")
    lines.append("")
    lines.append(f"**한 일 요약** (상세 → `{_detail_link(fm, 'report')}`)")
    lines.append("")
    lines.extend(_table(rows))
    lines.append("")
    # 블록4 주인공 — acceptance 결과 1:1 대조
    lines.append("**✅ Acceptance 결과** (G1 freeze 와 1:1 대조)")
    missing = []
    for a in acs:
        status = results.get(a["id"], "unverified")
        box, mark = RESULT_MARK.get(status, RESULT_MARK["unverified"])
        lines.append(f"- [{box}] {a['id']} {a['text']}  {mark}")
        if a["id"] not in results:
            missing.append(a["id"])
    if missing:
        lines.append("")
        lines.append(f"> ⚠️ 결과 미지정 {len(missing)}건({', '.join(missing)}) → '미검증' 처리. 1:1 대조 불완전.")
    # 🔁 제안된 개선 블록 (rules/80 §I) — pending 있을 때만, 없으면 무회귀
    lines.extend(_proposals_block(pending))
    lines.append("")
    lines.append("**종료?** [1] 종료 │ [2] 보류")
    return "\n".join(lines)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def main(argv=None):
    p = argparse.ArgumentParser(description="Gate Summary Card 조립 (rules/80 §H)")
    p.add_argument("gate", choices=["g1", "end"])
    p.add_argument("--plan", required=True)
    p.add_argument("--qa", required=True)
    p.add_argument("--yes", default="", help="G1 승인 대상 1줄 (end 는 고정)")
    p.add_argument("--row", action="append", default=[], help="JSON {domain,sub,impact} — 반복")
    p.add_argument("--results", default="{}", help="end: JSON {ac_id: pass|unverified|fail}")
    p.add_argument("--proposals-file", default=None,
                   help="end: retro 제안 큐 경로 (pending 을 '🔁 제안된 개선' 블록에 surface)")
    args = p.parse_args(argv)

    rows = [json.loads(r) for r in args.row]
    plan_text = _read(args.plan)
    qa_text = _read(args.qa)

    if args.gate == "g1":
        print(build_g1_card(plan_text, qa_text, args.yes or "acceptance freeze + 구현 시작", rows))
    else:
        results = json.loads(args.results)
        pending = None
        if args.proposals_file:
            from retro_proposals import list_pending  # 같은 _lib 디렉토리
            pending = list_pending(_read(args.proposals_file))
        print(build_end_card(plan_text, qa_text, rows, results, pending))
    return 0


if __name__ == "__main__":
    sys.exit(main())
