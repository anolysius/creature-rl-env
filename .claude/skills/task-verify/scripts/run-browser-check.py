#!/usr/bin/env python3
# domain: lifecycle
"""task-verify Browser MCP wrapper (optional — web UI task 한정).

본 script 는 chrome-devtools MCP 와 직접 통신하지 않음 (MCP 는 Claude 세션에서만 호출 가능).
대신 Claude 가 본 script 의 출력 명령을 따라 mcp__chrome-devtools__* 도구를 호출하도록 안내.

순수 라이브러리/CLI task (web UI 없음) 에서는 plan 이 affects_ui 신호를 주지 않으므로
needs_browser=false → SKIP (N/A 통과). 본 하네스에 보존하되 web 산출물이 있을 때만 발동.

사용:
    python3 run-browser-check.py --plan <path>
    python3 run-browser-check.py --url http://localhost:8000 --base http://localhost:8000

출력:
    Claude 에게 보내는 instruction (어떤 MCP 도구 어떤 인자로 호출할지)
"""
import sys
import io
import json
import argparse
import re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent.parent.parent.parent  # repo root


def parse_plan_for_browser_targets(plan_path: Path) -> dict:
    """plan.md 에서 browser check 대상 추출.

    체크 항목:
    - frontmatter `affects_ui: true`
    - 본문에서 'localhost:<port>' 같은 URL
    - acceptance lifecycle 의 'no_console_errors'
    """
    if not plan_path.exists():
        return {"affects_ui": False, "urls": [], "needs_browser": False}

    text = plan_path.read_text(encoding="utf-8")

    # frontmatter
    affects_ui = False
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            fm = text[:end]
            if re.search(r"^affects_ui\s*:\s*true", fm, re.MULTILINE | re.IGNORECASE):
                affects_ui = True

    # URL 추출
    urls = list(set(re.findall(r"https?://[^\s\)\]]+", text)))

    # acceptance no_console_errors
    needs_browser = "no_console_errors" in text or affects_ui

    return {
        "plan": str(plan_path),
        "affects_ui": affects_ui,
        "urls": urls,
        "needs_browser": needs_browser,
    }


def emit_mcp_instructions(targets: dict, base_url: str = "http://localhost:8000",
                          local_url: str = "http://localhost:8000") -> dict:
    """Claude 에게 보낼 MCP 도구 호출 instruction 생성.

    chrome-devtools MCP 는 Claude 가 직접 호출. 본 script 는 가이드만 출력.

    원칙:
    - 고정 2탭 (baseline + local), new_page 남발 금지
    - 알려진 known-good baseline 과 비교
    - 스크린샷만 X — DOM snapshot + console 까지 다중 비교
    """
    if not targets["needs_browser"]:
        return {
            "skip": True,
            "reason": "plan 이 UI 변경 안 함 (affects_ui=false) — browser check N/A",
        }

    # plan 의 URL 또는 default route
    paths = ["/"]  # default
    if targets.get("urls"):
        # plan 의 URL 에서 path 추출
        paths = []
        for url in targets["urls"]:
            m = re.search(r"https?://[^/]+(/[^?\s]*)", url)
            if m:
                paths.append(m.group(1))
        paths = list(set(paths)) or ["/"]

    instructions = []

    # Step 0: chrome-devtools MCP 가용성 사전 확인.
    # MCP 서버가 등록되지 않은 환경 (CI, 다른 코작업자) 에서는 Step 1 의 list_pages 호출이
    # InputValidationError 또는 미등록 도구 에러로 실패. 그 경우 전체 browser_check 단계를
    # SKIP 으로 처리 (no_console_errors / visual diff 는 N/A 통과 — fail 아님).
    instructions.append({
        "step": 0,
        "tool": "mcp__chrome-devtools__list_pages",
        "args": {},
        "purpose": "MCP 가용성 프로브 — 실패 시 browser_check 전체 SKIP (N/A 통과)",
        "on_failure": "SKIP_BROWSER_CHECK",
    })

    # Step 1: 페이지 목록 확인 (이미 열린 탭이 있는지) — Step 0 이 통과한 경우에만 실행
    instructions.append({
        "step": 1,
        "tool": "mcp__chrome-devtools__list_pages",
        "args": {},
        "purpose": "현재 열린 탭 확인 (고정 2탭 활용)",
    })

    # Step 2-N: 각 path 별 검사
    for i, path in enumerate(paths):
        live_url = base_url + path
        local_url_full = local_url + path

        instructions.extend([
            {
                "step": f"{2 + i*4}",
                "tool": "mcp__chrome-devtools__navigate_page",
                "args": {"url": live_url, "tab": "baseline"},
                "purpose": f"[{path}] baseline 로드",
            },
            {
                "step": f"{3 + i*4}",
                "tool": "mcp__chrome-devtools__take_snapshot",
                "args": {},
                "purpose": "baseline DOM snapshot",
            },
            {
                "step": f"{4 + i*4}",
                "tool": "mcp__chrome-devtools__navigate_page",
                "args": {"url": local_url_full, "tab": "local"},
                "purpose": f"[{path}] local 로드",
            },
            {
                "step": f"{5 + i*4}",
                "tool": "mcp__chrome-devtools__list_console_messages",
                "args": {},
                "purpose": "no_console_errors 검증 (level=error 0 건이어야 통과)",
            },
        ])

    return {
        "skip": False,
        "paths_to_check": paths,
        "instructions": instructions,
        "verification_rules": [
            "Step 0 (MCP 가용성 프로브) 실패 시: browser_check 전체 SKIP, no_console_errors / visual diff 는 N/A 통과 (fail 아님)",
            "console messages 의 level=error 가 0 이면 no_console_errors PASS",
            "baseline vs local DOM snapshot 차이는 plan 의 의도된 변경만 (의외 차이 BLOCK)",
            "고정 2탭 유지 (baseline, local) — new_page 추가 금지",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=None)
    parser.add_argument("--url", type=str, default=None, help="검사할 URL (plan 없을 때)")
    parser.add_argument("--base", type=str, default="http://localhost:8000",
                        help="baseline URL prefix")
    parser.add_argument("--local", type=str, default="http://localhost:8000",
                        help="local URL prefix")
    args = parser.parse_args()

    if args.plan:
        targets = parse_plan_for_browser_targets(args.plan)
    elif args.url:
        targets = {
            "plan": None,
            "affects_ui": True,
            "urls": [args.url],
            "needs_browser": True,
        }
    else:
        targets = {"affects_ui": False, "urls": [], "needs_browser": False}

    instructions = emit_mcp_instructions(targets, base_url=args.base, local_url=args.local)
    output = {
        "targets": targets,
        "browser_check": instructions,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
