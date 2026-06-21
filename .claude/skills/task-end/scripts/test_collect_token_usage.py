#!/usr/bin/env python3
"""
test_collect_token_usage.py — collect-token-usage.py 단위테스트.

합성 fixture JSONL 만 사용 (실 transcript 미사용 — 개인정보 회피).
실행: python3 -m unittest test_collect_token_usage -v
      (또는 python3 test_collect_token_usage.py)
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "collect_token_usage", Path(__file__).with_name("collect-token-usage.py")
)
ctu = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ctu)


def _assistant(mid, ts, inp, creation, read, out, sidechain=False, model="claude-test-1"):
    return json.dumps(
        {
            "type": "assistant",
            "timestamp": ts,
            "isSidechain": sidechain,
            "message": {
                "id": mid,
                "model": model,
                "usage": {
                    "input_tokens": inp,
                    "cache_creation_input_tokens": creation,
                    "cache_read_input_tokens": read,
                    "output_tokens": out,
                },
            },
        }
    )


def _noise():
    return json.dumps({"type": "user", "message": {"role": "user", "content": "x"}})


class FixtureBase(unittest.TestCase):
    """메인 1세션 + 서브에이전트 2개 fixture.

    s1.jsonl (메인):
      m1 6/05 — 3중 중복 기록 (스트리밍 누적 재현), 마지막 레코드가 최종값
      m2 6/07 — 단일
      m3 5/20 — since(6/01) 이전 → 필터 제외
    s1/subagents/agent-a.jsonl (qa-verifier):
      a1 6/05 첫 호출 cache_read=0 (cold), a2 6/05 cache_read>0
    s1/subagents/agent-b.jsonl (qa-verifier):
      b1 6/06 첫 호출 cache_read>0 (warm — fixed prefix cross-call hit)
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        s1 = root / "s1.jsonl"
        lines = [
            _noise(),
            # m1 중복 3회 — 처음 2개는 스트리밍 중간값(다른 output), 마지막이 최종
            _assistant("m1", "2026-06-05T10:00:00Z", 100, 1000, 0, 1),
            _assistant("m1", "2026-06-05T10:00:01Z", 100, 1000, 0, 5),
            _assistant("m1", "2026-06-05T10:00:02Z", 100, 1000, 0, 50),
            _assistant("m2", "2026-06-07T10:00:00Z", 200, 0, 1000, 30),
            _assistant("m3", "2026-05-20T10:00:00Z", 999, 999, 999, 999),  # since 이전
        ]
        s1.write_text("\n".join(lines) + "\n", encoding="utf-8")

        sub = root / "s1" / "subagents"
        sub.mkdir(parents=True)
        (sub / "agent-a.jsonl").write_text(
            "\n".join(
                [
                    _assistant("a1", "2026-06-05T11:00:00Z", 100, 1900, 0, 10),  # cold first call
                    _assistant("a2", "2026-06-05T11:00:30Z", 0, 100, 1900, 20),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (sub / "agent-a.meta.json").write_text(
            json.dumps({"agentType": "qa-verifier", "description": "t"}), encoding="utf-8"
        )
        (sub / "agent-b.jsonl").write_text(
            _assistant("b1", "2026-06-06T11:00:00Z", 100, 400, 1500, 10) + "\n",
            encoding="utf-8",
        )
        (sub / "agent-b.meta.json").write_text(
            json.dumps({"agentType": "qa-verifier"}), encoding="utf-8"
        )

        self.result = ctu.collect(root, since="2026-06-01", until=None)

    def tearDown(self):
        self.tmp.cleanup()


class TestDedup(FixtureBase):
    def test_duplicate_message_id_counted_once(self):
        # m1(3중) m2 m3 a1 a2 b1 → unique 6
        self.assertEqual(self.result["dedup"]["unique_api_calls"], 6)

    def test_last_record_wins(self):
        main = next(s for s in self.result["sessions"] if s["session"] == "s1")["main"]
        # m1 최종 output=50 (중간값 1, 5 아님) + m2 output=30
        self.assertEqual(main["output"], 80)
        self.assertEqual(main["calls"], 2)


class TestSinceFilter(FixtureBase):
    def test_may_call_excluded(self):
        self.assertEqual(self.result["dedup"]["in_window_calls"], 5)  # 6 - m3
        main = next(s for s in self.result["sessions"] if s["session"] == "s1")["main"]
        self.assertNotEqual(main["input"], 200 + 999)


class TestMainSubSeparation(FixtureBase):
    def test_subagent_calls_grouped_by_agent_type(self):
        qa = self.result["subagents_by_type"]["qa-verifier"]
        self.assertEqual(qa["calls"], 3)  # a1 a2 b1
        self.assertEqual(qa["agent_invocations"], 2)  # agent 파일 2개

    def test_main_excludes_subagent_tokens(self):
        main = next(s for s in self.result["sessions"] if s["session"] == "s1")["main"]
        self.assertEqual(main["input"], 300)  # m1 100 + m2 200
        self.assertEqual(main["cache_read"], 1000)  # m2 만


class TestHitRate(FixtureBase):
    def test_weighted_hit_rate_formula(self):
        qa = self.result["subagents_by_type"]["qa-verifier"]
        # read 합 = 0+1900+1500 = 3400, denom = (100+1900+0)+(0+100+1900)+(100+400+1500) = 6000
        self.assertAlmostEqual(qa["hit_rate_weighted"], 3400 / 6000, places=4)

    def test_per_call_mean(self):
        qa = self.result["subagents_by_type"]["qa-verifier"]
        rates = [0 / 2000, 1900 / 2000, 1500 / 2000]
        self.assertAlmostEqual(qa["hit_rate_mean_per_call"], sum(rates) / 3, places=4)

    def test_first_call_cache_hit_count(self):
        qa = self.result["subagents_by_type"]["qa-verifier"]
        # agent-a 첫 호출 read=0 (miss), agent-b 첫 호출 read>0 (hit)
        self.assertEqual(qa["first_call_cache_hit"], 1)

    def test_cost_savings_estimate(self):
        qa = self.result["subagents_by_type"]["qa-verifier"]
        baseline = 6000
        actual = (100 + 0 + 100) + 1.25 * (1900 + 100 + 400) + 0.1 * 3400
        self.assertAlmostEqual(qa["est_input_cost_savings_vs_nocache"], 1 - actual / baseline, places=4)


class TestOutputSafety(FixtureBase):
    def test_no_raw_text_fields(self):
        dumped = json.dumps(self.result, ensure_ascii=False)
        # fixture 의 메시지 본문 내용("x")이나 content/prompt 키가 결과에 없어야 함
        self.assertNotIn('"content"', dumped)
        self.assertNotIn('"prompt"', dumped)
        self.assertNotIn('"text"', dumped)


class TestModeAttribution(unittest.TestCase):
    def test_unattributed_when_no_plan_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "s9.jsonl").write_text(
                _assistant("z1", "2026-06-05T10:00:00Z", 10, 0, 0, 1) + "\n", encoding="utf-8"
            )
            result = ctu.collect(root, since="2026-06-01", until=None)
            self.assertEqual(result["sessions"][0]["mode"], "unattributed")

    def test_slug_extracted_from_plan_path_mention(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            line = _assistant("z2", "2026-06-05T10:00:00Z", 10, 0, 0, 1)
            mention = json.dumps(
                {"type": "user", "message": {"content": "docs/_active/foo-bar/plan.md 참조"}}
            )
            (root / "s9.jsonl").write_text(line + "\n" + mention + "\n", encoding="utf-8")
            self.assertEqual(ctu.attribute_task_slug(root / "s9.jsonl"), "foo-bar")


if __name__ == "__main__":
    unittest.main(verbosity=2)
