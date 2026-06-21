#!/usr/bin/env python3
# domain: lifecycle
"""task-evaluate verdict aggregator — N agent verdict 를 종합해 Decision 판정.

사용:
    echo '<verdicts text>' | python3 aggregate-verdicts.py [--prev-log <path>]

verdict 형식:
    APPROVE
    SUGGEST: <축>: <한줄>
    BLOCK: <축>: <한줄>

출력 (stdout, JSON):
    {"decision": "APPROVED|BLOCKED|SUGGEST_CUTOFF|NO_PROGRESS_ESCALATE", ...}
"""
import sys
import io
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


VERDICT_PATTERN = re.compile(r"^(APPROVE|SUGGEST|BLOCK)(?::\s*([\w-]+)\s*:\s*(.+))?$")


def parse_verdicts(text: str, agent_name: Optional[str] = None) -> List[Dict]:
    """verdict 텍스트에서 줄별 파싱.

    형식:
        APPROVE                        # 단독
        SUGGEST: scope: <한줄>          # KIND: 축: 메시지
        BLOCK: risk: <한줄>
    """
    verdicts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = VERDICT_PATTERN.match(line)
        if not m:
            continue
        kind = m.group(1)
        axis = m.group(2)
        message = m.group(3)
        verdicts.append({
            "agent": agent_name,
            "kind": kind,
            "axis": axis,
            "message": message,
            "raw": line,
        })
    return verdicts


def parse_verdicts_with_fallback(text: str, agent_name: Optional[str] = None) -> List[Dict]:
    """3-tier fallback 으로 verdict 추출.

    Tier 1 (primary): 줄별 정확 형식 매칭 (parse_verdicts)
    Tier 2 (multiline): Tier 1 결과를 그대로 반환 (parse_verdicts 가 이미 모든 줄 검사)
    Tier 3 (heuristic): Tier 1+2 가 0건이면 키워드 기반 추론
        - 본문에 "BLOCK" 키워드 있으면 → BLOCK (보수적, APPROVE 보다 우선)
        - "SUGGEST" 만 → SUGGEST
        - "APPROVE" 만 → APPROVE
        - 빈 본문 → 빈 리스트 (MALFORMED)

    각 verdict 에 source 필드: "exact" (Tier 1) or "heuristic" (Tier 3)

    qa-verifier MALFORMED 방지: agent 가 verdict 형식 못 맞춰도 본문에 의도가 명백하면 추출.
    """
    # Tier 1+2: 정확 매칭
    verdicts = parse_verdicts(text, agent_name)
    if verdicts:
        for v in verdicts:
            v.setdefault("source", "exact")
        return verdicts

    # Tier 3: 키워드 휴리스틱
    text_upper = text.upper()
    has_block = "BLOCK" in text_upper or "BLOCKED" in text_upper
    has_suggest = "SUGGEST" in text_upper
    has_approve = "APPROVE" in text_upper

    if has_block:
        return [{
            "agent": agent_name,
            "kind": "BLOCK",
            "axis": "heuristic",
            "message": "extracted from body (verdict 형식 위반 — 보수적 BLOCK)",
            "raw": text[:200],
            "source": "heuristic",
        }]
    if has_suggest:
        return [{
            "agent": agent_name,
            "kind": "SUGGEST",
            "axis": "heuristic",
            "message": "extracted from body",
            "raw": text[:200],
            "source": "heuristic",
        }]
    if has_approve:
        return [{
            "agent": agent_name,
            "kind": "APPROVE",
            "axis": None,
            "message": None,
            "raw": text[:200],
            "source": "heuristic",
        }]

    # 빈 본문 — 진짜 MALFORMED
    return []


def is_repeat_block(blocks: List[Dict], prev_log: Optional[Path]) -> bool:
    """이전 round 의 BLOCK 과 현재 BLOCK 이 동일한지 확인 (no-progress 감지)."""
    if not prev_log or not prev_log.exists():
        return False
    try:
        history = json.loads(prev_log.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not history:
        return False
    last_round = history[-1]
    last_blocks = [v for v in last_round.get("verdicts", []) if v["kind"] == "BLOCK"]
    if not last_blocks:
        return False
    # 동일 BLOCK set 인지 비교
    # agent 정보 부재 가능성 있어 axis + message 우선, fallback 으로 axis 만
    def keyset(blks):
        full = {(b["agent"], b["axis"], b["message"]) for b in blks}
        # agent 가 모두 None 이면 (wrapping 안 됨), axis+message 만으로 비교
        if all(b["agent"] is None for b in blks):
            return {(b["axis"], b["message"]) for b in blks}
        return full
    cur_keys = keyset(blocks)
    last_keys = keyset(last_blocks)
    return cur_keys == last_keys and len(cur_keys) > 0


def aggregate(verdicts: List[Dict], prev_log: Optional[Path] = None) -> Dict:
    if not verdicts:
        return {
            "decision": "EMPTY",
            "reason": "no verdicts parsed (agents may have responded in free format)",
        }

    blocks = [v for v in verdicts if v["kind"] == "BLOCK"]
    suggests = [v for v in verdicts if v["kind"] == "SUGGEST"]

    # 1. 모두 APPROVE
    if not blocks and not suggests:
        return {
            "decision": "APPROVED",
            "next": "G1 진입 권유 (qa-checklist 자동 생성)",
            "verdicts": verdicts,
        }

    # 2. BLOCK 1+ 있으면
    if blocks:
        if is_repeat_block(blocks, prev_log):
            return {
                "decision": "NO_PROGRESS_ESCALATE",
                "reason": "동일 BLOCK 2회 연속 — 사용자 직접 개입 권장",
                "blocks": blocks,
                "verdicts": verdicts,
            }
        return {
            "decision": "BLOCKED",
            "next": "plan 보완 → /task-evaluate 재호출 (selective re-evaluation)",
            "blocks": blocks,
            "suggests": suggests,
            "verdicts": verdicts,
        }

    # 3. SUGGEST 만
    return {
        "decision": "SUGGEST_CUTOFF",
        "next": "사용자 컷오프: [1] 보완 후 재평가 / [2] 컷오프 (현 plan 으로 G1)",
        "suggests": suggests,
        "verdicts": verdicts,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prev-log", type=Path, default=None)
    parser.add_argument("--input", type=str, default=None,
                        help="agent verdict 텍스트 (또는 stdin)")
    args = parser.parse_args()

    text = args.input if args.input else sys.stdin.read()
    verdicts = parse_verdicts(text)
    decision = aggregate(verdicts, args.prev_log)
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
