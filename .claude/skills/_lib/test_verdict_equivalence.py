#!/usr/bin/env python3
# domain: lifecycle
"""test_verdict_equivalence — 결정론 코어 단위테스트 (합성 fixture).

plan Step 1 의 5 케이스:
  ① decision 분포 diff
  ② known-issue recall 산식
  ③ 게이트 PASS/FAIL 경계
  ④ MALFORMED verdict 파싱 위임 (aggregate-verdicts.py 재사용)
  ⑤ corpus 로드

LLM·실제 plan 파일 없이 합성 fixture 로 결정론 부분만 검증.
"""
import json
import tempfile
import unittest
from pathlib import Path

import verdict_equivalence as ve


# ─── 합성 verdict fixture ──────────────────────────────────────────────
APPROVE_TXT = "5축 평가 결과 양호.\n\nAPPROVE"
SUGGEST_TXT = "축 1 미흡.\n\nSUGGEST: scope: scope_paths 보완 권장"
BLOCK_TXT = "축 3 위반.\n\nBLOCK: risk: 회귀 위험 미명시"
# per-axis + summary 혼합 — 최종 decision 은 가장 엄격한 것(BLOCK)
MIXED_BLOCK_TXT = (
    "**축 1**: APPROVE\n"
    "**축 3**: BLOCK: risk: 회귀\n\n"
    "종합:\nBLOCK: risk: 회귀 위험"
)
MALFORMED_TXT = "이 계획은 전반적으로 괜찮아 보입니다만 좀 더 검토가 필요합니다."  # verdict 라인 없음


class TestRunDecision(unittest.TestCase):
    """verdict 텍스트 → 단일 decision 환원 (aggregate-verdicts 파서 위임)."""

    def test_approve(self):
        self.assertEqual(ve.run_decision(APPROVE_TXT), "APPROVE")

    def test_suggest(self):
        self.assertEqual(ve.run_decision(SUGGEST_TXT), "SUGGEST")

    def test_block(self):
        self.assertEqual(ve.run_decision(BLOCK_TXT), "BLOCK")

    def test_mixed_reduces_to_most_severe(self):
        # per-axis APPROVE + BLOCK 혼합 → BLOCK (severity precedence)
        self.assertEqual(ve.run_decision(MIXED_BLOCK_TXT), "BLOCK")

    # ④ MALFORMED 파싱 위임 — heuristic fallback 도 못 잡으면 None
    def test_malformed_returns_none(self):
        self.assertIsNone(ve.run_decision(MALFORMED_TXT))


class TestDiffRuns(unittest.TestCase):
    """① decision 분포 diff — candidate 가 control 대비 악화되지 않았나."""

    def _runs(self, item_id, variant, decisions, known_issue=False, expected="SUGGEST"):
        return [
            ve.Run(item_id=item_id, variant=variant, decision=d,
                   known_issue=known_issue, expected_min_decision=expected)
            for d in decisions
        ]

    def test_identical_control_candidate_full_match(self):
        runs = (
            self._runs("i1", "control", ["BLOCK", "BLOCK", "BLOCK"]) +
            self._runs("i1", "candidate", ["BLOCK", "BLOCK", "BLOCK"])
        )
        diff = ve.diff_runs(runs)
        self.assertEqual(diff["decision_match_rate_overall"], 1.0)

    def test_candidate_downgrade_is_worsening(self):
        # control BLOCK → candidate APPROVE = 악화 (실패)
        runs = (
            self._runs("i1", "control", ["BLOCK", "BLOCK", "BLOCK"]) +
            self._runs("i1", "candidate", ["APPROVE", "APPROVE", "APPROVE"])
        )
        diff = ve.diff_runs(runs)
        self.assertEqual(diff["decision_match_rate_overall"], 0.0)

    def test_candidate_stricter_not_worsening(self):
        # control SUGGEST → candidate BLOCK = 더 엄격 → 악화 아님 (matched)
        runs = (
            self._runs("i1", "control", ["SUGGEST", "SUGGEST", "SUGGEST"]) +
            self._runs("i1", "candidate", ["BLOCK", "BLOCK", "BLOCK"])
        )
        diff = ve.diff_runs(runs)
        self.assertEqual(diff["decision_match_rate_overall"], 1.0)

    def test_majority_vote_per_item(self):
        # candidate 다수결 BLOCK (2/3) vs control BLOCK → matched
        runs = (
            self._runs("i1", "control", ["BLOCK", "BLOCK", "SUGGEST"]) +
            self._runs("i1", "candidate", ["BLOCK", "APPROVE", "BLOCK"])
        )
        diff = ve.diff_runs(runs)
        # control majority=BLOCK(2), candidate majority=BLOCK(2) → not worsened
        self.assertEqual(diff["decision_match_rate_overall"], 1.0)

    def test_mixed_items_partial_rate(self):
        runs = (
            # i1 matched, i2 worsened
            self._runs("i1", "control", ["BLOCK"]) +
            self._runs("i1", "candidate", ["BLOCK"]) +
            self._runs("i2", "control", ["SUGGEST"]) +
            self._runs("i2", "candidate", ["APPROVE"])
        )
        diff = ve.diff_runs(runs)
        self.assertEqual(diff["decision_match_rate_overall"], 0.5)


