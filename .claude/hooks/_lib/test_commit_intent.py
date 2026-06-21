#!/usr/bin/env python3
# domain: lifecycle
"""test_commit_intent — commit-authorization gate 결정 로직 단위테스트.

plan Step 1 의 4 케이스:
  ① 인가/비인가 발화
  ② commit/push 감지 vs status/diff/add 제외
  ③ state write→read round-trip
  ④ state 없음 → None
"""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import commit_intent as ci


class TestIsAuthorizingPrompt(unittest.TestCase):
    def test_korean_commit(self):
        self.assertTrue(ci.is_authorizing_prompt("커밋 푸시 해줘"))

    def test_korean_push(self):
        self.assertTrue(ci.is_authorizing_prompt("이거 푸시해줘"))

    def test_english_commit(self):
        self.assertTrue(ci.is_authorizing_prompt("commit and push this"))

    def test_merge_pr(self):
        self.assertTrue(ci.is_authorizing_prompt("PR 올려줘"))
        self.assertTrue(ci.is_authorizing_prompt("main 에 반영해줘"))

    def test_non_authorizing(self):
        self.assertFalse(ci.is_authorizing_prompt("이 컴포넌트 리팩터해줘"))
        self.assertFalse(ci.is_authorizing_prompt("테스트 돌려줘"))
        self.assertFalse(ci.is_authorizing_prompt("task 끝내줘"))

    def test_negation_not_authorizing(self):
        # "커밋" 있어도 부정이면 미인가
        self.assertFalse(ci.is_authorizing_prompt("커밋하지마"))
        self.assertFalse(ci.is_authorizing_prompt("아직 커밋 하지 마"))
        self.assertFalse(ci.is_authorizing_prompt("커밋 말고 그냥 보여줘"))


class TestIsCommitCommand(unittest.TestCase):
    def test_plain_commit(self):
        self.assertTrue(ci.is_commit_command("git commit -m 'x'"))

    def test_plain_push(self):
        self.assertTrue(ci.is_commit_command("git push origin main"))

    def test_push_upstream(self):
        self.assertTrue(ci.is_commit_command("git push"))

    def test_compound_add_commit(self):
        self.assertTrue(ci.is_commit_command("git add -A && git commit -m 'x'"))

    def test_compound_commit_push(self):
        self.assertTrue(ci.is_commit_command("git commit -m x && git push"))

    def test_git_C_global_flag(self):
        self.assertTrue(ci.is_commit_command("git -C /repo commit -m x"))

    def test_status_not_commit(self):
        self.assertFalse(ci.is_commit_command("git status"))

    def test_diff_not_commit(self):
        self.assertFalse(ci.is_commit_command("git diff --cached"))

    def test_add_not_commit(self):
        self.assertFalse(ci.is_commit_command("git add ."))

    def test_mv_not_commit(self):
        self.assertFalse(ci.is_commit_command("git mv a b"))

    def test_log_not_commit(self):
        self.assertFalse(ci.is_commit_command("git log --oneline"))

    def test_non_git(self):
        self.assertFalse(ci.is_commit_command("echo commit"))

    def test_commit_substring_safe(self):
        # 'commit' 이 경로/메시지에 있어도 subcommand 아니면 False
        self.assertFalse(ci.is_commit_command("cat docs/commit-notes.md"))

    def test_malformed_quotes_fallopen_false(self):
        # shlex 실패 시 보수적 — commit 토큰 단순 포함 검사로 fallback 가능하나
        # 최소 git+commit 동시 포함일 때만 True
        self.assertFalse(ci.is_commit_command("echo 'unclosed"))


class TestState(unittest.TestCase):
    def test_write_read_roundtrip(self):
        with TemporaryDirectory() as d:
            ci.write_state(True, "커밋 해줘", root=d)
            st = ci.read_state(root=d)
            self.assertIsNotNone(st)
            self.assertTrue(st["authorized"])
            self.assertIn("snippet", st)

    def test_write_false(self):
        with TemporaryDirectory() as d:
            ci.write_state(False, "리팩터", root=d)
            st = ci.read_state(root=d)
            self.assertFalse(st["authorized"])

    def test_overwrite_latest_wins(self):
        with TemporaryDirectory() as d:
            ci.write_state(True, "커밋", root=d)
            ci.write_state(False, "고마워", root=d)
            self.assertFalse(ci.read_state(root=d)["authorized"])

    def test_no_state_returns_none(self):
        with TemporaryDirectory() as d:
            self.assertIsNone(ci.read_state(root=d))


if __name__ == "__main__":
    unittest.main()
