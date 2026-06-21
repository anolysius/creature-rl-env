#!/usr/bin/env python3
"""
domain: lifecycle
test_qa_verifier_prompt — qa_verifier_prompt.build_self_contained_prompt() unit test.

6 케이스 (Acceptance 1:1):
1. extract_section 정상
2. extract_section 미존재 헤딩 → 빈 문자열
3. build_prompt 정상 — "external read forbidden" + INLINE + verdict 형식 포함
4. build_prompt axes > max → ValueError
5. build_prompt inline 비어있음 → "insufficient" 가이드 포함
6. build_prompt 가 모든 inline 정보 누락 없이 포함
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qa_verifier_prompt import build_self_contained_prompt, extract_section


class TestExtractSection(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "plan.md")
        with open(self.path, "w") as f:
            f.write(
                "# Plan\n"
                "\n"
                "## Acceptance Criteria\n"
                "- [ ] item 1\n"
                "- [ ] item 2\n"
                "\n"
                "## Other Section\n"
                "irrelevant\n"
            )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_normal(self):
        result = extract_section(self.path, "Acceptance Criteria")
        self.assertIn("item 1", result)
        self.assertIn("item 2", result)
        self.assertNotIn("irrelevant", result)

    def test_nonexistent(self):
        result = extract_section(self.path, "Nonexistent")
        self.assertEqual(result, "")


class TestBuildSelfContainedPrompt(unittest.TestCase):
    def test_normal_prompt_has_required_elements(self):
        prompt = build_self_contained_prompt(
            purpose="L3",
            inline_data={"acceptance": "- [ ] item 1", "test_results": "OK"},
            axes=["acceptance 정합", "회귀", "성능"],
        )
        # 4 강제 요소
        self.assertIn("EXTERNAL READ FORBIDDEN", prompt.upper())
        self.assertIn("INLINE:", prompt)
        self.assertIn("APPROVE", prompt)
        self.assertIn("BLOCK:", prompt)

    def test_axes_exceeds_max_raises(self):
        with self.assertRaises(ValueError):
            build_self_contained_prompt(
                purpose="L1",
                inline_data={},
                axes=["a", "b", "c", "d"],  # > max_axes=3
            )

    def test_empty_inline_data_includes_insufficient_guide(self):
        prompt = build_self_contained_prompt(
            purpose="L3",
            inline_data={},
            axes=["acceptance"],
        )
        self.assertIn("insufficient", prompt.lower())

    def test_all_inline_data_present(self):
        inline = {
            "acceptance": "- [ ] xyz uniq_marker",
            "test_results": "test_uniq_marker",
            "elapsed": "elapsed_uniq_marker",
        }
        prompt = build_self_contained_prompt(
            purpose="L3",
            inline_data=inline,
            axes=["acceptance"],
        )
        for v in inline.values():
            self.assertIn(v, prompt)


if __name__ == "__main__":
    unittest.main()