class TestKnownIssueRecall(unittest.TestCase):
    """② known-issue recall 산식 — 골든 위반을 BLOCK/SUGGEST 로 잡는 run 비율."""

    def _runs(self, item_id, variant, decisions, expected="BLOCK"):
        return [
            ve.Run(item_id=item_id, variant=variant, decision=d,
                   known_issue=True, expected_min_decision=expected)
            for d in decisions
        ]

    def test_partial_recall_block_expected(self):
        # expected_min=BLOCK 일 때 SUGGEST run 은 미달(miss) → partial recall 2/3
        runs = self._runs("k1", "control", ["BLOCK", "BLOCK", "SUGGEST"])
        diff = ve.diff_runs(runs)
        # control: 2/3 BLOCK (catch), 1 SUGGEST (miss) → recall 2/3
        self.assertAlmostEqual(diff["known_issue_recall"]["control"], 2/3)

    def test_suggest_expected_counts_suggest_and_block(self):
        runs = self._runs("k1", "control", ["SUGGEST", "BLOCK", "APPROVE"], expected="SUGGEST")
        # expected_min=SUGGEST → SUGGEST·BLOCK catch, APPROVE miss → 2/3
        diff = ve.diff_runs(runs)
        self.assertAlmostEqual(diff["known_issue_recall"]["control"], 2/3)

    def test_recall_per_variant(self):
        runs = (
            self._runs("k1", "control", ["BLOCK", "BLOCK"]) +
            self._runs("k1", "candidate", ["BLOCK", "APPROVE"])
        )
        diff = ve.diff_runs(runs)
        self.assertEqual(diff["known_issue_recall"]["control"], 1.0)
        self.assertEqual(diff["known_issue_recall"]["candidate"], 0.5)


