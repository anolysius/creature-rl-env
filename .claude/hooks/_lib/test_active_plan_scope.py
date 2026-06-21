#!/usr/bin/env python3
# domain: lifecycle
"""test_active_plan_scope — 하네스 우회 게이트 결정 로직 단위테스트 (합성 fixture).

plan Step 1 의 5 케이스:
  ① frozen plan 커버 → covering plan 반환
  ② frozen plan 없음 → None (비커버)
  ③ trivial edit 판정 (단일라인 ∧ ≤120자)
  ④ 대상/비대상 경로 (src vs .claude·docs)
  ⑤ scope_paths fnmatch 경계
"""
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import active_plan_scope as aps


def _write_plan(active_dir: Path, slug: str, frozen: bool, scope_paths):
    d = active_dir / slug
    d.mkdir(parents=True, exist_ok=True)
    sp = "\n".join(f"  - {p}" for p in scope_paths)
    (d / "plan.md").write_text(textwrap.dedent(f"""\
        ---
        slug: {slug}
        acceptance_freeze: {'true' if frozen else 'pending'}
        scope_paths:
        {sp}
        ---
        # {slug}
        """), encoding="utf-8")
    return d / "plan.md"


class TestIsTargetPath(unittest.TestCase):
    """④ src/** 만 게이트 대상."""

    def test_envs_is_target(self):
        self.assertTrue(aps.is_target_path("src/critter_gym/envs/critter_env.py", project_root="/repo"))

    def test_spaces_is_target(self):
        self.assertTrue(aps.is_target_path("src/critter_gym/spaces/obs.py", project_root="/repo"))

    def test_claude_not_target(self):
        self.assertFalse(aps.is_target_path(".claude/hooks/x.py", project_root="/repo"))

    def test_docs_not_target(self):
        self.assertFalse(aps.is_target_path("docs/_active/foo/plan.md", project_root="/repo"))

    def test_tests_not_target(self):
        self.assertFalse(aps.is_target_path("tests/test_env.py", project_root="/repo"))

    def test_absolute_path_relativized(self):
        self.assertTrue(aps.is_target_path("/repo/src/critter_gym/render/viewer.py", project_root="/repo"))
        self.assertFalse(aps.is_target_path("/repo/.claude/hooks/x.py", project_root="/repo"))

    def test_root_config_not_target(self):
        self.assertFalse(aps.is_target_path("pyproject.toml", project_root="/repo"))


class TestIsTrivialEdit(unittest.TestCase):
    """③ trivial = Edit ∧ 단일라인 ∧ ≤120 비공백자."""

    def test_single_line_small_is_trivial(self):
        ti = {"old_string": "const a = 1;", "new_string": "const a = 2;"}
        self.assertTrue(aps.is_trivial_edit("Edit", ti))

    def test_multiline_not_trivial(self):
        ti = {"old_string": "a\nb", "new_string": "a\nc"}
        self.assertFalse(aps.is_trivial_edit("Edit", ti))

    def test_long_change_not_trivial(self):
        ti = {"old_string": "x" * 5, "new_string": "y" * 200}
        self.assertFalse(aps.is_trivial_edit("Edit", ti))

    def test_write_never_trivial(self):
        ti = {"content": "small"}
        self.assertFalse(aps.is_trivial_edit("Write", ti))

    def test_boundary_120_is_trivial(self):
        ti = {"old_string": "a", "new_string": "y" * 120}
        self.assertTrue(aps.is_trivial_edit("Edit", ti))

    def test_boundary_121_not_trivial(self):
        ti = {"old_string": "a", "new_string": "y" * 121}
        self.assertFalse(aps.is_trivial_edit("Edit", ti))

    def test_whitespace_excluded_from_count(self):
        # 200 spaces + 3 non-space → 비공백 3 → trivial
        ti = {"old_string": "a", "new_string": (" " * 200) + "abc"}
        self.assertTrue(aps.is_trivial_edit("Edit", ti))


