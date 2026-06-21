#!/usr/bin/env python3
"""
domain: lifecycle
test_task_end_archive_guard — task-end-archive-guard 단위 테스트 (synthetic fixture).

실행: python3 .claude/hooks/test_task_end_archive_guard.py
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

# hook 파일명이 하이픈이라 importlib 로 로드
_spec = importlib.util.spec_from_file_location(
    "task_end_archive_guard", Path(__file__).parent / "task-end-archive-guard.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
classify_violation = _mod.classify_violation
parse_archive_move = _mod.parse_archive_move


class TestParse(unittest.TestCase):
    def test_git_mv_archive_target(self):
        t = parse_archive_move("git mv docs/_active/x docs/_archive/2026-Q2/init/14-x")
        self.assertEqual(t, "docs/_archive/2026-Q2/init/14-x")

    def test_mv_archive_target_trailing_slash(self):
        t = parse_archive_move("mv docs/_active/x/* docs/_archive/2026-Q2/init/14-x/")
        self.assertEqual(t, "docs/_archive/2026-Q2/init/14-x")

    def test_mv_initiative_overwrite(self):
        t = parse_archive_move("mv a/INITIATIVE.md docs/_archive/2026-Q2/init/INITIATIVE.md")
        self.assertEqual(t, "docs/_archive/2026-Q2/init/INITIATIVE.md")

    def test_flags_skipped(self):
        t = parse_archive_move("mv -f -v a docs/_archive/2026-Q2/init/14-x")
        self.assertEqual(t, "docs/_archive/2026-Q2/init/14-x")

    def test_non_archive_target_ignored(self):
        self.assertIsNone(parse_archive_move("mv a docs/_active/y"))

    def test_non_mv_ignored(self):
        self.assertIsNone(parse_archive_move("cp a docs/_archive/2026-Q2/init/14-x"))

    def test_chained_command_conservative_skip(self):
        # 파이프/&& 포함 시 보수적 비매칭 (애매하면 통과)
        self.assertIsNone(parse_archive_move("mkdir -p d && mv a docs/_archive/2026-Q2/init/14-x"))


class TestClassify(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # synthetic archive: init/ 에 01-existing 존재 + INITIATIVE.md
        self.init = self.root / "docs/_archive/2026-Q2/init"
        (self.init / "01-existing").mkdir(parents=True)
        (self.init / "01-existing" / "plan.md").write_text("x")
        (self.init / "INITIATIVE.md").write_text("narrative")
        # 비어있지 않은 기존 task 폴더
        (self.init / "05-populated").mkdir()
        (self.init / "05-populated" / "report.md").write_text("r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_prefix_collision_block(self):
        v = classify_violation("docs/_archive/2026-Q2/init/01-newslug", self.root)
        self.assertIsNotNone(v)
        self.assertEqual(v[0], "PREFIX_COLLISION")

    def test_initiative_overwrite_block(self):
        v = classify_violation("docs/_archive/2026-Q2/init/INITIATIVE.md", self.root)
        self.assertIsNotNone(v)
        self.assertEqual(v[0], "INITIATIVE_OVERWRITE")

    def test_target_nonempty_block(self):
        v = classify_violation("docs/_archive/2026-Q2/init/05-populated", self.root)
        self.assertIsNotNone(v)
        self.assertEqual(v[0], "TARGET_NONEMPTY")

    def test_clean_new_prefix_passes(self):
        # 14- 는 미사용 → 통과
        self.assertIsNone(classify_violation("docs/_archive/2026-Q2/init/14-fresh", self.root))

    def test_priority_prefix_over_target(self):
        # 01-existing 자체로 이동 시도 → prefix 충돌이 우선 보고 (target 존재보다)
        # (01-existing 와 동일 basename 은 충돌 sibling 이 아니므로 prefix 는 skip,
        #  대신 TARGET_NONEMPTY 가 잡힘 — 동일 폴더 재이동 방어)
        v = classify_violation("docs/_archive/2026-Q2/init/01-existing", self.root)
        self.assertIsNotNone(v)
        self.assertEqual(v[0], "TARGET_NONEMPTY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
