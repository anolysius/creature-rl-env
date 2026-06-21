#!/usr/bin/env python3
"""
domain: lifecycle
test_git_policy — branch 분류·머지 의도 파싱·정책 위반 판정 unit test.

10 케이스 (rules/85 acceptance 1:1):
- 합법 5: feature→qa, feature→main(PR), main→qa(sync), main→feature(sync), cherry-pick(-x)
- 위반 5: qa→feature, qa→feature(2), qa→main, qa→qa(cross), forbidden prefix push

이 fixture 는 sink 카테고리 동작을 검증하기 위해 가상의 'qa' sink prefix 를
정의한다. 실제 프로젝트 config (.claude/data/git-branch-prefixes.json) 의 sink 는
기본 비어 있으며, sink 분기를 도입할 때 이 엔진이 그대로 동작함을 보장한다.

실행: python3 .claude/hooks/_lib/test_git_policy.py
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from git_policy import (  # noqa: E402
    classify_branch,
    is_violation,
    parse_cherry_pick,
    parse_merge_intent,
    parse_push_intent,
)


PREFIXES = {
    "source": ["feature", "fix", "hotfix", "chore", "docs"],
    "sink": ["qa"],
    "trunk": ["main"],
    "special": ["backup", "renovate", "archive"],
    "forbidden_patterns": [r"^qa-(?!.*/)", r"^dev$"],
}


class TestClassifyBranch(unittest.TestCase):
    def test_source(self):
        self.assertEqual(classify_branch("feature/git-policy", PREFIXES), "source")
        self.assertEqual(classify_branch("fix/reward-bug", PREFIXES), "source")
        self.assertEqual(classify_branch("hotfix/env-reset", PREFIXES), "source")

    def test_sink(self):
        self.assertEqual(classify_branch("qa/global", PREFIXES), "sink")
        self.assertEqual(classify_branch("qa/kr", PREFIXES), "sink")
        self.assertEqual(classify_branch("qa/global-mobile", PREFIXES), "sink")

    def test_trunk(self):
        self.assertEqual(classify_branch("main", PREFIXES), "trunk")

    def test_special(self):
        self.assertEqual(classify_branch("backup/temp-pc", PREFIXES), "special")
        self.assertEqual(classify_branch("renovate/configure", PREFIXES), "special")

    def test_forbidden(self):
        self.assertEqual(classify_branch("qa-cart-fix", PREFIXES), "forbidden")
        self.assertEqual(classify_branch("dev", PREFIXES), "forbidden")
        self.assertEqual(classify_branch("random", PREFIXES), "forbidden")
        self.assertEqual(classify_branch("temp/option-renewal", PREFIXES), "forbidden")


class TestParseMergeIntent(unittest.TestCase):
    def test_merge_basic(self):
        intent = parse_merge_intent("git merge qa/global")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.source_ref, "qa/global")

    def test_merge_no_ff(self):
        intent = parse_merge_intent("git merge --no-ff feature/x")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.source_ref, "feature/x")

    def test_merge_origin_strip(self):
        intent = parse_merge_intent("git merge origin/qa/kr")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.source_ref, "qa/kr")

    def test_pull(self):
        intent = parse_merge_intent("git pull origin main")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.source_ref, "main")

    def test_pull_bare(self):
        self.assertIsNone(parse_merge_intent("git pull"))

    def test_not_merge(self):
        self.assertIsNone(parse_merge_intent("git status"))
        self.assertIsNone(parse_merge_intent("git log"))


class TestParsePushIntent(unittest.TestCase):
    def test_push_basic(self):
        intent = parse_push_intent("git push origin feature/x")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.target_ref, "feature/x")
        self.assertEqual(intent.remote, "origin")

    def test_push_refspec(self):
        intent = parse_push_intent("git push origin local-branch:qa/kr")
        self.assertIsNotNone(intent)
        self.assertEqual(intent.target_ref, "qa/kr")

    def test_push_bare(self):
        self.assertIsNone(parse_push_intent("git push"))

    def test_not_push(self):
        self.assertIsNone(parse_push_intent("git fetch origin"))


class TestCherryPick(unittest.TestCase):
    def test_cherry_pick_recognized(self):
        self.assertTrue(parse_cherry_pick("git cherry-pick -x abc123"))
        self.assertTrue(parse_cherry_pick("git cherry-pick abc123 def456"))

    def test_not_cherry_pick(self):
        self.assertFalse(parse_cherry_pick("git merge qa/global"))
        self.assertFalse(parse_cherry_pick("git revert abc123"))


class TestIsViolation(unittest.TestCase):
    """rules/85 의 5 합법 + 5 위반 (acceptance fixture)."""

    # === 합법 5 ===
    def test_legal_feature_to_qa(self):
        intent = parse_merge_intent("git merge feature/x")
        self.assertIsNone(is_violation(intent, current_branch="qa/kr", prefixes=PREFIXES))

    def test_legal_feature_to_main_via_pr(self):
        intent = parse_merge_intent("git merge feature/x")
        self.assertIsNone(is_violation(intent, current_branch="main", prefixes=PREFIXES))

    def test_legal_main_to_qa_sync(self):
        intent = parse_merge_intent("git merge main")
        self.assertIsNone(is_violation(intent, current_branch="qa/kr", prefixes=PREFIXES))

    def test_legal_main_to_feature_sync(self):
        intent = parse_merge_intent("git merge main")
        self.assertIsNone(is_violation(intent, current_branch="feature/x", prefixes=PREFIXES))

    def test_legal_cherry_pick_qa_to_main(self):
        # cherry-pick 은 escape hatch — parse_cherry_pick 가 분기, is_violation 미경유
        self.assertTrue(parse_cherry_pick("git cherry-pick -x deadbeef"))

    # === 위반 5 ===
    def test_violation_qa_to_feature(self):
        """sink → source 머지는 단방향 정책 위반."""
        intent = parse_merge_intent("git merge qa/global")
        v = is_violation(intent, current_branch="feature/curriculum-sampler", prefixes=PREFIXES)
        self.assertIsNotNone(v)
        self.assertEqual(v.kind, "sink_source")

    def test_violation_qa_to_feature_2(self):
        intent = parse_merge_intent("git merge qa/kr")
        v = is_violation(intent, current_branch="feature/x", prefixes=PREFIXES)
        self.assertIsNotNone(v)

    def test_violation_qa_to_main(self):
        intent = parse_merge_intent("git merge qa/global")
        v = is_violation(intent, current_branch="main", prefixes=PREFIXES)
        self.assertIsNotNone(v)
        self.assertEqual(v.kind, "sink_source")

    def test_violation_qa_cross(self):
        """qa/* → qa/* cross 머지"""
        intent = parse_merge_intent("git merge qa/kr")
        v = is_violation(intent, current_branch="qa/global", prefixes=PREFIXES)
        self.assertIsNotNone(v)
        self.assertIn("cross", v.detail.lower())

    def test_violation_forbidden_push(self):
        intent = parse_push_intent("git push origin qa-test")
        v = is_violation(intent, current_branch=None, prefixes=PREFIXES)
        self.assertIsNotNone(v)
        self.assertEqual(v.kind, "forbidden_prefix")


if __name__ == "__main__":
    unittest.main(verbosity=2)
