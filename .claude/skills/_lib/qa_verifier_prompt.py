#!/usr/bin/env python3
"""
domain: lifecycle
qa_verifier_prompt — qa-verifier 호출용 self-contained prompt builder.

사용처: task-evaluate (L1), task-verify (L2 inner), task-loop (L2 outer),
       task-review (L3) 의 qa-verifier 호출 지점 모두.

CLI 호출 (메인이 Bash 로):
  python3 .claude/skills/_lib/qa_verifier_prompt.py \\
    --purpose L3 \\
    --plan docs/_active/<slug>/plan.md \\
    --inline '{"test_results": "...", "elapsed": "..."}' \\
    --axes 'acceptance 정합' --axes '회귀' --axes '성능'
  → stdout: prompt 문자열 (Agent tool 의 prompt 인자로 사용)

Module import (다른 스크립트에서):
  from qa_verifier_prompt import build_self_contained_prompt, extract_section
"""
import argparse
import json
import os
import re
import sys


MAX_AXES = 3  # rules/80 C.10 강제

VALID_PURPOSES = ("L1", "G1", "L2", "G2", "L3")


def extract_section(md_path: str, heading: str) -> str:
    """plan.md / rules.md 의 특정 ## 헤딩 섹션 텍스트 추출.

    매칭 규칙:
    - `## {heading}` 또는 `### {heading}` (정확 매칭)
    - 다음 동급 또는 상위 헤딩 직전까지

    반환: 헤딩 본문 (헤딩 라인 제외, 끝 newline strip).
    미존재 시: 빈 문자열.
    """
    if not os.path.exists(md_path):
        return ""
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    pattern = re.compile(rf"^(#{{2,3}})\s+{re.escape(heading)}\s*$")
    capture = False
    captured_level = 0
    body = []

    for line in lines:
        m = pattern.match(line)
        if m and not capture:
            capture = True
            captured_level = len(m.group(1))
            continue
        if capture:
            # 다음 동급 또는 상위 헤딩 만나면 종료
            other = re.match(r"^(#{1,3})\s+", line)
            if other and len(other.group(1)) <= captured_level:
                break
            body.append(line)

    return "\n".join(body).strip()


def build_self_contained_prompt(
    purpose: str,
    inline_data: dict,
    axes: list,
    max_axes: int = MAX_AXES,
) -> str:
    """qa-verifier 호출용 self-contained prompt 생성.

    4 강제 요소:
      1. EXTERNAL READ FORBIDDEN 명시
      2. INLINE: ... 마커로 inline 정보 포함
      3. axes ≤ max_axes (rules/80 C.10)
      4. verdict 형식 강제 (마지막 줄)

    Args:
        purpose: "L1" | "G1" | "L2" | "G2" | "L3"
        inline_data: {"acceptance": "...", "test_results": "...", ...}
        axes: ["acceptance 정합", "회귀", ...] (max 3)
        max_axes: rules/80 C.10 강제 한도 (기본 3)

    Raises:
        ValueError: axes 개수가 max_axes 초과.
    """
    if purpose not in VALID_PURPOSES:
        raise ValueError(f"Invalid purpose: {purpose}. Must be one of {VALID_PURPOSES}")
    if len(axes) > max_axes:
        raise ValueError(
            f"axes count {len(axes)} exceeds max_axes={max_axes} (rules/80 C.10). "
            f"복잡 검증은 plan-reviewer 로 위임."
        )

    parts = []

    # Header — 강제 요소 1
    parts.append(f"⛔ EXTERNAL READ FORBIDDEN — Bash, Read, Grep, Glob 호출 금지.")
    parts.append(f"⛔ 아래 INLINE 정보만 사용해 텍스트 판정.")
    parts.append("")
    parts.append(f"Purpose: {purpose}")
    parts.append("")

    # Inline data — 강제 요소 2
    if not inline_data:
        parts.append("⚠ INLINE data 비어 있음 — insufficient context.")
        parts.append("Output: BLOCK: prompt-insufficient: <어느 정보 부족>")
        parts.append("")
    else:
        for key, value in inline_data.items():
            parts.append(f"== INLINE: {key} ==")
            parts.append(str(value).strip() or "(empty)")
            parts.append("")

    # Axes — 강제 요소 3
    parts.append(f"== Verification axes (≤{max_axes}) ==")
    for i, axis in enumerate(axes, 1):
        parts.append(f"{i}. {axis}")
    parts.append("")

    # Verdict format — 강제 요소 4
    parts.append("== ⚠ OUTPUT FORMAT (LAST LINE MUST MATCH) ==")
    parts.append("Last line of output MUST be ONE of:")
    parts.append("  • APPROVE")
    parts.append("  • SUGGEST: <axis>: <한줄>")
    parts.append("  • BLOCK: <axis>: <한줄>")
    parts.append("")
    parts.append(
        "Per-axis verdict 도 같은 형식으로 본문에 작성 가능. "
        "마지막 줄은 종합 verdict 한 줄."
    )

    return "\n".join(parts)


def _cli():
    p = argparse.ArgumentParser(description="qa-verifier self-contained prompt builder")
    p.add_argument("--purpose", required=True, choices=list(VALID_PURPOSES))
    p.add_argument("--plan", default=None, help="plan.md 경로 (Acceptance Criteria 섹션 자동 추출)")
    p.add_argument("--inline", default="{}", help="JSON dict 의 inline 데이터")
    p.add_argument("--axes", action="append", default=[], help="검증 축 (반복 가능, max 3)")
    p.add_argument("--max-axes", type=int, default=MAX_AXES)
    args = p.parse_args()

    try:
        inline = json.loads(args.inline)
    except json.JSONDecodeError as e:
        print(f"Error: --inline must be valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if args.plan:
        section = extract_section(args.plan, "Acceptance Criteria")
        if section:
            inline.setdefault("acceptance_criteria", section)

    try:
        prompt = build_self_contained_prompt(
            purpose=args.purpose,
            inline_data=inline,
            axes=args.axes,
            max_axes=args.max_axes,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    print(prompt)


if __name__ == "__main__":
    _cli()
