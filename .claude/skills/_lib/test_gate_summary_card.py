#!/usr/bin/env python3
"""
domain: lifecycle
test_gate_summary_card — gate_summary_card 단위 테스트.

실행: python3 .claude/skills/_lib/test_gate_summary_card.py
"""
import unittest

from gate_summary_card import (
    build_end_card,
    build_g1_card,
    extract_acceptance,
    parse_frontmatter,
    MAX_TABLE_ROWS,
)

PLAN = """\
---
slug: gate-summary-card
initiative: harness-stabilization
status: active
domains: [lifecycle]
scope_paths:
  - .claude/rules/80-task-lifecycle.md
---

# Gate Summary Card
본문.
"""

QA = """\
# QA 체크리스트

## Acceptance (G1 freeze)

- [ ] AC1 rules/80 §H 신설
- [ ] AC2 helper + 단위테스트 green
- [ ] AC3 task-evaluate 가 G1 카드 제시

## Pass 기준
- 단위테스트 green
"""

ROWS = [{"domain": "lifecycle", "sub": "§H 신설", "impact": "1 file"}]


class TestParse(unittest.TestCase):
    def test_frontmatter(self):
        fm = parse_frontmatter(PLAN)
        self.assertEqual(fm["slug"], "gate-summary-card")
        self.assertEqual(fm["initiative"], "harness-stabilization")
        self.assertEqual(fm["domains"], ["lifecycle"])

    def test_frontmatter_null_initiative(self):
        fm = parse_frontmatter("---\nslug: x\ninitiative: null\ndomains: [ds]\n---\n")
        self.assertIsNone(fm["initiative"])

    def test_extract_acceptance(self):
        acs = extract_acceptance(QA)
        self.assertEqual(len(acs), 3)
        self.assertEqual(acs[0]["id"], "AC1")
        self.assertIn("§H", acs[0]["text"])
        self.assertFalse(acs[0]["checked"])

    def test_acceptance_only_from_section(self):
        # 'Pass 기준' 섹션의 '- 단위테스트' 는 체크박스 아님 → 제외
        acs = extract_acceptance(QA)
        self.assertTrue(all(a["id"].startswith("AC") for a in acs))


class TestG1Card(unittest.TestCase):
    def setUp(self):
        self.card = build_g1_card(PLAN, QA, "acceptance freeze + 구현 시작", ROWS)

    def test_five_blocks_present(self):
        c = self.card
        self.assertIn("## 🚦 G1 승인 요청", c)        # 블록1 헤더 앵커
        self.assertIn("**승인 대상**", c)              # 블록2
        self.assertIn("| 대분류(도메인) | 소분류 | 영향 |", c)  # 블록3 표
        self.assertIn("🔒 freeze 될 Acceptance", c)    # 블록4 주인공
        self.assertIn("[1] GO", c)                     # 블록5 옵션

    def test_freeze_lists_all_acceptance_unchecked(self):
        for ac in ("AC1", "AC2", "AC3"):
            self.assertIn(f"- [ ] {ac}", self.card)

    def test_yes_line_echoed(self):
        self.assertIn("acceptance freeze + 구현 시작", self.card)


class TestEndCard(unittest.TestCase):
    def test_one_to_one_correspondence(self):
        results = {"AC1": "pass", "AC2": "pass", "AC3": "unverified"}
        card = build_end_card(PLAN, QA, ROWS, results)
        self.assertIn("## ✅ task-end 승인 요청", card)
        self.assertIn("Acceptance 결과", card)
        self.assertIn("- [x] AC1", card)
        self.assertIn("✅", card)
        self.assertIn("- [ ] AC3", card)
        self.assertIn("⚠️ 미검증", card)
        self.assertIn("[1] 종료", card)

    def test_missing_result_flagged(self):
        # AC3 결과 미지정 → 미검증 + 경고
        card = build_end_card(PLAN, QA, ROWS, {"AC1": "pass", "AC2": "pass"})
        self.assertIn("결과 미지정", card)
        self.assertIn("AC3", card)

    def test_fail_status(self):
        card = build_end_card(PLAN, QA, ROWS, {"AC1": "fail", "AC2": "pass", "AC3": "pass"})
        self.assertIn("❌ 실패", card)


class TestEndCardProposals(unittest.TestCase):
    PENDING = [
        {"id": "foo-guard", "summary": "빈틈 A", "proposal": "hook 추가"},
        {"id": "bar-rule", "summary": "빈틈 B", "proposal": "rule 보강"},
    ]

    def test_no_regression_when_no_pending(self):
        # pending None/빈 → 블록 생략, 기존 동작 동일
        card_none = build_end_card(PLAN, QA, ROWS, {"AC1": "pass"}, None)
        card_empty = build_end_card(PLAN, QA, ROWS, {"AC1": "pass"}, [])
        self.assertNotIn("제안된 개선", card_none)
        self.assertEqual(card_none, card_empty)

    def test_proposals_block_rendered(self):
        card = build_end_card(PLAN, QA, ROWS, {"AC1": "pass"}, self.PENDING)
        self.assertIn("🔁 제안된 개선 2건", card)
        self.assertIn("`foo-guard`", card)
        self.assertIn("hook 추가", card)
        self.assertIn("[seed] task 로", card)

    def test_proposals_appear_before_options(self):
        card = build_end_card(PLAN, QA, ROWS, {"AC1": "pass"}, self.PENDING)
        self.assertLess(card.index("제안된 개선"), card.index("**종료?**"))


class TestTableCap(unittest.TestCase):
    def test_table_row_cap(self):
        rows = [{"domain": "lifecycle", "sub": f"s{i}", "impact": "x"} for i in range(8)]
        card = build_g1_card(PLAN, QA, "x", rows)
        self.assertIn(f"외 {8 - MAX_TABLE_ROWS}건", card)
        # 표 데이터 행은 MAX_TABLE_ROWS + 오버플로 1행
        body_rows = [ln for ln in card.splitlines() if ln.startswith("| lifecycle")]
        self.assertEqual(len(body_rows), MAX_TABLE_ROWS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
