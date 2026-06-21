#!/usr/bin/env python3
"""
domain: lifecycle
test_worktree_safety — classify_worktree_safety() 8 시나리오 검증 (코어 6 + 보너스 2).

실행: `python3 .claude/hooks/_lib/test_worktree_safety.py`
exit 0 = 모두 통과, exit 1 = fail
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from worktree_safety import classify_worktree_safety, DISABLE_ENV  # noqa: E402


def assert_eq(actual, expected, label):
    if actual != expected:
        print(f"  ✗ FAIL [{label}]: expected={expected!r}, actual={actual!r}")
        return False
    print(f"  ✓ PASS [{label}]")
    return True


def scenario(name, info, expected_verdict):
    print(f"\n[{name}]")
    result = classify_worktree_safety(info)
    print(f"  reason: {result['reason']}")
    return assert_eq(result["verdict"], expected_verdict, "verdict")


def main() -> int:
    # 환경변수 비활성화 보장
    os.environ.pop(DISABLE_ENV, None)

    passes = []

    # 1. 빈 파일만 → AUTO_DISCARD
    passes.append(scenario(
        "빈 파일만",
        {
            "locked": False,
            "commits_ahead": 0,
            "files_meta": [{"path": "test.txt", "size": 0, "type": "untracked"}],
        },
        "AUTO_DISCARD",
    ))

    # 2. 의미 파일 → ASK_USER
    passes.append(scenario(
        "의미 파일",
        {
            "locked": False,
            "commits_ahead": 0,
            "files_meta": [{"path": "src/Button.tsx", "size": 1500, "type": "modified"}],
        },
        "ASK_USER",
    ))

    # 3. 다파일 임시 패턴 ≤5 → AUTO_DISCARD (narrowed pattern: tmp/temp/foo/bar 만)
    passes.append(scenario(
        "다파일 임시 패턴 (5건)",
        {
            "locked": False,
            "commits_ahead": 0,
            "files_meta": [
                {"path": "tmp.txt", "size": 10, "type": "untracked"},      # name match (tmp)
                {"path": "tmp.log", "size": 0, "type": "untracked"},       # ext match
                {"path": "temp.swp", "size": 0, "type": "untracked"},      # ext match
                {"path": "foo.bak", "size": 5, "type": "untracked"},       # name match (foo)
                {"path": "bar.pyc", "size": 100, "type": "untracked"},     # name match (bar)
            ],
        },
        "AUTO_DISCARD",
    ))

    # 4. 다파일 임시 패턴 >5 → ASK_USER (한도 초과)
    passes.append(scenario(
        "다파일 임시 패턴 (6건 — 한도 초과)",
        {
            "locked": False,
            "commits_ahead": 0,
            "files_meta": [
                {"path": "test.txt", "size": 0, "type": "untracked"},
                {"path": "tmp.log", "size": 0, "type": "untracked"},
                {"path": "debug.swp", "size": 0, "type": "untracked"},
                {"path": "foo.bak", "size": 0, "type": "untracked"},
                {"path": "bar.pyc", "size": 0, "type": "untracked"},
                {"path": "synthetic.tmp", "size": 0, "type": "untracked"},
            ],
        },
        "ASK_USER",
    ))

    # 5. locked → ASK_USER
    passes.append(scenario(
        "locked",
        {
            "locked": True,
            "commits_ahead": 0,
            "files_meta": [{"path": "test.txt", "size": 0, "type": "untracked"}],
        },
        "ASK_USER",
    ))

    # 6. commits_ahead > 0 → ASK_USER
    passes.append(scenario(
        "commits_ahead > 0",
        {
            "locked": False,
            "commits_ahead": 2,
            "files_meta": [{"path": "test.txt", "size": 0, "type": "untracked"}],
        },
        "ASK_USER",
    ))

    # 7. (보너스) 환경변수 비활성 → ASK_USER (분류 무시)
    os.environ[DISABLE_ENV] = "1"
    passes.append(scenario(
        "HARNESS_WT_AUTO_DISCARD_DISABLE=1 (강제 ASK_USER)",
        {
            "locked": False,
            "commits_ahead": 0,
            "files_meta": [{"path": "test.txt", "size": 0, "type": "untracked"}],
        },
        "ASK_USER",
    ))
    os.environ.pop(DISABLE_ENV, None)

    # 8. (보너스) 의미 파일 + 빈 파일 mix → ASK_USER
    passes.append(scenario(
        "mix (의미 파일 + 빈 파일)",
        {
            "locked": False,
            "commits_ahead": 0,
            "files_meta": [
                {"path": "test.txt", "size": 0, "type": "untracked"},
                {"path": "src/Real.tsx", "size": 500, "type": "modified"},
            ],
        },
        "ASK_USER",
    ))

    # 9. (보너스, narrowing 회귀) test.tsx (800 bytes 진짜 prototype) → ASK_USER
    #    L3 SUGGEST-1 흡수 — pattern narrowing 으로 'test/sample/debug/synthetic' 제외 검증
    passes.append(scenario(
        "narrowing 회귀: test.tsx 진짜 prototype (800 bytes)",
        {
            "locked": False,
            "commits_ahead": 0,
            "files_meta": [
                {"path": "test.tsx", "size": 800, "type": "untracked"},
            ],
        },
        "ASK_USER",
    ))

    print(f"\n--- {sum(passes)}/{len(passes)} passed ---")
    return 0 if all(passes) else 1


if __name__ == "__main__":
    sys.exit(main())
