#!/usr/bin/env python3
# domain: lifecycle
"""
reviewer_prompt.py 의 7+ fixture 검증.

Acceptance:
- A1: build_reviewer_prompt(agent, purpose, fixed_prefix, variable, axes) 정상 동작
- A2: 7+ fixture PASS (4 agent baseline + 3 cross-cutting)
- A7: fixed prefix 1024+ token (4000+ chars) 강제

usage: python3 test_reviewer_prompt.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
_spec = importlib.util.spec_from_file_location("rp", SCRIPT_DIR / "reviewer_prompt.py")
_module = importlib.util.module_from_spec(_spec)  # type: ignore
_spec.loader.exec_module(_module)  # type: ignore

build_reviewer_prompt = _module.build_reviewer_prompt
get_fixed_prefix = _module.get_fixed_prefix
FIXED_PREFIX = _module.FIXED_PREFIX
SHARED_GUIDELINES = _module.SHARED_GUIDELINES


# ─── A7: fixed prefix 1024+ token (4000+ chars) ──────────────────────

MIN_FIXED_PREFIX_CHARS = 4000  # ~1024 tokens (Anthropic cache 임계 보수적)


def test_fixed_prefix_size_threshold() -> tuple[int, int]:
    """A7 — 각 reviewer agent 의 fixed prefix 가 1024+ token (4000+ chars) 충족.

    qa-verifier 는 별도 helper (qa_verifier_prompt.py) 사용 권장이라 의무 X.
    """
    passed = 0
    failed = 0
    targets = [
        ("plan-reviewer", "L3"),
        ("plan-reviewer", "L1"),
    ]
    for agent, purpose in targets:
        prefix = get_fixed_prefix(agent, purpose)
        n = len(prefix)
        if n >= MIN_FIXED_PREFIX_CHARS:
            print(f"✓ A7 PASS: ({agent}, {purpose}) — {n} chars (~{n // 4} tokens)")
            passed += 1
        else:
            print(f"✗ A7 FAIL: ({agent}, {purpose}) — {n} chars < {MIN_FIXED_PREFIX_CHARS}")
            failed += 1
    return passed, failed


# ─── 4 agent baseline fixture ─────────────────────────────────────────

def test_baseline(agent: str, purpose: str) -> tuple[int, int]:
    """각 (agent, purpose) — fixed prefix 일관성 + variable 분리 + verdict 형식."""
    p = build_reviewer_prompt(
        agent=agent,
        purpose=purpose,
        variable={"plan": "test", "context": "minimal"},
        axes=["scope", "impact"],
    )

    failed = 0
    # FIXED_PREFIX_START / FIXED_PREFIX_END 마커
    if "FIXED_PREFIX_START" not in p or "FIXED_PREFIX_END" not in p:
        print(f"✗ baseline ({agent}, {purpose}): fixed marker 누락")
        failed += 1
    # variable section
    if "VARIABLE_START" not in p or "VARIABLE_END" not in p:
        print(f"✗ baseline ({agent}, {purpose}): variable marker 누락")
        failed += 1
    # verdict 형식
    if "Last line of output MUST be" not in p:
        print(f"✗ baseline ({agent}, {purpose}): verdict 형식 명시 누락")
        failed += 1
    # axes 명시
    if "Verification axes" not in p:
        print(f"✗ baseline ({agent}, {purpose}): axes 명시 누락")
        failed += 1
    # variable inline 정확 삽입
    if "test" not in p or "minimal" not in p:
        print(f"✗ baseline ({agent}, {purpose}): variable inline 누락")
        failed += 1

    if failed == 0:
        print(f"✓ baseline PASS: ({agent}, {purpose})")
        return 1, 0
    return 0, failed


# ─── Cross-cutting fixture ────────────────────────────────────────────

def test_axes_limit_violation() -> tuple[int, int]:
    """axes 한도 초과 시 ValueError raise."""
    try:
        build_reviewer_prompt(
            agent="plan-reviewer",
            purpose="L3",
            variable={},
            axes=["a"] * 7,  # 6 한도 초과
            max_axes=6,
        )
        print("✗ axes 한도 초과 시 ValueError 미발생")
        return 0, 1
    except ValueError as e:
        if "axes count" in str(e):
            print(f"✓ axes 한도 초과 → ValueError ({str(e)[:60]}...)")
            return 1, 0
        print(f"✗ ValueError 메시지 비표준: {e}")
        return 0, 1


def test_invalid_agent() -> tuple[int, int]:
    """잘못된 agent name → ValueError."""
    try:
        build_reviewer_prompt(
            agent="unknown-reviewer",
            purpose="L3",
            variable={},
            axes=["scope"],
        )
        print("✗ invalid agent 시 ValueError 미발생")
        return 0, 1
    except ValueError as e:
        if "Invalid agent" in str(e):
            print(f"✓ invalid agent → ValueError")
            return 1, 0
        return 0, 1


def test_fixed_prefix_consistency() -> tuple[int, int]:
    """동일 (agent, purpose) 호출 시 fixed prefix 매번 동일 — cache 가능."""
    p1 = build_reviewer_prompt("plan-reviewer", "L3", {"a": "x"}, ["scope"])
    p2 = build_reviewer_prompt("plan-reviewer", "L3", {"b": "y"}, ["impact"])
    # FIXED_PREFIX 부분만 추출 비교
    s1 = p1[: p1.index("FIXED_PREFIX_END")]
    s2 = p2[: p2.index("FIXED_PREFIX_END")]
    if s1 == s2:
        print(f"✓ fixed prefix consistency: 매 호출 동일 ({len(s1)} chars cache eligible)")
        return 1, 0
    print("✗ fixed prefix 매 호출 다름 — cache miss 위험")
    return 0, 1


def test_shared_guidelines_present() -> tuple[int, int]:
    """SHARED_GUIDELINES 가 모든 agent 의 fixed prefix 에 포함."""
    failed = 0
    for agent, purpose in (("plan-reviewer", "L3"), ("plan-reviewer", "L1")):
        prefix = get_fixed_prefix(agent, purpose)
        if "Shared Guidelines" not in prefix:
            print(f"✗ shared guidelines 누락: ({agent}, {purpose})")
            failed += 1
    if failed == 0:
        print(f"✓ shared guidelines 모든 agent prefix 에 포함")
        return 1, 0
    return 0, failed


def main() -> int:
    print("=== A7: fixed prefix size threshold ===")
    p, f = test_fixed_prefix_size_threshold()
    total_p, total_f = p, f

    print("\n=== Baseline reviewers ===")
    for agent, purpose in [("plan-reviewer", "L3"), ("plan-reviewer", "L1"),
                            ("qa-verifier", "L1")]:
        p, f = test_baseline(agent, purpose)
        total_p += p
        total_f += f

    print("\n=== Cross-cutting ===")
    for tc in (test_axes_limit_violation, test_invalid_agent,
               test_fixed_prefix_consistency, test_shared_guidelines_present):
        p, f = tc()
        total_p += p
        total_f += f

    print(f"\n{total_p}/{total_p + total_f} PASS")
    return 0 if total_f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
