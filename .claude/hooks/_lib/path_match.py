#!/usr/bin/env python3
"""
path_match — fnmatch 래퍼 + Windows/macOS 경로 정규화.

사용 이유:
- Windows의 백슬래시 경로를 슬래시로 정규화
- glob 패턴(**/ 접두사) 처리
- basename과 전체 경로 모두 비교
"""
import os
import fnmatch


def normalize(path: str) -> str:
    """경로 구분자를 슬래시로 통일."""
    return path.replace("\\", "/")


def match_any(file_path: str, patterns: list) -> bool:
    """
    file_path가 주어진 glob 패턴 중 하나라도 매칭되는지 검사.

    인자:
        file_path: 검사할 파일 경로
        patterns:  fnmatch 패턴 리스트 (예: ["**/config.json", "*.md"])

    반환:
        매칭되면 True, 아니면 False
    """
    if not file_path or not patterns:
        return False

    normalized = normalize(file_path)
    basename = os.path.basename(normalized)

    for pattern in patterns:
        # "**/" 접두사 패턴: 파일명 부분만 비교하거나 전체 경로 비교
        if pattern.startswith("**/"):
            file_pattern = pattern[3:]
            if fnmatch.fnmatch(basename, file_pattern):
                return True
            if fnmatch.fnmatch(normalized, pattern):
                return True
        elif fnmatch.fnmatch(normalized, pattern):
            return True
        elif fnmatch.fnmatch(basename, pattern):
            return True

    return False


def match_extension(file_path: str, extensions: set) -> bool:
    """
    파일 확장자 매칭. extensions는 '.py', '.json' 등 dot 포함.

    인자:
        file_path: 검사할 파일 경로
        extensions: {".py", ".json"} 같은 집합

    반환:
        확장자 매칭 시 True
    """
    if not file_path:
        return False
    _, ext = os.path.splitext(file_path)
    return ext.lower() in extensions


if __name__ == "__main__":
    # 간단 self-test
    cases = [
        ("src/config.json", ["**/config.json"], True),
        ("src\\config.json", ["**/config.json"], True),
        ("src/envs/critter.py", ["**/config.json"], False),
        ("foo/bar/baz.lock.json", ["**/*.lock.json"], True),
    ]
    for path, patterns, expected in cases:
        actual = match_any(path, patterns)
        mark = "OK" if actual == expected else "FAIL"
        print(f"[{mark}] match_any({path!r}, {patterns}) = {actual} (expected {expected})")
