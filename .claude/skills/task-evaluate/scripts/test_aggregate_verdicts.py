#!/usr/bin/env python3
"""
domain: lifecycle
test_aggregate_verdicts — 3-tier fallback 단위 테스트.

6 케이스 (Acceptance 1:1):
1. Tier 1: 정상 마지막 줄 "APPROVE"
2. Tier 1: 정상 마지막 줄 "BLOCK: scope: ..."
3. Tier 2: 본문 중간 "SUGGEST: scope: ..." 만
4. Tier 3: 본문에 "APPROVE" 단어만 (heuristic)
5. Tier 3: "BLOCK" + "APPROVE" 동시 — 보수적 (BLOCK 우선)
6. 진짜 빈 본문 → MALFORMED
"""
import importlib.util
import os
import sys
import unittest

# aggregate-verdicts.py 는 hyphen 포함 → importlib 필요
_AGG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aggregate-verdicts.py")
spec = importlib.util.spec_from_file_location("aggregate_verdicts", _AGG_PATH)
agg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agg)


class TestThreeTierFallback(unittest.TestCase):
    def test_tier1_approve_last_line(self):
        text = "분석 본문입니다.\nAPPROVE"
        verdicts = agg.parse_verdicts(text, agent_name="test")
        self.assertEqual(len(verdicts), 1)
        self.assertEqual(verdicts[0]["kind"], "APPROVE")

    def test_tier1_block_with_axis_message(self):
        text = "BLOCK: scope: scope_paths 누락"
        verdicts = agg.parse_verdicts(text, agent_name="test")
        self.assertEqual(len(verdicts), 1)
        self.assertEqual(verdicts[0]["kind"], "BLOCK")
        self.assertEqual(verdicts[0]["axis"], "scope")

    def test_tier2_multiline_only_suggest(self):
        # 마지막 줄이 verdict 형식 아니지만 본문 중간에 SUGGEST 라인 있음
        text = (
            "분석 본문\n"
            "SUGGEST: scope: 일부 누락\n"
            "추가 설명...\n"
            "본문 끝 (verdict 형식 아님)"
        )
        verdicts = agg.parse_verdicts(text, agent_name="test")
        # 현재 parse_verdicts 는 줄별 매칭이므로 multiline tier 자연 처리
        self.assertEqual(len(verdicts), 1)
        self.assertEqual(verdicts[0]["kind"], "SUGGEST")

    def test_tier3_keyword_approve_only(self):
        # verdict 형식 0건 → 키워드 휴리스틱
        text = "분석 결과 plan 은 잘 작성되었습니다. APPROVE 권장."
        verdicts = agg.parse_verdicts_with_fallback(text, agent_name="test")
        self.assertEqual(len(verdicts), 1)
        self.assertEqual(verdicts[0]["kind"], "APPROVE")
        self.assertEqual(verdicts[0].get("source"), "heuristic")

    def test_tier3_keyword_block_priority_over_approve(self):
        # BLOCK + APPROVE 동시 등장 — 보수적으로 BLOCK 우선
        text = "이 부분은 APPROVE 가능하나 다른 부분은 BLOCK 필요."
        verdicts = agg.parse_verdicts_with_fallback(text, agent_name="test")
        self.assertEqual(len(verdicts), 1)
        self.assertEqual(verdicts[0]["kind"], "BLOCK")
        self.assertEqual(verdicts[0].get("source"), "heuristic")

    def test_truly_empty_returns_malformed(self):
        text = ""
        verdicts = agg.parse_verdicts_with_fallback(text, agent_name="test")
        self.assertEqual(verdicts, [])


if __name__ == "__main__":
    unittest.main()