class TestFindCoveringPlan(unittest.TestCase):
    """① frozen plan 커버 / ② 비커버 / ⑤ fnmatch 경계."""

    def test_frozen_plan_covers(self):
        with TemporaryDirectory() as d:
            active = Path(d) / "docs" / "_active"
            _write_plan(active, "t1", frozen=True, scope_paths=["src/critter_gym/envs/**"])
            got = aps.find_covering_plan(
                "src/critter_gym/envs/critter_env.py", active_dir=active, project_root=d)
            self.assertIsNotNone(got)
            self.assertTrue(str(got).endswith("t1/plan.md"))

    def test_not_frozen_does_not_cover(self):
        with TemporaryDirectory() as d:
            active = Path(d) / "docs" / "_active"
            _write_plan(active, "t1", frozen=False, scope_paths=["src/critter_gym/**"])
            got = aps.find_covering_plan(
                "src/critter_gym/envs/x.py", active_dir=active, project_root=d)
            self.assertIsNone(got)

    def test_frozen_but_out_of_scope(self):
        with TemporaryDirectory() as d:
            active = Path(d) / "docs" / "_active"
            _write_plan(active, "t1", frozen=True, scope_paths=["src/critter_gym/spaces/**"])
            got = aps.find_covering_plan(
                "src/critter_gym/envs/x.py", active_dir=active, project_root=d)
            self.assertIsNone(got)

    def test_multiple_plans_one_covers(self):
        with TemporaryDirectory() as d:
            active = Path(d) / "docs" / "_active"
            _write_plan(active, "t1", frozen=True, scope_paths=["src/critter_gym/spaces/**"])
            _write_plan(active, "t2", frozen=True, scope_paths=["src/critter_gym/render/**"])
            got = aps.find_covering_plan(
                "src/critter_gym/render/viewer.py", active_dir=active, project_root=d)
            self.assertIsNotNone(got)
            self.assertTrue(str(got).endswith("t2/plan.md"))

    def test_no_active_dir(self):
        with TemporaryDirectory() as d:
            got = aps.find_covering_plan(
                "src/critter_gym/envs/x.py", active_dir=Path(d) / "nope", project_root=d)
            self.assertIsNone(got)


class TestDecide(unittest.TestCase):
    """게이트 종합 결정 (hook 이 호출) — gated True 면 BLOCK."""

    def _setup(self, d, frozen_scope=None):
        active = Path(d) / "docs" / "_active"
        if frozen_scope is not None:
            _write_plan(active, "t1", frozen=True, scope_paths=frozen_scope)
        return active

    def test_block_when_target_no_cover(self):
        with TemporaryDirectory() as d:
            active = self._setup(d)  # plan 없음
            gated, _ = aps.decide("Write", {"file_path": "src/critter_gym/envs/new.py",
                                            "content": "x"}, active_dir=active, project_root=d)
            self.assertTrue(gated)

    def test_pass_when_covered(self):
        with TemporaryDirectory() as d:
            active = self._setup(d, frozen_scope=["src/critter_gym/**"])
            gated, _ = aps.decide("Write", {"file_path": "src/critter_gym/envs/new.py",
                                            "content": "x"}, active_dir=active, project_root=d)
            self.assertFalse(gated)

    def test_pass_when_not_target(self):
        with TemporaryDirectory() as d:
            active = self._setup(d)
            gated, _ = aps.decide("Write", {"file_path": ".claude/hooks/x.py",
                                            "content": "x"}, active_dir=active, project_root=d)
            self.assertFalse(gated)

    def test_pass_when_trivial(self):
        with TemporaryDirectory() as d:
            active = self._setup(d)
            gated, _ = aps.decide("Edit", {"file_path": "src/critter_gym/envs/x.py",
                                           "old_string": "a=1", "new_string": "a=2"},
                                  active_dir=active, project_root=d)
            self.assertFalse(gated)


if __name__ == "__main__":
    unittest.main()
