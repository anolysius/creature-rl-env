#!/usr/bin/env python3
"""
domain: lifecycle
test_retro_proposals — retro_proposals 단위 테스트.

실행: python3 .claude/skills/_lib/test_retro_proposals.py
"""
import unittest

from retro_proposals import append, list_all, list_pending, parse_line, set_status

QUEUE = """\
# Retro Proposals

## 큐

- [seeded] gate-card-escalation | 2026-06-16 | task-seed | escalation 게이트 카드 미적용 | escalation 확장
- [proposed] foo-guard | 2026-06-16 | manual-revert | 무언가 빈틈 | hook 추가
"""


class TestParse(unittest.TestCase):
    def test_parse_line(self):
        d = parse_line("- [proposed] foo-guard | 2026-06-16 | manual-revert | 빈틈 | hook 추가")
        self.assertEqual(d["status"], "proposed")
        self.assertEqual(d["id"], "foo-guard")
        self.assertEqual(d["trigger"], "manual-revert")
        self.assertEqual(d["proposal"], "hook 추가")

    def test_parse_non_line(self):
        self.assertIsNone(parse_line("## 큐"))
        self.assertIsNone(parse_line("- 그냥 불릿"))


class TestList(unittest.TestCase):
    def test_list_all(self):
        self.assertEqual(len(list_all(QUEUE)), 2)

    def test_list_pending_filters(self):
        pend = list_pending(QUEUE)
        self.assertEqual(len(pend), 1)
        self.assertEqual(pend[0]["id"], "foo-guard")


class TestAppend(unittest.TestCase):
    def test_append_adds_pending(self):
        out = append(QUEUE, "bar-guard", "2026-06-16", "user-correction", "오인", "rule 보강")
        pend = list_pending(out)
        self.assertEqual(len(pend), 2)
        self.assertTrue(any(d["id"] == "bar-guard" for d in pend))

    def test_append_idempotent(self):
        # 동일 id 재적재 안 함
        out = append(QUEUE, "foo-guard", "2026-06-16", "manual-revert", "x", "y")
        self.assertEqual(len(list_all(out)), 2)


class TestSetStatus(unittest.TestCase):
    def test_seed_transition(self):
        out = set_status(QUEUE, "foo-guard", "seeded")
        self.assertEqual(len(list_pending(out)), 0)  # proposed → seeded
        self.assertTrue(any(d["id"] == "foo-guard" and d["status"] == "seeded"
                            for d in list_all(out)))

    def test_dismiss_transition(self):
        out = set_status(QUEUE, "foo-guard", "dismissed")
        self.assertEqual(len(list_pending(out)), 0)

    def test_unknown_id_noop(self):
        out = set_status(QUEUE, "nonexistent", "seeded")
        self.assertEqual(list_all(out), list_all(QUEUE))

    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            set_status(QUEUE, "foo-guard", "bogus")


class TestEmptyQueue(unittest.TestCase):
    def test_empty(self):
        empty = "# Retro Proposals\n\n## 큐\n"
        self.assertEqual(list_all(empty), [])
        self.assertEqual(list_pending(empty), [])
        out = append(empty, "first", "2026-06-16", "no-progress", "s", "p")
        self.assertEqual(len(list_pending(out)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