class TestGate(unittest.TestCase):
    """③ 게이트 PASS/FAIL 경계."""

    def test_pass_when_all_thresholds_met(self):
        diff = {
            "decision_match_rate_overall": 0.95,
            "decision_match_rate_known_issue": 1.0,
            "known_issue_recall": {"control": 0.9, "candidate": 0.9},
        }
        result = ve.gate(diff)
        self.assertTrue(result["passed"])

    def test_fail_overall_below_threshold(self):
        diff = {
            "decision_match_rate_overall": 0.89,  # < 0.9
            "decision_match_rate_known_issue": 1.0,
            "known_issue_recall": {"control": 0.9, "candidate": 0.9},
        }
        result = ve.gate(diff)
        self.assertFalse(result["passed"])
        self.assertIn("overall", " ".join(result["reasons"]))

    def test_fail_known_issue_not_perfect(self):
        diff = {
            "decision_match_rate_overall": 0.95,
            "decision_match_rate_known_issue": 0.99,  # < 1.0
            "known_issue_recall": {"control": 0.9, "candidate": 0.9},
        }
        result = ve.gate(diff)
        self.assertFalse(result["passed"])

    def test_fail_recall_regression(self):
        diff = {
            "decision_match_rate_overall": 0.95,
            "decision_match_rate_known_issue": 1.0,
            "known_issue_recall": {"control": 0.9, "candidate": 0.8},  # 악화
        }
        result = ve.gate(diff)
        self.assertFalse(result["passed"])
        self.assertIn("recall", " ".join(result["reasons"]))

    def test_boundary_exact_threshold_passes(self):
        diff = {
            "decision_match_rate_overall": 0.9,  # 정확히 경계
            "decision_match_rate_known_issue": 1.0,
            "known_issue_recall": {"control": 0.9, "candidate": 0.9},  # 동등 = OK
        }
        result = ve.gate(diff)
        self.assertTrue(result["passed"])

    def test_custom_thresholds(self):
        diff = {
            "decision_match_rate_overall": 0.85,
            "decision_match_rate_known_issue": 1.0,
            "known_issue_recall": {"control": 0.9, "candidate": 0.9},
        }
        result = ve.gate(diff, thresholds={"t_match_overall": 0.8,
                                            "t_match_known_issue": 1.0})
        self.assertTrue(result["passed"])


class TestCorpusLoad(unittest.TestCase):
    """⑤ corpus 로드."""

    def test_load_minimal_corpus(self):
        corpus = {
            "thresholds": {"t_match_overall": 0.9, "t_match_known_issue": 1.0},
            "items": [
                {"id": "arch1", "source": "docs/_archive/x/plan.md",
                 "reviewer": "plan-reviewer", "expected_min_decision": "APPROVE"},
                {"id": "ki_regression", "source_inline": "obs space dtype 변경 plan...",
                 "reviewer": "plan-reviewer", "expected_min_decision": "BLOCK",
                 "known_issue": True},
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "corpus.json"
            p.write_text(json.dumps(corpus), encoding="utf-8")
            loaded = ve.load_corpus(p)
        self.assertEqual(len(loaded.items), 2)
        self.assertEqual(loaded.thresholds["t_match_overall"], 0.9)
        # known_issue default False
        self.assertFalse(loaded.items[0].known_issue)
        self.assertTrue(loaded.items[1].known_issue)

    def test_corpus_requires_items(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "corpus.json"
            p.write_text(json.dumps({"items": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                ve.load_corpus(p)


class TestIngest(unittest.TestCase):
    """결과 jsonl ingest → Run 리스트 (verdict 파싱 위임)."""

    def test_ingest_parses_verdict_text(self):
        lines = [
            {"item_id": "i1", "variant": "control", "run_index": 0,
             "verdict_text": BLOCK_TXT, "known_issue": True,
             "expected_min_decision": "BLOCK"},
            {"item_id": "i1", "variant": "candidate", "run_index": 0,
             "verdict_text": APPROVE_TXT, "known_issue": True,
             "expected_min_decision": "BLOCK"},
        ]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "results.jsonl"
            p.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
            runs = ve.ingest_results(p)
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0].decision, "BLOCK")
        self.assertEqual(runs[1].decision, "APPROVE")
        self.assertTrue(runs[0].known_issue)


class TestReportSafety(unittest.TestCase):
    """산출 리포트에 raw verdict 본문/프롬프트 미포함 (AC7 커밋 안전성)."""

    def test_report_excludes_raw_text(self):
        runs = [
            ve.Run(item_id="i1", variant="control", decision="BLOCK",
                   known_issue=False, expected_min_decision="SUGGEST"),
            ve.Run(item_id="i1", variant="candidate", decision="BLOCK",
                   known_issue=False, expected_min_decision="SUGGEST"),
        ]
        diff = ve.diff_runs(runs)
        report = ve.build_report(diff, ve.gate(diff))
        # decision 라벨·집계 수치만 — raw verdict 문장 미포함
        self.assertNotIn("회귀 위험 미명시", report)
        self.assertIn("decision_match", report)
        self.assertIn("PASS", report.upper())


if __name__ == "__main__":
    unittest.main()
