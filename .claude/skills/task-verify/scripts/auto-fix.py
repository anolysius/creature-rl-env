#!/usr/bin/env python3
# domain: lifecycle
"""task-verify 자동수정 — whitelist 만 적용. 그 외 BLOCK + 사용자 승인.

사용:
    python3 auto-fix.py --files src/critter_gym/envs/critter_env.py,...
    python3 auto-fix.py --plan <path> --dry-run

화이트리스트 (안전한 결정론적 수정만):
    - format    (ruff format) — 공백/들여쓰기/quote style
    - lint_fix  (ruff check --fix) — unused import 제거 등 ruff 안전 자동수정

화이트리스트 외:
    BLOCK 응답 + 사용자 승인 요청

주의: 자동수정 도구 (ruff) 는 프로젝트에 설치돼 있어야 한다. 미설치 시
errors 로 보고하고 BLOCK 하지 않는다 (자동수정은 best-effort).
"""
import sys
import io
import re
import json
import argparse
import subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent.parent.parent.parent  # repo root


WHITELIST_FIXES = {
    "lint_fix": {
        "tool": "ruff check --fix",
        "description": "unused import 제거 등 ruff 안전 자동수정",
    },
    "format": {
        "tool": "ruff format",
        "description": "trailing whitespace, indent, quote style",
    },
}

# trailing whitespace 만 deterministic 하게 감지 (언어 무관 안전 신호).
_TRAILING_WS = re.compile(r"[ \t]+$", re.MULTILINE)


def detect_violations(files: list) -> dict:
    """파일들에서 자동수정 가능한 위반 감지 (보수적 — trailing whitespace 만)."""
    violations = {}
    for file_path in files:
        path = ROOT / file_path
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue

        file_violations = []
        ws = _TRAILING_WS.findall(text)
        if ws:
            file_violations.append({
                "type": "format",
                "count": len(ws),
                "samples": ["trailing whitespace"],
            })

        if file_violations:
            violations[file_path] = file_violations

    return violations


def apply_fixes(files: list, types: list, dry_run: bool = False) -> dict:
    """자동수정 적용. dry_run 이면 시뮬레이션만."""
    if not files:
        return {"applied": [], "errors": []}

    results = {"applied": [], "errors": [], "skipped": []}

    for fix_type in types:
        if fix_type not in WHITELIST_FIXES:
            results["skipped"].append({
                "type": fix_type,
                "reason": "whitelist 외 — 자동수정 BLOCK",
            })
            continue

        if fix_type == "lint_fix":
            cmd = ["ruff", "check", "--fix"] + files
        elif fix_type == "format":
            cmd = ["ruff", "format"] + files
        else:  # pragma: no cover — whitelist 가 위에서 보장
            continue

        if dry_run:
            results["applied"].append({
                "type": fix_type,
                "tool": " ".join(cmd),
                "dry_run": True,
            })
            continue

        try:
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
            results["applied"].append({
                "type": fix_type,
                "exit": proc.returncode,
                "stdout_tail": proc.stdout[-500:],
            })
        except FileNotFoundError:
            results["errors"].append({
                "type": fix_type,
                "error": "ruff 미설치 — 자동수정 skip (best-effort)",
            })
        except Exception as e:
            results["errors"].append({"type": fix_type, "error": str(e)})

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", type=str, default="",
                        help="콤마 구분 파일 경로")
    parser.add_argument("--plan", type=Path, default=None,
                        help="plan.md 에서 scope_paths 추출")
    parser.add_argument("--types", type=str, default="lint_fix,format",
                        help="콤마 구분 fix type")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--detect-only", action="store_true",
                        help="위반 감지만, 수정 안 함")
    args = parser.parse_args()

    files = [f.strip() for f in args.files.split(",") if f.strip()]
    types = [t.strip() for t in args.types.split(",") if t.strip()]

    if args.detect_only:
        violations = detect_violations(files)
        print(json.dumps({
            "violations": violations,
            "auto_fixable_count": sum(len(v) for v in violations.values()),
        }, ensure_ascii=False, indent=2))
        return

    # 1) 자동수정 가능한 type 만
    valid_types = [t for t in types if t in WHITELIST_FIXES]
    invalid_types = [t for t in types if t not in WHITELIST_FIXES]

    # 2) 위반 감지
    violations = detect_violations(files)

    # 3) 수정 적용
    results = apply_fixes(files, valid_types, dry_run=args.dry_run)

    # 4) summary
    summary = {
        "files": files,
        "requested_types": types,
        "valid_types": valid_types,
        "blocked_non_whitelist": invalid_types,  # whitelist 외 → BLOCK
        "violations_detected": violations,
        "fixes": results,
        "dry_run": args.dry_run,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
